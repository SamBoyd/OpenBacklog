"""
Utility functions for MCP server authentication and authorization.
"""

import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.mcp_server.providers.base import MCPAuthProvider, MCPContextError
from src.models import User, Workspace

logger = logging.getLogger(__name__)


def get_auth_context(
    session: Session,
    requires_workspace: bool = False,
) -> Tuple[str, Optional[str]]:
    """
    Consolidated helper to fetch authenticated user and optional workspace context.

    Uses the MCP auth provider configured by the MCPAuthFactory to extract user context
    based on the current authentication mode (dev, auth0, or test).

    Args:
        session: SQLAlchemy database session.
        requires_workspace: Whether a workspace is required for the caller.

    Returns:
        Tuple containing user_id and optional workspace_id as strings.

    Raises:
        MCPContextError: If the user or required workspace cannot be resolved.
    """
    from src.mcp_server.auth_factory import get_mcp_auth_factory

    factory = get_mcp_auth_factory()
    mcp_auth_context_provider = factory.get_mcp_auth_context_provider()

    if mcp_auth_context_provider is None:
        raise MCPContextError(
            "MCP auth provider not configured",
            error_type="server_error",
        )

    try:
        user_id, workspace_id = mcp_auth_context_provider.get_user_context(session)

        if requires_workspace and workspace_id is None:
            raise MCPContextError(
                "Workspace required but not found",
                error_type="workspace_error",
            )

        return str(user_id), str(workspace_id) if workspace_id else None

    except MCPContextError:
        raise
    except Exception as e:
        logger.exception(f"Error getting auth context: {str(e)}")
        raise MCPContextError(
            f"Failed to get auth context: {str(e)}",
            error_type="server_error",
        )


def get_user_workspace(
    session: Session, user_id: uuid.UUID
) -> Tuple[Optional[Workspace], Optional[str]]:
    """
    Get the workspace for a user.

    Args:
        session: SQLAlchemy database session
        user_id: User UUID

    Returns:
        Tuple of (workspace, error_message)
        - If successful: (Workspace, None)
        - If error: (None, error_message)
    """
    try:
        workspace = (
            session.query(Workspace).filter(Workspace.user_id == user_id).first()
        )
        if not workspace:
            return None, "No workspace found. Please create a workspace first."

        return workspace, None

    except Exception as e:
        logger.exception(f"Error fetching workspace: {str(e)}")
        return None, f"Error fetching workspace: {str(e)}"
