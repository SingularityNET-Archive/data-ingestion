# Test Suite Documentation

This directory contains comprehensive tests for the Meeting Summaries Data Ingestion Pipeline.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests for individual components
│   ├── test_json_downloader.py
│   ├── test_json_validator.py
│   ├── test_validators.py
│   ├── test_logger.py
│   └── test_models.py
├── integration/             # Integration tests for component interactions
│   ├── test_ingestion_service.py
│   ├── test_schema_manager.py
│   ├── test_e2e_ingestion.py
│   ├── test_error_handling.py
│   └── test_performance.py
└── contract/                # Contract tests for API/schema compliance
    └── test_json_structure.py
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Contract tests only
pytest tests/contract/
```

### Run Specific Test Files

```bash
pytest tests/unit/test_json_downloader.py
pytest tests/integration/test_ingestion_service.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:
- **JSON Downloader**: HTTP requests, error handling, timeout handling
- **JSON Validator**: Structure validation, record validation, error messages
- **Validators**: UUID validation, date parsing, circular reference detection
- **Logger**: JSON/text formatting, log levels, output streams
- **Models**: Pydantic validation, field extraction, serialization

### Integration Tests

Integration tests verify component interactions:
- **Ingestion Service**: Full meeting processing flow, workgroup extraction, atomic transactions
- **Schema Manager**: Workgroup extraction, UPSERT operations
- **End-to-End**: Complete pipeline from download to database insertion
- **Error Handling**: Network failures, database errors, invalid data handling
- **Performance**: Throughput, response times, 10-minute goal verification

### Contract Tests

Contract tests ensure API/schema compliance:
- **JSON Structure**: Required fields, nested structures, schema flexibility
- **Historic Data**: Compatibility with 2022-2024 data formats

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_meeting_summary`: Sample meeting summary JSON
- `sample_meeting_array`: Array of sample meeting summaries
- `sample_invalid_meeting_summary`: Invalid meeting summary for error testing
- `sample_meeting_with_nested_data`: Meeting with nested collections
- `mock_httpx_response`: Mock HTTP response
- `mock_httpx_client`: Mock HTTP client
- `temp_db_url`: Test database URL

## Test Data Sources

Test data is generated programmatically in fixtures. For integration tests that require real data:

1. Use sample data from `data/` directory
2. Create test fixtures with realistic data structures
3. Mock external dependencies (HTTP, database)

## Writing New Tests

### Unit Test Example

```python
def test_feature_name():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_integration_scenario():
    """Test integration scenario."""
    # Setup mocks
    mock_db = AsyncMock()
    
    # Execute
    service = Service(mock_db)
    result = await service.process()
    
    # Verify
    assert result["status"] == "success"
    mock_db.method.assert_called_once()
```

## Test Coverage Goals

- **Unit Tests**: >90% coverage for all services and utilities
- **Integration Tests**: Cover all major workflows and error scenarios
- **Contract Tests**: Verify all schema requirements

## Continuous Integration

Tests should pass in CI/CD pipeline:
- All unit tests must pass
- Integration tests run against test database
- Performance tests verify time requirements
- Contract tests ensure schema compliance

## Troubleshooting

### Tests Fail with Database Connection Errors

- Ensure test database is available or use mocks
- Check `TEST_DATABASE_URL` environment variable
- Use `dry_run=True` for tests that don't need database

### Tests Fail with Import Errors

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python path includes project root

### Performance Tests Fail

- Performance tests use mocks and should be fast
- If real network/database tests are slow, adjust timeouts
- Verify test environment performance

## Notes

- Tests use mocks for external dependencies (HTTP, database)
- Integration tests can use test database if available
- All tests should be deterministic and independent
- Use fixtures for shared test data
- Follow pytest best practices for async tests



