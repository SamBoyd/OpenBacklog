"""
Utility functions for MCP server authentication and authorization.
"""

import logging
import uuid
from typing import Optional, Tuple

from fastmcp.server.dependencies import get_access_token
from sqlalchemy.orm import Session

from src.models import OAuthAccount, User, Workspace

logger = logging.getLogger(__name__)


class MCPContextError(RuntimeError):
    """
    Raised when MCP tool context (user/workspace) resolution fails.

    Attributes:
        error_type: String identifier describing the error category.
    """

    def __init__(self, message: str, *, error_type: str = "context_error") -> None:
        super().__init__(message)
        self.error_type = error_type


def extract_user_from_request(
    session: Session,
) -> Tuple[Optional[uuid.UUID], Optional[str]]:
    """
    Extract and validate user ID from the access token claims.

    Args:
        session: SQLAlchemy database session

    Returns:
        Tuple of (user_id, error_message)
        - If successful: (uuid.UUID, None)
        - If error: (None, error_message)
    """
    try:
        token = get_access_token()
        if not token:
            return None, "No access token found"

        claims = token.claims
        if not claims:
            return None, "Token has no claims"

        sub = claims.get("sub")
        if not sub:
            return None, "Token claims missing 'sub' field"

        oauth_account = (
            session.query(OAuthAccount).filter(OAuthAccount.account_id == sub).first()
        )
        if not oauth_account:
            return None, f"No OAuth account found for sub: {sub}"

        user_id = oauth_account.user_id

        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"

        return user_id, None

    except Exception as e:
        logger.exception(f"Error extracting user from request: {str(e)}")
        return None, f"Authentication error: {str(e)}"


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


def get_auth_context(
    session: Session,
    requires_workspace: bool = False,
) -> Tuple[str, Optional[str]]:
    """
    Consolidated helper to fetch authenticated user and optional workspace context.

    Args:
        session: SQLAlchemy database session.
        requires_workspace: Whether a workspace is required for the caller.

    Returns:
        Tuple containing user_id and optional workspace_id as strings.

    Raises:
        MCPContextError: If the user or required workspace cannot be resolved.
    """
    user_id, error_message = extract_user_from_request(session)
    if error_message or user_id is None:
        message = error_message or "Authentication required."
        logger.warning(f"Authentication failed in get_auth_context: {message}")
        raise MCPContextError(message, error_type="auth_error")

    workspace_id: Optional[str] = None
    if requires_workspace:
        workspace, workspace_error = get_user_workspace(session, user_id)
        if workspace_error or workspace is None:
            message = workspace_error or "Workspace not found."
            logger.warning(f"Workspace lookup failed in get_auth_context: {message}")
            raise MCPContextError(message, error_type="workspace_error")
        workspace_id = str(workspace.id)
    else:
        workspace, workspace_error = get_user_workspace(session, user_id)
        if workspace:
            workspace_id = str(workspace.id)
        elif workspace_error:
            logger.info(
                f"Workspace lookup returned error without requiring workspace: {workspace_error}"
            )

    return str(user_id), workspace_id
