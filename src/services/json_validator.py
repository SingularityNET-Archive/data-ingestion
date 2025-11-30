"""JSON validator service for structure compatibility and record validation."""

from typing import List, Dict, Any, Tuple, Optional
from pydantic import ValidationError

from src.models.meeting_summary import MeetingSummary
from src.lib.logger import get_logger

logger = get_logger(__name__)


def validate_json_structure_compatibility(
    json_data: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Validate JSON structure compatibility before processing.

    Checks for required top-level fields and nested structure patterns.
    Accepts optional fields and additional fields for schema flexibility.

    Args:
        json_data: List of JSON objects to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not isinstance(json_data, list):
        return False, ["Root JSON must be an array"]

    if not json_data:
        return True, []  # Empty array is valid

    # Check required top-level fields in sample record
    sample = json_data[0]
    required_fields = ["workgroup", "workgroup_id", "meetingInfo", "agendaItems", "tags", "type"]

    for field in required_fields:
        if field not in sample:
            errors.append(f"Missing required field: {field}")

    # Check nested structure if meetingInfo exists
    if "meetingInfo" in sample:
        if not isinstance(sample["meetingInfo"], dict):
            errors.append("meetingInfo must be an object")
        elif "date" not in sample["meetingInfo"]:
            errors.append("Missing required field: meetingInfo.date")

    # Check agendaItems is array
    if "agendaItems" in sample:
        if not isinstance(sample["agendaItems"], list):
            errors.append("agendaItems must be an array")
        else:
            # Validate nested structure patterns in agendaItems
            for idx, agenda_item in enumerate(sample["agendaItems"][:5]):  # Check first 5 items
                if isinstance(agenda_item, dict):
                    # Check for nested collections (optional but validate structure if present)
                    if "actionItems" in agenda_item and not isinstance(agenda_item["actionItems"], list):
                        errors.append(f"agendaItems[{idx}].actionItems must be an array")
                    if "decisionItems" in agenda_item and not isinstance(agenda_item["decisionItems"], list):
                        errors.append(f"agendaItems[{idx}].decisionItems must be an array")
                    if "discussionPoints" in agenda_item and not isinstance(agenda_item["discussionPoints"], list):
                        errors.append(f"agendaItems[{idx}].discussionPoints must be an array")

    # Note: Additional fields are allowed (schema flexibility)
    # Optional fields are handled gracefully (missing fields result in NULL values)

    return len(errors) == 0, errors


def validate_record(
    record: Dict[str, Any],
) -> Tuple[bool, Optional[MeetingSummary], List[str]]:
    """
    Validate and parse a single meeting summary record.

    Args:
        record: JSON record to validate

    Returns:
        Tuple of (is_valid, parsed_model, error_messages)
    """
    errors = []

    try:
        model = MeetingSummary(**record)
        return True, model, []
    except ValidationError as e:
        for error in e.errors():
            field = ".".join(str(x) for x in error.get("loc", []))
            error_msg = f"Field '{field}': {error.get('msg', 'validation error')}"
            errors.append(error_msg)
        return False, None, errors
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, None, errors


class JSONValidator:
    """Service for validating JSON structure and records."""

    def validate_structure(self, json_data: List[Dict[str, Any]], source_url: str) -> bool:
        """
        Validate JSON structure compatibility for a source.

        Args:
            json_data: List of JSON objects to validate
            source_url: Source URL for logging

        Returns:
            True if structure is compatible, False otherwise
        """
        is_valid, errors = validate_json_structure_compatibility(json_data)

        if not is_valid:
            logger.error(
                f"JSON structure incompatible for {source_url}",
                extra={"source_url": source_url, "errors": errors},
            )
            return False

        logger.info(
            f"JSON structure validated for {source_url}",
            extra={"source_url": source_url, "record_count": len(json_data)},
        )
        return True

    def validate_records(
        self, json_data: List[Dict[str, Any]], source_url: str
    ) -> Tuple[List[MeetingSummary], List[Dict[str, Any]]]:
        """
        Validate all records in JSON array.

        Args:
            json_data: List of JSON objects to validate
            source_url: Source URL for logging

        Returns:
            Tuple of (valid_records, invalid_records_with_errors)
        """
        valid_records = []
        invalid_records = []

        for idx, record in enumerate(json_data):
            is_valid, model, errors = validate_record(record)

            if is_valid and model:
                valid_records.append(model)
            else:
                record_id = record.get("id") or record.get("workgroup_id") or str(idx)
                logger.warning(
                    f"Record validation failed: {record_id}",
                    extra={
                        "source_url": source_url,
                        "record_id": record_id,
                        "errors": errors,
                    },
                )
                invalid_records.append({"record": record, "errors": errors})

        logger.info(
            f"Validated {len(json_data)} records from {source_url}: "
            f"{len(valid_records)} valid, {len(invalid_records)} invalid",
            extra={
                "source_url": source_url,
                "valid_count": len(valid_records),
                "invalid_count": len(invalid_records),
            },
        )

        return valid_records, invalid_records
