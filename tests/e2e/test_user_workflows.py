"""
End-to-end tests for complete user workflows
Tests full user journeys from authentication to result
"""
import pytest
from fastapi.testclient import TestClient
import time
from unittest.mock import patch


@pytest.mark.e2e
class TestCompleteWorkoutPlanJourney:
    """Test complete user journey for workout plans"""
    
    def test_user_selects_saves_and_edits_plan(self, client, mock_clerk_user):
        """
        Complete workflow:
        1. User saves a workout plan
        2. User lists their saved plans
        3. User creates editable copy
        4. User modifies the plan
        5. User verifies changes
        """
        # Step 1: Find an available template plan
        available_response = client.get("/api/available-plans")
        assert available_response.status_code == 200
        available = available_response.json()
        assert available.get("success") is True

        all_plan_groups = list(available.get("plans", {}).values())
        assert all_plan_groups and all_plan_groups[0]
        plan_id = all_plan_groups[0][0]["id"]

        # Step 2: Select and save that plan
        select_response = client.post("/api/select-plan", data={"plan_id": plan_id})
        assert select_response.status_code == 200
        assert select_response.json().get("success") is True

        # Step 3: Verify it appears in user's plan list
        list_response = client.get("/api/my-plans")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload.get("success") is True
        items = payload.get("items", [])
        assert items

        selected = items[0]
        saved_id = selected["id"]

        # Step 4: Fetch editable details and modify day title
        editable_before = client.get(f"/api/my-plans/{saved_id}/editable")
        assert editable_before.status_code == 200
        editable_data = editable_before.json()
        assert editable_data.get("success") is True
        assert editable_data.get("days")

        day_id = editable_data["days"][0]["day_id"]
        new_title = "Modified Day 1"
        patch_response = client.patch(f"/api/edit/days/{day_id}", json={"title": new_title})
        assert patch_response.status_code == 200
        assert patch_response.json().get("success") is True

        # Step 5: Verify update persisted
        editable_after = client.get(f"/api/my-plans/{saved_id}/editable")
        assert editable_after.status_code == 200
        after_data = editable_after.json()
        assert after_data.get("success") is True
        assert after_data["days"][0]["title"] == new_title


@pytest.mark.e2e
class TestWorkoutLoggingJourney:
    """Test workout logging and progress tracking workflow"""
    
    def test_log_multiple_workouts_and_view_progress(self, client, mock_clerk_user):
        """
        Complete workout logging workflow:
        1. Log workout session
        2. Log multiple exercises
        3. View workout history
        4. Get progress statistics
        """
        
        # Step 1: Create a custom workout with one exercise
        create_response = client.post(
            "/api/custom-workouts",
            data={
                "name": "E2E Logging Workout",
                "description": "For logging workflow",
                "exercises": "[{\"exercise_name\": \"Bench Press\", \"sets\": 4, \"reps\": \"8\", \"rest_seconds\": 90, \"position\": 1}]",
            },
        )
        assert create_response.status_code == 200
        workout_id = create_response.json()["workout_id"]

        # Step 2: Start workout session
        session_response = client.post(
            "/api/workout-sessions",
            data={
                "workout_plan_id": workout_id,
                "workout_plan_type": "custom",
                "workout_name": "E2E Logging Workout",
                "day_number": 1,
            },
        )
        assert session_response.status_code == 200
        session_payload = session_response.json()
        assert session_payload.get("success") is True
        session_id = session_payload["session_id"]
        assert session_payload.get("exercises")
        session_exercise_id = session_payload["exercises"][0]["id"]

        # Step 3: Log completed exercise
        log_response = client.post(
            f"/api/workout-sessions/{session_id}/exercises/{session_exercise_id}/log",
            data={
                "completed_sets": 4,
                "completed_reps": "8",
                "weight_used": 60,
                "rpe": 8,
                "notes": "Solid session",
            },
        )
        assert log_response.status_code == 200
        assert log_response.json().get("success") is True

        # Step 4: Complete session and verify history/stats
        complete_response = client.post(
            f"/api/workout-sessions/{session_id}/complete",
            data={"duration_minutes": 30, "rating": 4, "notes": "Completed"},
        )
        assert complete_response.status_code == 200
        assert complete_response.json().get("success") is True

        history = client.get("/api/workout-sessions")
        assert history.status_code == 200
        history_payload = history.json()
        assert history_payload.get("success") is True
        assert any(s["id"] == session_id for s in history_payload.get("sessions", []))

        stats = client.get("/api/progress/stats")
        assert stats.status_code == 200
        stats_payload = stats.json()
        assert stats_payload.get("success") is True
        assert "stats" in stats_payload


