import uuid
import shutil
import csv
import io
import os
import json
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # Load from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analyzers.gemini_form_analyzer import GeminiFormAnalyzer
from .analyzers.user_image_analyzer import UserImageAnalyzer

from .clerk_auth import require_clerk_user
from .user_plans import save_user_plan, list_user_plans

# ✅ DB helper
from .db import get_conn

# ✅ editable copy creator
from .editable_plans import (
    ensure_editable_copy,
    update_day_title,
    add_day_item,
    update_day_item,
    delete_day_item,
    reorder_day_items,
)

# ✅ Custom workouts
from . import custom_workouts_api

# ✅ Database migrations
from .migrations import run_migrations

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

OUTPUTS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Load API key - prioritize .env file to override old system environment variables  
import dotenv
# Force reload of .env file
dotenv_path = Path(__file__).parent.parent / '.env'
if dotenv_path.exists():
    from dotenv import dotenv_values
    env_vars = dotenv_values(str(dotenv_path))
    GEMINI_API_KEY = env_vars.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
else:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

print(f"[STARTUP] Using GEMINI_API_KEY: {GEMINI_API_KEY[:20]}...")  # Show first 20 chars

app = FastAPI(title="SculpFit Web API")

# CORS: Only allow your domain (set via environment variable)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint for Railway (no auth required)"""
    import os
    return {
        "status": "ok",
        "db_host": os.getenv("DB_HOST", "not set"),
        "db_user": os.getenv("DB_USER", "not set"),
        "db_name": os.getenv("DB_NAME", "not set"),
        "db_port": os.getenv("DB_PORT", "not set"),
        "db_pass_set": bool(os.getenv("DB_PASS")),
    }

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


def current_user(request: Request):
    return require_clerk_user(request)


# Register custom workout routes
custom_workouts_api.register_custom_workout_routes(app, current_user)

# Register workout logging routes
from . import workout_logging_api
workout_logging_api.register_workout_logging_routes(app, current_user)


# Run database migrations on startup
@app.on_event("startup")
async def startup_event():
    """Run database migrations on app startup"""
    try:
        run_migrations()
    except Exception as e:
        print(f"[STARTUP] Migration error (non-fatal): {e}")


def _fallback_video_probe(path: Path):
    """
    Lightweight probe to verify the file is readable by OpenCV and return basic metadata.
    Used as a graceful fallback if analyzers fail (e.g., missing MediaPipe resources).
    """
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"OpenCV cannot open video at {path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0.0
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0.0
    cap.release()

    duration = frames / fps if fps else 0.0
    return {
        "fps": round(fps, 2),
        "frames": int(frames),
        "duration_sec": round(duration, 2),
        "width": int(width),
        "height": int(height),
    }


class DayTitlePatch(BaseModel):
    title: str


class AddItemBody(BaseModel):
    exercise_name: str
    muscle_group: str | None = None
    sets: int = 3
    reps: str = "8-12"
    rest_seconds: int = 60


class ItemPatchBody(BaseModel):
    exercise_name: str | None = None
    muscle_group: str | None = None
    sets: int | None = None
    reps: str | None = None
    rest_seconds: int | None = None
    notes: str | None = None


class ReorderBody(BaseModel):
    ordered_item_ids: list[int]


@app.get("/")
def home():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"ok": True, "note": "index.html not found in backend/static"}


@app.get("/signin")
def signin():
    """Serve the Clerk sign-in page"""
    signin_path = STATIC_DIR / "signin.html"
    if signin_path.exists():
        return FileResponse(signin_path)
    return {"ok": True, "note": "signin.html not found in backend/static"}


@app.get("/health")
def health():
    return {"ok": True}



@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "message": "API is running"}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return {"success": True, "clerk_user_id": user["clerk_user_id"]}


@app.get("/api/available-plans")
def available_plans(days: int = None):
    """
    Get all available workout plans.
    Optional query param: days=3 or days=5 to filter by workout days.
    
    Returns plans grouped by days_per_week, or filtered if days param provided.
    """
    try:
        if days and days not in (3, 5):
            return JSONResponse(status_code=400, content={
                "success": False, 
                "error": "Invalid days value. Must be 3 or 5."
            })
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                if days:
                    cur.execute("SELECT id, name, days_per_week, primary_focus FROM workout_plans WHERE days_per_week = %s ORDER BY id ASC;", (days,))
                else:
                    cur.execute("SELECT id, name, days_per_week, primary_focus FROM workout_plans ORDER BY days_per_week ASC, id ASC;")
                rows = cur.fetchall()
        
        # Group by days_per_week
        plans = {}
        for row in rows:
            day_count = str(row["days_per_week"])
            if day_count not in plans:
                plans[day_count] = []
            plans[day_count].append({
                "id": row["id"],
                "name": row["name"],
                "days_per_week": row["days_per_week"],
                "primary_focus": row["primary_focus"]
            })
        
        return {"success": True, "plans": plans}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/plans/{plan_id}")
