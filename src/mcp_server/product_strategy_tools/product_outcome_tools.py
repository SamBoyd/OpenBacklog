"""MCP tools for product strategy operations.

This module provides MCP tools for managing product strategy entities:
- Product Outcomes (measurable objectives)

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
    serialize_outcome,
)
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Product Outcome Tools
# ============================================================================


@mcp.tool()
async def create_product_outcome(
    workspace_id: str,
    name: str,
    description: Optional[str] = None,
    metrics: Optional[str] = None,
    time_horizon_months: Optional[int] = None,
    pillar_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new product outcome for a workspace.

    Args:
        workspace_id: UUID of the workspace
        name: Outcome name (1-150 characters, unique per workspace)
        description: Optional outcome description (max 1500 characters)
        metrics: How to measure this outcome (max 1000 characters)
        time_horizon_months: Time horizon in months (6-36)
        pillar_ids: List of pillar UUIDs to link to this outcome

    Returns:
        Created outcome data

    Example:
        >>> await create_product_outcome(
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "80% of users use AI weekly",
        ...     "Measure AI adoption",
        ...     "% of weekly active users who use AI features",
        ...     12,
        ...     ["223e4567-e89b-12d3-a456-426614174001"]
        ... )
        {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome created successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Creating outcome '{name}' for workspace {workspace_id}")

        user_id = get_user_id_from_request()

        # Convert pillar_ids from strings to UUIDs
        pillar_uuids = []
        if pillar_ids:
            pillar_uuids = [uuid.UUID(pid) for pid in pillar_ids]

        outcome = product_strategy_controller.create_product_outcome(
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            pillar_ids=pillar_uuids,
            session=session,
        )

        return {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome created successfully",
            "data": serialize_outcome(outcome),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error creating outcome: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def update_product_outcome(
    outcome_id: str,
    workspace_id: str,
    name: str,
    description: Optional[str] = None,
    metrics: Optional[str] = None,
    time_horizon_months: Optional[int] = None,
    pillar_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update an existing product outcome.

    Args:
        outcome_id: UUID of the outcome to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated outcome name (1-150 characters, unique per workspace)
        description: Updated outcome description (max 1500 characters)
        metrics: Updated outcome metrics (max 1000 characters)
        time_horizon_months: Updated time horizon (6-36 months)
        pillar_ids: List of pillar UUIDs to link to this outcome

    Returns:
        Updated outcome data

    Example:
        >>> await update_product_outcome(
        ...     "323e4567-e89b-12d3-a456-426614174002",
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "Updated outcome name",
        ...     "Updated description",
        ...     "Updated metrics",
        ...     18,
        ...     ["223e4567-e89b-12d3-a456-426614174001"]
        ... )
        {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome updated successfully",
            "data": {...}
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Updating outcome {outcome_id}")

        # Convert pillar_ids from strings to UUIDs
        pillar_uuids = []
        if pillar_ids:
            pillar_uuids = [uuid.UUID(pid) for pid in pillar_ids]

        outcome = product_strategy_controller.update_product_outcome(
            outcome_id=uuid.UUID(outcome_id),
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            pillar_ids=pillar_uuids,
            session=session,
        )

        return {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome updated successfully",
            "data": serialize_outcome(outcome),
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "outcome",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "outcome",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error updating outcome: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()


@mcp.tool()
async def delete_product_outcome(outcome_id: str, workspace_id: str) -> Dict[str, Any]:
    """Delete a product outcome.

    Args:
        outcome_id: UUID of the outcome to delete
        workspace_id: UUID of the workspace (for verification)

    Returns:
        Confirmation of deletion

    Example:
        >>> await delete_product_outcome(
        ...     "323e4567-e89b-12d3-a456-426614174002",
        ...     "123e4567-e89b-12d3-a456-426614174000"
        ... )
        {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome deleted successfully"
        }
    """
    session = SessionLocal()
    try:
        logger.info(f"Deleting outcome {outcome_id}")

        user_id = get_user_id_from_request()

        product_strategy_controller.delete_product_outcome(
            outcome_id=uuid.UUID(outcome_id),
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            session=session,
        )

        return {
            "status": "success",
            "type": "outcome",
            "message": "Product outcome deleted successfully",
        }

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        if "not found" in str(e).lower():
            return {
                "status": "error",
                "type": "outcome",
                "error_message": str(e),
                "error_type": "not_found",
            }
        return {
            "status": "error",
            "type": "outcome",
            "error_message": str(e),
        }
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Invalid UUID format: {str(e)}",
        }
    except Exception as e:
        logger.exception(f"Error deleting outcome: {e}")
        return {
            "status": "error",
            "type": "outcome",
            "error_message": f"Server error: {str(e)}",
        }
    finally:
        session.close()
