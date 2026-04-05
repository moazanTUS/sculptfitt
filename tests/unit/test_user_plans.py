import datetime as dt
from unittest.mock import Mock, patch

from backend import user_plans


def _mock_conn_with_cursor(cur):
    conn = Mock()
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)

    cm = Mock()
    cm.__enter__ = Mock(return_value=cur)
    cm.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cm
    return conn


class TestUserPlansModule:
    def test_save_user_plan_pads_focus_areas(self):
        cur = Mock()
        cur.lastrowid = 42
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            saved_id = user_plans.save_user_plan("user_1", 10, "lean", ["chest"])

        assert saved_id == 42
        args = cur.execute.call_args.args
        assert "INSERT INTO user_saved_plans" in args[0]
        assert args[1] == ("user_1", 10, "lean", "chest", "", "")

    def test_list_user_plans_combines_and_sorts_desc(self):
        cur = Mock()
        user_rows = [
            {"id": "ai_2", "created_at": dt.datetime(2026, 4, 2), "plan_name": "AI New"},
            {"id": "ai_1", "created_at": dt.datetime(2026, 4, 1), "plan_name": "AI Old"},
        ]
        custom_rows = [
            {"id": "custom_1", "created_at": dt.datetime(2026, 4, 3), "plan_name": "Custom Newest"},
        ]
        cur.fetchall.side_effect = [user_rows, custom_rows]
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            result = user_plans.list_user_plans("user_1")

        assert [r["id"] for r in result] == ["custom_1", "ai_2", "ai_1"]

    def test_get_saved_plan_returns_single_row(self):
        cur = Mock()
        cur.fetchone.return_value = {"id": 5, "plan_id": 2}
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            row = user_plans.get_saved_plan(5, "user_1")

        assert row == {"id": 5, "plan_id": 2}

    def test_delete_user_plan_custom_success_and_not_found(self):
        # success path
        cur_ok = Mock()
        cur_ok.rowcount = 1
        conn_ok = _mock_conn_with_cursor(cur_ok)

        with patch("backend.user_plans.get_conn", return_value=conn_ok):
            assert user_plans.delete_user_plan("custom_9", "user_1") is True
            conn_ok.commit.assert_called_once()

        # not found path
        cur_none = Mock()
        cur_none.rowcount = 0
        conn_none = _mock_conn_with_cursor(cur_none)

        with patch("backend.user_plans.get_conn", return_value=conn_none):
            assert user_plans.delete_user_plan("custom_9", "user_1") is False

    def test_delete_user_plan_ai_success(self):
        cur = Mock()
        cur.rowcount = 1
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("ai_7", "user_1") is True
            conn.commit.assert_called_once()

    def test_delete_user_plan_ai_not_found(self):
        cur = Mock()
        cur.rowcount = 0
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("ai_7", "user_1") is False

    def test_delete_user_plan_saved_not_found(self):
        cur = Mock()
        cur.fetchone.return_value = None
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("saved_22", "user_1") is False

    def test_delete_user_plan_saved_with_editable_copy(self):
        cur = Mock()
        cur.fetchone.return_value = {"user_plan_id": 99}
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("saved_22", "user_1") is True

        assert conn.commit.called
        # Expect at least select + delete saved + delete editable
        assert cur.execute.call_count >= 3

    def test_delete_user_plan_saved_without_editable_copy(self):
        cur = Mock()
        cur.fetchone.return_value = {"user_plan_id": None}
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("saved_22", "user_1") is True

        # Should not attempt editable-plan delete when user_plan_id is None
        executed_sql = [c.args[0] for c in cur.execute.call_args_list]
        assert not any("DELETE FROM user_workout_plans" in sql for sql in executed_sql)

    def test_delete_user_plan_fallback_plain_numeric_id(self):
        cur = Mock()
        cur.rowcount = 1
        conn = _mock_conn_with_cursor(cur)

        with patch("backend.user_plans.get_conn", return_value=conn):
            assert user_plans.delete_user_plan("123", "user_1") is True
