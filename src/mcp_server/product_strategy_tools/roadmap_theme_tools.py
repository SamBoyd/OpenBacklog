"""MCP tools for roadmap theme operations.

This module provides MCP tools for managing roadmap themes.
All tools call controller functions directly with database sessions.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from src.controllers import product_strategy_controller
from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.product_strategy_tools.utils import (
    get_user_id_from_request,
    serialize_theme,
)
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Roadmap Theme Tools
# ============================================================================


@mcp.tool()
async def create_roadmap_theme(
    workspace_id: str,
    name: str,
    problem_statement: str,
    hypothesis: Optional[str] = None,
    indicative_metrics: Optional[str] = None,
    time_horizon_months: Optional[int] = None,
    outcome_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new roadmap theme for a workspace.

    Args:
        workspace_id: UUID of the workspace
        name: Theme name (1-100 characters, unique per workspace)
        problem_statement: Problem being solved (1-1500 characters, required)
        hypothesis: Expected outcome (max 1500 characters)
        indicative_metrics: Success metrics (max 1000 characters)
        time_horizon_months: Time horizon in months (0-12)
        outcome_ids: List of outcome UUIDs to link to this theme

    Returns:
        Created theme data

    Example:
        >>> await create_roadmap_theme(
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "First Week Magic",
        ...     "Users fail to integrate in first week",
        ...     "Quick wins drive adoption",
        ...     "% users active in week 1",
        ...     6,
        ...     ["323e4567-e89b-12d3-a456-426614174002"]
        ... )
        {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme created successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Creating theme '{name}' for workspace {workspace_id}")

        user_id = get_user_id_from_request()

        # Convert outcome_ids from strings to UUIDs
        outcome_uuids = []
        if outcome_ids:
            outcome_uuids = [uuid.UUID(oid) for oid in outcome_ids]

        theme = product_strategy_controller.create_roadmap_theme(
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            outcome_ids=outcome_uuids,
            session=session,
        )

        return {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme created successfully",
            "data": serialize_theme(theme),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error creating theme: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def update_roadmap_theme(
    theme_id: str,
    workspace_id: str,
    name: str,
    problem_statement: str,
    hypothesis: Optional[str] = None,
    indicative_metrics: Optional[str] = None,
    time_horizon_months: Optional[int] = None,
    outcome_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update an existing roadmap theme.

    Args:
        theme_id: UUID of the theme to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated theme name (1-100 characters, unique per workspace)
        problem_statement: Updated problem statement (1-1500 characters)
        hypothesis: Updated hypothesis (max 1500 characters)
        indicative_metrics: Updated metrics (max 1000 characters)
        time_horizon_months: Updated time horizon (0-12 months)
        outcome_ids: List of outcome UUIDs to link to this theme

    Returns:
        Updated theme data

    Example:
        >>> await update_roadmap_theme(
        ...     "423e4567-e89b-12d3-a456-426614174003",
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "Updated theme name",
        ...     "Updated problem statement",
        ...     "Updated hypothesis",
        ...     "Updated metrics",
        ...     9,
        ...     ["323e4567-e89b-12d3-a456-426614174002"]
        ... )
        {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme updated successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Updating theme {theme_id}")

        # Convert outcome_ids from strings to UUIDs
        outcome_uuids = []
        if outcome_ids:
            outcome_uuids = [uuid.UUID(oid) for oid in outcome_ids]

        theme = product_strategy_controller.update_roadmap_theme(
            theme_id=uuid.UUID(theme_id),
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            outcome_ids=outcome_uuids,
            session=session,
        )

        return {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme updated successfully",
            "data": serialize_theme(theme),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "theme",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "theme",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error updating theme: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def delete_roadmap_theme(theme_id: str, workspace_id: str) -> Dict[str, Any]:
    """Delete a roadmap theme.

    Args:
        theme_id: UUID of the theme to delete
        workspace_id: UUID of the workspace (for verification)

    Returns:
        Confirmation of deletion

    Example:
        >>> await delete_roadmap_theme(
        ...     "423e4567-e89b-12d3-a456-426614174003",
        ...     "123e4567-e89b-12d3-a456-426614174000"
        ... )
        {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme deleted successfully"
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Deleting theme {theme_id}")

        user_id = get_user_id_from_request()

        product_strategy_controller.delete_roadmap_theme(
            theme_id=uuid.UUID(theme_id),
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            session=session,
        )

        return {
            "status": "success",
            "type": "theme",
            "message": "Roadmap theme deleted successfully",
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "theme",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "theme",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error deleting theme: {e}")
        return {
            "status": "error",
            "type": "theme",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()
