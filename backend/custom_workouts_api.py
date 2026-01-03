"""
Custom Workout Management Endpoints
These functions are registered in main.py
"""

from fastapi.responses import JSONResponse
from fastapi import Depends, Form
from .db import get_conn


def register_custom_workout_routes(app, current_user):
    """Register all custom workout routes with the FastAPI app"""
    
    @app.post("/api/custom-workouts")
    async def create_custom_workout(
        name: str = Form("My Workout"),
        description: str = Form(""),
        exercises: str = Form("[]"),  # JSON string of exercise array
        user=Depends(current_user)
    ):
        """Create a new custom workout with exercises"""
        import json
        try:
            # Parse exercises JSON
            exercise_list = json.loads(exercises)
            
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Create custom workout (single day workout, so days_per_week = 1)
                    cur.execute("""
                        INSERT INTO custom_workouts 
                        (clerk_user_id, name, description, days_per_week)
                        VALUES (%s, %s, %s, %s)
                    """, (user["clerk_user_id"], name, description, 1))
                    
                    workout_id = cur.lastrowid
                    
                    # Create single day
                    cur.execute("""
                        INSERT INTO custom_workout_days 
                        (custom_workout_id, day_number, title)
                        VALUES (%s, %s, %s)
                    """, (workout_id, 1, "Day 1"))
                    
                    day_id = cur.lastrowid
                    
                    # Add exercises to the day
                    for ex_data in exercise_list:
                        cur.execute("""
                            INSERT INTO custom_workout_exercises
                            (custom_day_id, exercise_name, sets, reps, rest_seconds, position)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            day_id,
                            ex_data.get("exercise_name", ""),
                            ex_data.get("sets", 3),
                            ex_data.get("reps", "8-12"),
                            ex_data.get("rest_seconds", 60),
                            ex_data.get("position", 1)
                        ))
                    
                    conn.commit()
            
            return {
                "success": True,
                "workout_id": workout_id,
                "message": f"Workout '{name}' created with {len(exercise_list)} exercise(s)"
            }
        except Exception as e:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": str(e)
            })


    @app.get("/api/custom-workouts")
    async def get_custom_workouts(user=Depends(current_user)):
        """Get all custom workouts for the user"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, description, days_per_week, difficulty, created_at
                        FROM custom_workouts
                        WHERE clerk_user_id = %s
                        ORDER BY created_at DESC
                    """, (user["clerk_user_id"],))
                    
                    workouts = []
                    for row in cur.fetchall():
                        workouts.append({
                            "id": row["id"],
                            "name": row["name"],
                            "description": row["description"],
                            "days_per_week": row["days_per_week"],
                            "difficulty": row["difficulty"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None
                        })
            
            return {"success": True, "workouts": workouts}
        except Exception as e:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": str(e)
            })


    @app.get("/api/custom-workouts/{workout_id}")
    async def get_custom_workout(workout_id: int, user=Depends(current_user)):
        """Get a specific custom workout with all its days and exercises"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Get workout
                    cur.execute("""
                        SELECT id, name, description, days_per_week, difficulty
                        FROM custom_workouts
                        WHERE id = %s AND clerk_user_id = %s
                    """, (workout_id, user["clerk_user_id"]))
                    
                    workout = cur.fetchone()
                    if not workout:
                        return JSONResponse(status_code=404, content={
                            "success": False,
                            "error": "Workout not found"
                        })
                    
                    # Get days with exercises
                    cur.execute("""
                        SELECT id, day_number, title
                        FROM custom_workout_days
                        WHERE custom_workout_id = %s
                        ORDER BY day_number
                    """, (workout_id,))
                    
                    days = []
                    for day_row in cur.fetchall():
                        day_id = day_row["id"]
                        
                        cur.execute("""
                            SELECT id, exercise_name, sets, reps, rest_seconds, notes, exercise_id
                            FROM custom_workout_exercises
                            WHERE custom_day_id = %s
                            ORDER BY position
                        """, (day_id,))
                        
                        exercises = []
                        for ex_row in cur.fetchall():
                            exercises.append({
                                "id": ex_row["id"],
                                "exercise_name": ex_row["exercise_name"],
                                "exercise_id": ex_row["exercise_id"],
                                "sets": ex_row["sets"],
                                "reps": ex_row["reps"],
                                "rest_seconds": ex_row["rest_seconds"],
                                "notes": ex_row["notes"]
                            })
                        
                        days.append({
                            "id": day_id,
                            "day_number": day_row["day_number"],
                            "title": day_row["title"],
                            "exercises": exercises
                        })
                    
                    return {
                        "success": True,
                        "id": workout["id"],
                        "name": workout["name"],
                        "description": workout["description"],
                        "days_per_week": workout["days_per_week"],
                        "difficulty": workout["difficulty"],
                        "days": days
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": str(e)
            })


    @app.post("/api/custom-workouts/{workout_id}/exercises")
    async def add_exercise_to_day(
        workout_id: int,
        day_number: int = Form(...),
        exercise_name: str = Form(""),
        exercise_id: int = Form(None),
        sets: int = Form(3),
        reps: str = Form("8-12"),
        rest_seconds: int = Form(60),
        notes: str = Form(""),
        user=Depends(current_user)
    ):
        """Add an exercise to a day in a custom workout"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Verify ownership
                    cur.execute("""
                        SELECT id FROM custom_workouts
                        WHERE id = %s AND clerk_user_id = %s
                    """, (workout_id, user["clerk_user_id"]))
                    
                    if not cur.fetchone():
                        return JSONResponse(status_code=403, content={
                            "success": False,
                            "error": "Unauthorized"
                        })
                    
                    # Get the day
                    cur.execute("""
                        SELECT id FROM custom_workout_days
                        WHERE custom_workout_id = %s AND day_number = %s
                    """, (workout_id, day_number))
                    
                    day = cur.fetchone()
                    if not day:
                        return JSONResponse(status_code=404, content={
                            "success": False,
                            "error": "Day not found"
                        })
                    
                    # Count existing exercises to set position
                    cur.execute("""
                        SELECT COUNT(*) as cnt FROM custom_workout_exercises
                        WHERE custom_day_id = %s
                    """, (day["id"],))
                    
                    position = cur.fetchone()["cnt"]
                    
                    # Add exercise
                    cur.execute("""
                        INSERT INTO custom_workout_exercises
                        (custom_day_id, exercise_id, exercise_name, sets, reps, rest_seconds, notes, position)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (day["id"], exercise_id, exercise_name, sets, reps, rest_seconds, notes, position))
                    
                    exercise_id_new = cur.lastrowid
                    conn.commit()
            
            return {
                "success": True,
                "exercise_id": exercise_id_new,
                "message": "Exercise added"
            }
        except Exception as e:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": str(e)
            })


    @app.delete("/api/custom-workouts/{workout_id}")
    async def delete_custom_workout(workout_id: int, user=Depends(current_user)):
        """Delete a custom workout"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Verify ownership
                    cur.execute("""
                        SELECT id FROM custom_workouts
                        WHERE id = %s AND clerk_user_id = %s
                    """, (workout_id, user["clerk_user_id"]))
                    
                    if not cur.fetchone():
                        return JSONResponse(status_code=403, content={
                            "success": False,
                            "error": "Unauthorized"
                        })
                    
                    # Delete (cascade will remove days and exercises)
                    cur.execute("DELETE FROM custom_workouts WHERE id = %s", (workout_id,))
                    conn.commit()
            
            return {"success": True, "message": "Workout deleted"}
        except Exception as e:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": str(e)
            })
