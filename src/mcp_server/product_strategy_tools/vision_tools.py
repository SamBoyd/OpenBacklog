"""MCP tools for product strategy operations.

This module provides MCP tools for managing product strategy entities:
- Product Vision (workspace vision statements)

All tools call controller functions directly with database sessions.
"""

import logging
import uuid
from typing import Any, Dict

from src.controllers import product_strategy_controller
from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.product_strategy_tools.utils import (
    get_user_id_from_request,
    serialize_vision,
)
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Vision Tools
# ============================================================================


@mcp.tool()
async def set_workspace_vision(workspace_id: str, vision_text: str) -> Dict[str, Any]:
    """Create or update the product vision for a workspace.

    Args:
        workspace_id: UUID of the workspace
        vision_text: Vision statement (1-1000 characters)

    Returns:
        Created or updated vision data

    Example:
        >>> await set_workspace_vision(
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "Build the best AI-powered task management tool for solo developers"
        ... )
        {
            "status": "success",
            "type": "vision",
            "message": "Vision created/updated successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Setting vision for workspace {workspace_id}")

        user_id = get_user_id_from_request()

        vision = product_strategy_controller.upsert_workspace_vision(
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            vision_text=vision_text,
            session=session,
        )

        return {
            "status": "success",
            "type": "vision",
            "message": "Vision created/updated successfully",
            "data": serialize_vision(vision),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return {
            "status": "error",
            "type": "vision",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "vision",
            "error_message": f"Invalid workspace_id format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error setting vision: {e}")
        return {
            "status": "error",
            "type": "vision",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def delete_workspace_vision(workspace_id: str) -> Dict[str, Any]:
    """Delete the product vision for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Confirmation of deletion

    Example:
        >>> await delete_workspace_vision("123e4567-e89b-12d3-a456-426614174000")
        {
            "status": "success",
            "type": "vision",
            "message": "Vision deleted successfully"
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Deleting vision for workspace {workspace_id}")

        vision = product_strategy_controller.get_workspace_vision(
            uuid.UUID(workspace_id), session
        )

        if not vision:
            return {
                "status": "error",
                "type": "vision",
                "error_message": "No vision found for workspace",
            }

        # Delete the vision
        session.delete(vision)
        session.commit()

        return {
            "status": "success",
            "type": "vision",
            "message": "Vision deleted successfully",
        }

    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "vision",
            "error_message": f"Invalid workspace_id format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error deleting vision: {e}")
        session.rollback()
        return {
            "status": "error",
            "type": "vision",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()
