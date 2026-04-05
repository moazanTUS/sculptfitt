"""
Unit tests for editable plans module
Tests plan copying, editing, and management functions
"""
import pytest
from unittest.mock import Mock, patch
from backend.editable_plans import (
    ensure_editable_copy,
    update_day_title,
    add_day_item,
    update_day_item,
    delete_day_item,
    reorder_day_items
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
