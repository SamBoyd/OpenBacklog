"""Response building utilities for prompt-driven tools."""

from typing import Any, Dict, List, Optional


def build_success_response(
    entity_type: str,
    message: str,
    data: Dict[str, Any],
    next_steps: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a standardized success response.

    Args:
        entity_type: Type of entity (vision, pillar, outcome, foundation)
        message: Human-readable success message
        data: Serialized entity data
        next_steps: Optional list of suggested next actions

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

    return response


def build_draft_response(
    entity_type: str,
    message: str,
    data: Dict[str, Any],
    next_steps: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a draft mode response with validation reminder.

    Draft mode responses indicate successful validation without persistence.
    They include explicit draft flag and reminder message for Claude Code.

    Args:
        entity_type: Type of entity (vision, pillar, outcome, etc.)
        message: Human-readable success message about validation
        data: Draft entity data dictionary with placeholder values
        next_steps: Optional list of suggested next actions

    Returns:
        Draft response dictionary with is_draft flag and validation reminder

    Example:
        >>> build_draft_response(
        ...     entity_type="strategic_pillar",
        ...     message="Draft pillar 'Developer Experience' validated successfully",
        ...     data={"id": "00000000-0000-0000-0000-000000000000", ...},
        ...     next_steps=["Review with user", "Submit with draft_mode=False if approved"]
        ... )
        {
            "status": "success",
            "type": "strategic_pillar",
            "is_draft": true,
            "message": "Draft pillar 'Developer Experience' validated successfully",
            "validation_message": "This is a draft. Please review with the user before final submission.",
            "data": {...},
            "next_steps": [...]
        }
    """
    response = {
        "status": "success",
        "type": entity_type,
        "is_draft": True,
        "message": message,
        "validation_message": "This is a draft. Please review with the user before final submission.",
        "data": data,
    }

    if next_steps:
        response["next_steps"] = next_steps

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
