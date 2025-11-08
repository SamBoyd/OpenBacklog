"""
Unit tests for MCP server authentication utilities.

Tests the get_auth_context function which handles user authentication
and workspace resolution for MCP tools.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.models import OAuthAccount, User, Workspace


class TestGetAuthContext:
    """Test suite for get_auth_context function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def test_user_id(self):
        """Generate a test user UUID."""
        return uuid.uuid4()

    @pytest.fixture
    def test_workspace_id(self):
        """Generate a test workspace UUID."""
        return uuid.uuid4()

    @pytest.fixture
    def mock_oauth_account(self, test_user_id):
        """Create a mock OAuth account."""
        account = MagicMock(spec=OAuthAccount)
        account.account_id = "auth0|test123"
        account.user_id = test_user_id
        return account

    @pytest.fixture
    def mock_user(self, test_user_id):
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = test_user_id
        return user

    @pytest.fixture
    def mock_workspace(self, test_workspace_id, test_user_id):
        """Create a mock workspace."""
        workspace = MagicMock(spec=Workspace)
        workspace.id = test_workspace_id
        workspace.user_id = test_user_id
        return workspace

    def test_success_with_workspace(
        self,
        mock_session,
        mock_oauth_account,
        mock_user,
        mock_workspace,
        test_user_id,
        test_workspace_id,
    ):
        """Test successful auth context retrieval with workspace."""
        # Mock get_access_token to return valid token
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            # Mock database queries
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_oauth_account,  # First query for OAuthAccount
                mock_user,  # Second query for User
                mock_workspace,  # Third query for Workspace
            ]

            # Call get_auth_context
            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=True
            )

            # Verify results
            assert user_id == str(test_user_id)
            assert workspace_id == str(test_workspace_id)

    def test_success_without_workspace_required(
        self,
        mock_session,
        mock_oauth_account,
        mock_user,
        mock_workspace,
        test_user_id,
        test_workspace_id,
    ):
        """Test successful auth with workspace found but not required."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_oauth_account,  # OAuthAccount
                mock_user,  # User
                mock_workspace,  # Workspace (optional)
            ]

            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=False
            )

            assert user_id == str(test_user_id)
            assert workspace_id == str(test_workspace_id)

    def test_success_without_workspace_found(
        self,
        mock_session,
        mock_oauth_account,
        mock_user,
        test_user_id,
    ):
        """Test successful auth when workspace not found and not required."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_oauth_account,  # OAuthAccount
                mock_user,  # User
                None,  # Workspace not found
            ]

            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=False
            )

            assert user_id == str(test_user_id)
            assert workspace_id is None

    def test_no_access_token(self, mock_session):
        """Test error when no access token is present."""
        with patch("src.mcp_server.auth_utils.get_access_token", return_value=None):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "No access token found" in str(exc_info.value)

    def test_token_missing_claims(self, mock_session):
        """Test error when token has no claims."""
        mock_token = MagicMock()
        mock_token.claims = None

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "Token has no claims" in str(exc_info.value)

    def test_token_missing_sub_claim(self, mock_session):
        """Test error when token claims don't include 'sub'."""
        mock_token = MagicMock()
        mock_token.claims = {"other": "value"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "missing 'sub' field" in str(exc_info.value)

    def test_oauth_account_not_found(self, mock_session):
        """Test error when OAuth account doesn't exist for sub."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|nonexistent"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.return_value.filter.return_value.first.return_value = (
                None
            )

            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "No OAuth account found" in str(exc_info.value)

    def test_user_not_found(self, mock_session, mock_oauth_account):
        """Test error when user doesn't exist for OAuth account."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_oauth_account,  # OAuthAccount found
                None,  # User not found
            ]

            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "User not found" in str(exc_info.value)

    def test_workspace_required_but_not_found(
        self,
        mock_session,
        mock_oauth_account,
        mock_user,
    ):
        """Test error when workspace is required but doesn't exist."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_oauth_account,  # OAuthAccount
                mock_user,  # User
                None,  # Workspace not found
            ]

            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session, requires_workspace=True)

            assert exc_info.value.error_type == "workspace_error"
            assert "No workspace found" in str(exc_info.value)

    def test_database_error_during_user_extraction(self, mock_session):
        """Test error handling when database query fails."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            mock_session.query.side_effect = Exception("Database connection failed")

            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "Authentication error" in str(exc_info.value)

    def test_database_error_during_workspace_lookup(
        self,
        mock_session,
        mock_oauth_account,
        mock_user,
    ):
        """Test error handling when workspace query fails."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|test123"}

        with patch(
            "src.mcp_server.auth_utils.get_access_token", return_value=mock_token
        ):
            # First two queries succeed, third fails
            mock_query = MagicMock()
            mock_filter = MagicMock()

            def query_side_effect(model):
                if model == Workspace:
                    raise Exception("Workspace query failed")
                return mock_query

            mock_session.query.side_effect = query_side_effect
            mock_query.filter.return_value = mock_filter
            mock_filter.first.side_effect = [
                mock_oauth_account,  # OAuthAccount
                mock_user,  # User
            ]

            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session, requires_workspace=True)

            assert exc_info.value.error_type == "workspace_error"
            assert "Error fetching workspace" in str(exc_info.value)
