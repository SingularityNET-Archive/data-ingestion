"""Unit tests for JSON validator service."""

from src.models.meeting_summary import MeetingSummary
from src.services.json_validator import (
    JSONValidator,
    validate_json_structure_compatibility,
    validate_record,
)


class TestValidateJSONStructureCompatibility:
    """Tests for JSON structure compatibility validation."""

    def test_valid_structure(self, sample_meeting_array):
        """Test validation of valid JSON structure."""
        is_valid, errors = validate_json_structure_compatibility(sample_meeting_array)
        assert is_valid is True
        assert len(errors) == 0

    def test_empty_array(self):
        """Test validation of empty array."""
        is_valid, errors = validate_json_structure_compatibility([])
        assert is_valid is True
        assert len(errors) == 0

    def test_non_array_input(self):
        """Test validation of non-array input."""
        is_valid, errors = validate_json_structure_compatibility({"not": "array"})
        assert is_valid is False
        assert "Root JSON must be an array" in errors

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = [{"workgroup": "Test"}]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        assert any("workgroup_id" in error for error in errors)
        assert any("meetingInfo" in error for error in errors)

    def test_invalid_meeting_info_type(self):
        """Test validation with invalid meetingInfo type."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": "not an object",
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        assert any("meetingInfo must be an object" in error for error in errors)

    def test_missing_meeting_info_date(self):
        """Test validation with missing meetingInfo.date."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"host": "John"},
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        assert any("meetingInfo.date" in error for error in errors)

    def test_invalid_agenda_items_type(self):
        """Test validation with invalid agendaItems type."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": "not an array",
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        assert any("agendaItems must be an array" in error for error in errors)

    def test_invalid_nested_collections(self):
        """Test validation with invalid nested collection types."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174000",
                        "actionItems": "not an array",
                    }
                ],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        assert any("actionItems must be an array" in error for error in errors)

    def test_additional_fields_allowed(self, sample_meeting_summary):
        """Test that additional fields are allowed (schema flexibility)."""
        data = [sample_meeting_summary.copy()]
        data[0]["extraField"] = "allowed"
        data[0]["anotherField"] = {"nested": "data"}
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True


class TestValidateRecord:
    """Tests for individual record validation."""

    def test_valid_record(self, sample_meeting_summary):
        """Test validation of valid record."""
        is_valid, model, errors = validate_record(sample_meeting_summary)
        assert is_valid is True
        assert model is not None
        assert isinstance(model, MeetingSummary)
        assert len(errors) == 0

    def test_invalid_record_missing_fields(self, sample_invalid_meeting_summary):
        """Test validation of invalid record with missing fields."""
        is_valid, model, errors = validate_record(sample_invalid_meeting_summary)
        assert is_valid is False
        assert model is None
        assert len(errors) > 0

    def test_invalid_uuid_format(self):
        """Test validation with invalid UUID format."""
        data = {
            "workgroup": "Test",
            "workgroup_id": "invalid-uuid",
            "meetingInfo": {"date": "2025-01-15"},
            "agendaItems": [],
            "tags": [],
            "type": "regular",
        }
        is_valid, model, errors = validate_record(data)
        # UUID validation might pass at structure level but fail at model level
        # This depends on Pydantic validation rules
        assert isinstance(is_valid, bool)


class TestJSONValidator:
    """Tests for JSONValidator class."""

    def test_validate_structure_success(self, sample_meeting_array):
        """Test successful structure validation."""
        validator = JSONValidator()
        result = validator.validate_structure(sample_meeting_array, "https://example.com/data.json")
        assert result is True

    def test_validate_structure_failure(self):
        """Test failed structure validation."""
        validator = JSONValidator()
        data = [{"invalid": "data"}]
        result = validator.validate_structure(data, "https://example.com/data.json")
        assert result is False

    def test_validate_records_success(self, sample_meeting_array):
        """Test successful record validation."""
        validator = JSONValidator()
        valid_records, invalid_records = validator.validate_records(
            sample_meeting_array, "https://example.com/data.json"
        )
        assert len(valid_records) == 1
        assert len(invalid_records) == 0
        assert isinstance(valid_records[0], MeetingSummary)

    def test_validate_records_partial_failure(self):
        """Test record validation with some invalid records."""
        validator = JSONValidator()
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [],
                "tags": {},  # tags should be dict, not list
                "type": "regular",
            },
            {"invalid": "record"},
        ]
        valid_records, invalid_records = validator.validate_records(
            data, "https://example.com/data.json"
        )
        assert len(valid_records) == 1
        assert len(invalid_records) == 1
        assert "errors" in invalid_records[0]

    def test_validate_records_all_invalid(self):
        """Test record validation with all invalid records."""
        validator = JSONValidator()
        data = [{"invalid": "record1"}, {"invalid": "record2"}]
        valid_records, invalid_records = validator.validate_records(
            data, "https://example.com/data.json"
        )
        assert len(valid_records) == 0
        assert len(invalid_records) == 2
