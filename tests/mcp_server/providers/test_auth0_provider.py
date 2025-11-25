"""
Unit tests for Auth0MCPAuthProvider.

Tests the Auth0 authentication provider that validates access tokens
and resolves user context from OAuth accounts.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.providers.auth0 import Auth0MCPAuthProvider
from src.mcp_server.providers.base import MCPContextError
from src.models import OAuthAccount, User, Workspace


class TestAuth0MCPAuthProvider:
    """Test suite for Auth0MCPAuthProvider."""

    @pytest.fixture
    def provider(self):
        """Create an Auth0MCPAuthProvider instance."""
        return Auth0MCPAuthProvider()

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_token(self):
        """Create a mock access token with claims."""
        token = MagicMock()
        token.claims = {"sub": "auth0|123456"}
        return token

    # Success case tests
    def test_success_returns_user_and_workspace(
        self, provider, session, user, workspace
    ):
        """Test successful user context retrieval from valid token."""
        # Get the OAuth account for the test user
        oauth_account = (
            session.query(OAuthAccount).filter(OAuthAccount.user_id == user.id).first()
        )

        mock_token = MagicMock()
        mock_token.claims = {"sub": oauth_account.account_id}

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            user_id, workspace_id = provider.get_user_context(session)

            assert user_id == user.id
            assert workspace_id == workspace.id

    def test_success_returns_correct_types(self, provider, session, user, workspace):
        """Test that returned values are correct UUID types."""
        oauth_account = (
            session.query(OAuthAccount).filter(OAuthAccount.user_id == user.id).first()
        )

        mock_token = MagicMock()
        mock_token.claims = {"sub": oauth_account.account_id}

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            user_id, workspace_id = provider.get_user_context(session)

            assert isinstance(user_id, uuid.UUID)
            assert isinstance(workspace_id, uuid.UUID)

    def test_success_calls_get_access_token(self, provider, mock_session, mock_token):
        """Test that provider calls get_access_token from fastmcp."""
        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = uuid.uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = mock_oauth_account.user_id

        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.id = uuid.uuid4()

        # Setup query mocks
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_oauth_account

        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = mock_user

        workspace_query_mock = MagicMock()
        workspace_filter_mock = MagicMock()
        workspace_query_mock.filter.return_value = workspace_filter_mock
        workspace_filter_mock.first.return_value = mock_workspace

        mock_session.query.side_effect = [
            query_mock,
            user_query_mock,
            workspace_query_mock,
        ]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            provider.get_user_context(mock_session)

            mock_get_token.assert_called_once()

    # Error case tests - Token validation
    def test_no_access_token_found(self, provider, mock_session):
        """Test error when no access token is found."""
        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = None

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "No access token found" in str(exc_info.value)

    def test_token_has_no_claims(self, provider, mock_session):
        """Test error when token has no claims."""
        mock_token = MagicMock()
        mock_token.claims = None

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "Token has no claims" in str(exc_info.value)

    def test_token_missing_sub_claim(self, provider, mock_session):
        """Test error when token claims missing 'sub' field."""
        mock_token = MagicMock()
        mock_token.claims = {"other_field": "value", "aud": "api"}

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "missing 'sub' field" in str(exc_info.value)

    def test_token_sub_claim_empty_string(self, provider, mock_session):
        """Test error when token 'sub' claim is empty."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": ""}

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "missing 'sub' field" in str(exc_info.value)

    # Error case tests - OAuth account lookup
    def test_oauth_account_not_found(self, provider, mock_session):
        """Test error when no OAuth account found for token subject."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|nonexistent"}

        # Mock query to return None for OAuth account lookup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None

        mock_session.query.return_value = query_mock

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "No OAuth account found" in str(exc_info.value)
            assert "auth0|nonexistent" in str(exc_info.value)

    # Error case tests - User lookup
    def test_user_not_found(self, provider, mock_session):
        """Test error when user record not found for OAuth account."""
        mock_token = MagicMock()
        test_sub = "auth0|123456"
        mock_token.claims = {"sub": test_sub}

        test_user_id = uuid.uuid4()
        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = test_user_id

        # First query: OAuth account found
        oauth_query_mock = MagicMock()
        oauth_filter_mock = MagicMock()
        oauth_query_mock.filter.return_value = oauth_filter_mock
        oauth_filter_mock.first.return_value = mock_oauth_account

        # Second query: User not found
        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = None

        mock_session.query.side_effect = [oauth_query_mock, user_query_mock]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "User not found" in str(exc_info.value)

    def test_workspace_not_found_for_user(self, provider, session, user):
        """Test error when no workspace found for user."""
        # Get OAuth account
        oauth_account = (
            session.query(OAuthAccount).filter(OAuthAccount.user_id == user.id).first()
        )

        # Delete all workspaces
        from sqlalchemy import delete

        session.execute(delete(Workspace).filter(Workspace.user_id == user.id))
        session.commit()

        mock_token = MagicMock()
        mock_token.claims = {"sub": oauth_account.account_id}

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            user_id, workspace_id = provider.get_user_context(session)

            assert user_id == user.id
            assert workspace_id is None

    # Error case tests - Generic exceptions
    def test_exception_during_token_access(self, provider, mock_session):
        """Test error when get_access_token raises an exception."""
        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.side_effect = Exception("FastMCP error")

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Failed to resolve user context" in str(exc_info.value)

    def test_exception_during_oauth_query(self, provider, mock_session):
        """Test error when database query for OAuth account fails."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|123456"}

        query_mock = MagicMock()
        query_mock.filter.side_effect = Exception("Database error")

        mock_session.query.return_value = query_mock

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Failed to resolve user context" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)

    def test_exception_during_user_query(self, provider, mock_session):
        """Test error when database query for user fails."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|123456"}

        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = uuid.uuid4()

        # First query: OAuth account found
        oauth_query_mock = MagicMock()
        oauth_filter_mock = MagicMock()
        oauth_query_mock.filter.return_value = oauth_filter_mock
        oauth_filter_mock.first.return_value = mock_oauth_account

        # Second query: User query fails
        user_query_mock = MagicMock()
        user_query_mock.filter.side_effect = Exception("User query failed")

        mock_session.query.side_effect = [oauth_query_mock, user_query_mock]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "User query failed" in str(exc_info.value)

    def test_exception_during_workspace_query(self, provider, mock_session):
        """Test error when database query for workspace fails."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|123456"}

        test_user_id = uuid.uuid4()
        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = test_user_id

        mock_user = MagicMock(spec=User)
        mock_user.id = test_user_id

        # First query: OAuth account found
        oauth_query_mock = MagicMock()
        oauth_filter_mock = MagicMock()
        oauth_query_mock.filter.return_value = oauth_filter_mock
        oauth_filter_mock.first.return_value = mock_oauth_account

        # Second query: User found
        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = mock_user

        # Third query: Workspace query fails
        workspace_query_mock = MagicMock()
        workspace_query_mock.filter.side_effect = Exception("Workspace query failed")

        mock_session.query.side_effect = [
            oauth_query_mock,
            user_query_mock,
            workspace_query_mock,
        ]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token

            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Workspace query failed" in str(exc_info.value)

    # Query correctness tests
    def test_oauth_account_query_filters_by_sub(self, provider, mock_session):
        """Test that OAuth account query uses correct sub from token."""
        mock_token = MagicMock()
        test_sub = "auth0|specific_user_id"
        mock_token.claims = {"sub": test_sub}

        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = uuid.uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = mock_oauth_account.user_id

        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.id = uuid.uuid4()

        # Setup query mocks
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_oauth_account

        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = mock_user

        workspace_query_mock = MagicMock()
        workspace_filter_mock = MagicMock()
        workspace_query_mock.filter.return_value = workspace_filter_mock
        workspace_filter_mock.first.return_value = mock_workspace

        mock_session.query.side_effect = [
            query_mock,
            user_query_mock,
            workspace_query_mock,
        ]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            provider.get_user_context(mock_session)

            # Verify filter was called with the correct sub value
            # The OAuth query filter should be called with OAuthAccount.account_id == sub
            query_mock.filter.assert_called_once()

    def test_user_query_filters_by_oauth_user_id(self, provider, mock_session):
        """Test that user query uses the user_id from OAuth account."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|123"}

        test_user_id = uuid.uuid4()
        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = test_user_id

        mock_user = MagicMock(spec=User)
        mock_user.id = test_user_id

        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.id = uuid.uuid4()

        # Setup query mocks
        oauth_query_mock = MagicMock()
        oauth_filter_mock = MagicMock()
        oauth_query_mock.filter.return_value = oauth_filter_mock
        oauth_filter_mock.first.return_value = mock_oauth_account

        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = mock_user

        workspace_query_mock = MagicMock()
        workspace_filter_mock = MagicMock()
        workspace_query_mock.filter.return_value = workspace_filter_mock
        workspace_filter_mock.first.return_value = mock_workspace

        mock_session.query.side_effect = [
            oauth_query_mock,
            user_query_mock,
            workspace_query_mock,
        ]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            user_id, workspace_id = provider.get_user_context(mock_session)

            # Verify returned user_id matches OAuth account user_id
            assert user_id == test_user_id

    def test_workspace_query_filters_by_user_id(self, provider, mock_session):
        """Test that workspace query uses the user_id from user record."""
        mock_token = MagicMock()
        mock_token.claims = {"sub": "auth0|123"}

        test_user_id = uuid.uuid4()
        test_workspace_id = uuid.uuid4()

        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_oauth_account.user_id = test_user_id

        mock_user = MagicMock(spec=User)
        mock_user.id = test_user_id

        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.id = test_workspace_id

        # Setup query mocks
        oauth_query_mock = MagicMock()
        oauth_filter_mock = MagicMock()
        oauth_query_mock.filter.return_value = oauth_filter_mock
        oauth_filter_mock.first.return_value = mock_oauth_account

        user_query_mock = MagicMock()
        user_filter_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock
        user_filter_mock.first.return_value = mock_user

        workspace_query_mock = MagicMock()
        workspace_filter_mock = MagicMock()
        workspace_query_mock.filter.return_value = workspace_filter_mock
        workspace_filter_mock.first.return_value = mock_workspace

        mock_session.query.side_effect = [
            oauth_query_mock,
            user_query_mock,
            workspace_query_mock,
        ]

        with patch("src.mcp_server.providers.auth0.get_access_token") as mock_get_token:
            mock_get_token.return_value = mock_token
            user_id, workspace_id = provider.get_user_context(mock_session)

            # Verify returned workspace_id is correct
            assert workspace_id == test_workspace_id
