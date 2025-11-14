"""
Auth0 MCP authentication provider.

Validates access tokens from Auth0 and resolves user context.
Used in production environments where users authenticate via Auth0.
"""

import logging
import uuid
from typing import Optional, Tuple

from fastmcp.server.dependencies import get_access_token
from sqlalchemy.orm import Session

from src.mcp_server.providers.base import MCPAuthProvider, MCPContextError
from src.models import OAuthAccount, User, Workspace

logger = logging.getLogger(__name__)


class Auth0MCPAuthProvider(MCPAuthProvider):
    """Auth0 MCP auth provider that validates access tokens."""

    def get_user_context(
        self, session: Session
    ) -> Tuple[uuid.UUID, Optional[uuid.UUID]]:
        """
        Extract user and workspace context from Auth0 access token.

        Validates the token, extracts the subject (sub) claim, looks up
        the corresponding OAuthAccount and User, and returns their context.

        Args:
            session: SQLAlchemy database session

        Returns:
            Tuple of (user_id, workspace_id)

        Raises:
            MCPContextError: If token is invalid or user/workspace not found
        """
        try:
            # Get the access token from FastMCP request context
            token = get_access_token()
            if not token:
                raise MCPContextError("No access token found", error_type="auth_error")

            # Extract claims from token
            claims = token.claims
            if not claims:
                raise MCPContextError("Token has no claims", error_type="auth_error")

            # Extract subject (user identifier) from claims
            sub = claims.get("sub")
            if not sub:
                raise MCPContextError(
                    "Token claims missing 'sub' field", error_type="auth_error"
                )

            # Look up OAuthAccount by subject
            oauth_account = (
                session.query(OAuthAccount)
                .filter(OAuthAccount.account_id == sub)
                .first()
            )
            if not oauth_account:
                raise MCPContextError(
                    f"No OAuth account found for sub: {sub}",
                    error_type="auth_error",
                )

            # Get User from OAuthAccount
            user_id = oauth_account.user_id
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise MCPContextError("User not found", error_type="auth_error")

            # Get User's workspace
            workspace = (
                session.query(Workspace).filter(Workspace.user_id == user_id).first()
            )
            if not workspace:
                raise MCPContextError(
                    "No workspace found. Please create a workspace first.",
                    error_type="workspace_error",
                )

            logger.debug(
                f"Auth0 context resolved: user={user_id}, workspace={workspace.id}"
            )

            return user_id, workspace.id

        except MCPContextError:
            raise
        except Exception as e:
            logger.exception(f"Error resolving Auth0 user context: {str(e)}")
            raise MCPContextError(
                f"Failed to resolve user context: {str(e)}",
                error_type="server_error",
            )
