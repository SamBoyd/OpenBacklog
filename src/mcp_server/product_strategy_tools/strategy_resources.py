"""MCP resources for product strategy entities.

This module provides MCP resources for read-only access to product strategy data:
- Product Vision (workspace vision statements)
- Strategic Pillars (ways to win)
- Product Outcomes (measurable objectives)
- Roadmap Themes (tactical bets)
- Strategic Initiatives (strategic context for initiatives)
- Strategy Overview (complete strategy in one call)

Resources use hierarchical URIs scoped to workspace for clear data organization.
All resources call controller functions directly with database sessions.

URI Schema:
  strategy://{workspace_id}/vision - Get workspace vision
  strategy://{workspace_id}/pillars - Get all strategic pillars
  strategy://{workspace_id}/pillars/{pillar_id} - Get single pillar
  strategy://{workspace_id}/outcomes - Get all product outcomes
  strategy://{workspace_id}/outcomes/{outcome_id} - Get single outcome
  strategy://{workspace_id}/themes - Get all roadmap themes
  strategy://{workspace_id}/themes/{theme_id} - Get single theme
  strategy://{workspace_id}/initiatives/{initiative_id} - Get strategic context
  strategy://{workspace_id}/overview - Get complete strategy overview
"""

import logging
import uuid
from typing import Any, Dict, List

from fastmcp.exceptions import ResourceError

from src.controllers import product_strategy_controller
from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.product_strategy_tools.utils import (
    serialize_outcome,
    serialize_pillar,
    serialize_strategic_initiative,
    serialize_theme,
    serialize_vision,
)
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.strategic_initiative import StrategicInitiative
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Vision Resources
# ============================================================================


@mcp.resource("strategy://{workspace_id}/vision")
def get_workspace_vision(workspace_id: str) -> Dict[str, Any]:
    """Get the product vision for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Vision data as dict with id, workspace_id, vision_text, timestamps

    Raises:
        ResourceError: If vision not found or workspace_id invalid

    Example:
        Resource URI: strategy://123e4567-e89b-12d3-a456-426614174000/vision
        Returns:
        {
            "id": "...",
            "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
            "vision_text": "Build the best AI-powered task management tool",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching vision for workspace {workspace_id}")

        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid workspace_id format: {workspace_id}") from e

        vision = product_strategy_controller.get_workspace_vision(
            workspace_uuid, session
        )

        if not vision:
            raise ResourceError(f"No vision found for workspace {workspace_id}")

        return serialize_vision(vision)

    except ResourceError:
        raise  # Re-raise ResourceError as-is
    except Exception as e:
        logger.exception(f"Error getting vision: {e}")
        raise ResourceError(f"Failed to retrieve vision: {str(e)}") from e
    finally:
        session.close()


# ============================================================================
# Strategic Pillar Resources
# ============================================================================


@mcp.resource("strategy://{workspace_id}/pillars")
def get_strategic_pillars(workspace_id: str) -> List[Dict[str, Any]]:
    """Get all strategic pillars for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        List of strategic pillar dicts ordered by display_order

    Raises:
        ResourceError: If workspace_id invalid or retrieval fails

    Example:
        Resource URI: strategy://123e4567-e89b-12d3-a456-426614174000/pillars
        Returns:
        [
            {
                "id": "...",
                "name": "AI-Native Workflows",
                "description": "Build AI-first features",
                "anti_strategy": "No enterprise features",
                "display_order": 0,
                ...
            }
        ]
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching pillars for workspace {workspace_id}")

        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid workspace_id format: {workspace_id}") from e

        pillars = product_strategy_controller.get_strategic_pillars(
            workspace_uuid, session
        )

        return [serialize_pillar(pillar) for pillar in pillars]

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting pillars: {e}")
        raise ResourceError(f"Failed to retrieve pillars: {str(e)}") from e
    finally:
        session.close()


@mcp.resource("strategy://{workspace_id}/pillars/{pillar_id}")
def get_strategic_pillar(workspace_id: str, pillar_id: str) -> Dict[str, Any]:
    """Get a single strategic pillar by ID.

    Args:
        workspace_id: UUID of the workspace (for hierarchical scoping)
        pillar_id: UUID of the pillar

    Returns:
        Pillar data as dict

    Raises:
        ResourceError: If pillar not found or IDs invalid

    Example:
        Resource URI: strategy://123.../pillars/223...
        Returns: {...pillar data...}
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching pillar {pillar_id} in workspace {workspace_id}")

        try:
            pillar_uuid = uuid.UUID(pillar_id)
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid UUID format") from e

        pillar = (
            session.query(StrategicPillar)
            .filter_by(id=pillar_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not pillar:
            raise ResourceError(
                f"Strategic pillar {pillar_id} not found in workspace {workspace_id}"
            )

        return serialize_pillar(pillar)

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting pillar: {e}")
        raise ResourceError(f"Failed to retrieve pillar: {str(e)}") from e
    finally:
        session.close()


# ============================================================================
# Product Outcome Resources
# ============================================================================


@mcp.resource("strategy://{workspace_id}/outcomes")
def get_product_outcomes(workspace_id: str) -> List[Dict[str, Any]]:
    """Get all product outcomes for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        List of product outcome dicts ordered by display_order

    Raises:
        ResourceError: If workspace_id invalid or retrieval fails

    Example:
        Resource URI: strategy://123e4567-e89b-12d3-a456-426614174000/outcomes
        Returns:
        [
            {
                "id": "...",
                "name": "80% of users use AI weekly",
                "description": "Measure AI adoption",
                "metrics": "% of weekly active users who use AI",
                "time_horizon_months": 12,
                ...
            }
        ]
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching outcomes for workspace {workspace_id}")

        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid workspace_id format: {workspace_id}") from e

        outcomes = product_strategy_controller.get_product_outcomes(
            workspace_uuid, session
        )

        return [serialize_outcome(outcome) for outcome in outcomes]

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting outcomes: {e}")
        raise ResourceError(f"Failed to retrieve outcomes: {str(e)}") from e
    finally:
        session.close()


