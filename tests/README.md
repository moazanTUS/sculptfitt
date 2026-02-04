# Testing Quick Reference

## Installation
```bash
pip install -r requirements-dev.txt
```

## Running Tests

### All tests
```bash
pytest
```

### By type
```bash
pytest -m unit              # Fast unit tests
pytest -m integration       # API + Database tests
pytest -m e2e              # Full user workflows
pytest -m "not slow"       # Skip slow tests
```

### With coverage
```bash
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html to view
```

### Specific file
```bash
pytest tests/unit/test_clerk_auth.py -v
```

### Specific test
```bash
pytest tests/unit/test_clerk_auth.py::TestBearerTokenExtraction::test_valid_bearer_token
```

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Fast, isolated tests
│   ├── test_clerk_auth.py         # ✅ Already exists
│   ├── test_database.py           # ✅ New
│   ├── test_analyzers.py          # ✅ New
│   └── test_editable_plans.py     # ✅ New
├── integration/                   # API + Database
│   └── test_api_integration.py    # ✅ New
└── e2e/                          # Complete workflows
    └── test_user_workflows.py     # ✅ New
```

## Key Fixtures (from conftest.py)

- `client` - Authenticated test client
- `unauthenticated_client` - No auth test client
- `db_connection` - Test database connection
- `mock_clerk_user` - Mock user data
- `sample_workout_plan` - Sample plan data
- `mock_video_file` - Mock video upload

## Writing Tests

### Unit Test Template
```python
def test_function_name():
    """Test description"""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_value
```

### Integration Test Template
```python
@pytest.mark.integration
def test_api_endpoint(client, db_connection):
    """Test API with database"""
    response = client.post("/api/endpoint", json=data)
    assert response.status_code == 200
    
    # Verify in DB
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM table")
        assert cursor.fetchone() is not None
```

### E2E Test Template
```python
@pytest.mark.e2e
def test_user_workflow(client):
    """Test complete user journey"""
    # Step 1
    response1 = client.post("/api/step1", json=data1)
    assert response1.status_code == 200
    
    # Step 2
    response2 = client.get("/api/step2")
    assert response2.status_code == 200
    
    # Verify final state
    assert response2.json()["expected_field"] == "value"
```

## Common Patterns

### Mocking external APIs
```python
@patch('backend.module.external_api_call')
def test_with_mock(mock_api):
    mock_api.return_value = {"data": "mocked"}
    result = function_that_calls_api()
    assert result is not None
```

### Testing exceptions
```python
def test_raises_exception():
    with pytest.raises(ValueError) as exc:
        function_that_raises()
    assert "error message" in str(exc.value)
```

### Parametrized tests
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_multiple_cases(input, expected):
    assert my_function(input) == expected
```

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests

View results: GitHub Actions tab

## Coverage Goals

- Overall: 80%+
- Auth & Security: 100%
- Business Logic: 90%+
- Analyzers: 85%+

## Troubleshooting

### Database connection fails
```bash
# Check MySQL is running
mysql -u root -p

# Create test database
CREATE DATABASE sculpfit_test;
```

### Import errors
```bash
# Install in development mode
pip install -e .
```

### Tests hang
```bash
# Run with timeout
pytest --timeout=30
```

## For Final Year Report

Document these metrics:
1. Total number of tests
2. Coverage percentage
3. Test execution time
4. Pass/fail rates
5. Critical paths covered
6. Bug examples caught by tests

Run for report data:
```bash
pytest --cov=backend --cov-report=term-missing > test_report.txt
```
