# Testing Documentation

## Overview
This document explains the testing strategy for the Sculpt fitness application.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_clerk_auth.py
│   ├── test_database.py
│   ├── test_analyzers.py
│   └── test_editable_plans.py
├── integration/             # Integration tests (API + DB)
│   └── test_api_integration.py
└── e2e/                     # End-to-end tests (full workflows)
    └── test_user_workflows.py
```

## Running Tests

### Install dependencies
```bash
pip install -r requirements-dev.txt
```

### Run all tests
```bash
pytest
```

### Run specific test types
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

### Run with coverage
```bash
pytest --cov=backend --cov-report=html
```

View coverage report: Open `htmlcov/index.html`

### Run specific test file
```bash
pytest tests/unit/test_clerk_auth.py
pytest tests/integration/test_api_integration.py -v
```

### Run specific test
```bash
pytest tests/unit/test_clerk_auth.py::TestBearerTokenExtraction::test_valid_bearer_token
```

## Test Database Setup

1. **Create test database**:
```sql
CREATE DATABASE sculpfit_test;
```

2. **Set environment variables** (create `.env.test`):
```env
DB_HOST=127.0.0.1
DB_USER=root
DB_PASS=your_password
DB_NAME=sculpfit
TEST_DB_NAME=sculpfit_test
DB_PORT=3306
TESTING=1
```

3. **Run migrations on test database**:
```bash
# The conftest.py automatically runs init_database.sql
# But you can manually run migrations:
mysql -u root -p sculpfit_test < init_database.sql
```

## Writing Tests

### Unit Test Example
```python
def test_calculate_angle():
    """Test angle calculation between three points"""
    analyzer = PushupAnalyzer()
    angle = analyzer.calculate_angle(p1, p2, p3)
    assert 85 <= angle <= 95
```

### Integration Test Example
```python
@pytest.mark.integration
def test_save_user_plan(client, db_connection):
    """Test saving plan via API and verifying in database"""
    response = client.post("/api/save-plan", json=plan_data)
    assert response.status_code == 200
    
    # Verify in database
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user_saved_plans WHERE ...")
        result = cursor.fetchone()
        assert result is not None
```

### E2E Test Example
```python
@pytest.mark.e2e
def test_complete_workout_flow(client):
    """Test full user journey"""
    # 1. Save plan
    save_response = client.post("/api/save-plan", json=...)
    
    # 2. Create editable copy
    copy_response = client.post("/api/plans/1/copy")
    
    # 3. Modify plan
    update_response = client.put("/api/editable-plans/1", json=...)
    
    # 4. Verify changes
    verify_response = client.get("/api/user-plans")
    assert verify_response.status_code == 200
```

## Test Fixtures

### Available Fixtures
- `client`: Authenticated FastAPI test client
- `unauthenticated_client`: Unauthenticated test client
- `db_connection`: Test database connection
- `mock_clerk_user`: Mock authenticated user data
- `sample_workout_plan`: Sample workout plan data
- `mock_video_file`: Mock video file for testing

### Using Fixtures
```python
def test_with_fixtures(client, db_connection, mock_clerk_user):
    # client is automatically authenticated with mock_clerk_user
    response = client.get("/api/user-plans")
    assert response.status_code == 200
```

## Continuous Integration

### GitHub Actions Workflow
Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpass
          MYSQL_DATABASE: sculpfit_test
        ports:
          - 3306:3306
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        env:
          DB_HOST: 127.0.0.1
          DB_USER: root
          DB_PASS: testpass
          TEST_DB_NAME: sculpfit_test
          DB_PORT: 3306
        run: |
          pytest --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

1. **Follow AAA pattern**:
   - Arrange: Set up test data
   - Act: Execute the function
   - Assert: Verify the results

2. **Use descriptive test names**:
   ```python
   def test_user_can_save_plan_successfully()  # Good
   def test_save()  # Bad
   ```

3. **Test one thing per test**:
   - Each test should verify one behavior
   - Makes debugging easier

4. **Mock external dependencies**:
   - Mock API calls (Gemini, Clerk)
   - Mock file system operations
   - Use test database for DB operations

5. **Clean up after tests**:
   - Use fixtures with cleanup
   - Test database is automatically cleaned
   - Delete test files after tests

6. **Test edge cases**:
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error scenarios

## Coverage Goals

- **Overall**: Aim for 80%+ coverage
- **Critical paths**: 100% (auth, payments, data integrity)
- **Business logic**: 90%+ (analyzers, workout logic)
- **UI/presentation**: 60%+ (less critical)

## For Your Final Year Project Report

Include these sections:

1. **Testing Strategy**: Explain the test pyramid approach
2. **Test Coverage**: Show coverage reports and percentages
3. **Test Cases**: Document key test scenarios
4. **CI/CD**: Explain automated testing pipeline
5. **Quality Metrics**: Test pass rates, coverage trends
6. **Bug Prevention**: Examples of bugs caught by tests

## Next Steps

1. Install dev dependencies: `pip install -r requirements-dev.txt`
2. Run existing tests: `pytest -v`
3. Add more unit tests for your specific functions
4. Implement integration tests for your API endpoints
5. Add E2E tests for critical user journeys
6. Set up CI/CD with GitHub Actions
7. Monitor coverage and aim for 80%+
