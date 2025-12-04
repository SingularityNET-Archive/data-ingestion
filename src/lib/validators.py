"""Validation utilities for UUID, dates, and circular references."""

import uuid
import re
from typing import Any, Dict, List, Optional, Set
from datetime import datetime


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID

    Returns:
        True if valid UUID, False otherwise
    """
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.

    Supports multiple formats:
    - ISO 8601: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZ
    - Common formats: MM/DD/YYYY, DD-MM-YYYY

    Args:
        date_str: Date string to parse

    Returns:
        Datetime object or None if parsing fails
    """
    if not isinstance(date_str, str):
        return None

    # ISO 8601 formats
    iso_formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]

    for fmt in iso_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Other common formats
    other_formats = [
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]

    for fmt in other_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def detect_circular_reference(
    obj: Any, max_depth: int = 10, visited: Optional[Set[int]] = None
) -> bool:
    """
    Detect circular references in nested data structures.

    Args:
        obj: Object to check for circular references
        max_depth: Maximum nesting depth before considering it circular
        visited: Set of object IDs already visited (for internal recursion)

    Returns:
        True if circular reference detected, False otherwise
    """
    if visited is None:
        visited = set()

    obj_id = id(obj)

    # Check if we've seen this object before
    if obj_id in visited:
        return True

    # Check max depth
    if max_depth <= 0:
        return True

    # Add current object to visited set
    visited.add(obj_id)

    try:
        if isinstance(obj, dict):
            for value in obj.values():
                if detect_circular_reference(value, max_depth - 1, visited):
                    return True
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                if detect_circular_reference(item, max_depth - 1, visited):
                    return True
        elif hasattr(obj, "__dict__"):
            for value in obj.__dict__.values():
                if detect_circular_reference(value, max_depth - 1, visited):
                    return True
    finally:
        # Remove from visited set when backtracking
        visited.discard(obj_id)

    return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL format, False otherwise
    """
    if not isinstance(url, str):
        return False

    # Basic URL pattern
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def sanitize_text(text: str) -> str:
    """
    Sanitize text by trimming whitespace.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    return text.strip()


def validate_array_elements(arr: List[str], allow_empty: bool = True) -> List[str]:
    """
    Validate and clean array elements.

    Args:
        arr: Array of strings to validate
        allow_empty: Whether to allow empty strings

    Returns:
        Cleaned array with empty strings removed (if allow_empty=False)
    """
    if not isinstance(arr, list):
        return []

    if allow_empty:
        return [str(item) for item in arr]

    return [str(item).strip() for item in arr if item and str(item).strip()]









