"""Unit tests for validation utilities."""

from datetime import datetime

from src.lib.validators import (
    detect_circular_reference,
    parse_date,
    sanitize_text,
    validate_array_elements,
    validate_url,
    validate_uuid,
)


class TestValidateUUID:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Test validation of valid UUID."""
        assert validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True

    def test_invalid_uuid_format(self):
        """Test validation of invalid UUID format."""
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("123") is False
        assert validate_uuid("") is False

    def test_non_string_input(self):
        """Test validation with non-string input."""
        assert validate_uuid(123) is False
        assert validate_uuid(None) is False
        assert validate_uuid([]) is False


class TestParseDate:
    """Tests for date parsing."""

    def test_parse_iso_date(self):
        """Test parsing ISO 8601 date format."""
        result = parse_date("2025-01-15")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_iso_datetime(self):
        """Test parsing ISO 8601 datetime format."""
        result = parse_date("2025-01-15T10:30:00")
        assert isinstance(result, datetime)
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_datetime_with_timezone(self):
        """Test parsing ISO 8601 datetime with timezone."""
        result = parse_date("2025-01-15T10:30:00Z")
        assert isinstance(result, datetime)

    def test_parse_common_formats(self):
        """Test parsing common date formats."""
        result = parse_date("01/15/2025")
        assert isinstance(result, datetime)
        assert result.year == 2025

        result = parse_date("15-01-2025")
        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_parse_invalid_date(self):
        """Test parsing invalid date strings."""
        assert parse_date("invalid-date") is None
        assert parse_date("2025-13-45") is None
        assert parse_date("") is None

    def test_parse_non_string_input(self):
        """Test parsing with non-string input."""
        assert parse_date(123) is None
        assert parse_date(None) is None
        assert parse_date([]) is None


class TestDetectCircularReference:
    """Tests for circular reference detection."""

    def test_no_circular_reference(self):
        """Test detection with no circular references."""
        data = {"a": 1, "b": {"c": 2}}
        assert detect_circular_reference(data) is False

    def test_circular_reference_in_dict(self):
        """Test detection of circular reference in dictionary."""
        data = {}
        data["self"] = data  # Create circular reference
        assert detect_circular_reference(data) is True

    def test_circular_reference_in_list(self):
        """Test detection of circular reference in list."""
        data = []
        data.append(data)  # Create circular reference
        assert detect_circular_reference(data) is True

    def test_max_depth_exceeded(self):
        """Test detection when max depth is exceeded."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {}}}}}}}}}}}
        assert detect_circular_reference(data, max_depth=5) is True

    def test_max_depth_not_exceeded(self):
        """Test that normal nesting doesn't trigger max depth."""
        data = {"a": {"b": {"c": {"d": {"e": {}}}}}}
        assert detect_circular_reference(data, max_depth=10) is False

    def test_nested_structure_no_circular(self):
        """Test complex nested structure without circular references."""
        data = {
            "meeting": {
                "agenda": [
                    {"item": "item1"},
                    {"item": "item2"},
                ],
                "attendees": ["Alice", "Bob"],
            }
        }
        assert detect_circular_reference(data) is False


class TestValidateURL:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        assert validate_url("http://example.com") is True
        assert validate_url("http://example.com/path") is True
        assert validate_url("http://example.com:8080/path") is True

    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        assert validate_url("https://example.com") is True
        assert validate_url("https://example.com/api/data") is True

    def test_invalid_url(self):
        """Test validation of invalid URLs."""
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False
        assert validate_url("example.com") is False

    def test_localhost_url(self):
        """Test validation of localhost URL."""
        assert validate_url("http://localhost:3000") is True
        assert validate_url("http://127.0.0.1:5432") is True

    def test_non_string_input(self):
        """Test validation with non-string input."""
        assert validate_url(123) is False
        assert validate_url(None) is False


class TestSanitizeText:
    """Tests for text sanitization."""

    def test_trim_whitespace(self):
        """Test trimming whitespace from text."""
        assert sanitize_text("  hello world  ") == "hello world"
        assert sanitize_text("\t\n  test  \n\t") == "test"

    def test_empty_string(self):
        """Test handling of empty string."""
        assert sanitize_text("") == ""
        assert sanitize_text("   ") == ""

    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert sanitize_text(123) == ""
        assert sanitize_text(None) == ""


class TestValidateArrayElements:
    """Tests for array element validation."""

    def test_valid_array(self):
        """Test validation of valid array."""
        result = validate_array_elements(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_empty_array(self):
        """Test handling of empty array."""
        result = validate_array_elements([])
        assert result == []

    def test_array_with_empty_strings_allow_empty(self):
        """Test array with empty strings when allow_empty=True."""
        result = validate_array_elements(["a", "", "b", "   "], allow_empty=True)
        assert result == ["a", "", "b", "   "]

    def test_array_with_empty_strings_disallow_empty(self):
        """Test array with empty strings when allow_empty=False."""
        result = validate_array_elements(["a", "", "b", "   "], allow_empty=False)
        assert result == ["a", "b"]

    def test_non_array_input(self):
        """Test handling of non-array input."""
        assert validate_array_elements("not an array") == []
        assert validate_array_elements(123) == []
        assert validate_array_elements(None) == []