def get_plan_details(plan_id: int):
    """
    Get details of a specific available plan (without saving).
    Returns the plan with all its exercises organized by day.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get plan metadata
                cur.execute(
                    "SELECT id, name, days_per_week, primary_focus FROM workout_plans WHERE id = %s LIMIT 1;",
                    (plan_id,)
                )
                plan = cur.fetchone()
                
                if not plan:
                    return JSONResponse(status_code=404, content={
                        "success": False,
                        "error": f"Plan {plan_id} not found"
                    })
                
                # Get exercises for pre-built plans using plan_exercises
                cur.execute(
                    """
                    SELECT pe.day_number as day, ex.name as exercise, ex.primary_muscle, 
                           pe.sets, pe.reps, pe.rest_seconds
                    FROM plan_exercises pe
                    LEFT JOIN exercises ex ON pe.exercise_id = ex.id
                    WHERE pe.plan_id = %s
                    ORDER BY pe.day_number ASC, pe.position ASC;
                    """,
                    (plan_id,)
                )
                exercises_raw = cur.fetchall()
                
                # Organize into days with items
                days_dict = {}
                for row in exercises_raw:
                    day_num = row.get("day")
                    if day_num not in days_dict:
                        days_dict[day_num] = {"day": day_num, "items": []}
                    
                    # Only add item if exercise exists (not NULL)
                    if row.get("exercise"):
                        days_dict[day_num]["items"].append({
                            "exercise": row.get("exercise"),
                            "muscle_group": row.get("primary_muscle"),
                            "sets": row.get("sets"),
                            "reps": row.get("reps"),
                            "rest_seconds": row.get("rest_seconds")
                        })
                
                days = sorted(days_dict.values(), key=lambda x: x["day"])
                
                return {
                    "success": True,
                    "plan": {
                        "id": plan["id"],
                        "name": plan["name"],
                        "primary_focus": plan["primary_focus"],
                        "days_per_week": plan["days_per_week"]
                    },
                    "days": days
                }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/select-plan")
async def select_plan(
    plan_id: int = Form(...),
    user=Depends(current_user),
):
    """
    User selects a predefined workout plan.
    Creates a saved plan without requiring image analysis first.
    """
    try:
        from .user_plans import save_user_plan
        from .editable_plans import ensure_editable_copy
        
        # Verify plan exists
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, days_per_week, primary_focus FROM workout_plans WHERE id = %s LIMIT 1;", (plan_id,))
                selected_plan = cur.fetchone()
        
        if not selected_plan:
            return JSONResponse(status_code=404, content={
                "success": False,
                "error": "Plan not found"
            })
        
        # Save the plan for this user
        saved_id = save_user_plan(
            clerk_user_id=user["clerk_user_id"],
            plan_id=plan_id,
            body_type=f"{selected_plan['days_per_week']}-day {selected_plan['primary_focus'].title()}",
            focus_areas=[selected_plan["primary_focus"]],
        )
        
        # Create editable copy
        ensure_editable_copy(saved_id, user["clerk_user_id"])
        
        return {
            "success": True,
            "saved_id": saved_id,
            "plan": selected_plan,
            "message": f"Selected {selected_plan['name']}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    consent: bool = Form(...),
    plan_days: str = Form(default="3"),
    user=Depends(current_user),
):
    try:
        if not consent:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Consent required to analyze image."},
            )

        # Validate and convert plan_days
        try:
            plan_days = int(plan_days)
        except (ValueError, TypeError):
            plan_days = 3
        
        if plan_days not in (3, 5):
            plan_days = 3

        print(f"[analyze_image] plan_days selected: {plan_days}")
        print(f"[analyze_image] Using API Key: {GEMINI_API_KEY}")

        # Read file into memory as BytesIO
        file_bytes = await file.read()
        image_file = io.BytesIO(file_bytes)
        print(f"[analyze_image] Loaded image into memory: {len(file_bytes)} bytes")

        analyzer = UserImageAnalyzer(
            image_path=None,
            image_bytes=image_file,
            api_key=GEMINI_API_KEY,
        )

        report = analyzer.analyze()
        result = report.get("result", {})
        focus_areas = result.get("focus_areas", [])
        body_type = result.get("body_type")

        print(f"[analyze_image] focus_areas: {focus_areas}")
        print(f"[analyze_image] body_type: {body_type}")

        # Note: Old endpoint - not currently used (uses /api/analyze-image-v2 instead)
        # This can be deprecated in future versions
        
        saved_id = None
        plan_body_type = None
        plan_name = None

        # Return deprecated endpoint response
        db_plan_id = None
        if False:  # This entire block is deprecated
            plan_info = matched.get("plan")
            focus_area = plan_info.get("primary_focus") if isinstance(plan_info, dict) else str(plan_info)
            plan_name = plan_info.get("name") if isinstance(plan_info, dict) else None
            plan_body_type = plan_info.get("body_type") if isinstance(plan_info, dict) else None

        return {
            "success": True,
            "type": "image",
            "plan_days_selected": plan_days,
            "detected_body_type": body_type,
            "selected_plan_body_type": plan_body_type,
            "selected_plan_name": plan_name,
            "saved_id": saved_id,
            "deprecated": "This endpoint is deprecated. Use /api/analyze-image-v2 instead",
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/analyze-image-v2")
async def analyze_image_v2(
    file: UploadFile = File(...),
    difficulty: str = Form(default="intermediate"),
    daysPerWeek: str = Form(default="4"),
    consent: bool = Form(default=True),
    user=Depends(current_user),
):
    """
    Simplified endpoint: Get complete workout from Gemini
    - Analyze image with Gemini Vision
    - Get body type + primary focus
    - Gemini generates complete 4-day personalized workout plan
    - Save plan to database
    """
    try:
        # Validate difficulty
        if difficulty not in ("beginner", "intermediate", "advanced"):
            difficulty = "intermediate"
        
        print(f"[analyze_image_v2] difficulty: {difficulty}, consent: {consent}")
        
        # Read file into memory as BytesIO (never save to disk)
        file_bytes = await file.read()
        image_file = io.BytesIO(file_bytes)
        print(f"[analyze_image_v2] Loaded image into memory: {len(file_bytes)} bytes")

        # Use Gemini to analyze image and generate complete workout
        analyzer = UserImageAnalyzer(
            image_path=None,
            image_bytes=image_file,
            api_key=GEMINI_API_KEY,
            difficulty=difficulty,
            days_per_week=int(daysPerWeek),
        )
        report = analyzer.analyze()
        result = report.get("result", {})
        
        print(f"[analyze_image_v2] Full result keys: {result.keys()}")
        print(f"[analyze_image_v2] Result: {json.dumps(result, indent=2)[:500]}")
        
        body_type = result.get("body_type", "mesomorph")
        primary_focus = result.get("primary_focus", "chest")
        secondary_focuses = result.get("secondary_focuses", ["back", "shoulders"])
        rationale = result.get("rationale", "")
        
        # Get the complete workout plan from Gemini (should be in result)
        workout_plan = result.get("workout_plan", {})

        print(f"[analyze_image_v2] Gemini analysis:")
        print(f"  body_type: {body_type}")
        print(f"  primary_focus: {primary_focus}")
        print(f"  secondary_focuses: {secondary_focuses}")
        print(f"  difficulty: {difficulty}")
        print(f"  Generated plan with {len(workout_plan.get('days', []))} days")
        
        # Save plan to database
        if user and user.get('clerk_user_id'):
            clerk_user_id = user['clerk_user_id']
            print(f"[analyze_image_v2] Saving plan for user: {clerk_user_id}")
            
            plan_name = f"{body_type.capitalize()} - {primary_focus.capitalize()} ({difficulty})"
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        # Insert plan to USER plans (not shared plans)
                        cur.execute(
                            """INSERT INTO user_workout_plans (clerk_user_id, name, days_per_week, primary_focus)
                               VALUES (%s, %s, %s, %s)""",
                            (clerk_user_id, plan_name, len(workout_plan.get('days', [])), primary_focus)
                        )
                        user_plan_id = int(cur.lastrowid)
                        
                        # Insert days and exercises
                        days = workout_plan.get('days', [])
                        for day_obj in days:
                            day_num = day_obj.get('day', 0)
                            day_focus = day_obj.get('focus', '')
                            
                            cur.execute(
                                """INSERT INTO user_workout_days (user_plan_id, day_number, title)
                                   VALUES (%s, %s, %s)""",
                                (user_plan_id, day_num, day_focus)
                            )
                            day_id = int(cur.lastrowid)
                            
                            # Insert exercises for this day
                            exercises = day_obj.get('exercises', [])
                            for idx, ex in enumerate(exercises, 1):
                                ex_name = ex.get('name', '')
                                # Look up or create exercise
                                cur.execute("SELECT id FROM exercises WHERE name = %s LIMIT 1", (ex_name,))
                                ex_row = cur.fetchone()
                                if ex_row:
                                    exercise_id = ex_row['id']
                                else:
                                    # Create new exercise if it doesn't exist
                                    cur.execute(
                                        """INSERT INTO exercises (name, primary_muscle, difficulty)
                                           VALUES (%s, %s, %s)""",
                                        (ex_name, ex.get('primary_muscle', 'chest'), difficulty)
                                    )
                                    exercise_id = int(cur.lastrowid)
                                
                                cur.execute(
                                    """INSERT INTO user_workout_day_items 
                                       (user_day_id, exercise_id, sets, reps, rest_seconds, position)
                                       VALUES (%s, %s, %s, %s, %s, %s)""",
                                    (day_id, exercise_id, ex.get('sets', 3), ex.get('reps', '6-12'), 
                                     ex.get('rest_seconds', 90), idx)
                                )
                        
                        print(f"[analyze_image_v2] Plan saved with ID: {user_plan_id} with {len(days)} days and {sum(len(d.get('exercises', [])) for d in days)} exercises")
            except Exception as save_error:
                print(f"[analyze_image_v2] Error saving plan: {save_error}")
                import traceback
                traceback.print_exc()

        # Return full analysis data regardless of save success
        return {
            "success": True,
            "type": "image_v2",
            "body_type": body_type,
            "primary_focus": primary_focus,
            "secondary_focuses": secondary_focuses,
            "difficulty": difficulty,
            "rationale": rationale,
            "workout_plan": workout_plan,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans")
def my_plans(user=Depends(current_user)):
    items = list_user_plans(user["clerk_user_id"])
    return {"success": True, "items": items}


def _get_editable_payload(saved_id: str, clerk_user_id: str):
    """
    Force correct payload shape:
      days[]: { day_id, day, title, items: [{ item_id, exercise, sets, reps, rest_seconds, ...}] }
    Handles both custom workouts and user_workout_plans
    
    saved_id is composite: 'custom_123', 'ai_456', 'saved_789'
    """
    
    # Parse the composite ID
    if saved_id.startswith('custom_'):
        plan_type = 'custom'
        actual_id = int(saved_id.split('_')[1])
    elif saved_id.startswith('ai_'):
        plan_type = 'ai'
        actual_id = int(saved_id.split('_')[1])
    elif saved_id.startswith('saved_'):
        plan_type = 'saved'
        actual_id = int(saved_id.split('_')[1])
    else:
        # Fallback for backward compatibility
        plan_type = 'ai'
        actual_id = int(saved_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Handle custom workout
            if plan_type == 'custom':
                cur.execute(
                    """
                    SELECT id, name, days_per_week, name as primary_focus
                    FROM custom_workouts
                    WHERE id=%s AND clerk_user_id=%s
                    LIMIT 1;
                    """,
                    (actual_id, clerk_user_id),
                )
                plan = cur.fetchone()
                if not plan:
                    raise ValueError("Custom workout not found")
                
                cur.execute(
                    """
                    SELECT id, day_number, title
                    FROM custom_workout_days
                    WHERE custom_workout_id=%s
                    ORDER BY day_number ASC;
                    """,
                    (actual_id,),
                )
                days = cur.fetchall()

                out_days = []
                for d in days:
                    day_id = int(d["id"])
                    cur.execute(
                        """
                        SELECT cwe.id AS item_id,
                               cwe.exercise_name AS exercise,
                               cwe.sets, cwe.reps, cwe.rest_seconds, cwe.position, cwe.notes
                        FROM custom_workout_exercises cwe
                        WHERE cwe.custom_day_id=%s
                        ORDER BY cwe.position ASC;
                        """,
                        (day_id,),
                    )
                    items = cur.fetchall()

                    out_days.append(
                        {
                            "day_id": day_id,
                            "day": int(d["day_number"]),
                            "title": d.get("title") or "",
                            "items": items,
                        }
                    )

                return {"plan": plan, "days": out_days}
            
            # Otherwise, handle regular user plan (ai or saved)
            user_plan_id = ensure_editable_copy(actual_id, clerk_user_id)

            cur.execute(
                """
                SELECT id, name, days_per_week, primary_focus
                FROM user_workout_plans
                WHERE id=%s AND clerk_user_id=%s
                LIMIT 1;
                """,
                (user_plan_id, clerk_user_id),
            )
            plan = cur.fetchone()
            if not plan:
                raise ValueError("User plan not found")

            cur.execute(
                """
                SELECT id, day_number, title
                FROM user_workout_days
                WHERE user_plan_id=%s
                ORDER BY day_number ASC;
                """,
                (user_plan_id,),
            )
            days = cur.fetchall()

            out_days = []
            for d in days:
                day_id = int(d["id"])
                cur.execute(
                    """
                    SELECT uwdi.id AS item_id,
                           e.name AS exercise,
                           e.primary_muscle,
                           uwdi.sets, uwdi.reps, uwdi.rest_seconds, uwdi.position, uwdi.notes
                    FROM user_workout_day_items uwdi
                    JOIN exercises e ON e.id = uwdi.exercise_id
                    WHERE uwdi.user_day_id=%s
                    ORDER BY uwdi.position ASC;
                    """,
                    (day_id,),
                )
                items = cur.fetchall()

                out_days.append(
                    {
                        "day_id": day_id,
                        "day": int(d["day_number"]),
                        "title": d.get("title") or "",
                        "items": items,
                    }
                )

            return {"plan": plan, "days": out_days}


@app.delete("/api/my-plans/{saved_id}")
def delete_plan(saved_id: str, user=Depends(current_user)):
    """Delete a saved plan by composite ID (user-owned only)."""
    try:
        from .user_plans import delete_user_plan
        deleted = delete_user_plan(saved_id, user["clerk_user_id"])
        if not deleted:
            return JSONResponse(status_code=404, content={"success": False, "error": "Plan not found"})
        return {"success": True, "message": "Plan deleted"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans/{saved_id}/editable")
def my_plan_editable(saved_id: str, user=Depends(current_user)):
    try:
        data = _get_editable_payload(saved_id, user["clerk_user_id"])
        return {"success": True, **data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans/{saved_id}")
def my_plan_detail(saved_id: str, user=Depends(current_user)):
    try:
        data = _get_editable_payload(saved_id, user["clerk_user_id"])
        return {"success": True, **data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


# =========================
# Editable endpoints
# =========================

@app.patch("/api/edit/days/{user_day_id}")
def edit_day_title(user_day_id: int, body: DayTitlePatch, user=Depends(current_user)):
    try:
        update_day_title(user_day_id, user["clerk_user_id"], body.title)
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/edit/days/{user_day_id}/items")
def add_item(user_day_id: int, body: AddItemBody, user=Depends(current_user)):
    try:
        item_id = add_day_item(
            user_day_id,
            user["clerk_user_id"],
            exercise_name=body.exercise_name,
            muscle_group=body.muscle_group,
            sets=body.sets,
            reps=body.reps,
            rest_seconds=body.rest_seconds,
        )
        return {"success": True, "item_id": item_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.patch("/api/edit/items/{item_id}")
def patch_item(item_id: int, body: ItemPatchBody, user=Depends(current_user)):
    try:
        update_day_item(item_id, user["clerk_user_id"], body.model_dump())
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.delete("/api/edit/items/{item_id}")
def remove_item(item_id: int, user=Depends(current_user)):
    try:
        delete_day_item(item_id, user["clerk_user_id"])
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.patch("/api/edit/days/{user_day_id}/reorder")
def reorder_items(user_day_id: int, body: ReorderBody, user=Depends(current_user)):
    try:
        reorder_day_items(user_day_id, user["clerk_user_id"], body.ordered_item_ids)
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/analyze-video")
async def analyze_video(
    exercise: str = Form(...),
    file: UploadFile = File(...),
    start_time: float = Form(None),  # Optional start time in seconds
    end_time: float = Form(None),    # Optional end time in seconds
    rep_count: int = Form(None),     # Optional number of reps
    user=Depends(current_user),
):
    """
    Analyze exercise form using Gemini Vision.
    Supports any exercise type - squats, pushups, lateral raises, deadlifts, etc.
    Extracts key frames and provides detailed feedback.
    Can analyze specific time range and distribute frames across reps.
    """
    try:
        # Read file into memory as BytesIO (never save to disk)
        file_bytes = await file.read()
        video_file = io.BytesIO(file_bytes)
        print(f"[analyze_video] Loaded video into memory: {len(file_bytes)} bytes for exercise={exercise}")
        
        time_range_str = f" (time: {start_time or 'start'}-{end_time or 'end'}s)" if start_time or end_time else ""
        rep_str = f" ({rep_count} reps)" if rep_count else ""

        # Use Gemini for universal form analysis with optional time range and rep count
        print(f"[analyze_video] starting Gemini analysis for {exercise}{time_range_str}{rep_str}")
        # Frame count depends on rep count (min 3, max equal to reps)
        rep_count_int = int(rep_count) if rep_count else None
        num_frames = max(3, min(rep_count_int, 7)) if rep_count_int else 7
        print(f"[analyze_video] rep_count={rep_count_int}, num_frames={num_frames}")
        analyzer = GeminiFormAnalyzer(
            video_bytes=video_file,
            api_key=GEMINI_API_KEY, 
            num_frames=num_frames,  # Extract frames based on rep count
            start_time=start_time,
            end_time=end_time,
            rep_count=rep_count_int
        )
        report = analyzer.analyze(exercise=exercise)
        
        print(f"[analyze_video] completed analysis: {report}")
        
        # If analyzer returned an error, pass it through
        if not report.get("success", False):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "error": report.get("error", "Unknown error during analysis"),
                    "type": "gemini_analysis",
                }
            )

        return {
            "success": True,
            "type": "gemini_analysis",
            "exercise": exercise,
            "feedback": report.get("feedback", "No feedback available"),
            "raw_response": report.get("raw_response", ""),
            "num_frames_analyzed": report.get("num_frames_analyzed", 0),
            "detected_reps": report.get("detected_reps", None),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[analyze_video] error: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "error": str(e),
                "exercise": locals().get("exercise", None),
            },
        )


@app.websocket("/ws/analyze-video/{video_id}")
async def websocket_analyze_video(websocket: WebSocket, video_id: str):
    """
    WebSocket endpoint for real-time video analysis with live rep counting.
    """
    await websocket.accept()
    print(f"[WebSocket] Client connected for video_id: {video_id}")
    
    # Get parameters from query string
    exercise = websocket.query_params.get('exercise', 'squats')
    rep_count_str = websocket.query_params.get('rep_count')
    start_time_str = websocket.query_params.get('start_time')
    end_time_str = websocket.query_params.get('end_time')
    
    # Parse optional parameters
    rep_count = int(rep_count_str) if rep_count_str else None
    start_time = float(start_time_str) if start_time_str else None
    end_time = float(end_time_str) if end_time_str else None
    
    print(f"[WebSocket] Exercise: {exercise}, Rep count: {rep_count}, Time range: {start_time}-{end_time}")
    
    try:
        # Find the uploaded video file
        video_path = None
        for ext in ['.mp4', '.avi', '.mov', '.webm']:
            candidate_path = UPLOADS_DIR / f"{video_id}{ext}"
            if candidate_path.exists():
                video_path = candidate_path
                print(f"[WebSocket] Found video file: {video_path}")
                break
        
        if not video_path:
            error_msg = f"Video file not found: {video_id}"
            print(f"[WebSocket] {error_msg}")
            await websocket.send_json({
                "type": "error",
                "message": error_msg
            })
            return
        
        # Initialize analyzer with streaming and user parameters
        print(f"[WebSocket] Starting analysis for {video_path}")
        num_frames = max(3, min(rep_count, 7)) if rep_count else 7
        analyzer = GeminiFormAnalyzer(
            str(video_path), 
            api_key=GEMINI_API_KEY, 
            num_frames=num_frames,
            start_time=start_time,
            end_time=end_time,
            rep_count=rep_count
        )
        
        # Get the Gemini analysis
        print(f"[WebSocket] Getting Gemini analysis for {exercise}...")
        report = analyzer.analyze(exercise=exercise)

        # Send completion message with full analysis
        completion_data = {
            "type": "analysis_complete",
            "feedback": report.get("feedback", ""),
            "raw_response": report.get("raw_response", ""),
            "num_frames_analyzed": report.get("num_frames_analyzed", 0),
            "exercise": exercise
        }
        print(f"[WebSocket] Analysis complete: {completion_data}")
        await websocket.send_json(completion_data)
        
    except Exception as e:
        await websocket.send_json({
            "type": "error", 
            "message": str(e)
        })
    finally:
        await websocket.close()


@app.get("/api/my-plans/{saved_id}/export-csv")
async def export_plan_csv(
    saved_id: str,
    user=Depends(current_user),
):
    """
    Export a user's saved workout plan, AI-generated plan, or custom workout as a branded CSV file.
    Downloads a CSV with plan name, exercises, and formatting.
    
    saved_id is composite: 'custom_123', 'ai_456', 'saved_789'
    """
    try:
        # Parse the composite ID
        if saved_id.startswith('custom_'):
            plan_type = 'custom'
            actual_id = int(saved_id.split('_')[1])
        elif saved_id.startswith('ai_'):
            plan_type = 'ai'
            actual_id = int(saved_id.split('_')[1])
        elif saved_id.startswith('saved_'):
            plan_type = 'saved'
            actual_id = int(saved_id.split('_')[1])
        else:
            # Fallback for backward compatibility
            plan_type = 'ai'
            actual_id = int(saved_id)
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Handle custom workout
                if plan_type == 'custom':
                    cur.execute(
                        """
                        SELECT id, name AS plan_name, days_per_week, difficulty
                        FROM custom_workouts
                        WHERE id = %s AND clerk_user_id = %s;
                        """,
                        (actual_id, user["clerk_user_id"]),
                    )
                    custom_plan = cur.fetchone()
                    
                    if custom_plan:
                        # It's a custom workout
                        plan_name = custom_plan.get("plan_name", "Custom Workout")
                        days_per_week = custom_plan.get("days_per_week", 1)
                        is_custom = True
                    else:
                        return JSONResponse(status_code=404, content={
                            "success": False,
                            "error": "Custom workout not found"
                        })
                else:
                    # Check if it's an AI-generated plan
                    cur.execute(
                        """
                        SELECT id, name AS plan_name, days_per_week, primary_focus
                        FROM user_workout_plans
                        WHERE id = %s AND clerk_user_id = %s;
                        """,
                        (actual_id, user["clerk_user_id"]),
                    )
                    ai_plan = cur.fetchone()
                    is_custom = False
                    
                    if ai_plan:
                        # It's an AI-generated plan
                        plan_name = ai_plan.get("plan_name", "Workout Plan")
                        user_plan_id = ai_plan["id"]
                        days_per_week = ai_plan.get("days_per_week", 0)
                        focus_areas_data = ai_plan
                    else:
                        # Check if it's a saved pre-built plan
                        cur.execute(
                            """
                            SELECT usp.id, usp.plan_id, usp.body_type, usp.focus1, usp.focus2, usp.focus3, usp.user_plan_id,
                                   wp.name AS plan_name, wp.days_per_week, wp.primary_focus
                            FROM user_saved_plans usp
                            JOIN workout_plans wp ON wp.id = usp.plan_id
                            WHERE usp.id = %s AND usp.clerk_user_id = %s;
                            """,
                            (actual_id, user["clerk_user_id"]),
                        )
                        saved_plan = cur.fetchone()
                        
                        if not saved_plan:
                            return JSONResponse(status_code=404, content={
                                "success": False,
                                "error": "Plan not found"
                            })
                        
                        plan_name = saved_plan.get("plan_name", "Workout Plan")
                        user_plan_id = saved_plan.get("user_plan_id")
                        days_per_week = saved_plan.get("days_per_week", 0)
                        focus_areas_data = saved_plan
                        
                        if not user_plan_id:
                            return JSONResponse(status_code=400, content={
                                "success": False,
                                "error": "No editable copy found for this plan"
                            })
                
                # Build CSV in memory
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Header rows - branded
                timestamp = datetime.now().strftime("%B %d, %Y")
                writer.writerow(["🏋️ SCULPFIT WORKOUT PLAN"])
                writer.writerow([])
                writer.writerow(["Plan Name:", plan_name])
                writer.writerow(["Duration:", f"{days_per_week} days per week"])
                
                if plan_type == 'custom':
                    writer.writerow(["Type:", "Custom Workout"])
                else:
                    focus_areas = ", ".join([focus_areas_data.get("focus1") or focus_areas_data.get("primary_focus") or "", focus_areas_data.get("focus2") or "", focus_areas_data.get("focus3") or ""]).strip(", ")
                    writer.writerow(["Focus Areas:", focus_areas])
                
                writer.writerow(["Generated:", timestamp])
                writer.writerow([])
                writer.writerow([])
                
                # Exercises by day
                if plan_type == 'custom':
                    # Custom workout
                    cur.execute(
                        """
                        SELECT id, day_number, title
                        FROM custom_workout_days
                        WHERE custom_workout_id = %s
                        ORDER BY day_number;
                        """,
                        (actual_id,)
                    )
                    days = cur.fetchall()
                    
                    for day in days:
                        cur.execute(
                            """
                            SELECT cwe.sets, cwe.reps, cwe.rest_seconds, cwe.notes,
                                   cwe.exercise_name AS exercise
                            FROM custom_workout_exercises cwe
                            WHERE cwe.custom_day_id = %s
                            ORDER BY cwe.position;
                            """,
                            (day["id"],)
                        )
                        items = cur.fetchall()
                        
                        day_title = day.get("title") or f"Day {day['day_number']}"
                        writer.writerow([day_title])
                        writer.writerow(["Exercise", "Sets", "Reps", "Rest (sec)", "Notes"])
                        
                        for item in items:
                            writer.writerow([
                                item.get("exercise", ""),
                                item.get("sets", ""),
                                item.get("reps", ""),
                                item.get("rest_seconds", ""),
                                item.get("notes", "") or ""
                            ])
                        
                        writer.writerow([])
                else:
                    # Regular AI or pre-built plan
                    cur.execute(
                        """
                        SELECT id, day_number, title
                        FROM user_workout_days
                        WHERE user_plan_id = %s
                        ORDER BY day_number;
                        """,
                        (user_plan_id,)
                    )
                    days = cur.fetchall()
                    
                    for day in days:
                        cur.execute(
                            """
                            SELECT uwdi.sets, uwdi.reps, uwdi.rest_seconds, uwdi.notes,
                                   e.name AS exercise, e.primary_muscle AS muscle_group
                            FROM user_workout_day_items uwdi
                            JOIN exercises e ON e.id = uwdi.exercise_id
                            WHERE uwdi.user_day_id = %s
                            ORDER BY uwdi.position;

                        """,
                        (day["id"],)
                    )
                    items = cur.fetchall()
                    
                    # Day header
                    day_title = day.get("title") or f"Day {day['day_number']}"
                    writer.writerow([f"📅 {day_title}"])
                    writer.writerow(["Exercise", "Muscle Group", "Sets", "Reps", "Rest (sec)", "Notes"])
                    
                    # Exercises
                    for item in items:
                        exercise = str(item.get("exercise") or "")
                        muscle_group = str(item.get("muscle_group") or "")
                        sets = str(item.get("sets", "")) if item.get("sets") is not None else ""
                        reps = str(item.get("reps", "")) if item.get("reps") is not None else ""
                        rest = str(item.get("rest_seconds", "")) if item.get("rest_seconds") is not None else ""
                        notes = str(item.get("notes", "")) if item.get("notes") else ""
                        
                        # Prefix reps with ' to force Excel to treat as text and prevent date formatting
                        writer.writerow([
                            exercise,
                            muscle_group,
                            sets,
                            f"'{reps}" if reps else "",  # Add single quote prefix for Excel
                            rest,
                            notes,
                        ])
                    
                    writer.writerow([])
                
                # Footer
                writer.writerow([])
                writer.writerow(["📌 NOTES:", "Remember to warm up before starting any workout."])
                writer.writerow(["", "Rest appropriately between sets as indicated."])
                writer.writerow(["", "Adjust weights to match the target rep range."])
                
                csv_content = output.getvalue()
                
                # Generate filename
                plan_filename = plan_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
                filename = f"sculpfit_{plan_filename}_{datetime.now().strftime('%Y%m%d')}.csv"
                
                return StreamingResponse(
                    iter([csv_content]),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(e)
        })

