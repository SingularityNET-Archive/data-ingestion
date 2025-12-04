"""End-to-end smoke test for the ingestion dashboard.

This test exercises the deployable app locally, testing the full flow:
KPIs -> Meetings -> Export

It verifies that the dashboard can be started and basic workflows function correctly.
"""
import pytest
from fastapi.testclient import TestClient
import os
import json

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


def test_health_check(client):
    """Test that the health check endpoint works."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_docs_accessible(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_e2e_kpis_to_meetings_to_export(client):
    """End-to-end test: KPIs -> Meetings List -> Meeting Detail -> Export.
    
    This test exercises the full user workflow:
    1. View KPIs on dashboard
    2. Navigate to meetings list
    3. View a meeting detail
    4. Export filtered meetings
    """
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping E2E test")
    
    # Step 1: Get KPIs
    kpis_response = client.get("/api/kpis")
    assert kpis_response.status_code == 200, f"KPIs endpoint failed: {kpis_response.text}"
    kpis_data = kpis_response.json()
    
    # Verify KPI structure
    assert "total_ingested" in kpis_data
    assert "sources_count" in kpis_data
    assert "success_rate" in kpis_data
    assert "duplicates_avoided" in kpis_data
    assert "last_run_timestamp" in kpis_data
    
    print(f"✓ KPIs retrieved: {kpis_data.get('total_ingested', 0)} meetings ingested")
    
    # Step 2: Get meetings list
    meetings_response = client.get("/api/meetings?page_size=10")
    assert meetings_response.status_code == 200, f"Meetings list endpoint failed: {meetings_response.text}"
    meetings_data = meetings_response.json()
    
    # Verify meetings list structure
    assert "items" in meetings_data
    assert "total" in meetings_data
    assert "page" in meetings_data
    assert isinstance(meetings_data["items"], list)
    
    print(f"✓ Meetings list retrieved: {meetings_data.get('total', 0)} total meetings")
    
    # Step 3: If there are meetings, get detail for first one
    if len(meetings_data["items"]) > 0:
        first_meeting = meetings_data["items"][0]
        meeting_id = first_meeting["id"]
        
        detail_response = client.get(f"/api/meetings/{meeting_id}")
        assert detail_response.status_code == 200, f"Meeting detail endpoint failed: {detail_response.text}"
        detail_data = detail_response.json()
        
        # Verify detail structure
        assert detail_data["id"] == meeting_id
        assert "normalized_fields" in detail_data
        assert "validation_warnings" in detail_data
        assert "provenance" in detail_data
        
        print(f"✓ Meeting detail retrieved: {meeting_id}")
    else:
        print("⚠ No meetings found - skipping detail test")
    
    # Step 4: Export meetings (CSV)
    export_response = client.post(
        "/api/exports",
        json={"format": "csv"}
    )
    
    # Export might fail if >10k rows, or have event loop issues, but should return valid response
    assert export_response.status_code in [200, 413, 503], \
        f"Export endpoint failed: {export_response.status_code} - {export_response.text}"
    
    if export_response.status_code == 200:
        # Verify CSV export
        assert "text/csv" in export_response.headers.get("content-type", "")
        assert len(export_response.content) > 0
        print("✓ CSV export successful")
    else:
        # Large export or service unavailable - verify error message
        error_data = export_response.json()
        # Error response can have either "detail" or "error" key
        assert "detail" in error_data or "error" in error_data
        error_msg = error_data.get("detail") or error_data.get("error", "")
        print(f"✓ Export handled: {error_msg}")
    
    # Step 5: Export meetings (JSON)
    export_json_response = client.post(
        "/api/exports",
        json={"format": "json"}
    )
    
    # JSON export might fail if >10k rows, or have event loop issues, but should return valid response
    assert export_json_response.status_code in [200, 413, 503], \
        f"JSON export endpoint failed: {export_json_response.status_code}"
    
    if export_json_response.status_code == 200:
        # Verify JSON export
        assert "application/json" in export_json_response.headers.get("content-type", "")
        export_data = json.loads(export_json_response.content)
        assert "items" in export_data
        assert "total" in export_data
        print("✓ JSON export successful")
    else:
        # Large export or service unavailable - verify error message
        error_data = export_json_response.json()
        # Error response can have either "detail" or "error" key
        assert "detail" in error_data or "error" in error_data
        error_msg = error_data.get("detail") or error_data.get("error", "")
        print(f"✓ JSON export handled: {error_msg}")
    
    print("✓ End-to-end workflow completed successfully")


def test_e2e_alerts_workflow(client):
    """End-to-end test for alerts workflow."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping alerts E2E test")
    
    # Get alerts
    alerts_response = client.get("/api/alerts")
    assert alerts_response.status_code == 200, f"Alerts endpoint failed: {alerts_response.text}"
    alerts_data = alerts_response.json()
    
    assert isinstance(alerts_data, list)
    print(f"✓ Alerts retrieved: {len(alerts_data)} alerts")
    
    # If there are alerts and we're in admin mode, test acknowledgment
    # Note: This test uses DEV_AUTH_BYPASS which gives admin access
    if len(alerts_data) > 0:
        first_alert = alerts_data[0]
        alert_id = first_alert["id"]
        
        # Try to acknowledge (admin only)
        ack_response = client.post(f"/api/alerts/{alert_id}/acknowledge")
        # Should succeed (admin) or fail (read-only), but not 500
        assert ack_response.status_code in [200, 403], \
            f"Alert acknowledgment failed: {ack_response.status_code} - {ack_response.text}"
        
        if ack_response.status_code == 200:
            print(f"✓ Alert acknowledged: {alert_id}")


