"""
Development MCP authentication provider.

Returns the configured dev user for all requests without token validation.
Used for local development and multi-cluster testing where each cluster
runs independently with its own dev user.
"""

import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.config import settings
from src.mcp_server.providers.base import MCPAuthProvider, MCPContextError
from src.models import User, Workspace

logger = logging.getLogger(__name__)


class DevMCPAuthProvider(MCPAuthProvider):
    """Development MCP auth provider that returns the dev user for all requests."""

    def get_user_context(
        self, session: Session
    ) -> Tuple[uuid.UUID, Optional[uuid.UUID]]:
        """
        Get dev user context without token validation.

        For development, this returns the configured dev user and their
        first workspace. No authentication is performed.

        Args:
            session: SQLAlchemy database session

        Returns:
            Tuple of (user_id, workspace_id)

        Raises:
            MCPContextError: If dev user or workspace cannot be found
        """
        try:
            # Find the dev user by email
            user = (
                session.query(User)
                .filter(User.email == settings.dev_user_email)
                .first()
            )

            if not user:
                error_msg = (
                    f"Dev user not found for email: {settings.dev_user_email}. "
                    f"Did you initialize the database with dev fixtures?"
                )
                logger.error(error_msg)
                raise MCPContextError(error_msg, error_type="auth_error")

            # Find the user's first workspace
            workspace = (
                session.query(Workspace).filter(Workspace.user_id == user.id).first()
            )

            if not workspace:
                error_msg = (
                    f"No workspace found for dev user {user.email}. "
                    f"Create a workspace first."
                )
                logger.error(error_msg)
                raise MCPContextError(error_msg, error_type="workspace_error")

            logger.debug(
                f"Dev auth context resolved: user={user.id}, workspace={workspace.id}"
            )

            return user.id, workspace.id

        except MCPContextError:
            raise
        except Exception as e:
            logger.exception(f"Error resolving dev user context: {str(e)}")
            raise MCPContextError(
                f"Failed to resolve dev user context: {str(e)}",
                error_type="server_error",
            )
