from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from src.mcp_server.healthcheck_tool import health_check


class TestHealthCheck:
    """Test suite for health_check MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock()
        request.headers = {
            "Authorization": "Bearer valid_token",
        }
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock()
        request.headers = {}
        return request

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.healthcheck_tool.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_health_check_successful_api_response(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful health check with valid API response."""
        mock_response = Mock()
        mock_response.status_code = 200

        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.requests.get") as mock_get,
            patch("src.mcp_server.healthcheck_tool.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await health_check.fn()

            # Verify the result
            assert result["status"] == "success"
            assert result["type"] == "health_check"
            assert (
                result["message"]
                == "MCP server OAuth authentication and PostgREST connectivity verified"
            )
            assert result["api_endpoint"] == "https://api.test.com"

            # Verify API call was made correctly
            expected_url = "https://api.test.com/initiative?limit=1"
            mock_get.assert_called_once_with(
                expected_url,
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

            # Verify logging
            mock_logger.info.assert_any_call("Performing health check")
            mock_logger.info.assert_any_call(
                "Health check successful - OAuth and PostgREST connectivity verified"
            )

    @pytest.mark.asyncio
    async def test_health_check_api_error_response(
        self, mock_request_with_auth, mock_settings
    ):
        """Test health check with API error response."""
        mock_response = Mock()
        mock_response.status_code = 401

        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.requests.get") as mock_get,
            patch("src.mcp_server.healthcheck_tool.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await health_check.fn()

            # Verify the result
            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "api_error"
            assert result["error_message"] == "PostgREST API returned status 401"

            # Verify logging
            mock_logger.warning.assert_called_once_with(
                "Health check failed with PostgREST status 401"
            )

    @pytest.mark.asyncio
    async def test_health_check_api_500_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test health check with API 500 error response."""
        mock_response = Mock()
        mock_response.status_code = 500

        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.requests.get") as mock_get,
            patch("src.mcp_server.healthcheck_tool.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await health_check.fn()

            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "api_error"
            assert result["error_message"] == "PostgREST API returned status 500"

    @pytest.mark.asyncio
    async def test_health_check_requests_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test health check with requests exception."""
        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.requests.get") as mock_get,
            patch("src.mcp_server.healthcheck_tool.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = Exception("Connection timeout")

            result = await health_check.fn()

            # Verify the result
            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "server_error"
            assert "Health check failed: Connection timeout" in result["error_message"]

            # Verify logging
            mock_logger.exception.assert_called_once_with(
                "Health check failed with exception: Connection timeout"
            )

    @pytest.mark.asyncio
    async def test_health_check_get_http_request_exception(self, mock_settings):
        """Test health check when get_http_request raises exception."""
        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.logger") as mock_logger,
        ):

            mock_get_request.side_effect = Exception("Request context error")

            result = await health_check.fn()

            # Verify the result
            assert result["status"] == "error"
            assert result["type"] == "health_check"
            assert result["error_type"] == "server_error"
            assert (
                "Health check failed: Request context error" in result["error_message"]
            )

            # Verify logging
            mock_logger.exception.assert_called_once_with(
                "Health check failed with exception: Request context error"
            )

    @pytest.mark.asyncio
    async def test_health_check_headers_passed_correctly(
        self, mock_request_with_auth, mock_settings
    ):
        """Test that headers are passed correctly to the API request."""
        mock_response = Mock()
        mock_response.status_code = 200

        # Test with different token
        mock_request_with_auth.headers["Authorization"] = "Bearer custom-token-xyz"

        with (
            patch(
                "src.mcp_server.healthcheck_tool.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.healthcheck_tool.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            await health_check.fn()

            # Verify headers
            mock_get.assert_called_once_with(
                "https://api.test.com/initiative?limit=1",
                headers={
                    "Authorization": "Bearer custom-token-xyz",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
