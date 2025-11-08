"""Authentication utilities for prompt-driven tools.

Provides user identification and authentication helpers for MCP tools.
"""

import uuid
from typing import Optional

from src.db import SessionLocal
from src.mcp_server.auth_utils import (
    MCPContextError,
    get_auth_context,
    get_user_workspace,
)

__all__ = [
    "get_user_id_from_request",
    "get_workspace_id_from_user_id",
    "get_workspace_id_from_request",
]


def get_user_id_from_request() -> uuid.UUID:
    """Extract user ID from access token claims.

    OAuth authentication is handled by FastMCP's Auth0Provider.
    This function extracts the user_id from the validated access token claims.

    Returns:
        User UUID from access token

    Raises:
        ValueError: If token is missing or invalid
    """
    session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=False)
        return uuid.UUID(user_id_str)
    except MCPContextError as e:
        raise ValueError(str(e)) from e
    finally:
        session.close()


def get_workspace_id_from_user_id(user_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get workspace ID for a given user ID.

    Users can only have a single workspace, so this returns the first
    (and only) workspace for the user.

    Args:
        user_id: User UUID

    Returns:
        Workspace UUID if found, None otherwise
    """
    session = SessionLocal()
    try:
        workspace, _ = get_user_workspace(session, user_id)
        if workspace is None:
            return None
        return workspace.id
    finally:
        session.close()


def get_workspace_id_from_request() -> uuid.UUID:
    """Extract workspace ID from authenticated user in request.

    Convenience function that extracts user_id from access token and looks up
    their workspace. Raises error if user has no workspace.

    Returns:
        Workspace UUID for the authenticated user

    Raises:
        ValueError: If user not authenticated or has no workspace
    """
    session = SessionLocal()
    try:
        _, workspace_id_str = get_auth_context(session, requires_workspace=True)
        if not workspace_id_str:
            raise MCPContextError(
                "User has no workspace. Please create a workspace first.",
                error_type="workspace_error",
            )
        return uuid.UUID(workspace_id_str)
    except MCPContextError as e:
        raise ValueError(str(e)) from e
    finally:
        session.close()