@mcp.resource("strategy://{workspace_id}/outcomes/{outcome_id}")
def get_product_outcome(workspace_id: str, outcome_id: str) -> Dict[str, Any]:
    """Get a single product outcome by ID.

    Args:
        workspace_id: UUID of the workspace (for hierarchical scoping)
        outcome_id: UUID of the outcome

    Returns:
        Outcome data as dict

    Raises:
        ResourceError: If outcome not found or IDs invalid

    Example:
        Resource URI: strategy://123.../outcomes/323...
        Returns: {...outcome data...}
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching outcome {outcome_id} in workspace {workspace_id}")

        try:
            outcome_uuid = uuid.UUID(outcome_id)
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid UUID format") from e

        outcome = (
            session.query(ProductOutcome)
            .filter_by(id=outcome_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not outcome:
            raise ResourceError(
                f"Product outcome {outcome_id} not found in workspace {workspace_id}"
            )

        return serialize_outcome(outcome)

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting outcome: {e}")
        raise ResourceError(f"Failed to retrieve outcome: {str(e)}") from e
    finally:
        session.close()


# ============================================================================
# Roadmap Theme Resources
# ============================================================================


@mcp.resource("strategy://{workspace_id}/themes")
def get_roadmap_themes(workspace_id: str) -> List[Dict[str, Any]]:
    """Get all roadmap themes for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        List of roadmap theme dicts ordered by display_order

    Raises:
        ResourceError: If workspace_id invalid or retrieval fails

    Example:
        Resource URI: strategy://123e4567-e89b-12d3-a456-426614174000/themes
        Returns:
        [
            {
                "id": "...",
                "name": "First Week Magic",
                "problem_statement": "Users fail to integrate in first week",
                "hypothesis": "Quick wins drive adoption",
                "indicative_metrics": "% users active in week 1",
                "time_horizon_months": 6,
                ...
            }
        ]
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching themes for workspace {workspace_id}")

        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid workspace_id format: {workspace_id}") from e

        themes = product_strategy_controller.get_roadmap_themes(workspace_uuid, session)

        return [serialize_theme(theme) for theme in themes]

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting themes: {e}")
        raise ResourceError(f"Failed to retrieve themes: {str(e)}") from e
    finally:
        session.close()