@pytest.mark.e2e
class TestVideoAnalysisJourney:
    """Test complete video upload and analysis workflow"""
    
    @pytest.mark.slow
    def test_upload_analyze_get_feedback(self, client, mock_clerk_user, mock_video_file):
        """
        Complete video analysis workflow:
        1. Upload workout video
        2. Wait for processing
        3. Get analysis results
        4. Receive feedback
        """
        
        class _FakeAnalyzer:
            def __init__(self, *args, **kwargs):
                pass

            def analyze(self, exercise: str):
                return {
                    "success": True,
                    "feedback": f"Mocked feedback for {exercise}",
                    "raw_response": "ok",
                    "num_frames_analyzed": 3,
                    "detected_reps": 5,
                }

        with patch("backend.main.GeminiFormAnalyzer", _FakeAnalyzer):
            upload_response = client.post(
                "/api/analyze-video",
                files={"file": ("workout.mp4", mock_video_file["file"], "video/mp4")},
                data={"exercise": "pushup", "rep_count": 5},
            )

        assert upload_response.status_code == 200
        payload = upload_response.json()
        assert payload.get("success") is True
        assert "feedback" in payload
        assert payload.get("exercise") == "pushup"


@pytest.mark.e2e  
class TestCustomWorkoutFullCycle:
    """Test creating, using, and managing custom workouts"""
    
    def test_create_use_modify_delete_workout(self, client, mock_clerk_user):
        """
        Complete custom workout lifecycle:
        1. Create custom workout
        2. Add to training plan
        3. Log workout session
        4. Modify workout
        5. Delete workout
        """
        
        # Step 1: Create custom workout
        create_response = client.post(
            "/api/custom-workouts",
            data={
                "name": "E2E Custom Workout",
                "description": "Test workout for E2E testing",
                "exercises": "[{\"exercise_name\": \"Custom Push-up\", \"sets\": 3, \"reps\": \"15\", \"position\": 1}]",
            },
        )
        assert create_response.status_code == 200
        workout_id = create_response.json()["workout_id"]
        
        # Step 2: Verify it appears in list
        list_response = client.get("/api/custom-workouts")
        assert list_response.status_code == 200
        workouts_payload = list_response.json()
        assert workouts_payload.get("success") is True
        workouts = workouts_payload.get("workouts", [])
        assert any(w["name"] == "E2E Custom Workout" for w in workouts)
        
        # Step 3: Add another exercise to day 1 (modify workflow)
        add_response = client.post(
            f"/api/custom-workouts/{workout_id}/exercises",
            data={
                "day_number": 1,
                "exercise_name": "Custom Squat",
                "sets": 4,
                "reps": "12",
                "rest_seconds": 75,
            },
        )
        assert add_response.status_code == 200
        assert add_response.json().get("success") is True

        detail_response = client.get(f"/api/custom-workouts/{workout_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        assert detail_payload.get("success") is True
        assert detail_payload.get("days")
        assert len(detail_payload["days"][0].get("exercises", [])) >= 2
        
        # Step 4: Delete workout
        delete_response = client.delete(f"/api/custom-workouts/{workout_id}")
        assert delete_response.status_code == 200
        assert delete_response.json().get("success") is True
        
        # Verify deletion
        get_response = client.get(f"/api/custom-workouts/{workout_id}")
        assert get_response.status_code == 404


@pytest.mark.e2e
class TestAuthenticationFlow:
    """Test authentication and authorization workflows"""
    
    def test_protected_endpoint_without_auth(self, unauthenticated_client):
        """Should reject requests without authentication"""
        response = unauthenticated_client.get("/api/my-plans")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client):
        """Should allow requests with valid authentication"""
        response = client.get("/api/my-plans")
        assert response.status_code == 200
    
    def test_invalid_token_handling(self, unauthenticated_client):
        """Should reject invalid authentication tokens"""
        response = unauthenticated_client.get(
            "/api/my-plans",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401
