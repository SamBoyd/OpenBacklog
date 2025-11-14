"""
Unit tests for MCP server authentication utilities.

Tests the get_auth_context function which handles user authentication
and workspace resolution for MCP tools using the configured MCP auth provider.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.auth_utils import (
    MCPContextError,
    get_auth_context,
    get_user_workspace,
)
from src.models import User, Workspace


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

    def test_success_with_workspace(
        self, mock_session, test_user_id, test_workspace_id
    ):
        """Test successful auth context retrieval with workspace."""
        # Mock provider that returns user and workspace
        mock_provider = MagicMock()
        mock_provider.get_user_context.return_value = (test_user_id, test_workspace_id)

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=True
            )

            assert user_id == str(test_user_id)
            assert workspace_id == str(test_workspace_id)
            mock_provider.get_user_context.assert_called_once_with(mock_session)

    def test_success_without_workspace_required(
        self, mock_session, test_user_id, test_workspace_id
    ):
        """Test successful auth with workspace found but not required."""
        mock_provider = MagicMock()
        mock_provider.get_user_context.return_value = (test_user_id, test_workspace_id)

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=False
            )

            assert user_id == str(test_user_id)
            assert workspace_id == str(test_workspace_id)

    def test_success_without_workspace_found(self, mock_session, test_user_id):
        """Test successful auth when workspace not found and not required."""
        mock_provider = MagicMock()
        mock_provider.get_user_context.return_value = (test_user_id, None)

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            user_id, workspace_id = get_auth_context(
                mock_session, requires_workspace=False
            )

            assert user_id == str(test_user_id)
            assert workspace_id is None

    def test_workspace_required_but_not_found(self, mock_session, test_user_id):
        """Test error when workspace is required but not found."""
        mock_provider = MagicMock()
        mock_provider.get_user_context.return_value = (test_user_id, None)

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session, requires_workspace=True)

            assert exc_info.value.error_type == "workspace_error"
            assert "Workspace required but not found" in str(exc_info.value)

    def test_provider_not_configured(self, mock_session):
        """Test error when provider is not configured."""
        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=None,
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "not configured" in str(exc_info.value)

    def test_provider_raises_context_error(self, mock_session):
        """Test that provider MCPContextError is propagated."""
        mock_provider = MagicMock()
        mock_provider.get_user_context.side_effect = MCPContextError(
            "Auth failed", error_type="auth_error"
        )

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "auth_error"
            assert "Auth failed" in str(exc_info.value)

    def test_provider_raises_generic_exception(self, mock_session):
        """Test error handling when provider raises generic exception."""
        mock_provider = MagicMock()
        mock_provider.get_user_context.side_effect = Exception("Database error")

        with patch(
            "src.mcp_server.auth_factory.MCPAuthFactory.get_mcp_auth_context_provider",
            return_value=mock_provider,
        ):
            with pytest.raises(MCPContextError) as exc_info:
                get_auth_context(mock_session)

            assert exc_info.value.error_type == "server_error"
            assert "Failed to get auth context" in str(exc_info.value)


class TestGetUserWorkspace:
    """Test suite for get_user_workspace helper function."""

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
    def mock_workspace(self, test_workspace_id, test_user_id):
        """Create a mock workspace."""
        workspace = MagicMock(spec=Workspace)
        workspace.id = test_workspace_id
        workspace.user_id = test_user_id
        return workspace

    def test_success(self, mock_session, test_user_id, mock_workspace):
        """Test successful workspace lookup."""
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_workspace
        )

        workspace, error = get_user_workspace(mock_session, test_user_id)

        assert workspace == mock_workspace
        assert error is None

    def test_workspace_not_found(self, mock_session, test_user_id):
        """Test when workspace is not found."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        workspace, error = get_user_workspace(mock_session, test_user_id)

        assert workspace is None
        assert "No workspace found" in error

    def test_database_error(self, mock_session, test_user_id):
        """Test error handling when database query fails."""
        mock_session.query.side_effect = Exception("Database connection failed")

        workspace, error = get_user_workspace(mock_session, test_user_id)

        assert workspace is None
        assert "Error fetching workspace" in error
