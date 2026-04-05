from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.video_library_api import register_video_library_routes


def _mock_conn(cur):
    conn = Mock()
    cm = Mock()
    cm.__enter__ = Mock(return_value=cur)
    cm.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cm
    return conn


def _mock_conn_raising_on_cursor_enter():
    conn = Mock()
    cm = Mock()
    cm.__enter__ = Mock(side_effect=Exception("cursor enter failed"))
    cm.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cm
    return conn


def _client_with_routes():
    app = FastAPI()
    register_video_library_routes(app)
    return TestClient(app)


class TestVideoLibraryRoutes:
    def test_get_muscle_groups_success(self):
        cur = Mock()
        cur.fetchall.return_value = [{"muscle_group": "chest"}, {"muscle_group": "legs"}]

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/muscle-groups")

        assert r.status_code == 200
        assert r.json() == {"muscle_groups": ["chest", "legs"]}

    def test_get_muscle_groups_error(self):
        with patch("backend.video_library_api.get_conn", side_effect=Exception("db down")):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/muscle-groups")

        assert r.status_code == 500

    def test_search_videos_query_too_short(self):
        with _client_with_routes() as client:
            r = client.get("/api/exercises/videos/search?q=a")

        assert r.status_code == 400
        assert "at least 2 characters" in r.json()["detail"]

    def test_search_videos_success(self):
        cur = Mock()
        cur.fetchall.return_value = [{"id": 1, "name": "Push Up", "video_count": 2}]

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/videos/search?q=push")

        assert r.status_code == 200
        assert r.json()["exercises"][0]["name"] == "Push Up"

    def test_search_videos_error(self):
        with patch("backend.video_library_api.get_conn", side_effect=Exception("query fail")):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/videos/search?q=push")

        assert r.status_code == 500

    def test_get_all_exercises_success(self):
        cur = Mock()
        cur.fetchall.return_value = [{"id": 1, "name": "Squat", "video_count": 1}]

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises")

        assert r.status_code == 200
        assert r.json()["exercises"][0]["name"] == "Squat"

    def test_get_all_exercises_error(self):
        with patch("backend.video_library_api.get_conn", side_effect=Exception("db error")):
            with _client_with_routes() as client:
                r = client.get("/api/exercises")

        assert r.status_code == 500

    def test_get_exercise_details_not_found(self):
        cur = Mock()
        cur.fetchone.return_value = None

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/999")

        assert r.status_code == 404

    def test_get_exercise_details_success_with_videos(self):
        cur = Mock()
        cur.fetchone.return_value = {
            "id": 1,
            "name": "Bench Press",
            "muscle_group": "chest",
            "difficulty": "intermediate",
        }
        cur.fetchall.return_value = [{"id": 10, "title": "Bench Press Tutorial"}]

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/1")

        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Bench Press"
        assert body["videos"][0]["title"] == "Bench Press Tutorial"

    def test_get_exercise_details_generic_error(self):
        with patch("backend.video_library_api.get_conn", return_value=_mock_conn_raising_on_cursor_enter()):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/1")

        assert r.status_code == 500

    def test_get_exercises_by_muscle_group_success(self):
        cur = Mock()
        cur.fetchall.return_value = [{"id": 3, "name": "Biceps Curl", "muscle_group": "arms", "video_count": 1}]

        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur)):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/by-muscle-group/arms")

        assert r.status_code == 200
        assert r.json()["exercises"][0]["muscle_group"] == "arms"

    def test_get_exercises_by_muscle_group_error(self):
        with patch("backend.video_library_api.get_conn", side_effect=Exception("db error")):
            with _client_with_routes() as client:
                r = client.get("/api/exercises/by-muscle-group/chest")

        assert r.status_code == 500

    def test_record_video_view_success_and_not_found(self):
        # success
        cur_ok = Mock()
        cur_ok.fetchone.return_value = {"views": 5}
        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur_ok)):
            with _client_with_routes() as client:
                r = client.post("/api/video/record-view/11")
        assert r.status_code == 200
        assert r.json()["views"] == 5

        # not found
        cur_none = Mock()
        cur_none.fetchone.return_value = None
        with patch("backend.video_library_api.get_conn", return_value=_mock_conn(cur_none)):
            with _client_with_routes() as client:
                r = client.post("/api/video/record-view/11")
        assert r.status_code == 404

    def test_record_video_view_generic_error(self):
        with patch("backend.video_library_api.get_conn", return_value=_mock_conn_raising_on_cursor_enter()):
            with _client_with_routes() as client:
                r = client.post("/api/video/record-view/11")

        assert r.status_code == 500
