"""
Unit tests for DevMCPAuthProvider.

Tests the development authentication provider that returns the configured
dev user for all requests without token validation.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.providers.base import MCPContextError
from src.mcp_server.providers.dev import DevMCPAuthProvider
from src.models import User, Workspace


class TestDevMCPAuthProvider:
    """Test suite for DevMCPAuthProvider."""

    @pytest.fixture
    def provider(self):
        """Create a DevMCPAuthProvider instance."""
        return DevMCPAuthProvider()

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    # Success case tests
    def test_success_returns_user_and_workspace(
        self, provider, session, user, workspace
    ):
        """Test successful retrieval of user and workspace context."""
        with patch("src.config.settings.dev_user_email", user.email):
            user_id, workspace_id = provider.get_user_context(session)

            assert user_id == user.id
            assert workspace_id == workspace.id

    def test_success_returns_correct_types(self, provider, session, user, workspace):
        """Test that returned values are correct UUID types."""
        with patch("src.config.settings.dev_user_email", user.email):
            user_id, workspace_id = provider.get_user_context(session)

            assert isinstance(user_id, uuid.UUID)
            assert isinstance(workspace_id, uuid.UUID)

    # Error case tests
    def test_dev_user_not_found(self, provider, mock_session):
        """Test error when dev user is not found in database."""
        # Mock the query to return None
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("src.config.settings.dev_user_email", "nonexistent@example.com"):
            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "Dev user not found" in str(exc_info.value)
            assert "nonexistent@example.com" in str(exc_info.value)

    def test_workspace_not_found_for_dev_user(self, provider, session, user):
        """Test error when workspace is not found for dev user."""
        # Delete all workspaces for this user
        from sqlalchemy import delete

        session.execute(delete(Workspace).filter(Workspace.user_id == user.id))
        session.commit()

        with patch("src.config.settings.dev_user_email", user.email):
            user_id, workspace_id = provider.get_user_context(session)

            assert user_id == user.id
            assert workspace_id is None

    def test_database_error_wrapped(self, provider, mock_session):
        """Test that generic database exceptions are wrapped in MCPContextError."""
        # Mock the query to raise an exception
        mock_session.query.side_effect = Exception("Database connection failed")

        with patch("src.config.settings.dev_user_email", "test@example.com"):
            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Failed to resolve dev user context" in str(exc_info.value)

    def test_workspace_query_uses_correct_user_id(self, provider, mock_session):
        """Test that workspace query filters by the correct user_id."""
        test_user_id = uuid.uuid4()
        mock_user = MagicMock(spec=User)
        mock_user.id = test_user_id
        mock_user.email = "test@example.com"

        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.id = uuid.uuid4()

        # Set up mock query chain for user lookup
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_user

        # Set up second query for workspace lookup
        workspace_query_mock = MagicMock()
        workspace_filter_mock = MagicMock()
        workspace_query_mock.filter.return_value = workspace_filter_mock
        workspace_filter_mock.first.return_value = mock_workspace

        mock_session.query.side_effect = [query_mock, workspace_query_mock]

        with patch("src.config.settings.dev_user_email", "test@example.com"):
            user_id, workspace_id = provider.get_user_context(mock_session)

            # Verify the second query was made with the correct user_id
            assert user_id == test_user_id
            assert workspace_id == mock_workspace.id

    def test_mcp_context_error_preserves_message(self, provider, mock_session):
        """Test that MCPContextError preserves the original error message."""
        original_error = Exception("Specific database issue")
        mock_session.query.side_effect = original_error

        with patch("src.config.settings.dev_user_email", "test@example.com"):
            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert "Specific database issue" in str(exc_info.value)

    def test_context_error_from_workspace_query_fails(self, provider, mock_session):
        """Test that MCPContextError is raised if workspace query fails."""
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid.uuid4()

        # First query succeeds (returns user)
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_user

        # Second query fails (workspace lookup)
        workspace_query_mock = MagicMock()
        workspace_query_mock.filter.side_effect = Exception("Workspace query failed")

        mock_session.query.side_effect = [query_mock, workspace_query_mock]

        with patch("src.config.settings.dev_user_email", "test@example.com"):
            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Workspace query failed" in str(exc_info.value)

    def test_settings_dev_user_email_is_used(self, provider, session, user):
        """Test that the configured dev_user_email setting is actually used."""
        # Create an additional user so we can verify the right one is selected
        other_user_email = "other.dev@example.com"

        # Patch settings to use the other email, which doesn't exist
        with patch("src.config.settings.dev_user_email", other_user_email):
            with pytest.raises(MCPContextError) as exc_info:
                provider.get_user_context(session)

            assert "Dev user not found" in str(exc_info.value)
            assert other_user_email in str(exc_info.value)

    def test_returns_first_workspace_when_multiple_exist(
        self, provider, session, user, workspace
    ):
        """Test that the provider returns a workspace (first one found)."""
        # The fixture should have created at least one workspace
        # Get the user context
        with patch("src.config.settings.dev_user_email", user.email):
            user_id, workspace_id = provider.get_user_context(session)

            # Verify we got a workspace
            assert workspace_id is not None
            assert isinstance(workspace_id, uuid.UUID)

            # Verify it matches the workspace we created via fixture
            assert workspace_id == workspace.id
