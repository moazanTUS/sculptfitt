"""
Workout Logging and Progress Tracking Endpoints
"""

from fastapi.responses import JSONResponse
from fastapi import Depends, Form
from datetime import date, datetime
from .db import get_conn


def register_workout_logging_routes(app, current_user):
    """Register all workout logging routes"""
    
    @app.post("/api/workout-sessions")
    async def start_workout_session(
        workout_plan_id: int = Form(...),
        workout_plan_type: str = Form("ai"),
        workout_name: str = Form(...),
        day_number: int = Form(1),
        user=Depends(current_user)
    ):
        """Start a new workout session"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Create session record
                    cur.execute("""
                        INSERT INTO workout_sessions 
                        (clerk_user_id, workout_plan_id, workout_plan_type, workout_name, day_number, session_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user["clerk_user_id"], workout_plan_id, workout_plan_type, workout_name, day_number, date.today()))
                    
                    session_id = cur.lastrowid
                    
                    # Get exercises for this workout day
                    if workout_plan_type == 'custom':
                        cur.execute("""
                            SELECT cwe.exercise_id, cwe.exercise_name, cwe.sets, cwe.reps, cwe.rest_seconds, cwe.position
                            FROM custom_workout_exercises cwe
                            JOIN custom_workout_days cwd ON cwd.id = cwe.custom_day_id
                            WHERE cwd.custom_workout_id = %s AND cwd.day_number = %s
                            ORDER BY cwe.position
                        """, (workout_plan_id, day_number))
                    else:
                        cur.execute("""
                            SELECT uwdi.exercise_id, e.name, uwdi.sets, uwdi.reps, uwdi.rest_seconds, uwdi.position
                            FROM user_workout_day_items uwdi
                            JOIN user_workout_days uwd ON uwd.id = uwdi.user_day_id
                            JOIN exercises e ON e.id = uwdi.exercise_id
                            WHERE uwd.user_plan_id = %s AND uwd.day_number = %s
                            ORDER BY uwdi.position
                        """, (workout_plan_id, day_number))
                    
                    exercises = cur.fetchall()
                    
                    # Create exercise log entries
                    exercise_logs = []
                    for ex in exercises:
                        # For custom workouts, exercise_id can be NULL when not linked to catalog exercises.
                        exercise_id = ex.get("exercise_id")
                        exercise_name = ex.get("exercise_name") or ex.get("name")
                        
                        cur.execute("""
                            INSERT INTO workout_session_exercises
                            (session_id, exercise_id, exercise_name, planned_sets, planned_reps, planned_rest_seconds, position)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (session_id, exercise_id, exercise_name, ex["sets"], ex["reps"], ex["rest_seconds"], ex["position"]))
                        
                        exercise_logs.append({
                            "id": cur.lastrowid,
                            "exercise_name": exercise_name,
                            "planned_sets": ex["sets"],
                            "planned_reps": ex["reps"],
                            "planned_rest_seconds": ex["rest_seconds"]
                        })
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "exercises": exercise_logs
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.get("/api/workout-sessions")
    async def list_workout_sessions(user=Depends(current_user)):
        """List all workout sessions for the user"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, workout_name, workout_plan_type, day_number, session_date, 
                               completed_at, duration_minutes, rating, notes
                        FROM workout_sessions
                        WHERE clerk_user_id = %s
                        ORDER BY session_date DESC, created_at DESC
                        LIMIT 100
                    """, (user["clerk_user_id"],))
                    
                    sessions = cur.fetchall()
                    return {
                        "success": True,
                        "sessions": sessions
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.get("/api/workout-sessions/{session_id}")
    async def get_workout_session(session_id: int, user=Depends(current_user)):
        """Get details of a specific workout session"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Get session
                    cur.execute("""
                        SELECT id, workout_name, workout_plan_type, day_number, session_date,
                               completed_at, duration_minutes, rating, notes
                        FROM workout_sessions
                        WHERE id = %s AND clerk_user_id = %s
                    """, (session_id, user["clerk_user_id"]))
                    
                    session = cur.fetchone()
                    if not session:
                        return JSONResponse(status_code=404, content={"success": False, "error": "Session not found"})
                    
                    # Get exercises for this session
                    cur.execute("""
                        SELECT id, exercise_name, planned_sets, planned_reps, planned_rest_seconds,
                               completed_sets, completed_reps, weight_used, rpe, notes, position
                        FROM workout_session_exercises
                        WHERE session_id = %s
                        ORDER BY position
                    """, (session_id,))
                    
                    exercises = cur.fetchall()
                    
                    return {
                        "success": True,
                        "session": session,
                        "exercises": exercises
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.delete("/api/workout-sessions/{session_id}")
    async def delete_workout_session(session_id: int, user=Depends(current_user)):
        """Delete/abandon a workout session"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Verify session belongs to user
                    cur.execute("""
                        SELECT id FROM workout_sessions
                        WHERE id = %s AND clerk_user_id = %s
                    """, (session_id, user["clerk_user_id"]))
                    
                    if not cur.fetchone():
                        return JSONResponse(status_code=404, content={"success": False, "error": "Session not found"})
                    
                    # Delete all exercises for this session
                    cur.execute("""
                        DELETE FROM workout_session_exercises
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    # Delete the session
                    cur.execute("""
                        DELETE FROM workout_sessions
                        WHERE id = %s
                    """, (session_id,))
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "message": "Workout session deleted"
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.post("/api/workout-sessions/{session_id}/exercises/{exercise_id}/log")
    async def log_exercise_completion(
        session_id: int,
        exercise_id: int,
        completed_sets: int = Form(...),
        completed_reps: str = Form(...),
        weight_used: float = Form(None),
        rpe: int = Form(None),
        notes: str = Form(""),
        user=Depends(current_user)
    ):
        """Log completion of an exercise in a workout session"""
        try:
            pr_date = date.today() if weight_used is not None else None
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Verify session belongs to user
                    cur.execute("""
                        SELECT id FROM workout_sessions
                        WHERE id = %s AND clerk_user_id = %s
                    """, (session_id, user["clerk_user_id"]))
                    
                    if not cur.fetchone():
                        return JSONResponse(status_code=404, content={"success": False, "error": "Session not found"})
                    
                    # Update exercise log
                    cur.execute("""
                        UPDATE workout_session_exercises
                        SET completed_sets = %s, completed_reps = %s, weight_used = %s, 
                            rpe = %s, notes = %s, completed_at = NOW()
                        WHERE session_id = %s AND id = %s
                    """, (completed_sets, completed_reps, weight_used, rpe, notes, session_id, exercise_id))
                    
                    # Update progress tracking
                    cur.execute("""
                        SELECT exercise_id, exercise_name FROM workout_session_exercises
                        WHERE id = %s
                    """, (exercise_id,))
                    
                    ex_data = cur.fetchone()
                    ex_id = ex_data["exercise_id"]
                    ex_name = ex_data["exercise_name"]
                    
                    # Upsert progress record
                    cur.execute("""
                        INSERT INTO workout_progress 
                        (clerk_user_id, exercise_id, exercise_name, personal_record_weight, 
                         personal_record_date, total_times_completed, last_completed_date)
                        VALUES (%s, %s, %s, %s, %s, 1, %s)
                        ON DUPLICATE KEY UPDATE
                        total_times_completed = total_times_completed + 1,
                        last_completed_date = %s,
                        personal_record_weight = CASE
                            WHEN %s IS NULL THEN personal_record_weight
                            WHEN personal_record_weight IS NULL OR %s > personal_record_weight THEN %s
                            ELSE personal_record_weight
                        END,
                        personal_record_date = CASE
                            WHEN %s IS NULL THEN personal_record_date
                            WHEN personal_record_weight IS NULL OR %s > personal_record_weight THEN %s
                            ELSE personal_record_date
                        END
                    """, (
                        user["clerk_user_id"],
                        ex_id,
                        ex_name,
                        weight_used,
                        pr_date,
                        date.today(),
                        date.today(),
                        weight_used,
                        weight_used,
                        weight_used,
                        weight_used,
                        weight_used,
                        pr_date,
                    ))
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "message": "Exercise logged successfully"
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.post("/api/workout-sessions/{session_id}/complete")
    async def complete_workout_session(
        session_id: int,
        duration_minutes: int = Form(0),
        rating: int = Form(None),
        notes: str = Form(""),
        user=Depends(current_user)
    ):
        """Mark a workout session as completed"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE workout_sessions
                        SET completed_at = NOW(), duration_minutes = %s, rating = %s, notes = %s
                        WHERE id = %s AND clerk_user_id = %s
                    """, (duration_minutes, rating, notes, session_id, user["clerk_user_id"]))
                    
                    if cur.rowcount == 0:
                        return JSONResponse(status_code=404, content={"success": False, "error": "Session not found"})
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "message": "Workout completed!"
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    
    
    @app.get("/api/progress/stats")
    async def get_progress_stats(user=Depends(current_user)):
        """Get progress statistics for the user"""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Total workouts
                    cur.execute("""
                        SELECT COUNT(*) as total_workouts,
                               SUM(duration_minutes) as total_minutes,
                               AVG(rating) as average_rating
                        FROM workout_sessions
                        WHERE clerk_user_id = %s AND completed_at IS NOT NULL
                    """, (user["clerk_user_id"],))
                    
                    stats = cur.fetchone()
                    
                    # Top exercises
                    cur.execute("""
                        SELECT exercise_name, total_times_completed, personal_record_weight
                        FROM workout_progress
                        WHERE clerk_user_id = %s
                        ORDER BY total_times_completed DESC
                        LIMIT 10
                    """, (user["clerk_user_id"],))
                    
                    top_exercises = cur.fetchall()
                    
                    # Workout frequency (last 7 days)
                    cur.execute("""
                        SELECT DATE(session_date) as workout_date, COUNT(*) as count
                        FROM workout_sessions
                        WHERE clerk_user_id = %s AND session_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                        GROUP BY DATE(session_date)
                        ORDER BY workout_date DESC
                    """, (user["clerk_user_id"],))
                    
                    frequency = cur.fetchall()
                    
                    return {
                        "success": True,
                        "stats": stats,
                        "top_exercises": top_exercises,
                        "recent_frequency": frequency
                    }
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
