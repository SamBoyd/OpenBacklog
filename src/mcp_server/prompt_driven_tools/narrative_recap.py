"""Prompt-driven MCP tools for narrative recaps and story bible.

This module provides tools for generating narrative recaps ("Previously on...")
and retrieving the complete story bible for a workspace.
"""

import logging
import uuid
from typing import Any, Dict, List

from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_conflict,
    serialize_hero,
    serialize_turning_point,
    serialize_villain,
)
from src.narrative.services.conflict_service import ConflictService
from src.narrative.services.hero_service import HeroService
from src.narrative.services.narrator_service import NarratorService
from src.narrative.services.villain_service import VillainService
from src.roadmap_intelligence import controller as roadmap_controller
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Narrative Recap Tools
# ============================================================================


@mcp.tool()
async def get_recent_turning_points(limit: int = 10) -> Dict[str, Any]:
    """Retrieves recent turning points for narrative recap.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        limit: Maximum number of turning points to return (default 10)

    Returns:
        List of recent turning points ordered by created_at DESC
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting recent turning points for workspace {workspace_uuid} (limit={limit})"
        )

        narrator_service = NarratorService(session)
        turning_points = narrator_service.get_recent_turning_points(
            workspace_uuid, limit=limit
        )

        return build_success_response(
            entity_type="turning_point",
            message=f"Found {len(turning_points)} recent turning point(s)",
            data=[serialize_turning_point(tp) for tp in turning_points],
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("turning_point", str(e))
    except Exception as e:
        logger.exception(f"Error getting turning points: {e}")
        return build_error_response("turning_point", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def generate_previously_on() -> Dict[str, Any]:
    """Generates 'Previously on...' narrative recap.

    This is the key MCP tool that enables narrative-aware development.
    It generates a story-style summary of recent progress.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Narrative recap including:
        - recap_text: Story-style summary
        - primary_hero: Primary hero details
        - active_arcs: Active story arcs with narrative context
        - recent_turning_points: Recent turning points
        - open_conflicts: Open conflicts
        - suggested_next_tasks: Suggested next tasks (placeholder)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Generating 'Previously on...' recap for workspace {workspace_uuid}"
        )

        narrator_service = NarratorService(session)
        recap = narrator_service.generate_previously_on(workspace_uuid)

        return build_success_response(
            entity_type="narrative_recap",
            message="Generated narrative recap successfully",
            data=recap,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("narrative_recap", str(e))
    except Exception as e:
        logger.exception(f"Error generating recap: {e}")
        return build_error_response("narrative_recap", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_story_bible() -> Dict[str, Any]:
    """Retrieves complete story bible for workspace.

    Returns all narrative entities in one unified view.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Complete story bible including:
        - heroes: All heroes
        - villains: All villains
        - story_arcs: All roadmap themes with narrative context
        - conflicts: All conflicts
        - turning_points: Recent turning points
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting story bible for workspace {workspace_uuid}")

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        villain_service = VillainService(session, publisher)
        conflict_service = ConflictService(session, publisher)
        narrator_service = NarratorService(session)

        heroes = hero_service.get_heroes_for_workspace(workspace_uuid)
        villains = villain_service.get_villains_for_workspace(workspace_uuid)
        conflicts = conflict_service.get_conflicts_for_workspace(workspace_uuid)
        turning_points = narrator_service.get_recent_turning_points(
            workspace_uuid, limit=20
        )

        story_arcs = roadmap_controller.get_roadmap_themes(workspace_uuid, session)
        story_arcs_with_narrative = []
        for arc in story_arcs:
            arc_data = {
                "id": str(arc.id),
                "name": arc.name,
                "description": getattr(arc, "description", None),
                "hero_id": str(arc.hero_id) if arc.hero_id else None,
                "primary_villain_id": (
                    str(arc.primary_villain_id) if arc.primary_villain_id else None
                ),
            }
            if arc.hero_id:
                matching_hero = next((h for h in heroes if h.id == arc.hero_id), None)
                if matching_hero:
                    arc_data["hero"] = serialize_hero(matching_hero)

            if arc.primary_villain_id:
                matching_villain = next(
                    (v for v in villains if v.id == arc.primary_villain_id), None
                )
                if matching_villain:
                    arc_data["villain"] = serialize_villain(matching_villain)

            story_arcs_with_narrative.append(arc_data)

        story_bible = {
            "type": "story_bible",
            "heroes": [serialize_hero(hero) for hero in heroes],
            "villains": [serialize_villain(villain) for villain in villains],
            "story_arcs": story_arcs_with_narrative,
            "conflicts": [serialize_conflict(conflict) for conflict in conflicts],
            "turning_points": [serialize_turning_point(tp) for tp in turning_points],
        }

        return build_success_response(
            entity_type="story_bible",
            message="Retrieved complete story bible",
            data=story_bible,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("story_bible", str(e))
    except Exception as e:
        logger.exception(f"Error getting story bible: {e}")
        return build_error_response("story_bible", f"Server error: {str(e)}")
    finally:
        session.close()
