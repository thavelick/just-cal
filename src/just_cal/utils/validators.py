"""Input validation utilities."""

from datetime import datetime


def validate_date_range(start: datetime, end: datetime) -> None:
    """Validate that end date is after start date.

    Args:
        start: Start datetime
        end: End datetime

    Raises:
        ValueError: If end is before start
    """
    if end < start:
        raise ValueError(f"End date ({end}) cannot be before start date ({start})")


def validate_non_empty(value: str, field_name: str) -> None:
    """Validate that a string field is not empty.

    Args:
        value: String value to validate
        field_name: Name of the field (for error messages)

    Raises:
        ValueError: If value is None or empty/whitespace
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
