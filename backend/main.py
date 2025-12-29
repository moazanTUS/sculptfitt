import uuid
import shutil
import csv
import io
import os
from pathlib import Path
from typing import Literal
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analyzers.squat_analyzer import SquatAnalyzer
from .analyzers.pushup_analyzer import PushupAnalyzer
from .analyzers.shoulder_press_analyzer import ShoulderPressAnalyzer
from .analyzers.user_image_analyzer import UserImageAnalyzer

from .plan_matcher import match_plan
from .clerk_auth import require_clerk_user
from .user_plans import save_user_plan, list_user_plans
from .plan_store import ensure_plan_in_db

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

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Load API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="SculpFit Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


def current_user(request: Request):
    return require_clerk_user(request)


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


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/debug/uploads")
def debug_uploads():
    """Temporary debug endpoint: lists files under `backend/uploads`.

    Use this to confirm the uploaded file exists and to inspect its saved path/size.
    Remove this endpoint before deploying to production.
    """
    try:
        files = []
        for p in sorted(UPLOADS_DIR.iterdir()):
            if p.is_file():
                try:
                    sz = p.stat().st_size
                except Exception:
                    sz = None
                files.append({
                    "name": p.name,
                    "size": sz,
                    "path": str(p.resolve()),
                })
        return {"ok": True, "uploads_dir": str(UPLOADS_DIR.resolve()), "files": files}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


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
        from .plan_store import get_available_plans_by_days
        
        if days and days not in (3, 5):
            return JSONResponse(status_code=400, content={
                "success": False, 
                "error": "Invalid days value. Must be 3 or 5."
            })
        
        plans = get_available_plans_by_days(days if days else None)
        return {"success": True, "plans": plans}
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
        from .plan_store import get_available_plans_by_days
        from .user_plans import save_user_plan
        from .editable_plans import ensure_editable_copy
        
        # Verify plan exists
        all_plans = get_available_plans_by_days()
        found = False
        selected_plan = None
        for day_plans in all_plans.values():
            for p in day_plans:
                if p["id"] == plan_id:
                    found = True
                    selected_plan = p
                    break
        
        if not found:
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

        ext = Path(file.filename).suffix.lower() or ".jpg"
        image_id = str(uuid.uuid4())
        image_path = UPLOADS_DIR / f"{image_id}{ext}"

        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        analyzer = UserImageAnalyzer(
            image_path=str(image_path),
            api_key=GEMINI_API_KEY,
        )

        report = analyzer.analyze()
        result = report.get("result", {})
        focus_areas = result.get("focus_areas", [])
        body_type = result.get("body_type")

        print(f"[analyze_image] focus_areas: {focus_areas}")
        print(f"[analyze_image] body_type: {body_type}")

        # Match plan with user's preferred plan_days and body_type
        matched = match_plan(focus_areas, body_type=body_type)
        
        print(f"[analyze_image] matched plan: {matched}")

        saved_id = None
        plan_body_type = None
        plan_name = None

        if matched and matched.get("plan"):
            db_plan_id = None
            plan_info = matched.get("plan")
            focus_area = plan_info.get("primary_focus") if isinstance(plan_info, dict) else str(plan_info)
            plan_name = plan_info.get("name") if isinstance(plan_info, dict) else None
            plan_body_type = plan_info.get("body_type") if isinstance(plan_info, dict) else None
            
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Priority 1: Body-type specific plan (closest day match if exact days don't exist)
                    if body_type and body_type in ('ectomorph', 'mesomorph', 'endomorph'):
                        # First try exact: body_type + focus + preferred days
                        cur.execute(
                            """
                            SELECT id, name, days_per_week, body_type FROM workout_plans
                            WHERE primary_focus = %s AND body_type = %s AND days_per_week = %s
                            LIMIT 1;
                            """,
                            (focus_area, body_type, plan_days),
                        )
                        row = cur.fetchone()
                        
                        # If not found, get the closest days for this body_type + focus
                        if not row:
                            cur.execute(
                                """
                                SELECT id, name, days_per_week, body_type FROM workout_plans
                                WHERE primary_focus = %s AND body_type = %s
                                ORDER BY ABS(days_per_week - %s) ASC
                                LIMIT 1;
                                """,
                                (focus_area, body_type, plan_days),
                            )
                            row = cur.fetchone()
                        
                        if row:
                            db_plan_id = row["id"]
                            plan_name = row["name"]
                            plan_body_type = row["body_type"]
                            print(f"[analyze_image] body-type plan found: {row['id']} - {row['name']} ({row['body_type']}) ({row['days_per_week']}-day)")
                    
                    # Priority 2: Generic plan (body_type = 'all' or NULL) - exact days preferred
                    if not db_plan_id:
                        cur.execute(
                            """
                            SELECT id, name, days_per_week, body_type FROM workout_plans
                            WHERE primary_focus = %s AND (body_type = 'all' OR body_type IS NULL) AND days_per_week = %s
                            LIMIT 1;
                            """,
                            (focus_area, plan_days),
                        )
                        row = cur.fetchone()
                        
                        # If not found, get any generic plan for this focus
                        if not row:
                            cur.execute(
                                """
                                SELECT id, name, days_per_week, body_type FROM workout_plans
                                WHERE primary_focus = %s AND (body_type = 'all' OR body_type IS NULL)
                                LIMIT 1;
                                """,
                                (focus_area,),
                            )
                            row = cur.fetchone()
                        
                        if row:
                            db_plan_id = row["id"]
                            plan_name = row["name"]
                            plan_body_type = row["body_type"]
                            print(f"[analyze_image] generic plan found: {row['id']} - {row['name']} ({row['days_per_week']}-day)")
            
            # If still no match, use the matched plan from pattern matching
            if not db_plan_id:
                print(f"[analyze_image] no specific plan found, using ensure_plan_in_db")
                db_plan_id = ensure_plan_in_db(matched)

            print(f"[analyze_image] using plan_id: {db_plan_id}")

            print(f"[analyze_image] calling save_user_plan with plan_id={db_plan_id}, body_type={body_type}, focus_areas={focus_areas}")
            saved_id = save_user_plan(
                clerk_user_id=user["clerk_user_id"],
                plan_id=db_plan_id,
                body_type=body_type,
                focus_areas=focus_areas,
            )
            print(f"[analyze_image] saved_id returned: {saved_id}")

            # ✅ ensure editable copy
            ensure_editable_copy(saved_id, user["clerk_user_id"])

        return {
            "success": True,
            "type": "image",
            "plan_days_selected": plan_days,
            "detected_body_type": body_type,
            "selected_plan_body_type": plan_body_type,
            "selected_plan_name": plan_name,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans")
def my_plans(user=Depends(current_user)):
    items = list_user_plans(user["clerk_user_id"])
    return {"success": True, "items": items}


def _get_editable_payload(saved_id: int, clerk_user_id: str):
    """
    Force correct payload shape:
      days[]: { day_id, day, title, items: [{ item_id, exercise, sets, reps, rest_seconds, ...}] }
    """
    user_plan_id = ensure_editable_copy(saved_id, clerk_user_id)

    with get_conn() as conn:
        with conn.cursor() as cur:
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
                           e.muscle_group,
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
def delete_plan(saved_id: int, user=Depends(current_user)):
    """Delete a saved plan by ID (user-owned only)."""
    try:
        from .user_plans import delete_user_plan
        deleted = delete_user_plan(saved_id, user["clerk_user_id"])
        if not deleted:
            return JSONResponse(status_code=404, content={"success": False, "error": "Plan not found"})
        return {"success": True, "message": "Plan deleted"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans/{saved_id}/editable")
def my_plan_editable(saved_id: int, user=Depends(current_user)):
    try:
        data = _get_editable_payload(saved_id, user["clerk_user_id"])
        return {"success": True, **data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/my-plans/{saved_id}")
def my_plan_detail(saved_id: int, user=Depends(current_user)):
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
    exercise: Literal["squats", "pushups", "shoulder_press"] = Form(...),
    file: UploadFile = File(...),
):
    try:
        ext = Path(file.filename).suffix.lower() or ".mp4"
        video_id = str(uuid.uuid4())
        video_path = (UPLOADS_DIR / f"{video_id}{ext}").resolve()

        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Debug: confirm saved upload info
        try:
            size = video_path.stat().st_size
        except FileNotFoundError:
            size = 0
        print(f"[analyze_video] saved upload -> path={video_path} size={size} bytes ext={ext} cwd={Path.cwd()}")

        if not video_path.exists() or size == 0:
            raise FileNotFoundError(f"Uploaded video missing or empty at {video_path}")

        if exercise == "squats":
            analyzer = SquatAnalyzer(str(video_path))
        elif exercise == "pushups":
            analyzer = PushupAnalyzer(str(video_path))
        else:
            analyzer = ShoulderPressAnalyzer(str(video_path))

        print(f"[analyze_video] starting analysis for {exercise} on {video_path}")
        report = analyzer.analyze()
        print(f"[analyze_video] completed analysis -> report keys: {list(report.keys())}")

        annotated_src = Path(report.get("annotated_video", ""))
        annotated_url = None

        if annotated_src.exists():
            annotated_dst = OUTPUTS_DIR / annotated_src.name
            if annotated_src.resolve() != annotated_dst.resolve():
                shutil.copy2(annotated_src, annotated_dst)
            annotated_url = f"/outputs/{annotated_dst.name}"

        return {
            "success": True,
            "type": "video",
            "report": {
                "exercise": report.get("exercise"),
                "total_reps": report.get("total_reps"),
                "perfect_reps": report.get("perfect_reps"),
                "partial_reps": report.get("partial_reps"),
                "form_score": report.get("form_score"),
            },
            "annotated_video_url": annotated_url,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        tb = traceback.format_exc()
        path = str(locals().get("video_path", ""))
        probe = None
        probe_error = None
        if path:
            try:
                probe = _fallback_video_probe(Path(path))
            except Exception as pe:
                probe_error = str(pe)
        try:
            exists = Path(path).exists()
            sz = Path(path).stat().st_size if exists else 0
        except Exception:
            exists = False
            sz = 0
        return JSONResponse(
            status_code=200,  # return 200 so frontend can show message without hard failure
            content={
                "success": False,
                "error": str(e),
                "path": path,
                "path_exists": exists,
                "upload_size": sz,
                "exercise": locals().get("exercise", None),
                "cwd": str(Path.cwd()),
                "details": repr(e),
                "traceback": tb,
                "probe": probe,
                "probe_error": probe_error,
            },
        )


@app.get("/api/my-plans/{saved_id}/export-csv")
async def export_plan_csv(
    saved_id: int,
    user=Depends(current_user),
):
    """
    Export a user's saved workout plan as a branded CSV file.
    Downloads a CSV with plan name, exercises, and formatting.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get the saved plan details and its editable copy
                cur.execute(
                    """
                    SELECT usp.id, usp.plan_id, usp.body_type, usp.focus1, usp.focus2, usp.focus3, usp.user_plan_id,
                           wp.name AS plan_name, wp.days_per_week, wp.primary_focus
                    FROM user_saved_plans usp
                    JOIN workout_plans wp ON wp.id = usp.plan_id
                    WHERE usp.id = %s AND usp.clerk_user_id = %s;
                    """,
                    (saved_id, user["clerk_user_id"]),
                )
                saved_plan = cur.fetchone()
                
                if not saved_plan:
                    return JSONResponse(status_code=404, content={
                        "success": False,
                        "error": "Plan not found"
                    })
                
                plan_name = saved_plan.get("plan_name", "Workout Plan")
                days_per_week = saved_plan.get("days_per_week", 0)
                user_plan_id = saved_plan.get("user_plan_id")
                
                if not user_plan_id:
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "error": "No editable copy found for this plan"
                    })
                
                # Get all days from editable copy
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
                
                # Build CSV in memory
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Header rows - branded
                timestamp = datetime.now().strftime("%B %d, %Y")
                writer.writerow(["🏋️ SCULPFIT WORKOUT PLAN"])
                writer.writerow([])
                writer.writerow(["Plan Name:", plan_name])
                writer.writerow(["Duration:", f"{days_per_week} days per week"])
                focus_areas = ", ".join([saved_plan.get("focus1") or "", saved_plan.get("focus2") or "", saved_plan.get("focus3") or ""]).strip(", ")
                writer.writerow(["Focus Areas:", focus_areas])
                writer.writerow(["Generated:", timestamp])
                writer.writerow([])
                writer.writerow([])
                
                # Exercises by day
                for day in days:
                    cur.execute(
                        """
                        SELECT uwdi.sets, uwdi.reps, uwdi.rest_seconds, uwdi.notes,
                               e.name AS exercise, e.muscle_group
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

