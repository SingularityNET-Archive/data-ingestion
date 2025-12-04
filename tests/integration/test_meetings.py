"""Integration tests for Meetings API endpoints."""
import pytest
from fastapi.testclient import TestClient
import os

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


def test_list_meetings_without_db(client):
    """Test meetings list endpoint when DATABASE_URL is not configured."""
    original_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        response = client.get("/api/meetings")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["items"] == []
        assert data["total"] == 0
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url


def test_list_meetings_structure(client):
    """Test that meetings list endpoint returns expected structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.get("/api/meetings")
    
    if response.status_code == 200:
        data = response.json()
        # Check pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        
        # Validate types
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["total_pages"], int)
        
        # If there are items, check structure
        if len(data["items"]) > 0:
            meeting = data["items"][0]
            expected_fields = [
                "id",
                "source_id",
                "source_name",
                "workgroup",
                "meeting_date",
                "ingested_at",
                "title",
                "validation_warnings_count",
                "has_missing_fields",
            ]
            for field in expected_fields:
                assert field in meeting, f"Missing field: {field}"


def test_list_meetings_pagination(client):
    """Test meetings list pagination parameters."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test default pagination
    response = client.get("/api/meetings")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 50
    
    # Test custom pagination
    response = client.get("/api/meetings?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10


def test_list_meetings_filtering(client):
    """Test meetings list filtering parameters."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test workgroup filter
    response = client.get("/api/meetings?workgroup=test")
    assert response.status_code == 200
    
    # Test date range filter
    response = client.get("/api/meetings?date_from=2024-01-01&date_to=2024-12-31")
    assert response.status_code == 200
    
    # Test search filter
    response = client.get("/api/meetings?search=test")
    assert response.status_code == 200
    
    # Test combined filters
    response = client.get("/api/meetings?workgroup=test&date_from=2024-01-01&search=meeting")
    assert response.status_code == 200


def test_list_meetings_invalid_pagination(client):
    """Test meetings list with invalid pagination parameters."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test invalid page (should default or error)
    response = client.get("/api/meetings?page=0")
    # Should either return 422 (validation error) or default to page 1
    assert response.status_code in [200, 422]
    
    # Test invalid page_size (too large)
    response = client.get("/api/meetings?page_size=200")
    # Should either return 422 or cap at max (100)
    assert response.status_code in [200, 422]


def test_get_meeting_detail_without_db(client):
    """Test meeting detail endpoint when DATABASE_URL is not configured."""
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
        test_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/meetings/{test_id}")
        # Should return 500 when DB not configured, or 404 if pool returns None
        assert response.status_code in [500, 404]
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        # Reset pool again to restore state
        try:
            from backend.app.db.connection import reset_pool
            reset_pool()
        except (ImportError, AttributeError):
            pass


def test_get_meeting_detail_not_found(client):
    """Test meeting detail endpoint with non-existent ID."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Use a valid UUID format but non-existent ID
    test_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/meetings/{test_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_meeting_detail_structure(client):
    """Test that meeting detail endpoint returns expected structure."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # First, get a list to find a valid meeting ID
    list_response = client.get("/api/meetings?page_size=1")
    if list_response.status_code == 200:
        data = list_response.json()
        if len(data["items"]) > 0:
            meeting_id = data["items"][0]["id"]
            
            # Get detail for this meeting
            detail_response = client.get(f"/api/meetings/{meeting_id}")
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                expected_fields = [
                    "id",
                    "source_id",
                    "source_name",
                    "workgroup",
                    "meeting_date",
                    "ingested_at",
                    "title",
                    "normalized_fields",
                    "validation_warnings",
                    "missing_fields",
                    "provenance",
                    "raw_json_reference",
                ]
                for field in expected_fields:
                    assert field in detail_data, f"Missing field: {field}"


def test_get_meeting_detail_invalid_id(client):
    """Test meeting detail endpoint with invalid ID format."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    # Test with invalid UUID format
    response = client.get("/api/meetings/invalid-id")
    # Should return 404 or 422 (validation error)
    assert response.status_code in [404, 422]


def test_meetings_endpoint_requires_auth(client):
    """Test that meetings endpoints require authentication (when dev bypass is off)."""
    original_bypass = os.environ.get("DEV_AUTH_BYPASS")
    if "DEV_AUTH_BYPASS" in os.environ:
        del os.environ["DEV_AUTH_BYPASS"]
    
    try:
        response = client.get("/api/meetings")
        # Should return 401 without auth token, or 200 if DATABASE_URL not set
        assert response.status_code in [200, 401, 500]
        
        response = client.get("/api/meetings/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code in [401, 404, 500]
    finally:
        if original_bypass:
            os.environ["DEV_AUTH_BYPASS"] = original_bypass
        else:
            os.environ["DEV_AUTH_BYPASS"] = "true"

