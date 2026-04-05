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


@pytest.fixture(scope="session")
def test_db_config():
    """Database configuration for tests"""
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "database": os.getenv("DB_NAME"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }


@pytest.fixture
def db_connection(test_db_config):
    """
    Provide database connection for tests
    Automatically rolls back changes after each test
    """
    required = ("host", "user", "database")
    if any(not test_db_config.get(key) for key in required):
        pytest.skip("Database environment variables are not set for integration DB tests")

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
    try:
        conn.rollback()
    except Exception:
        # Some tests may close the connection; teardown should remain non-fatal.
        pass
    try:
        conn.close()
    except Exception:
        pass


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
    async def _mock_require_clerk_user(request=None):
        return mock_clerk_user
    return _mock_require_clerk_user


@pytest.fixture
def client(mock_auth, mock_clerk_user):
    """
    FastAPI test client with mocked authentication
    """
    from backend.main import app, current_user
    from backend.clerk_auth import require_clerk_user
    
    # Create sync version for current_user (it's not async)
    def sync_mock(request=None):
        return mock_clerk_user
    
    # Override both authentication functions
    app.dependency_overrides[require_clerk_user] = mock_auth
    app.dependency_overrides[current_user] = sync_mock
    
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
