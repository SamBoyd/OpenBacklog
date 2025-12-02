"""Response building utilities for prompt-driven tools."""

from typing import Any, Dict, List, Optional


def build_success_response(
    entity_type: str,
    message: str,
    data: Dict[str, Any],
    next_steps: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a standardized success response.

    Args:
        entity_type: Type of entity (vision, pillar, outcome, foundation)
        message: Human-readable success message
        data: Serialized entity data
        next_steps: Optional list of suggested next actions
        warnings: Optional list of warning messages (e.g., skipped invalid IDs)

    Returns:
        Standardized success response dictionary
    """
    response = {
        "status": "success",
        "type": entity_type,
        "message": message,
        "data": data,
    }

    if next_steps:
        response["next_steps"] = next_steps

    if warnings:
        response["warnings"] = warnings

    return response


def build_error_response(
    entity_type: str,
    error_message: str,
) -> Dict[str, Any]:
    """Build a standardized error response.

    Args:
        entity_type: Type of entity (vision, pillar, outcome, foundation)
        error_message: Human-readable error message

    Returns:
        Standardized error response dictionary
    """
    return {
        "status": "error",
        "type": entity_type,
        "error_message": error_message,
    }
