"""
Global test fixtures and configuration
Provides shared fixtures for database, FastAPI client, authentication, etc.
"""
import pytest
import pymysql
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from typing import Generator

# Set test environment variables before importing app
os.environ["TESTING"] = "1"
os.environ["DB_NAME"] = os.getenv("TEST_DB_NAME", "sculpfit_test")


@pytest.fixture(scope="session")
def test_db_config():
    """Test database configuration"""
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("TEST_DB_NAME", "sculpfit_test"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }


@pytest.fixture(scope="session")
def setup_test_database(test_db_config):
    """
    Create test database and tables before all tests
    Drop database after all tests complete
    """
    # Connect without database to create it
    conn = pymysql.connect(
        host=test_db_config["host"],
        user=test_db_config["user"],
        password=test_db_config["password"] if test_db_config["password"] else None,
        port=test_db_config["port"],
    )
    
    try:
        with conn.cursor() as cursor:
            # Drop and recreate test database
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db_config['database']}")
            cursor.execute(f"CREATE DATABASE {test_db_config['database']}")
        conn.commit()
        
        # Run initialization script
        conn.select_db(test_db_config['database'])
        with open("init_database.sql", "r") as f:
            sql_script = f.read()
            # Execute each statement separately
            for statement in sql_script.split(';'):
                if statement.strip():
                    with conn.cursor() as cursor:
                        cursor.execute(statement)
        conn.commit()
        
        yield conn
        
    finally:
        # Cleanup: drop test database
        with conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db_config['database']}")
        conn.commit()
        conn.close()


@pytest.fixture
def db_connection(setup_test_database, test_db_config):
    """
    Provide a fresh database connection for each test
    Automatically rolls back changes after each test
    """
    conn = pymysql.connect(
        host=test_db_config["host"],
        user=test_db_config["user"],
        password=test_db_config["password"] if test_db_config["password"] else None,
        database=test_db_config["database"],
        port=test_db_config["port"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    
    yield conn
    
    # Rollback any changes and close
    conn.rollback()
    conn.close()


@pytest.fixture
def mock_clerk_user():
    """Mock authenticated Clerk user for testing protected endpoints"""
    return {
        "clerk_user_id": "user_test123",
        "claims": {
            "sub": "user_test123",
            "email": "test@example.com",
        }
    }


@pytest.fixture
def mock_auth(mock_clerk_user):
    """
    Mock Clerk authentication dependency
    Use with app.dependency_overrides
    """
    def _mock_require_clerk_user(request):
        return mock_clerk_user
    return _mock_require_clerk_user


@pytest.fixture
def client(mock_auth):
    """
    FastAPI test client with mocked authentication
    """
    from backend.main import app
    from backend.clerk_auth import require_clerk_user
    
    # Override authentication dependency
    app.dependency_overrides[require_clerk_user] = mock_auth
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """
    FastAPI test client without authentication
    For testing public endpoints and auth failures
    """
    from backend.main import app
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_workout_plan():
    """Sample workout plan data for testing"""
    return {
        "plan_name": "Test Beginner Plan",
        "days": [
            {
                "day_title": "Day 1 - Push",
                "items": [
                    {"exercise": "Push-ups", "sets": 3, "reps": 10},
                    {"exercise": "Bench Press", "sets": 4, "reps": 8},
                ]
            },
            {
                "day_title": "Day 2 - Pull",
                "items": [
                    {"exercise": "Pull-ups", "sets": 3, "reps": 8},
                    {"exercise": "Rows", "sets": 4, "reps": 10},
                ]
            },
        ]
    }


@pytest.fixture
def mock_video_file():
    """Mock video file for upload testing"""
    from io import BytesIO
    
    video_content = b"fake video content for testing"
    return {
        "file": BytesIO(video_content),
        "filename": "test_workout.mp4",
        "content_type": "video/mp4"
    }


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for form analysis"""
    return {
        "feedback": "Good form! Keep your back straight.",
        "score": 85,
        "improvements": ["Widen your stance slightly", "Control the descent"]
    }


# Cleanup fixture for uploaded files
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically clean up test files after each test"""
    yield
    
    # Clean up any test files created
    test_output_dir = "backend/outputs"
    if os.path.exists(test_output_dir):
        for filename in os.listdir(test_output_dir):
            if filename.startswith("test_"):
                file_path = os.path.join(test_output_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
