"""
Unit tests for workout_logging_api.py
Covers all routes via a minimal FastAPI app with mocked DB connections.
"""
from unittest.mock import Mock, patch, MagicMock
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.workout_logging_api import register_workout_logging_routes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_conn(cur):
    conn = Mock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)
    cm = Mock()
    cm.__enter__ = Mock(return_value=cur)
    cm.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cm
    return conn


def _make_client():
    app = FastAPI()

    def current_user():
        return {"clerk_user_id": "user_test123"}

    register_workout_logging_routes(app, current_user)
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/workout-sessions  POST
# ---------------------------------------------------------------------------

class TestStartWorkoutSession:
    def test_start_session_ai_plan_success(self):
        cur = Mock()
        cur.lastrowid = 42
        cur.fetchall.return_value = [
            {"exercise_id": 1, "name": "Bench Press", "sets": 3,
             "reps": "10", "rest_seconds": 60, "position": 1}
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post("/api/workout-sessions", data={
                    "workout_plan_id": 7,
                    "workout_plan_type": "ai",
                    "workout_name": "Chest Day",
                    "day_number": 1,
                })

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["session_id"] == 42

    def test_start_session_custom_plan_success(self):
        cur = Mock()
        cur.lastrowid = 99
        cur.fetchall.return_value = [
            {"exercise_id": None, "exercise_name": "Dips", "sets": 4,
             "reps": "12", "rest_seconds": 90, "position": 1}
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post("/api/workout-sessions", data={
                    "workout_plan_id": 3,
                    "workout_plan_type": "custom",
                    "workout_name": "My Custom",
                    "day_number": 2,
                })

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["session_id"] == 99

    def test_start_session_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("db down")):
            with _make_client() as client:
                r = client.post("/api/workout-sessions", data={
                    "workout_plan_id": 1,
                    "workout_plan_type": "ai",
                    "workout_name": "Fail",
                    "day_number": 1,
                })

        assert r.status_code == 400
        assert r.json()["success"] is False


# ---------------------------------------------------------------------------
# /api/workout-sessions  GET
# ---------------------------------------------------------------------------

class TestListWorkoutSessions:
    def test_list_sessions_success(self):
        cur = Mock()
        cur.fetchall.return_value = [
            {"id": 1, "workout_name": "Leg Day", "workout_plan_type": "ai",
             "day_number": 1, "session_date": "2024-01-01",
             "completed_at": None, "duration_minutes": None,
             "rating": None, "notes": ""},
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.get("/api/workout-sessions")

        assert r.status_code == 200
        assert r.json()["success"] is True
        assert len(r.json()["sessions"]) == 1

    def test_list_sessions_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("boom")):
            with _make_client() as client:
                r = client.get("/api/workout-sessions")

        assert r.status_code == 400
        assert r.json()["success"] is False


# ---------------------------------------------------------------------------
# /api/workout-sessions/{session_id}  GET
# ---------------------------------------------------------------------------

class TestGetWorkoutSession:
    def test_get_session_success(self):
        cur = Mock()
        cur.fetchone.return_value = {
            "id": 5, "workout_name": "Push Day", "workout_plan_type": "ai",
            "day_number": 1, "session_date": "2024-01-01",
            "completed_at": None, "duration_minutes": None,
            "rating": None, "notes": "",
        }
        cur.fetchall.return_value = [
            {"id": 1, "exercise_name": "Bench", "planned_sets": 3,
             "planned_reps": "10", "planned_rest_seconds": 60,
             "completed_sets": None, "completed_reps": None,
             "weight_used": None, "rpe": None, "notes": "", "position": 1},
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.get("/api/workout-sessions/5")

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["session"]["id"] == 5

    def test_get_session_not_found_returns_404(self):
        cur = Mock()
        cur.fetchone.return_value = None

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.get("/api/workout-sessions/999")

        assert r.status_code == 404

    def test_get_session_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("crash")):
            with _make_client() as client:
                r = client.get("/api/workout-sessions/1")

        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/workout-sessions/{session_id}  DELETE
# ---------------------------------------------------------------------------

class TestDeleteWorkoutSession:
    def test_delete_session_success(self):
        cur = Mock()
        cur.fetchone.return_value = {"id": 5}

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.delete("/api/workout-sessions/5")

        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_delete_session_not_found_returns_404(self):
        cur = Mock()
        cur.fetchone.return_value = None

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.delete("/api/workout-sessions/999")

        assert r.status_code == 404

    def test_delete_session_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("err")):
            with _make_client() as client:
                r = client.delete("/api/workout-sessions/1")

        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/workout-sessions/{session_id}/exercises/{exercise_id}/log  POST
# ---------------------------------------------------------------------------

class TestLogExerciseCompletion:
    def test_log_exercise_success(self):
        cur = Mock()
        cur.fetchone.side_effect = [
            {"id": 5},                                         # session ownership check
            {"exercise_id": 1, "exercise_name": "Bench Press"},  # exercise lookup
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/5/exercises/1/log",
                    data={
                        "completed_sets": 3,
                        "completed_reps": "10",
                        "weight_used": 80.0,
                        "rpe": 7,
                        "notes": "felt good",
                    },
                )

        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_log_exercise_no_weight(self):
        """Log without weight — pr_date should be None."""
        cur = Mock()
        cur.fetchone.side_effect = [
            {"id": 5},
            {"exercise_id": None, "exercise_name": "Bodyweight Squat"},
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/5/exercises/2/log",
                    data={"completed_sets": 3, "completed_reps": "15"},
                )

        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_log_exercise_session_not_found_returns_404(self):
        cur = Mock()
        cur.fetchone.return_value = None

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/999/exercises/1/log",
                    data={"completed_sets": 3, "completed_reps": "10"},
                )

        assert r.status_code == 404

    def test_log_exercise_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("fail")):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/1/exercises/1/log",
                    data={"completed_sets": 3, "completed_reps": "10"},
                )

        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/workout-sessions/{session_id}/complete  POST
# ---------------------------------------------------------------------------

class TestCompleteWorkoutSession:
    def test_complete_session_success(self):
        cur = Mock()
        cur.rowcount = 1

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/5/complete",
                    data={"duration_minutes": 45, "rating": 4, "notes": "great session"},
                )

        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_complete_session_not_found_returns_404(self):
        cur = Mock()
        cur.rowcount = 0

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/999/complete",
                    data={"duration_minutes": 30},
                )

        assert r.status_code == 404

    def test_complete_session_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("err")):
            with _make_client() as client:
                r = client.post(
                    "/api/workout-sessions/1/complete",
                    data={"duration_minutes": 10},
                )

        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/progress/stats  GET
# ---------------------------------------------------------------------------

class TestGetProgressStats:
    def test_get_stats_success(self):
        cur = Mock()
        cur.fetchone.return_value = {
            "total_workouts": 10,
            "total_minutes": 300,
            "average_rating": 4.2,
        }
        cur.fetchall.side_effect = [
            [{"exercise_name": "Bench", "total_times_completed": 5,
              "personal_record_weight": 100.0}],
            [{"workout_date": "2024-01-07", "count": 2}],
        ]

        with patch("backend.workout_logging_api.get_conn", return_value=_mock_conn(cur)):
            with _make_client() as client:
                r = client.get("/api/progress/stats")

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["stats"]["total_workouts"] == 10

    def test_get_stats_db_error_returns_400(self):
        with patch("backend.workout_logging_api.get_conn", side_effect=Exception("gone")):
            with _make_client() as client:
                r = client.get("/api/progress/stats")

        assert r.status_code == 400
        assert r.json()["success"] is False
