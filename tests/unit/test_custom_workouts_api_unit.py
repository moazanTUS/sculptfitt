from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.custom_workouts_api import register_custom_workout_routes


def _mock_conn(cur):
    conn = Mock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)

    cm = Mock()
    cm.__enter__ = Mock(return_value=cur)
    cm.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cm
    return conn


def _client():
    app = FastAPI()

    def current_user():
        return {"clerk_user_id": "user_test123"}

    register_custom_workout_routes(app, current_user)
    return TestClient(app)


class TestCustomWorkoutRoutesUnit:
    def test_create_custom_workout_invalid_json_returns_400(self):
        with _client() as client:
            r = client.post(
                "/api/custom-workouts",
                data={"name": "Bad JSON", "description": "x", "exercises": "{"},
            )

        assert r.status_code == 400
        assert r.json()["success"] is False

    def test_get_custom_workouts_db_error_returns_400(self):
        with patch("backend.custom_workouts_api.get_conn", side_effect=Exception("db down")):
            with _client() as client:
                r = client.get("/api/custom-workouts")

        assert r.status_code == 400
        assert r.json()["success"] is False

    def test_get_custom_workout_db_error_returns_400(self):
        with patch("backend.custom_workouts_api.get_conn", side_effect=Exception("boom")):
            with _client() as client:
                r = client.get("/api/custom-workouts/1")

        assert r.status_code == 400
        assert r.json()["success"] is False

    def test_add_exercise_unauthorized_and_day_not_found(self):
        # Unauthorized path
        cur_unauth = Mock()
        cur_unauth.fetchone.return_value = None
        with patch("backend.custom_workouts_api.get_conn", return_value=_mock_conn(cur_unauth)):
            with _client() as client:
                r = client.post(
                    "/api/custom-workouts/1/exercises",
                    data={"day_number": 1, "exercise_name": "Push-up"},
                )
        assert r.status_code == 403

        # Day not found path
        cur_day_missing = Mock()
        cur_day_missing.fetchone.side_effect = [{"id": 1}, None]
        with patch("backend.custom_workouts_api.get_conn", return_value=_mock_conn(cur_day_missing)):
            with _client() as client:
                r = client.post(
                    "/api/custom-workouts/1/exercises",
                    data={"day_number": 1, "exercise_name": "Push-up"},
                )
        assert r.status_code == 404

    def test_add_exercise_exception_returns_400(self):
        with patch("backend.custom_workouts_api.get_conn", side_effect=Exception("db error")):
            with _client() as client:
                r = client.post(
                    "/api/custom-workouts/1/exercises",
                    data={"day_number": 1, "exercise_name": "Push-up"},
                )

        assert r.status_code == 400

    def test_delete_custom_workout_unauthorized_and_error(self):
        cur_unauth = Mock()
        cur_unauth.fetchone.return_value = None
        with patch("backend.custom_workouts_api.get_conn", return_value=_mock_conn(cur_unauth)):
            with _client() as client:
                r = client.delete("/api/custom-workouts/1")
        assert r.status_code == 403

        with patch("backend.custom_workouts_api.get_conn", side_effect=Exception("delete error")):
            with _client() as client:
                r = client.delete("/api/custom-workouts/1")
        assert r.status_code == 400
