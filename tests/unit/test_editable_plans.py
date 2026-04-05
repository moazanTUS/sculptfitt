"""
Unit tests for editable plans module
Tests plan copying, editing, and management functions
"""
import pytest
from unittest.mock import Mock, patch, call
from backend.editable_plans import (
    _get_or_create_exercise,
    ensure_editable_copy,
    get_editable_plan,
    update_day_title,
    add_day_item,
    update_day_item,
    delete_day_item,
    reorder_day_items,
)


def _mock_conn_and_cursor():
    """Build a connection mock that supports nested context-manager usage."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
    return mock_conn, mock_cursor


class TestEditablePlansCopy:
    """Test editable plan creation and copying"""
    
    @patch('backend.editable_plans.get_conn')
    def test_ensure_editable_copy_creates_new(self, mock_get_conn):
        """Should create editable copy when none exists in saved plans."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        
        # 1) Not an AI direct plan, 2) found saved plan, 3) max position query etc.
        mock_cursor.fetchone.side_effect = [
            None,
            {
                "id": 1,
                "plan_id": 10,
                "user_plan_id": None,
                "plan_name": "Starter Plan",
                "days_per_week": 3,
                "primary_focus": "Strength",
            },
            {"m": 0},
        ]
        mock_cursor.fetchall.side_effect = [
            [{"day_number": 1}],
            [{"exercise_id": 7, "sets": 3, "reps": "10", "rest_seconds": 60, "position": 10}],
        ]
        mock_cursor.lastrowid = 123
        
        editable_id = ensure_editable_copy(1, "user_123")
        
        assert mock_cursor.execute.called
        assert editable_id == 123
    
    @patch('backend.editable_plans.get_conn')
    def test_ensure_editable_copy_returns_existing(self, mock_get_conn):
        """Should return existing AI plan ID when saved_id is already user_workout_plans."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {"id": 456}
        
        editable_id = ensure_editable_copy(1, "user_123")
        
        assert editable_id == 456


class TestDayModifications:
    """Test day-level modifications"""
    
    @patch('backend.editable_plans.get_conn')
    def test_update_day_title(self, mock_get_conn):
        """Should update day title successfully"""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        
        update_day_title(1, "user_123", "Upper Body Day")
        
        assert mock_cursor.execute.called
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "UPDATE" in sql_call


class TestDayItemOperations:
    """Test individual exercise/item operations"""
    
    @patch('backend.editable_plans.get_conn')
    def test_add_day_item(self, mock_get_conn):
        """Should add new item to a day"""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn

        # First lookup finds user day, then exercise exists, then max position query.
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "day_type": "user"},
            {"id": 5},
            {"m": 10},
        ]
        mock_cursor.lastrowid = 789

        new_id = add_day_item(
            1,
            "user_123",
            exercise_name="Push-ups",
            muscle_group="chest",
            sets=3,
            reps="15",
            rest_seconds=60,
        )
        
        assert mock_cursor.execute.called
        assert new_id == 789
    
    @patch('backend.editable_plans.get_conn')
    def test_update_day_item(self, mock_get_conn):
        """Should update existing day item"""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn

        mock_cursor.fetchone.return_value = {"id": 5, "exercise_id": 77, "item_type": "user"}
        
        update_data = {
            "exercise_name": "Modified Push-ups",
            "sets": 4,
            "reps": "12",
            "rest_seconds": 75,
        }
        
        update_day_item(5, "user_123", update_data)
        
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
    
    @patch('backend.editable_plans.get_conn')
    def test_delete_day_item(self, mock_get_conn):
        """Should delete day item"""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        
        delete_day_item(5, "user_123")
        
        assert mock_cursor.execute.called
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "DELETE" in sql_call
    
    @patch('backend.editable_plans.get_conn')
    def test_reorder_day_items(self, mock_get_conn):
        """Should reorder items within a day"""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {"id": 1}
        
        new_order = [3, 1, 2]  # New order of item IDs
        
        reorder_day_items(1, "user_123", new_order)
        
        assert mock_cursor.execute.called


# ---------------------------------------------------------------------------
# _get_or_create_exercise
# ---------------------------------------------------------------------------

class TestGetOrCreateExercise:
    def test_returns_existing_exercise(self):
        cur = Mock()
        cur.fetchone.return_value = {"id": 42}
        result = _get_or_create_exercise(cur, "Squat")
        assert result == 42
        # Should SELECT but not INSERT
        calls = [c[0][0] for c in cur.execute.call_args_list]
        assert any("SELECT" in c for c in calls)
        assert not any("INSERT" in c for c in calls)

    def test_creates_new_exercise_when_not_found(self):
        cur = Mock()
        cur.fetchone.return_value = None
        cur.lastrowid = 99
        result = _get_or_create_exercise(cur, "NewExercise", "arms")
        assert result == 99
        calls = [c[0][0] for c in cur.execute.call_args_list]
        assert any("INSERT" in c for c in calls)

    def test_creates_exercise_with_default_muscle_group(self):
        cur = Mock()
        cur.fetchone.return_value = None
        cur.lastrowid = 55
        _get_or_create_exercise(cur, "Mystery Move", None)
        # muscle_group should default to "custom"
        insert_args = cur.execute.call_args_list[-1][0][1]
        assert insert_args[1] == "custom"


# ---------------------------------------------------------------------------
# ensure_editable_copy — extra branches
# ---------------------------------------------------------------------------

class TestEnsureEditableCopyExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_returns_existing_user_plan_id(self, mock_get_conn):
        """When saved plan already has a user_plan_id, return it immediately."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        # First fetchone: not an AI plan; second: saved plan WITH existing user_plan_id
        mock_cursor.fetchone.side_effect = [
            None,
            {"id": 1, "plan_id": 10, "user_plan_id": 77,
             "plan_name": "Plan", "days_per_week": 3, "primary_focus": "Strength"},
        ]
        result = ensure_editable_copy(1, "user_x")
        assert result == 77

    @patch('backend.editable_plans.get_conn')
    def test_raises_when_plan_not_found(self, mock_get_conn):
        """Raises ValueError when saved plan not found."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, None]
        with pytest.raises(ValueError, match="Plan not found"):
            ensure_editable_copy(999, "user_x")

    @patch('backend.editable_plans.get_conn')
    def test_full_clone_with_no_days(self, mock_get_conn):
        """Clone path when the source plan has zero days."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            None,
            {"id": 1, "plan_id": 5, "user_plan_id": None,
             "plan_name": "Empty Plan", "days_per_week": 0, "primary_focus": "core"},
        ]
        mock_cursor.fetchall.return_value = []   # no days
        mock_cursor.lastrowid = 200
        result = ensure_editable_copy(1, "user_x")
        assert result == 200

    @patch('backend.editable_plans.get_conn')
    def test_full_clone_with_multiple_days_and_exercises(self, mock_get_conn):
        """Clone path: creates plan, days, exercises, and links saved row."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            None,
            {"id": 1, "plan_id": 5, "user_plan_id": None,
             "plan_name": "Power", "days_per_week": 2, "primary_focus": "strength"},
        ]
        mock_cursor.fetchall.side_effect = [
            [{"day_number": 1}, {"day_number": 2}],  # unique days
            [{"exercise_id": 3, "sets": 4, "reps": "8", "rest_seconds": 90, "position": 10}],  # day 1 exercises
            [],  # day 2 exercises (empty)
        ]
        mock_cursor.lastrowid = 300
        result = ensure_editable_copy(1, "user_x")
        assert result == 300
        # Should have called UPDATE to link saved plan
        update_calls = [c for c in mock_cursor.execute.call_args_list
                        if "UPDATE user_saved_plans" in c[0][0]]
        assert update_calls


# ---------------------------------------------------------------------------
# get_editable_plan
# ---------------------------------------------------------------------------

class TestGetEditablePlan:
    @patch('backend.editable_plans.ensure_editable_copy')
    @patch('backend.editable_plans.get_conn')
    def test_returns_plan_with_days_and_items(self, mock_get_conn, mock_ensure):
        mock_ensure.return_value = 10
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn

        mock_cursor.fetchone.side_effect = [
            {"id": 10, "name": "Plan A", "days_per_week": 2,
             "primary_focus": "chest", "source_plan_id": 1,
             "created_at": "2024-01-01", "updated_at": "2024-01-01"},
        ]
        mock_cursor.fetchall.side_effect = [
            [{"id": 1, "day_number": 1, "title": "Day 1"}],
            [{"item_id": 5, "exercise_id": 3, "exercise": "Bench Press",
              "muscle_group": "chest", "sets": 3, "reps": "10",
              "rest_seconds": 60, "position": 10, "notes": None}],
        ]

        result = get_editable_plan(1, "user_x")
        assert result["plan"]["id"] == 10
        assert len(result["days"]) == 1
        assert result["days"][0]["day_id"] == 1
        assert len(result["days"][0]["items"]) == 1

    @patch('backend.editable_plans.ensure_editable_copy')
    @patch('backend.editable_plans.get_conn')
    def test_raises_when_plan_not_found_in_db(self, mock_get_conn, mock_ensure):
        mock_ensure.return_value = 99
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None  # plan not found

        with pytest.raises(ValueError, match="Plan not found"):
            get_editable_plan(1, "user_x")


# ---------------------------------------------------------------------------
# update_day_title — extra branches
# ---------------------------------------------------------------------------

class TestUpdateDayTitleExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_update_custom_workout_day(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        # user_workout_days lookup: not found; custom_workout_days: found
        mock_cursor.fetchone.side_effect = [None, {"id": 5}]

        update_day_title(5, "user_x", "Custom Day Title")

        update_calls = [c[0][0] for c in mock_cursor.execute.call_args_list
                        if "UPDATE" in c[0][0]]
        assert any("custom_workout_days" in c for c in update_calls)

    @patch('backend.editable_plans.get_conn')
    def test_raises_when_day_not_found(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, None]

        with pytest.raises(ValueError, match="Day not found"):
            update_day_title(999, "user_x", "Title")


# ---------------------------------------------------------------------------
# add_day_item — extra branches
# ---------------------------------------------------------------------------

class TestAddDayItemExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_add_item_to_custom_day(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        # user_workout_days: not found; custom_workout_days: found
        mock_cursor.fetchone.side_effect = [
            None,
            {"id": 7, "day_type": "custom"},
            {"m": 0},
        ]
        mock_cursor.lastrowid = 55

        result = add_day_item(
            7, "user_x",
            exercise_name="Dips", muscle_group=None,
            sets=3, reps="12", rest_seconds=60,
        )
        assert result == 55
        insert_calls = [c[0][0] for c in mock_cursor.execute.call_args_list
                        if "INSERT INTO custom_workout_exercises" in c[0][0]]
        assert insert_calls

    @patch('backend.editable_plans.get_conn')
    def test_add_item_raises_when_day_not_found(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, None]

        with pytest.raises(ValueError, match="Day not found"):
            add_day_item(999, "user_x", exercise_name="X", muscle_group=None,
                         sets=3, reps="10", rest_seconds=60)

    @patch('backend.editable_plans.get_conn')
    def test_add_item_creates_new_exercise(self, mock_get_conn):
        """When exercise doesn't exist, _get_or_create_exercise inserts it."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "day_type": "user"},  # user day found
            None,                            # exercise SELECT → not found
            {"m": 20},                       # max position
        ]
        mock_cursor.lastrowid = 101

        result = add_day_item(
            1, "user_x",
            exercise_name="Brand New Move", muscle_group="legs",
            sets=4, reps="8", rest_seconds=90,
        )
        assert result == 101


