from unittest.mock import Mock, patch

import pytest

from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.healthcheck_tool import health_check
from src.models import User, Workspace


class TestHealthCheck:
    """Test suite for health_check MCP tool."""

    @pytest.mark.asyncio
    async def test_health_check_successful(
        self, user: User, workspace: Workspace, session
    ):
        """Test successful health check."""
        with patch(
            "src.mcp_server.healthcheck_tool.SessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value = session

            result = await health_check.fn()

            # Verify the result
            assert result["status"] == "success"
            assert result["type"] == "health_check"
            assert (
                result["message"]
                == "MCP server authentication and database connectivity verified"
            )
            assert result["user_id"] == str(user.id)
            assert result["workspace_id"] == str(workspace.id)
            assert result["workspace_name"] == workspace.name

    @pytest.mark.asyncio
    async def test_health_check_workspace_not_found(self, user: User, session):
        """Test health check when workspace is not found."""
        # Mock get_auth_context to return None for workspace
        with (
            patch("src.mcp_server.healthcheck_tool.SessionLocal") as mock_session_local,
            patch("src.mcp_server.healthcheck_tool.get_auth_context") as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), None)

            result = await health_check.fn()

            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "workspace_error"

    @pytest.mark.asyncio
    async def test_health_check_database_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test health check with database query error."""
        with (
            patch("src.mcp_server.healthcheck_tool.SessionLocal") as mock_session_local,
        ):
            mock_session_local.return_value = session

            # Patch the session.query method to raise exception during count()
            with patch.object(session, "query") as mock_query:
                mock_chain = Mock()
                mock_chain.filter.return_value.limit.return_value.count.side_effect = (
                    Exception("Database query failed")
                )
                mock_query.return_value = mock_chain

                result = await health_check.fn()

                assert result["status"] == "error"
                assert result["type"] == "health_check"
                assert result["error_type"] == "database_error"
                assert "Database connectivity test failed" in result["error_message"]

    @pytest.mark.asyncio
    async def test_health_check_auth_error(self):
        """Test health check with authentication error."""
        with (
            patch("src.mcp_server.healthcheck_tool.SessionLocal") as mock_session_local,
            patch("src.mcp_server.healthcheck_tool.get_auth_context") as mock_auth,
        ):
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            mock_auth.side_effect = MCPContextError(
                "No access token found", error_type="auth_error"
            )

            result = await health_check.fn()

            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "auth_error"
            assert "No access token found" in result["error_message"]
