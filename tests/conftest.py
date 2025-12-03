"""Pytest configuration and shared fixtures."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Sample JSON data for testing
SAMPLE_MEETING_SUMMARY = {
    "workgroup": "Test Workgroup",
    "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
    "meetingInfo": {
        "date": "2025-01-15",
        "host": "John Doe",
        "documenter": "Jane Smith",
        "attendees": ["Alice", "Bob"],
        "purpose": "Test meeting",
    },
    "agendaItems": [
        {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "status": "completed",
            "actionItems": [
                {
                    "id": "323e4567-e89b-12d3-a456-426614174000",
                    "text": "Test action",
                    "assignee": "Alice",
                }
            ],
            "decisionItems": [],
            "discussionPoints": [],
        }
    ],
    "tags": {"category": "test", "type": "meeting"},
    "type": "regular",
}

SAMPLE_MEETING_ARRAY = [SAMPLE_MEETING_SUMMARY]


@pytest.fixture
def sample_meeting_summary() -> Dict[str, Any]:
    """Fixture providing a sample meeting summary JSON."""
    return SAMPLE_MEETING_SUMMARY.copy()


@pytest.fixture
def sample_meeting_array() -> List[Dict[str, Any]]:
    """Fixture providing a sample array of meeting summaries."""
    return [SAMPLE_MEETING_SUMMARY.copy()]


@pytest.fixture
def sample_invalid_meeting_summary() -> Dict[str, Any]:
    """Fixture providing an invalid meeting summary (missing required fields)."""
    return {
        "workgroup": "Test Workgroup",
        # Missing workgroup_id, meetingInfo, agendaItems, tags, type
    }


@pytest.fixture
def sample_meeting_with_nested_data() -> Dict[str, Any]:
    """Fixture providing a meeting summary with nested collections."""
    return {
        "workgroup": "Test Workgroup",
        "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
        "meetingInfo": {
            "date": "2025-01-15",
            "host": "John Doe",
            "documenter": "Jane Smith",
            "attendees": ["Alice", "Bob"],
            "purpose": "Test meeting",
            "workingDocs": [{"name": "doc1.pdf", "url": "https://example.com/doc1.pdf"}],
            "timestampedVideo": {"segments": [{"timestamp": "00:05:30", "topic": "Discussion"}]},
        },
        "agendaItems": [
            {
                "id": "223e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "actionItems": [
                    {
                        "id": "323e4567-e89b-12d3-a456-426614174000",
                        "text": "Test action",
                        "assignee": "Alice",
                        "dueDate": "2025-02-01",
                        "status": "pending",
                    }
                ],
                "decisionItems": [
                    {
                        "id": "423e4567-e89b-12d3-a456-426614174000",
                        "decision": "Test decision",
                        "rationale": "Test rationale",
                    }
                ],
                "discussionPoints": [
                    {
                        "id": "523e4567-e89b-12d3-a456-426614174000",
                        "point": "Test discussion point",
                    }
                ],
            }
        ],
        "tags": {"category": "test", "type": "meeting"},
        "type": "regular",
    }


@pytest.fixture
def mock_httpx_response():
    """Fixture providing a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = SAMPLE_MEETING_ARRAY
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Fixture providing a mock httpx async client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=mock_httpx_response)
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_url():
    """Fixture providing a test database URL (can be overridden with env var)."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/test_meeting_summaries",
    )


@pytest.fixture
def sample_json_file(tmp_path, sample_meeting_array):
    """Fixture creating a temporary JSON file with sample data."""
    json_file = tmp_path / "test_data.json"
    json_file.write_text(json.dumps(sample_meeting_array))
    return str(json_file)


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    # Clear all handlers
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    yield

    # Cleanup after test
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
