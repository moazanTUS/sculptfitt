"""
Integration tests for User Plans API
Tests complete API workflows with real database interactions
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserPlansAPI:
    """Test user plans database operations"""
    
    def test_list_user_plans_from_db(self, db_connection):
        """Should retrieve user's plans directly from database"""
        from backend.user_plans import list_user_plans
        
        # Query database directly
        plans = list_user_plans("user_test123")
        assert isinstance(plans, list)
    
    def test_unauthorized_access(self, unauthenticated_client):
        """Should reject unauthenticated requests"""
        response = unauthenticated_client.get("/api/my-plans")
        assert response.status_code == 401


@pytest.mark.integration
class TestCustomWorkoutsAPI:
    """Test custom workout database operations"""
    
    def test_custom_workouts_table_exists(self, db_connection):
        """Should verify custom_workouts table exists and can be queried"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'custom_workouts'
            """)
            result = cur.fetchone()
            assert result["count"] == 1
    
    @pytest.mark.skip(reason="Update/delete endpoints need checking")
    def test_update_custom_workout(self, client, mock_clerk_user):
        """Should update existing workout"""
        # Create workout first
        create_response = client.post("/api/custom-workouts", json={
            "name": "Original Name",
            "description": "Original description",
            "exercises": []
        })
        workout_id = create_response.json()["workout_id"]
        
        # Update workout
        update_response = client.put(f"/api/custom-workouts/{workout_id}", json={
            "name": "Updated Name",
            "description": "Updated description",
            "exercises": []
        })
        
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Name"
    
    @pytest.mark.skip(reason="Delete endpoint needs checking")
    def test_delete_custom_workout(self, client, mock_clerk_user):
        """Should delete workout and return 204"""
        # Create workout
        create_response = client.post("/api/custom-workouts", json={
            "name": "To Be Deleted",
            "description": "Test",
            "exercises": []
        })
        workout_id = create_response.json()["workout_id"]
        
        # Delete workout
        delete_response = client.delete(f"/api/custom-workouts/{workout_id}")
        
        assert delete_response.status_code == 200 or delete_response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/custom-workouts/{workout_id}")
        assert get_response.status_code == 404


@pytest.mark.integration
class TestWorkoutLoggingAPI:
    """Test workout logging database operations"""
    
    def test_workout_sessions_table_exists(self, db_connection):
        """Should verify workout_sessions table exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'workout_sessions'
            """)
            result = cur.fetchone()
            assert result["count"] == 1
    
    def test_query_workout_sessions(self, db_connection):
        """Should be able to query workout sessions"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT id, workout_name, session_date 
                FROM workout_sessions 
                LIMIT 5
            """)
            sessions = cur.fetchall()
            assert isinstance(sessions, list)


@pytest.mark.integration
class TestVideoLibraryAPI:
    """Test video library endpoints"""
    
    def test_get_all_exercises(self, client):
        """Should return all exercises with videos"""
        response = client.get("/api/exercises")
        
        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert isinstance(data["exercises"], list)
    
    def test_get_muscle_groups(self, client):
        """Should return available muscle groups"""
        response = client.get("/api/exercises/muscle-groups")
        
        assert response.status_code == 200
        data = response.json()
        assert "muscle_groups" in data
        assert isinstance(data["muscle_groups"], list)
    
    def test_search_videos(self, client):
        """Should search videos by name or muscle group"""
        response = client.get("/api/exercises/videos/search?q=push")
        
        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert isinstance(data["exercises"], list)
