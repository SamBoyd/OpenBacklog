"""MCP tools for product strategy operations.

This module provides MCP tools for managing product strategy entities:
- Product Vision (workspace vision statements)
- Strategic Pillars (ways to win)
- Product Outcomes (measurable objectives)
- Roadmap Themes (tactical bets)
- Strategic Initiatives (strategic context for initiatives)

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
    serialize_pillar,
)
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Strategic Pillar Tools
# ============================================================================


@mcp.tool()
async def create_strategic_pillar(
    workspace_id: str,
    name: str,
    description: Optional[str] = None,
    anti_strategy: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new strategic pillar for a workspace.

    Args:
        workspace_id: UUID of the workspace
        name: Pillar name (1-100 characters, unique per workspace)
        description: Optional pillar description (max 1000 characters)
        anti_strategy: Optional anti-strategy text (max 1000 characters)

    Returns:
        Created pillar data

    Example:
        >>> await create_strategic_pillar(
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "Developer Experience",
        ...     "Make developers love our product",
        ...     "Not enterprise features"
        ... )
        {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar created successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Creating pillar '{name}' for workspace {workspace_id}")

        user_id = get_user_id_from_request()

        pillar = product_strategy_controller.create_strategic_pillar(
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            name=name,
            description=description,
            anti_strategy=anti_strategy,
            session=session,
        )

        return {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar created successfully",
            "data": serialize_pillar(pillar),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Invalid workspace_id format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error creating pillar: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def update_strategic_pillar(
    pillar_id: str,
    workspace_id: str,
    name: str,
    description: Optional[str] = None,
    anti_strategy: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing strategic pillar.

    Args:
        pillar_id: UUID of the pillar to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated pillar name (1-100 characters, unique per workspace)
        description: Updated pillar description (max 1000 characters)
        anti_strategy: Updated anti-strategy text (max 1000 characters)

    Returns:
        Updated pillar data

    Example:
        >>> await update_strategic_pillar(
        ...     "223e4567-e89b-12d3-a456-426614174001",
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "Updated Pillar Name",
        ...     "Updated description"
        ... )
        {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar updated successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Updating pillar {pillar_id}")

        pillar = product_strategy_controller.update_strategic_pillar(
            pillar_id=uuid.UUID(pillar_id),
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            description=description,
            anti_strategy=anti_strategy,
            session=session,
        )

        return {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar updated successfully",
            "data": serialize_pillar(pillar),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "pillar",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "pillar",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error updating pillar: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def delete_strategic_pillar(pillar_id: str, workspace_id: str) -> Dict[str, Any]:
    """Delete a strategic pillar.

    Args:
        pillar_id: UUID of the pillar to delete
        workspace_id: UUID of the workspace (for verification)

    Returns:
        Confirmation of deletion

    Example:
        >>> await delete_strategic_pillar(
        ...     "223e4567-e89b-12d3-a456-426614174001",
        ...     "123e4567-e89b-12d3-a456-426614174000"
        ... )
        {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar deleted successfully"
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Deleting pillar {pillar_id}")

        user_id = get_user_id_from_request()

        product_strategy_controller.delete_strategic_pillar(
            pillar_id=uuid.UUID(pillar_id),
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            session=session,
        )

        return {
            "status": "success",
            "type": "pillar",
            "message": "Strategic pillar deleted successfully",
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "pillar",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "pillar",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error deleting pillar: {e}")
        return {
            "status": "error",
            "type": "pillar",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()
