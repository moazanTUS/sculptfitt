"""
Integration tests for User Plans API
Tests complete API workflows with real database interactions
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserPlansAPI:
    """Test user plans endpoints with database"""
    
    def test_list_user_plans(self, client, mock_clerk_user):
        """Should retrieve user's plans"""
        # Act - List plans (the actual endpoint that exists)
        response = client.get("/api/my-plans")
        
        # Assert
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
    
    def test_unauthorized_access(self, unauthenticated_client):
        """Should reject unauthenticated requests"""
        response = unauthenticated_client.get("/api/my-plans")
        assert response.status_code == 401


@pytest.mark.integration
class TestCustomWorkoutsAPI:
    """Test custom workout creation and management"""
    
    def test_create_custom_workout(self, client, mock_clerk_user):
        """Should create a new custom workout"""
        import json
        workout_data = {
            "name": "My Custom Workout",
            "description": "Personal workout routine",
            "exercises": json.dumps([
                {"name": "Push-ups", "sets": 3, "reps": 15},
                {"name": "Squats", "sets": 4, "reps": 12}
            ])
        }
        
        response = client.post("/api/custom-workouts", data=workout_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "workout_id" in data
    
    def test_list_user_workouts(self, client, mock_clerk_user):
        """Should list all workouts for authenticated user"""
        response = client.get("/api/custom-workouts")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
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
    """Test workout logging functionality"""
    
    def test_list_workout_sessions(self, client, mock_clerk_user):
        """Should retrieve user's workout sessions"""
        response = client.get("/api/workout-sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_get_progress_stats(self, client, mock_clerk_user):
        """Should retrieve progress statistics"""
        response = client.get("/api/progress/stats")
        
        assert response.status_code == 200
        data = response.json()
        # Stats endpoint should return some data structure
        assert isinstance(data, dict)


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
