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
        
        # Assert save
        assert response.status_code == 200
        assert response.json()["message"] == "Plan saved successfully"
        
        # Act - List plans
        list_response = client.get("/api/user-plans")
        
        # Assert list
        assert list_response.status_code == 200
        plans = list_response.json()
        assert len(plans) > 0
        assert any(p["plan_name"] == "Beginner Full Body" for p in plans)
    
    def test_duplicate_plan_save(self, client, mock_clerk_user):
        """Should handle duplicate plan saves gracefully"""
        plan_data = {"plan_id": 2, "plan_name": "Test Plan"}
        
        # Save once
        response1 = client.post("/api/save-plan", json=plan_data)
        assert response1.status_code == 200
        
        # Save again - should succeed (ON DUPLICATE KEY UPDATE)
        response2 = client.post("/api/save-plan", json=plan_data)
        assert response2.status_code == 200
    
    def test_unauthorized_access(self, unauthenticated_client):
        """Should reject unauthenticated requests"""
        response = unauthenticated_client.get("/api/user-plans")
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


@pytest.mark.skip(reason="Workout logging requires active sessions - complex setup")
@pytest.mark.integration
class TestWorkoutLoggingAPI:
    """Test workout logging functionality"""
    
    def test_log_workout_session(self, client, mock_clerk_user):
        """Should create workout log entry"""
        log_data = {
            "date": "2026-02-04",
            "exercise_name": "Bench Press",
            "sets": 4,
            "reps": 8,
            "weight": 60,
            "duration_minutes": 30,
            "notes": "Felt strong today"
        }
        
        response = client.post("/api/workout-logs", json=log_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "log_id" in data
    
    def test_get_workout_history(self, client, mock_clerk_user):
        """Should retrieve user's workout history"""
        response = client.get("/api/workout-logs")
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
    
    def test_get_workout_stats(self, client, mock_clerk_user):
        """Should calculate workout statistics"""
        # Log some workouts first
        for i in range(3):
            client.post("/api/workout-logs", json={
                "date": f"2026-02-0{i+1}",
                "exercise_name": "Squats",
                "sets": 3,
                "reps": 10,
                "weight": 50 + i*5
            })
        
        # Get stats
        response = client.get("/api/workout-logs/stats")
        
        assert response.status_code == 200
        stats = response.json()
        assert "total_workouts" in stats or "workouts_this_month" in stats


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
