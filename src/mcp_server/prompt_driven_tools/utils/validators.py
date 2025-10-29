"""Input validation utilities for prompt-driven tools."""

import uuid


def validate_uuid(value: str, field_name: str = "UUID") -> uuid.UUID:
    """Validate and convert string to UUID.

    Args:
        value: String representation of UUID
        field_name: Name of field being validated (for error messages)

    Returns:
        UUID object

    Raises:
        ValueError: If string is not a valid UUID
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError) as e:
        raise ValueError(f"Invalid {field_name} format: {str(e)}")


def validate_time_horizon(months: int | None) -> None:
    """Validate time horizon is within acceptable range.

    Args:
        months: Time horizon in months (or None)

    Raises:
        ValueError: If time horizon is outside 1-36 month range
    """
    if months is not None and (months < 1 or months > 36):
        raise ValueError("Time horizon must be between 1 and 36 months")
