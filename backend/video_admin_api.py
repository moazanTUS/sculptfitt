"""
Video Library Admin API
Endpoints for managing exercises and videos
"""

from fastapi import HTTPException, Form
from .db import get_conn


def register_video_admin_routes(app):
    """Register admin routes for video management"""
    
    @app.post("/api/admin/exercises")
    async def create_exercise(
        name: str = Form(...),
        description: str = Form(""),
        muscle_group: str = Form(""),
        difficulty: str = Form("intermediate")
    ):
        """Create a new exercise"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO exercises (name, description, muscle_group, difficulty)
                    VALUES (%s, %s, %s, %s)
                """, (name, description, muscle_group, difficulty))
                
                # Get the newly created exercise ID
                cur.execute("SELECT LAST_INSERT_ID() as id")
                result = cur.fetchone()
                exercise_id = result['id']
                
                return {"success": True, "exercise_id": exercise_id, "name": name}
        except Exception as e:
            print(f"Error creating exercise: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/admin/videos")
    async def add_video(
        exercise_id: int = Form(...),
        title: str = Form(...),
        video_url: str = Form(...),
        thumbnail_url: str = Form(""),
        duration_seconds: int = Form(0),
        description: str = Form(""),
        common_mistakes: str = Form(""),
        form_tips: str = Form(""),
        difficulty_level: str = Form("intermediate")
    ):
        """Add a video to an exercise"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                # Check exercise exists
                cur.execute("SELECT id FROM exercises WHERE id = %s", (exercise_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Exercise not found")
                
                cur.execute("""
                    INSERT INTO exercise_videos 
                    (exercise_id, title, video_url, thumbnail_url, duration_seconds, 
                     description, common_mistakes, form_tips, difficulty_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (exercise_id, title, video_url, thumbnail_url, duration_seconds,
                      description, common_mistakes, form_tips, difficulty_level))
                
                cur.execute("SELECT LAST_INSERT_ID() as id")
                result = cur.fetchone()
                video_id = result['id']
                
                return {"success": True, "video_id": video_id, "title": title}
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error adding video: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/admin/videos/{video_id}")
    async def delete_video(video_id: int):
        """Delete a video"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM exercise_videos WHERE id = %s", (video_id,))
                return {"success": True, "message": "Video deleted"}
        except Exception as e:
            print(f"Error deleting video: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/admin/exercises/{exercise_id}")
    async def delete_exercise(exercise_id: int):
        """Delete an exercise (and all its videos)"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM exercises WHERE id = %s", (exercise_id,))
                return {"success": True, "message": "Exercise and videos deleted"}
        except Exception as e:
            print(f"Error deleting exercise: {e}")
            raise HTTPException(status_code=500, detail=str(e))
