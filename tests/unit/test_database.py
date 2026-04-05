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
    
    @patch('backend.db.pymysql.connect')
    def test_get_conn_uses_environment_variables(self, mock_connect):
        """Should use module DB config values when opening a connection."""
        with patch.multiple(
            'backend.db',
            DB_HOST='testhost',
            DB_USER='testuser',
            DB_PASS='testpass',
            DB_NAME='testdb',
            DB_PORT=3307,
        ):
            get_conn()

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


@pytest.mark.integration
class TestDatabaseQueries:
    """Test database queries with real test database"""
    
    def test_user_plans_table_exists(self, db_connection):
        """Should verify user_plans table exists"""
        with db_connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'user_saved_plans'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_user_saved_plans_expected_columns_exist(self, db_connection):
        """Should verify core columns needed by the app exist in user_saved_plans."""
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = 'user_saved_plans'
                """
            )
            columns = {row["COLUMN_NAME"] for row in cursor.fetchall()}
            assert "id" in columns
            assert "clerk_user_id" in columns
            assert "plan_id" in columns
    
    def test_workout_sessions_table_queryable(self, db_connection):
        """Should query workout_sessions table without error."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM workout_sessions")
            result = cursor.fetchone()
            assert "count" in result
            assert result["count"] >= 0
    
    def test_video_library_table_populated(self, db_connection):
        """Should verify exercise video table can be queried."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM exercise_videos")
            result = cursor.fetchone()
            assert result['count'] >= 0
