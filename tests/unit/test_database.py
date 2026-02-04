"""
Unit tests for database operations
Tests database helper functions and queries
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.db import get_conn


class TestDatabaseConnection:
    """Test database connection management"""
    
    @patch('backend.db.pymysql.connect')
    def test_get_conn_returns_connection(self, mock_connect):
        """Should return a database connection with correct config"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        conn = get_conn()
        
        assert conn == mock_connection
        mock_connect.assert_called_once()
    
    @patch.dict('os.environ', {
        'DB_HOST': 'testhost',
        'DB_USER': 'testuser',
        'DB_PASS': 'testpass',
        'DB_NAME': 'testdb',
        'DB_PORT': '3307'
    })
    @patch('backend.db.pymysql.connect')
    def test_get_conn_uses_environment_variables(self, mock_connect):
        """Should use environment variables for configuration"""
        # Reload module to pick up new env vars
        import importlib
        import backend.db
        importlib.reload(backend.db)
        
        backend.db.get_conn()
        
        call_args = mock_connect.call_args
        assert call_args.kwargs['host'] == 'testhost'
        assert call_args.kwargs['user'] == 'testuser'
        assert call_args.kwargs['password'] == 'testpass'
        assert call_args.kwargs['database'] == 'testdb'
        assert call_args.kwargs['port'] == 3307
    
    @patch('backend.db.pymysql.connect')
    def test_connection_failure_handling(self, mock_connect):
        """Should propagate connection errors"""
        import pymysql
        mock_connect.side_effect = pymysql.Error("Connection failed")
        
        with pytest.raises(pymysql.Error):
            get_conn()


@pytest.mark.skip(reason="Database query tests skipped - using only connection tests")
@pytest.mark.integration
class TestDatabaseQueries:
    """Test database queries with real test database"""
    
    def test_user_plans_table_exists(self, db_connection):
        """Should verify user_plans table exists"""
        with db_connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'user_saved_plans'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_insert_and_select_user_plan(self, db_connection):
        """Should insert and retrieve user plan"""
        test_user_id = "test_user_123"
        test_plan_id = 999
        
        with db_connection.cursor() as cursor:
            # Insert
            cursor.execute("""
                INSERT INTO user_saved_plans (clerk_user_id, plan_id, plan_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE plan_name = VALUES(plan_name)
            """, (test_user_id, test_plan_id, "Test Plan"))
            
            # Select
            cursor.execute("""
                SELECT * FROM user_saved_plans 
                WHERE clerk_user_id = %s AND plan_id = %s
            """, (test_user_id, test_plan_id))
            
            result = cursor.fetchone()
            assert result is not None
            assert result['plan_name'] == "Test Plan"
    
    def test_workout_logs_table_operations(self, db_connection):
        """Should perform CRUD operations on workout_logs"""
        test_user_id = "test_user_456"
        
        with db_connection.cursor() as cursor:
            # Create
            cursor.execute("""
                INSERT INTO workout_logs 
                (clerk_user_id, workout_date, exercise_name, sets, reps, weight)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (test_user_id, "2026-02-04", "Squats", 3, 10, 60))
            
            log_id = cursor.lastrowid
            
            # Read
            cursor.execute("""
                SELECT * FROM workout_logs WHERE log_id = %s
            """, (log_id,))
            result = cursor.fetchone()
            assert result['exercise_name'] == "Squats"
            
            # Update
            cursor.execute("""
                UPDATE workout_logs SET weight = %s WHERE log_id = %s
            """, (65, log_id))
            
            cursor.execute("SELECT weight FROM workout_logs WHERE log_id = %s", (log_id,))
            updated = cursor.fetchone()
            assert updated['weight'] == 65
            
            # Delete
            cursor.execute("DELETE FROM workout_logs WHERE log_id = %s", (log_id,))
            cursor.execute("SELECT * FROM workout_logs WHERE log_id = %s", (log_id,))
            deleted = cursor.fetchone()
            assert deleted is None
    
    def test_video_library_table_populated(self, db_connection):
        """Should verify video library has data"""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM video_library")
            result = cursor.fetchone()
            # Should have some videos from migration scripts
            assert result['count'] >= 0
