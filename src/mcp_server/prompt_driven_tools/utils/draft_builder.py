"""Draft entity data builders for validation workflows.

This module provides functions to build draft entity data dictionaries
with placeholder values for IDs and timestamps. These are used in draft mode
to validate entity data without persisting to the database.
"""

import uuid
from typing import Any, Dict, List, Optional

from src.models import InitiativeStatus


def build_draft_vision_data(
    workspace_id: uuid.UUID,
    vision_text: str,
    existing_vision_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """Build draft vision data dictionary with placeholder values.

    Args:
        workspace_id: UUID of the workspace
        vision_text: The vision text
        existing_vision_id: If vision exists, use its ID; otherwise use placeholder

    Returns:
        Dictionary with vision data and placeholder timestamps
    """
    return {
        "id": (
            str(existing_vision_id)
            if existing_vision_id
            else "00000000-0000-0000-0000-000000000000"
        ),
        "workspace_id": str(workspace_id),
        "description": vision_text,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_pillar_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: Optional[str],
    display_order: int,
) -> Dict[str, Any]:
    """Build draft pillar data dictionary with placeholder values.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        name: Pillar name
        description: Optional pillar description
        display_order: Display order (0-4)

    Returns:
        Dictionary with pillar data and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "name": name,
        "description": description,
        "display_order": display_order,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_outcome_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: str,
    display_order: int,
    pillar_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build draft outcome data dictionary with placeholder values.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        name: Outcome name
        description: Outcome description
        display_order: Display order
        pillar_ids: Optional list of pillar UUIDs to link

    Returns:
        Dictionary with outcome data and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "name": name,
        "description": description,
        "display_order": display_order,
        "pillar_ids": pillar_ids or [],
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_conflict_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    hero_identifier: str,
    villain_identifier: str,
    description: str,
    story_arc_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build draft conflict data dictionary with placeholder values.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        hero_identifier: Hero identifier
        villain_identifier: Villain identifier
        description: Conflict description
        story_arc_id: Optional story arc ID to link

    Returns:
        Dictionary with conflict data and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "hero_identifier": hero_identifier,
        "villain_identifier": villain_identifier,
        "description": description,
        "story_arc_id": story_arc_id,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_hero_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: Optional[str],
    is_primary: bool,
) -> Dict[str, Any]:
    """Build draft hero data dictionary with temporary identifier.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        name: Hero name
        description: Optional hero description
        is_primary: Whether this is the primary hero

    Returns:
        Dictionary with hero data, temporary identifier, and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "identifier": "H-DRAFT-001",  # Temporary identifier
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "name": name,
        "description": description,
        "is_primary": is_primary,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_villain_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    villain_type: str,
    description: str,
    severity: int,
) -> Dict[str, Any]:
    """Build draft villain data dictionary with temporary identifier.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        name: Villain name
        villain_type: Villain type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER)
        description: Villain description
        severity: Severity rating (1-5)

    Returns:
        Dictionary with villain data, temporary identifier, and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "identifier": "V-DRAFT-001",  # Temporary identifier
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "name": name,
        "villain_type": villain_type,
        "description": description,
        "severity": severity,
        "is_defeated": False,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_theme_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: str,
    display_order: int,
    outcome_ids: Optional[List[str]] = None,
    hero_identifier: Optional[str] = None,
    primary_villain_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Build draft roadmap theme data dictionary with placeholder values.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user
        name: Theme name
        description: Theme description
        display_order: Display order
        outcome_ids: Optional list of outcome UUIDs to link
        hero_identifier: Optional hero identifier to link
        primary_villain_identifier: Optional villain identifier to link

    Returns:
        Dictionary with theme data and placeholder ID/timestamps
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "name": name,
        "description": description,
        "display_order": display_order,
        "is_prioritized": False,
        "outcome_ids": outcome_ids or [],
        "hero_identifier": hero_identifier,
        "primary_villain_identifier": primary_villain_identifier,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }


def build_draft_initiative_data(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    description: str,
    status: InitiativeStatus,
) -> Dict[str, Any]:
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "title": title,
        "description": description,
        "status": status,
        "created_at": "0001-01-01T00:00:00",
        "updated_at": "0001-01-01T00:00:00",
    }