# ---------------------------------------------------------------------------
# update_day_item — extra branches
# ---------------------------------------------------------------------------

class TestUpdateDayItemExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_empty_patch_no_ops(self, mock_get_conn):
        """Passing an empty (or all-disallowed-fields) patch should be a no-op."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        # Should return early without any DB calls
        update_day_item(1, "user_x", {"unknown_field": "ignored"})
        mock_cursor.execute.assert_not_called()

    @patch('backend.editable_plans.get_conn')
    def test_update_custom_item_by_type(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = {"id": 3, "exercise_name": "Dip", "item_type": "custom"}

        update_day_item(3, "user_x", {"sets": 4, "reps": "10"}, item_type="custom")

        update_calls = [c[0][0] for c in mock_cursor.execute.call_args_list
                        if "UPDATE" in c[0][0]]
        assert any("custom_workout_exercises" in c for c in update_calls)

    @patch('backend.editable_plans.get_conn')
    def test_update_user_item_by_type(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            {"id": 9, "exercise_id": 5, "item_type": "user"},
            {"id": 5},  # exercise lookup in _get_or_create_exercise
        ]

        update_day_item(9, "user_x", {"exercise_name": "Pull-Up", "sets": 3}, item_type="user")

        update_calls = [c[0][0] for c in mock_cursor.execute.call_args_list
                        if "UPDATE" in c[0][0]]
        assert any("user_workout_day_items" in c for c in update_calls)

    @patch('backend.editable_plans.get_conn')
    def test_update_item_not_found_raises(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, None]

        with pytest.raises(ValueError, match="Item not found"):
            update_day_item(999, "user_x", {"sets": 3})

    @patch('backend.editable_plans.get_conn')
    def test_update_item_fallback_finds_custom(self, mock_get_conn):
        """Fallback path: user table miss → custom table hit."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_cursor.rowcount = 1
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            None,   # user_workout_day_items: not found
            {"id": 7, "exercise_name": "Cable Row", "item_type": "custom"},  # custom: found
        ]

        update_day_item(7, "user_x", {"rest_seconds": 90})

        update_calls = [c[0][0] for c in mock_cursor.execute.call_args_list
                        if "UPDATE" in c[0][0]]
        assert any("custom_workout_exercises" in c for c in update_calls)