@mcp.resource("strategy://{workspace_id}/themes/{theme_id}")
def get_roadmap_theme(workspace_id: str, theme_id: str) -> Dict[str, Any]:
    """Get a single roadmap theme by ID.

    Args:
        workspace_id: UUID of the workspace (for hierarchical scoping)
        theme_id: UUID of the theme

    Returns:
        Theme data as dict

    Raises:
        ResourceError: If theme not found or IDs invalid

    Example:
        Resource URI: strategy://123.../themes/423...
        Returns: {...theme data...}
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching theme {theme_id} in workspace {workspace_id}")

        try:
            theme_uuid = uuid.UUID(theme_id)
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid UUID format") from e

        theme = (
            session.query(RoadmapTheme)
            .filter_by(id=theme_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            raise ResourceError(
                f"Roadmap theme {theme_id} not found in workspace {workspace_id}"
            )

        return serialize_theme(theme)

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting theme: {e}")
        raise ResourceError(f"Failed to retrieve theme: {str(e)}") from e
    finally:
        session.close()


# ============================================================================
# Strategic Initiative Resources
# ============================================================================


@mcp.resource("strategy://{workspace_id}/initiatives/{initiative_id}")
def get_strategic_initiative_context(
    workspace_id: str, initiative_id: str
) -> Dict[str, Any]:
    """Get strategic context for an initiative.

    Args:
        workspace_id: UUID of the workspace (for hierarchical scoping)
        initiative_id: UUID of the initiative

    Returns:
        Strategic initiative context data as dict

    Raises:
        ResourceError: If strategic context not found or IDs invalid

    Example:
        Resource URI: strategy://123.../initiatives/523...
        Returns:
        {
            "id": "...",
            "initiative_id": "523e4567-e89b-12d3-a456-426614174004",
            "pillar_id": "223e4567-e89b-12d3-a456-426614174001",
            "theme_id": "423e4567-e89b-12d3-a456-426614174003",
            "user_need": "Solo developers need AI-powered assistance",
            "connection_to_vision": "Enables productive AI-assisted development",
            "success_criteria": "80% of users use AI weekly",
            "out_of_scope": "Team collaboration features",
            ...
        }
    """
    session = SessionLocal()
    try:
        logger.info(
            f"Fetching strategic context for initiative {initiative_id} in workspace {workspace_id}"
        )

        try:
            initiative_uuid = uuid.UUID(initiative_id)
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid UUID format") from e

        strategic_initiative = (
            session.query(StrategicInitiative)
            .filter_by(initiative_id=initiative_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not strategic_initiative:
            raise ResourceError(
                f"No strategic context found for initiative {initiative_id} in workspace {workspace_id}"
            )

        return serialize_strategic_initiative(strategic_initiative)

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting strategic context: {e}")
        raise ResourceError(f"Failed to retrieve strategic context: {str(e)}") from e
    finally:
        session.close()


# ============================================================================
# Strategy Overview Resource (Composite)
# ============================================================================


@mcp.resource("strategy://{workspace_id}/overview")
def get_workspace_strategy_overview(workspace_id: str) -> Dict[str, Any]:
    """Get complete product strategy overview for a workspace.

    This resource returns a comprehensive view of the workspace's product strategy,
    including vision, strategic pillars, product outcomes, roadmap themes,
    and strategic initiatives in a single call.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Complete strategy overview as dict with:
        - vision: Product vision (or null if not set)
        - pillars: List of strategic pillars
        - outcomes: List of product outcomes
        - themes: List of roadmap themes
        - strategic_initiatives: List of initiatives with strategic context
        - summary: Counts and metadata

    Raises:
        ResourceError: If workspace_id invalid or retrieval fails

    Example:
        Resource URI: strategy://123e4567-e89b-12d3-a456-426614174000/overview
        Returns:
        {
            "vision": {
                "id": "...",
                "vision_text": "Build the best AI-powered task management tool"
            },
            "pillars": [
                {
                    "id": "...",
                    "name": "AI-Native Workflows",
                    "description": "...",
                    ...
                }
            ],
            "outcomes": [
                {
                    "id": "...",
                    "name": "80% of users use AI weekly",
                    ...
                }
            ],
            "themes": [
                {
                    "id": "...",
                    "name": "First Week Magic",
                    ...
                }
            ],
            "strategic_initiatives": [
                {
                    "id": "...",
                    "initiative_id": "...",
                    "pillar_id": "...",
                    "theme_id": "...",
                    ...
                }
            ],
            "summary": {
                "has_vision": true,
                "pillar_count": 3,
                "outcome_count": 5,
                "theme_count": 2,
                "strategic_initiative_count": 8
            }
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Fetching complete strategy overview for workspace {workspace_id}")

        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as e:
            raise ResourceError(f"Invalid workspace_id format: {workspace_id}") from e

        # Fetch vision
        vision = product_strategy_controller.get_workspace_vision(
            workspace_uuid, session
        )
        vision_data = serialize_vision(vision) if vision else None

        # Fetch strategic pillars
        pillars = product_strategy_controller.get_strategic_pillars(
            workspace_uuid, session
        )
        pillars_data = [serialize_pillar(pillar) for pillar in pillars]

        # Fetch product outcomes
        outcomes = product_strategy_controller.get_product_outcomes(
            workspace_uuid, session
        )
        outcomes_data = [serialize_outcome(outcome) for outcome in outcomes]

        # Fetch roadmap themes
        themes = product_strategy_controller.get_roadmap_themes(workspace_uuid, session)
        themes_data = [serialize_theme(theme) for theme in themes]

        # Fetch all strategic initiatives for the workspace
        strategic_initiatives = (
            session.query(StrategicInitiative)
            .filter_by(workspace_id=workspace_uuid)
            .all()
        )
        strategic_initiatives_data = [
            serialize_strategic_initiative(si) for si in strategic_initiatives
        ]

        logger.info(
            f"Fetched strategy for workspace {workspace_id}: "
            f"{len(pillars)} pillars, {len(outcomes)} outcomes, "
            f"{len(themes)} themes, {len(strategic_initiatives)} strategic initiatives"
        )

        return {
            "vision": vision_data,
            "pillars": pillars_data,
            "outcomes": outcomes_data,
            "themes": themes_data,
            "strategic_initiatives": strategic_initiatives_data,
            "summary": {
                "has_vision": vision is not None,
                "pillar_count": len(pillars),
                "outcome_count": len(outcomes),
                "theme_count": len(themes),
                "strategic_initiative_count": len(strategic_initiatives),
            },
        }

    except ResourceError:
        raise
    except Exception as e:
        logger.exception(f"Error getting workspace strategy overview: {e}")
        raise ResourceError(f"Failed to retrieve strategy overview: {str(e)}") from e
    finally:
        session.close()
