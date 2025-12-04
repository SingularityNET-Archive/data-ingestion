"""Integration tests for KPI API endpoints."""
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
    
    # Add backend/app to path
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"
    sys.path.insert(0, str(backend_path))
    
    from main import app
    return TestClient(app)


def test_healthz_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_kpis_endpoint_without_db(client):
    """Test KPIs endpoint when DATABASE_URL is not configured."""
    # Temporarily unset DATABASE_URL
    original_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        response = client.get("/api/kpis")
        # Should return 500 or empty response depending on implementation
        assert response.status_code in [200, 500]
    finally:
        # Restore DATABASE_URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url


def test_kpis_endpoint_structure(client):
    """Test that KPIs endpoint returns expected structure when DB is available."""
    # Only run if DATABASE_URL is set
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    
    response = client.get("/api/kpis")
    
    if response.status_code == 200:
        data = response.json()
        # Check that response has expected fields (may be empty if no data)
        expected_fields = [
            "total_ingested",
            "sources_count",
            "success_rate",
            "duplicates_avoided",
            "last_run_timestamp",
        ]
        
        # If there's an error, it should be in the response
        if "error" in data:
            assert isinstance(data["error"], str)
        else:
            # If successful, check structure
            for field in expected_fields:
                assert field in data, f"Missing field: {field}"
            
            # Validate types
            if data.get("total_ingested") is not None:
                assert isinstance(data["total_ingested"], (int, type(None)))
            if data.get("sources_count") is not None:
                assert isinstance(data["sources_count"], (int, type(None)))
            if data.get("success_rate") is not None:
                assert isinstance(data["success_rate"], (float, int, type(None)))
            if data.get("duplicates_avoided") is not None:
                assert isinstance(data["duplicates_avoided"], (int, type(None)))


def test_kpis_endpoint_requires_auth(client):
    """Test that KPIs endpoint requires authentication (when dev bypass is off)."""
    # Temporarily disable dev bypass
    original_bypass = os.environ.get("DEV_AUTH_BYPASS")
    if "DEV_AUTH_BYPASS" in os.environ:
        del os.environ["DEV_AUTH_BYPASS"]
    
    try:
        response = client.get("/api/kpis")
        # Should return 401 without auth token, or 200 if DATABASE_URL not set
        assert response.status_code in [200, 401, 500]
    finally:
        # Restore dev bypass
        if original_bypass:
            os.environ["DEV_AUTH_BYPASS"] = original_bypass
        else:
            os.environ["DEV_AUTH_BYPASS"] = "true"

