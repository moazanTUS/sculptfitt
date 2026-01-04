"""
Video Library API
Endpoints for managing and viewing exercise videos
"""

from fastapi import HTTPException
from .db import get_conn


def register_video_library_routes(app):
    """Register all video library routes with the FastAPI app"""
    
    @app.get("/api/exercises/muscle-groups")
    async def get_muscle_groups():
        """Get muscle groups from exercises with videos"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT muscle_group
                    FROM exercises e
                    WHERE muscle_group IS NOT NULL
                    AND e.id IN (SELECT exercise_id FROM exercise_videos)
                    ORDER BY muscle_group
                """)
                groups = cur.fetchall()
                return {"muscle_groups": [g['muscle_group'] for g in groups] if groups else []}
        except Exception as e:
            print(f"Error fetching muscle groups: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/exercises/videos/search")
    async def search_videos(q: str = ""):
        """Search exercises with videos by name or muscle group"""
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                search_term = f"%{q}%"
                cur.execute("""
                    SELECT DISTINCT
                        e.id,
                        e.name,
                        e.description,
                        e.muscle_group,
                        e.difficulty,
                        COUNT(ev.id) as video_count
                    FROM exercises e
                    LEFT JOIN exercise_videos ev ON e.id = ev.exercise_id
                    WHERE (e.name LIKE %s OR e.muscle_group LIKE %s OR e.description LIKE %s)
                    AND e.id IN (SELECT exercise_id FROM exercise_videos)
                    GROUP BY e.id
                    ORDER BY e.name
                """, (search_term, search_term, search_term))
                exercises = cur.fetchall()
                return {"exercises": exercises if exercises else []}
        except Exception as e:
            print(f"Error searching videos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/exercises")
    async def get_all_exercises():
        """Get all exercises with videos"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        e.id,
                        e.name,
                        e.description,
                        e.muscle_group,
                        e.difficulty,
                        COUNT(ev.id) as video_count
                    FROM exercises e
                    LEFT JOIN exercise_videos ev ON e.id = ev.exercise_id
                    GROUP BY e.id
                    HAVING COUNT(ev.id) > 0
                    ORDER BY e.name
                """)
                exercises = cur.fetchall()
                return {"exercises": exercises if exercises else []}
        except Exception as e:
            print(f"Error fetching exercises: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/exercises/{exercise_id}")
    async def get_exercise_details(exercise_id: int):
        """Get exercise details with all its videos"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                # Get exercise info
                cur.execute("""
                    SELECT id, name, description, muscle_group, difficulty
                    FROM exercises
                    WHERE id = %s
                """, (exercise_id,))
                exercise = cur.fetchone()
                
                if not exercise:
                    raise HTTPException(status_code=404, detail="Exercise not found")
                
                # Get all videos for this exercise
                cur.execute("""
                    SELECT 
                        id,
                        title,
                        video_url,
                        thumbnail_url,
                        duration_seconds,
                        description,
                        common_mistakes,
                        form_tips,
                        difficulty_level,
                        views
                    FROM exercise_videos
                    WHERE exercise_id = %s
                    ORDER BY created_at DESC
                """, (exercise_id,))
                videos = cur.fetchall()
                
                exercise['videos'] = videos if videos else []
                return exercise
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching exercise details: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/exercises/by-muscle-group/{muscle_group}")
    async def get_exercises_by_muscle_group(muscle_group: str):
        """Get exercises with videos for a specific muscle group"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        e.id,
                        e.name,
                        e.description,
                        e.muscle_group,
                        e.difficulty,
                        COUNT(ev.id) as video_count
                    FROM exercises e
                    LEFT JOIN exercise_videos ev ON e.id = ev.exercise_id
                    WHERE e.muscle_group = %s
                    AND e.id IN (SELECT exercise_id FROM exercise_videos)
                    GROUP BY e.id
                    ORDER BY e.name
                """, (muscle_group,))
                exercises = cur.fetchall()
                return {"exercises": exercises if exercises else []}
        except Exception as e:
            print(f"Error fetching exercises by muscle group: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/video/record-view/{video_id}")
    async def record_video_view(video_id: int):
        """Record a view for a video"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE exercise_videos
                    SET views = views + 1
                    WHERE id = %s
                """, (video_id,))
                
                cur.execute("SELECT views FROM exercise_videos WHERE id = %s", (video_id,))
                result = cur.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="Video not found")
                
                return {"views": result['views']}
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error recording video view: {e}")
            raise HTTPException(status_code=500, detail=str(e))
