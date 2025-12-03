"""Contract tests for JSON structure validation."""

from src.services.json_validator import validate_json_structure_compatibility


class TestJSONStructureContract:
    """Contract tests ensuring JSON structure validation matches expected schema."""

    def test_required_top_level_fields(self):
        """Contract: All required top-level fields must be present."""
        required_fields = [
            "workgroup",
            "workgroup_id",
            "meetingInfo",
            "agendaItems",
            "tags",
            "type",
        ]
        data = [{}]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is False
        for field in required_fields:
            assert any(f"Missing required field: {field}" in error for error in errors)

    def test_meeting_info_structure(self):
        """Contract: meetingInfo must be an object with date field."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True

    def test_agenda_items_array_structure(self):
        """Contract: agendaItems must be an array."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True

    def test_nested_collections_structure(self):
        """Contract: Nested collections (actionItems, decisionItems, discussionPoints) must be arrays."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174000",
                        "actionItems": [],
                        "decisionItems": [],
                        "discussionPoints": [],
                    }
                ],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True

    def test_schema_flexibility_additional_fields(self):
        """Contract: Additional fields beyond base model are allowed."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},
                "agendaItems": [],
                "tags": [],
                "type": "regular",
                "extraField1": "value1",
                "extraField2": {"nested": "data"},
                "extraField3": [1, 2, 3],
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True

    def test_optional_fields_handling(self):
        """Contract: Missing optional fields are accepted."""
        data = [
            {
                "workgroup": "Test",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2025-01-15"},  # Only required field
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(data)
        assert is_valid is True

    def test_empty_array_valid(self):
        """Contract: Empty array is valid."""
        is_valid, errors = validate_json_structure_compatibility([])
        assert is_valid is True

    def test_root_must_be_array(self):
        """Contract: Root JSON must be an array."""
        is_valid, errors = validate_json_structure_compatibility({"not": "array"})
        assert is_valid is False
        assert "Root JSON must be an array" in errors

    def test_historic_data_compatibility(self):
        """Contract: Historic data (2022-2024) should match same structure as 2025."""
        # Simulate historic data structure
        historic_data = [
            {
                "workgroup": "Historic Workgroup",
                "workgroup_id": "123e4567-e89b-12d3-a456-426614174000",
                "meetingInfo": {"date": "2024-01-15"},
                "agendaItems": [],
                "tags": [],
                "type": "regular",
            }
        ]
        is_valid, errors = validate_json_structure_compatibility(historic_data)
        assert is_valid is True

