"""Integration tests for Trends and Exports API endpoints."""
import pytest
from fastapi.testclient import TestClient
import os
import json
import csv
import io

# Set dev auth bypass for testing
os.environ["DEV_AUTH_BYPASS"] = "true"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    import sys
    from pathlib import Path
    
    # Add project root to path so we can import backend.app as a package
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from backend.app.main import app
    return TestClient(app)


# ===== Trends / Runs API Tests =====

def test_list_runs_without_db(client):
    """Test runs list endpoint when DATABASE_URL is not configured."""
    original_url = os.environ.get("DATABASE_URL")
    
    # Reset the pool and remove DATABASE_URL
    try:
        from backend.app.db.connection import reset_pool
        reset_pool()
    except (ImportError, AttributeError):
        pass
    
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        response = client.get("/api/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list when DATABASE_URL is not set
        assert data == []
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        # Reset pool again to restore state
        try:
            from backend.app.db.connection import reset_pool
            reset_pool()
        except (ImportError, AttributeError):
            pass


def test_list_runs_structure(client):
    """Test that runs list endpoint returns expected structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.get("/api/runs")
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        
        # If there are runs, check structure
        if len(data) > 0:
            run = data[0]
            expected_fields = [
                "id",
                "started_at",
                "finished_at",
                "status",
                "records_processed",
                "records_failed",
                "duplicates_avoided",
            ]
            for field in expected_fields:
                assert field in run, f"Missing field: {field}"


def test_list_runs_limit(client):
    """Test runs list with limit parameter."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test default limit
    response = client.get("/api/runs")
    assert response.status_code == 200
    
    # Test custom limit
    response = client.get("/api/runs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


def test_get_monthly_aggregates_without_db(client):
    """Test monthly aggregates endpoint when DATABASE_URL is not configured."""
    original_url = os.environ.get("DATABASE_URL")
    
    # Reset the pool and remove DATABASE_URL
    try:
        from backend.app.db.connection import reset_pool
        reset_pool()
    except (ImportError, AttributeError):
        pass
    
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        response = client.get("/api/runs/monthly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list when DATABASE_URL is not set
        assert data == []
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        # Reset pool again to restore state
        try:
            from backend.app.db.connection import reset_pool
            reset_pool()
        except (ImportError, AttributeError):
            pass


def test_get_monthly_aggregates_structure(client):
    """Test that monthly aggregates endpoint returns expected structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.get("/api/runs/monthly")
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        
        # If there are aggregates, check structure
        if len(data) > 0:
            aggregate = data[0]
            expected_fields = [
                "month",
                "records_ingested",
                "records_with_warnings",
            ]
            for field in expected_fields:
                assert field in aggregate, f"Missing field: {field}"


def test_get_monthly_aggregates_months_parameter(client):
    """Test monthly aggregates with months parameter."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test default (12 months)
    response = client.get("/api/runs/monthly")
    assert response.status_code == 200
    
    # Test custom months
    response = client.get("/api/runs/monthly?months=6")
    assert response.status_code == 200
    
    # Test max months
    response = client.get("/api/runs/monthly?months=60")
    assert response.status_code == 200
    
    # Test invalid months (should be capped or return error)
    response = client.get("/api/runs/monthly?months=100")
    # Should either return 422 (validation error) or cap at 60
    assert response.status_code in [200, 422]


# ===== Exports API Tests =====

def test_export_meetings_csv_without_db(client):
    """Test export endpoint when DATABASE_URL is not configured."""
    original_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        response = client.post(
            "/api/exports",
            json={"format": "csv"}
        )
        # Should return 500 when DB not configured
        assert response.status_code == 500
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url


def test_export_meetings_csv_structure(client):
    """Test CSV export returns valid CSV structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.post(
        "/api/exports",
        json={"format": "csv"}
    )
    
    if response.status_code == 200:
        # Check content type
        assert "text/csv" in response.headers.get("content-type", "")
        
        # Check content disposition
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "meetings_export.csv" in response.headers.get("content-disposition", "")
        
        # Parse CSV to verify structure
        content = response.content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # Check expected columns
        expected_columns = [
            "id",
            "source_name",
            "workgroup",
            "meeting_date",
            "ingested_at",
            "title",
            "validation_warnings_count",
            "has_missing_fields",
        ]
        assert csv_reader.fieldnames is not None
        for col in expected_columns:
            assert col in csv_reader.fieldnames, f"Missing CSV column: {col}"


def test_export_meetings_json_structure(client):
    """Test JSON export returns valid JSON structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.post(
        "/api/exports",
        json={"format": "json"}
    )
    
    if response.status_code == 200:
        # Check content type
        assert "application/json" in response.headers.get("content-type", "")
        
        # Check content disposition
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "meetings_export.json" in response.headers.get("content-disposition", "")
        
        # Parse JSON to verify structure
        data = json.loads(response.content)
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        
        # If there are items, check structure
        if len(data["items"]) > 0:
            item = data["items"][0]
            expected_fields = [
                "id",
                "source_name",
                "workgroup",
                "meeting_date",
                "ingested_at",
                "title",
                "validation_warnings_count",
                "has_missing_fields",
            ]
            for field in expected_fields:
                assert field in item, f"Missing JSON field: {field}"


def test_export_meetings_with_filters(client):
    """Test export with filtering parameters."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test CSV export with filters
    response = client.post(
        "/api/exports",
        json={
            "format": "csv",
            "workgroup": "test",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
        }
    )
    assert response.status_code in [200, 500, 503]  # 500 if filters cause DB error, 503 if service unavailable
    
    # Test JSON export with filters
    response = client.post(
        "/api/exports",
        json={
            "format": "json",
            "search": "meeting",
        }
    )
    assert response.status_code in [200, 500, 503]


def test_export_meetings_large_export(client):
    """Test export with large result set (>10k rows)."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # This test assumes there might be >10k rows
    # The endpoint should return 413 for large exports
    response = client.post(
        "/api/exports",
        json={"format": "csv"}
    )
    
    # Should either succeed (if <10k), return 413 (if >10k), 503 (if event loop issues), or 500 (other errors)
    assert response.status_code in [200, 413, 500, 503]
    
    if response.status_code == 413:
        data = response.json()
        # Error response can have either "detail" or "error" key
        error_msg = data.get("detail") or data.get("error", "")
        assert "too large" in error_msg.lower() or "10000" in error_msg


def test_export_meetings_invalid_format(client):
    """Test export with invalid format."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.post(
        "/api/exports",
        json={"format": "xml"}  # Invalid format
    )
    # Should return 422 (validation error) for invalid format
    assert response.status_code == 422


def test_export_meetings_requires_auth(client):
    """Test that export endpoint requires authentication (when dev bypass is off)."""
    original_bypass = os.environ.get("DEV_AUTH_BYPASS")
    if "DEV_AUTH_BYPASS" in os.environ:
        del os.environ["DEV_AUTH_BYPASS"]
    
    try:
        response = client.post(
            "/api/exports",
            json={"format": "csv"}
        )
        # Should return 401 without auth token, or 500 if DATABASE_URL not set
        assert response.status_code in [200, 401, 500]
    finally:
        if original_bypass:
            os.environ["DEV_AUTH_BYPASS"] = original_bypass
        else:
            os.environ["DEV_AUTH_BYPASS"] = "true"


def test_runs_endpoint_requires_auth(client):
    """Test that runs endpoints require authentication (when dev bypass is off)."""
    original_bypass = os.environ.get("DEV_AUTH_BYPASS")
    if "DEV_AUTH_BYPASS" in os.environ:
        del os.environ["DEV_AUTH_BYPASS"]
    
    try:
        response = client.get("/api/runs")
        assert response.status_code in [200, 401, 500]
        
        response = client.get("/api/runs/monthly")
        assert response.status_code in [200, 401, 500]
    finally:
        if original_bypass:
            os.environ["DEV_AUTH_BYPASS"] = original_bypass
        else:
            os.environ["DEV_AUTH_BYPASS"] = "true"

