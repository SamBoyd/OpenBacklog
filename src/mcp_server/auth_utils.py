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
