"""MCP tools for strategic initiative operations.

This module provides MCP tools for managing strategic initiative context.
All tools call controller functions directly with database sessions.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from src.controllers import product_strategy_controller
from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.product_strategy_tools.utils import (
    get_user_id_from_request,
    serialize_strategic_initiative,
)
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Strategic Initiative Tools
# ============================================================================


@mcp.tool()
async def create_strategic_context(
    initiative_id: str,
    workspace_id: str,
    pillar_id: Optional[str] = None,
    theme_id: Optional[str] = None,
    user_need: Optional[str] = None,
    connection_to_vision: Optional[str] = None,
    success_criteria: Optional[str] = None,
    out_of_scope: Optional[str] = None,
) -> Dict[str, Any]:
    """Create strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        workspace_id: UUID of the workspace
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        user_need: What user need or problem this addresses (max 1000 chars)
        connection_to_vision: How this connects to vision (max 1000 chars)
        success_criteria: What success looks like (max 1000 chars)
        out_of_scope: What is explicitly NOT being done (max 1000 chars)

    Returns:
        Created strategic initiative context data

    Example:
        >>> await create_strategic_context(
        ...     "523e4567-e89b-12d3-a456-426614174004",
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "223e4567-e89b-12d3-a456-426614174001",
        ...     "423e4567-e89b-12d3-a456-426614174003",
        ...     "Solo developers need AI-powered assistance",
        ...     "Enables productive AI-assisted development",
        ...     "80% of users use AI weekly",
        ...     "Team collaboration features"
        ... )
        {
            "status": "success",
            "type": "strategic_initiative",
            "message": "Strategic context created successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Creating strategic context for initiative {initiative_id}")

        user_id = get_user_id_from_request()

        # Convert IDs from strings to UUIDs
        pillar_uuid = uuid.UUID(pillar_id) if pillar_id else None
        theme_uuid = uuid.UUID(theme_id) if theme_id else None

        strategic_initiative = product_strategy_controller.create_strategic_initiative(
            initiative_id=uuid.UUID(initiative_id),
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            pillar_id=pillar_uuid,
            theme_id=theme_uuid,
            user_need=user_need,
            connection_to_vision=connection_to_vision,
            success_criteria=success_criteria,
            out_of_scope=out_of_scope,
            session=session,
        )

        return {
            "status": "success",
            "type": "strategic_initiative",
            "message": "Strategic context created successfully",
            "data": serialize_strategic_initiative(strategic_initiative),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error creating strategic context: {e}")
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def update_strategic_context(
    initiative_id: str,
    pillar_id: Optional[str] = None,
    theme_id: Optional[str] = None,
    user_need: Optional[str] = None,
    connection_to_vision: Optional[str] = None,
    success_criteria: Optional[str] = None,
    out_of_scope: Optional[str] = None,
) -> Dict[str, Any]:
    """Update strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        user_need: Updated user need (max 1000 chars)
        connection_to_vision: Updated vision connection (max 1000 chars)
        success_criteria: Updated success criteria (max 1000 chars)
        out_of_scope: Updated out of scope (max 1000 chars)

    Returns:
        Updated strategic initiative context data

    Example:
        >>> await update_strategic_context(
        ...     "523e4567-e89b-12d3-a456-426614174004",
        ...     "223e4567-e89b-12d3-a456-426614174001",
        ...     "423e4567-e89b-12d3-a456-426614174003",
        ...     "Updated user need",
        ...     "Updated vision connection",
        ...     "Updated success criteria",
        ...     "Updated out of scope"
        ... )
        {
            "status": "success",
            "type": "strategic_initiative",
            "message": "Strategic context updated successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Updating strategic context for initiative {initiative_id}")

        # Convert IDs from strings to UUIDs
        pillar_uuid = uuid.UUID(pillar_id) if pillar_id else None
        theme_uuid = uuid.UUID(theme_id) if theme_id else None

        strategic_initiative = product_strategy_controller.update_strategic_initiative(
            initiative_id=uuid.UUID(initiative_id),
            pillar_id=pillar_uuid,
            theme_id=theme_uuid,
            user_need=user_need,
            connection_to_vision=connection_to_vision,
            success_criteria=success_criteria,
            out_of_scope=out_of_scope,
            session=session,
        )

        return {
            "status": "success",
            "type": "strategic_initiative",
            "message": "Strategic context updated successfully",
            "data": serialize_strategic_initiative(strategic_initiative),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "strategic_initiative",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error updating strategic context: {e}")
        return {
            "status": "error",
            "type": "strategic_initiative",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()
