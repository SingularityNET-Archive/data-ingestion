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

### Prerequisites

Before running tests, ensure:
1. Virtual environment is activated: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
2. Dependencies are installed: `pip install -r requirements.txt`
3. Test database is available (for integration tests) OR use mocks
4. Python path includes project root (usually automatic)

### Run All Tests

```bash
pytest
```

**Expected Output Format**:
```
============================= test session starts ==============================
platform darwin -- Python 3.9.0, pytest-7.4.0, pluggy-1.3.0
collected 55 items

tests/unit/test_json_downloader.py ..........                          [ 18%]
tests/unit/test_json_validator.py ...........                          [ 38%]
tests/integration/test_ingestion_service.py ........                   [ 55%]
tests/contract/test_json_structure.py ............                    [ 77%]
...                                                                     [100%]

======================== 55 passed in 48.23s =========================
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

**Example Verbose Output**:
```
tests/unit/test_json_downloader.py::test_download_json_success PASSED
tests/unit/test_json_downloader.py::test_download_json_timeout PASSED
tests/unit/test_json_validator.py::test_validate_structure_compatible PASSED
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html` showing which code is covered by tests.

### Run Tests Matching a Pattern

```bash
# Run tests matching "json" in name
pytest -k json

# Run tests matching "error" in name
pytest -k error
```

## Test Categories

### Unit Tests

**Purpose**: Verify individual components work correctly in isolation without external dependencies (database, network).

**What Each Test Category Verifies**:
- **JSON Downloader**: HTTP requests, error handling, timeout handling, retry logic
- **JSON Validator**: Structure validation, record validation, error messages, schema compatibility
- **Validators**: UUID validation, date parsing, circular reference detection, data type validation
- **Logger**: JSON/text formatting, log levels, output streams, structured logging
- **Models**: Pydantic validation, field extraction, serialization, data transformation

**Example Successful Output**:
```
tests/unit/test_json_downloader.py::test_download_json_success PASSED
tests/unit/test_json_downloader.py::test_download_json_timeout PASSED
tests/unit/test_json_validator.py::test_validate_structure_compatible PASSED
tests/unit/test_validators.py::test_validate_uuid_valid PASSED
tests/unit/test_models.py::test_meeting_model_serialization PASSED

======================== 25 passed in 2.34s ========================
```

**Expected Outcomes**:
- All validation functions return correct results for valid and invalid inputs
- Models serialize/deserialize correctly with all field types
- Error handling works as expected (raises appropriate exceptions)
- Logging produces correct format and includes required fields
- HTTP client handles timeouts and errors gracefully

**Common Failure Scenarios**:
- **Import errors**: Missing dependencies or incorrect Python path
- **Validation failures**: Test data doesn't match expected schema
- **Type errors**: Pydantic model validation issues
- **Mock setup errors**: Incorrect mock configuration

### Integration Tests

**Purpose**: Verify component interactions work correctly together, including database operations and end-to-end workflows.

**What Each Test Category Verifies**:
- **Ingestion Service**: Full meeting processing flow, workgroup extraction, atomic transactions, nested entity processing
- **Schema Manager**: Workgroup extraction, UPSERT operations, duplicate handling
- **End-to-End**: Complete pipeline from download to database insertion, multiple sources, error recovery
- **Error Handling**: Network failures, database errors, invalid data handling, transaction rollback
- **Performance**: Throughput, response times, 10-minute goal verification, resource usage

**Example Successful Output**:
```
tests/integration/test_ingestion_service.py::test_ingest_single_meeting PASSED
tests/integration/test_ingestion_service.py::test_ingest_multiple_meetings PASSED
tests/integration/test_e2e_ingestion.py::test_full_pipeline PASSED
tests/integration/test_error_handling.py::test_network_failure_recovery PASSED
tests/integration/test_performance.py::test_ingestion_within_time_limit PASSED

======================== 18 passed in 45.67s ========================
```

**Expected Outcomes**:
- Complete ingestion workflows process all records successfully
- Database transactions are atomic (all-or-nothing)
- Workgroups are processed before meetings (referential integrity)
- Error recovery continues processing remaining sources after failures
- Performance meets 10-minute target for 677 records
- UPSERT operations prevent duplicates on re-runs

**Common Failure Scenarios**:
- **Database connection errors**: Test database not available or incorrect connection string
- **Transaction failures**: Database constraints violated or connection lost
- **Performance timeouts**: Tests exceed time limits due to slow database or network
- **Referential integrity errors**: Workgroups not created before meetings
- **Mock configuration errors**: Database mocks not properly configured

### Contract Tests

**Purpose**: Ensure API/schema compliance and data structure compatibility across different data sources.

**What Each Test Category Verifies**:
- **JSON Structure**: Required fields present, nested structures valid, schema flexibility (additional fields allowed)
- **Historic Data**: Compatibility with 2022-2024 data formats, missing optional fields handled gracefully
- **Schema Evolution**: Backward compatibility with older data formats

**Example Successful Output**:
```
tests/contract/test_json_structure.py::test_required_fields_present PASSED
tests/contract/test_json_structure.py::test_nested_structures_valid PASSED
tests/contract/test_json_structure.py::test_historic_data_compatibility PASSED
tests/contract/test_json_structure.py::test_schema_flexibility PASSED

======================== 12 passed in 1.23s ========================
```

**Expected Outcomes**:
- All required fields are present and correctly typed
- Nested structures (agenda items, action items, etc.) are valid
- Historic data from 2022-2024 is compatible with current schema
- Additional fields beyond schema are accepted (schema flexibility)
- Missing optional fields don't cause failures

**Common Failure Scenarios**:
- **Missing required fields**: JSON structure doesn't match expected schema
- **Type mismatches**: Field types don't match expected types (string vs number, etc.)
- **Nested structure errors**: Invalid structure in nested collections
- **Historic data incompatibility**: Older data formats not handled correctly

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