# ---------------------------------------------------------------------------
# delete_day_item — extra branches
# ---------------------------------------------------------------------------

class TestDeleteDayItemExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_delete_custom_item_fallback(self, mock_get_conn):
        """rowcount=0 from user table triggers custom table delete."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.rowcount = 0  # user table miss → try custom

        # Second execute (custom), set rowcount = 1
        original_execute = mock_cursor.execute

        call_count = [0]

        def counting_execute(sql, args=None):
            call_count[0] += 1
            if call_count[0] == 2:
                mock_cursor.rowcount = 1

        mock_cursor.execute.side_effect = counting_execute

        delete_day_item(5, "user_x")
        assert call_count[0] == 2

    @patch('backend.editable_plans.get_conn')
    def test_delete_item_not_found_raises(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.rowcount = 0

        with pytest.raises(ValueError, match="Item not found"):
            delete_day_item(999, "user_x")


# ---------------------------------------------------------------------------
# reorder_day_items — extra branches
# ---------------------------------------------------------------------------

class TestReorderDayItemsExtraBranches:
    @patch('backend.editable_plans.get_conn')
    def test_empty_list_is_noop(self, mock_get_conn):
        """Empty ordered_item_ids should return immediately without DB calls."""
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn

        reorder_day_items(1, "user_x", [])
        mock_get_conn.assert_not_called()

    @patch('backend.editable_plans.get_conn')
    def test_day_not_found_raises(self, mock_get_conn):
        mock_conn, mock_cursor = _mock_conn_and_cursor()
        mock_get_conn.return_value = mock_conn
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Day not found"):
            reorder_day_items(999, "user_x", [1, 2, 3])