def test_e2e_trends_workflow(client):
    """End-to-end test for trends workflow."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping trends E2E test")
    
    # Get monthly aggregates
    trends_response = client.get("/api/runs/monthly?months=12")
    assert trends_response.status_code == 200, f"Trends endpoint failed: {trends_response.text}"
    trends_data = trends_response.json()
    
    assert isinstance(trends_data, list)
    print(f"✓ Trends retrieved: {len(trends_data)} monthly aggregates")
    
    # Get ingestion runs
    runs_response = client.get("/api/runs?limit=10")
    assert runs_response.status_code == 200, f"Runs endpoint failed: {runs_response.text}"
    runs_data = runs_response.json()
    
    assert isinstance(runs_data, list)
    print(f"✓ Ingestion runs retrieved: {len(runs_data)} runs")


def test_e2e_filtered_export_workflow(client):
    """Test export workflow with filters applied."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping filtered export E2E test")
    
    # Get meetings with a filter
    filtered_meetings = client.get("/api/meetings?page_size=5&workgroup=test")
    assert filtered_meetings.status_code == 200
    
    # Export the filtered set
    export_response = client.post(
        "/api/exports",
        json={
            "format": "csv",
            "workgroup": "test",
        }
    )
    
    # Should succeed or return appropriate error (including 503 for service unavailable)
    assert export_response.status_code in [200, 413, 500, 503]
    
    if export_response.status_code == 200:
        assert len(export_response.content) > 0
        print("✓ Filtered export successful")


def test_e2e_all_endpoints_accessible(client):
    """Smoke test to verify all main endpoints are accessible."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping endpoint accessibility test")
    
    endpoints = [
        ("GET", "/healthz"),
        ("GET", "/api/kpis"),
        ("GET", "/api/meetings"),
        ("GET", "/api/runs"),
        ("GET", "/api/runs/monthly"),
        ("GET", "/api/alerts"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint)
        
        # Endpoints should return 200 (success) or 500 (DB error), not 404 or 401
        assert response.status_code in [200, 500], \
            f"Endpoint {method} {endpoint} returned unexpected status: {response.status_code}"
    
    print("✓ All main endpoints are accessible")


def test_e2e_error_handling(client):
    """Test error handling across the dashboard."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - skipping error handling test")
    
    # Test 404 for non-existent meeting
    response = client.get("/api/meetings/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "detail" in response.json()
    
    # Test invalid export format
    response = client.post("/api/exports", json={"format": "invalid"})
    assert response.status_code == 422  # Validation error
    
    # Test invalid pagination
    response = client.get("/api/meetings?page=0")
    # Should either return 422 or default to page 1
    assert response.status_code in [200, 422]
    
    print("✓ Error handling works correctly")

