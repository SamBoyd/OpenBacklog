import json
import urllib.parse
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, is_
from starlette.requests import Request

from src.mcp_server.initiative_tools import (
    get_active_initiatives,
    get_initiative_details,
    search_initiatives,
)


class TestGetActiveInitiatives:
    """Test suite for get_active_initiatives MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {
            "Authorization": "Bearer valid_token",
            "X-Workspace-Id": "workspace-123",
        }
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {"X-Workspace-Id": "workspace-123"}
        return request

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.initiative_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_initiatives_data(self):
        """Sample initiative data for testing."""
        return [
            {
                "id": str(uuid.uuid4()),
                "title": "Initiative 1",
                "description": "Description 1",
                "status": "IN_PROGRESS",
                "identifier": "INIT-001",
                "workspace_id": "workspace-123",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Initiative 2",
                "description": "Description 2",
                "status": "IN_PROGRESS",
                "identifier": "INIT-002",
                "workspace_id": "workspace-123",
            },
        ]

    @pytest.mark.asyncio
    async def test_get_active_initiatives_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test get_active_initiatives with missing authorization header."""
        with patch(
            "src.mcp_server.initiative_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await get_active_initiatives.fn()

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_successful_retrieval(
        self, mock_request_with_auth, sample_initiatives_data, mock_settings
    ):
        """Test successful retrieval of active initiatives."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_initiatives_data

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_active_initiatives.fn()

            # Verify correct URL construction
            expected_url = "https://api.test.com/initiative?status=eq.IN_PROGRESS&workspace_id=eq.workspace-123&select=*"
            mock_get.assert_called_once_with(
                expected_url,
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative",
                        "message": "Found 2 active initiatives",
                        "data": sample_initiatives_data,
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_active_initiatives.fn()

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = Exception("Connection timeout")

            result = await get_active_initiatives.fn()

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_empty_response(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of empty initiative list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_active_initiatives.fn()

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative",
                        "message": "Found 0 active initiatives",
                        "data": [],
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_missing_workspace_id(self, mock_settings):
        """Test handling when workspace ID is missing from headers."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}

        with patch(
            "src.mcp_server.initiative_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = request

            result = await get_active_initiatives.fn()

            # Should still make request but with workspace_id=eq.None
            assert_that(result["status"], equal_to("error"))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    async def test_get_active_initiatives_client_errors(
        self, mock_request_with_auth, mock_settings, status_code
    ):
        """Test handling of various client error status codes."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {"error": f"Client error {status_code}"}

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_active_initiatives.fn()

            assert_that(
                result,
                has_entries(
                    {"status": "error", "error_message": f"Server error: {status_code}"}
                ),
            )


class TestSearchInitiatives:
    """Test suite for search_initiatives MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {
            "Authorization": "Bearer valid_token",
            "X-Workspace-Id": "workspace-123",
        }
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {"X-Workspace-Id": "workspace-123"}
        return request

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.initiative_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "id": "initiative-1",
                "title": "Fix authentication system",
                "description": "Authentication is not working correctly",
                "identifier": "AUTH-123",
            },
            {
                "id": "initiative-2",
                "title": "Add user authentication",
                "description": "Implement OAuth authentication",
                "identifier": "AUTH-124",
            },
        ]

    @pytest.mark.asyncio
    async def test_search_initiatives_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test search_initiatives with missing authorization header."""
        with patch(
            "src.mcp_server.initiative_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await search_initiatives.fn("authentication")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_successful_search(
        self, mock_request_with_auth, sample_search_results, mock_settings
    ):
        """Test successful initiative search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_results

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = "authentication"

            result = await search_initiatives.fn("authentication")

            # Verify URL encoding was called
            mock_quote.assert_called_once_with("authentication")

            # Verify correct API call
            expected_url = "https://api.test.com/initiative?or(title.plfts(authentication),description.plfts(authentication),identifier.plfts(authentication))&workspace_id=eq.workspace-123"
            mock_get.assert_called_once_with(
                expected_url,
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative",
                        "data": sample_search_results,
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_with_special_characters(
        self, mock_request_with_auth, mock_settings
    ):
        """Test search with special characters that need URL encoding."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = "oauth%202.0"

            result = await search_initiatives.fn("oauth 2.0")

            # Verify URL encoding was called with special characters
            mock_quote.assert_called_once_with("oauth 2.0")

            # Verify encoded query was used in URL
            expected_url = "https://api.test.com/initiative?or(title.plfts(oauth%202.0),description.plfts(oauth%202.0),identifier.plfts(oauth%202.0))&workspace_id=eq.workspace-123"
            assert mock_get.call_args[0][0] == expected_url

    @pytest.mark.asyncio
    async def test_search_initiatives_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error during search."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await search_initiatives.fn("test")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = Exception("Connection timeout")

            result = await search_initiatives.fn("test")

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_empty_results(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of empty search results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await search_initiatives.fn("nonexistent")

            assert_that(
                result,
                has_entries({"status": "success", "type": "initiative", "data": []}),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_empty_query(
        self, mock_request_with_auth, mock_settings
    ):
        """Test search with empty query string."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = ""

            result = await search_initiatives.fn("")

            # Should still make the request even with empty query
            mock_quote.assert_called_once_with("")
            assert_that(result["status"], equal_to("success"))

    @pytest.mark.asyncio
    async def test_search_initiatives_missing_workspace_id(self, mock_settings):
        """Test handling when workspace ID is missing from headers."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = request
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = await search_initiatives.fn("test")

            # Should still work but workspace filter will be None
            expected_url = "https://api.test.com/initiative?or(title.plfts(test),description.plfts(test),identifier.plfts(test))&workspace_id=eq.None"
            assert mock_get.call_args[0][0] == expected_url

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query", ["test query", "special!@#$%", "unicode🚀test", "123456"]
    )
    async def test_search_initiatives_various_query_types(
        self, mock_request_with_auth, mock_settings, query
    ):
        """Test search with various types of query strings."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = f"encoded_{query}"

            result = await search_initiatives.fn(query)

            # Should URL encode the query
            mock_quote.assert_called_once_with(query)
            assert_that(result["status"], equal_to("success"))


class TestGetInitiativeDetails:
    """Test suite for get_initiative_details MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {
            "Authorization": "Bearer valid_token",
            "X-Workspace-Id": "workspace-123",
        }
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {"X-Workspace-Id": "workspace-123"}
        return request

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.initiative_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_initiative_data(self):
        """Sample initiative data for testing."""
        return {
            "id": "initiative-123",
            "title": "User Authentication System",
            "description": "Implement comprehensive user authentication",
            "status": "IN_PROGRESS",
            "identifier": "AUTH-001",
            "workspace_id": "workspace-123",
        }

    @pytest.fixture
    def sample_tasks_for_initiative(self):
        """Sample tasks data for testing."""
        return [
            {
                "id": "task-1",
                "title": "Implement OAuth login",
                "description": "Add OAuth 2.0 authentication",
                "status": "IN_PROGRESS",
                "identifier": "AUTH-001-T1",
                "initiative_id": "initiative-123",
            },
            {
                "id": "task-2",
                "title": "Add session management",
                "description": "Implement secure session handling",
                "status": "TO_DO",
                "identifier": "AUTH-001-T2",
                "initiative_id": "initiative-123",
            },
        ]

    @pytest.mark.asyncio
    async def test_get_initiative_details_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test get_initiative_details with missing authorization header."""
        with patch(
            "src.mcp_server.initiative_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await get_initiative_details.fn("initiative-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_successful_retrieval(
        self,
        mock_request_with_auth,
        sample_initiative_data,
        sample_tasks_for_initiative,
        mock_settings,
    ):
        """Test successful retrieval of initiative details with tasks."""
        # Mock initiative response
        mock_initiative_response = Mock()
        mock_initiative_response.status_code = 200
        mock_initiative_response.json.return_value = [sample_initiative_data]

        # Mock tasks response
        mock_tasks_response = Mock()
        mock_tasks_response.status_code = 200
        mock_tasks_response.json.return_value = sample_tasks_for_initiative

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            # First call returns initiative, second call returns tasks
            mock_get.side_effect = [mock_initiative_response, mock_tasks_response]

            result = await get_initiative_details.fn("initiative-123")

            # Verify initiative URL was called correctly
            assert mock_get.call_args_list[0][0][0] == (
                "https://api.test.com/initiative?id=eq.initiative-123&workspace_id=eq.workspace-123&select=*"
            )

            # Verify tasks URL was called correctly
            assert mock_get.call_args_list[1][0][0] == (
                "https://api.test.com/task?initiative_id=eq.initiative-123&workspace_id=eq.workspace-123&select=*&order=status,identifier"
            )

            # Verify successful result structure
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative_details",
                        "message": "Retrieved comprehensive initiative context for User Authentication System",
                        "initiative": sample_initiative_data,
                        "tasks": sample_tasks_for_initiative,
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_initiative_not_found(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling when initiative is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_initiative_details.fn("nonexistent-id")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Initiative nonexistent-id not found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_tasks_fetch_fails(
        self, mock_request_with_auth, sample_initiative_data, mock_settings
    ):
        """Test when initiative is found but tasks fetch fails gracefully."""
        # Mock initiative response (success)
        mock_initiative_response = Mock()
        mock_initiative_response.status_code = 200
        mock_initiative_response.json.return_value = [sample_initiative_data]

        # Mock tasks response (failure)
        mock_tasks_response = Mock()
        mock_tasks_response.status_code = 500

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [mock_initiative_response, mock_tasks_response]

            result = await get_initiative_details.fn("initiative-123")

            # Should still return initiative even if tasks fetch fails
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative_details",
                        "initiative": sample_initiative_data,
                        "tasks": [],  # Empty tasks list on failure
                    }
                ),
            )

            # Should log warning
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_initiative_details_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error during initiative fetch."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_initiative_details.fn("initiative-123")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Server error fetching initiative: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
            patch("src.mcp_server.initiative_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = Exception("Connection timeout")

            result = await get_initiative_details.fn("initiative-123")

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_empty_tasks(
        self, mock_request_with_auth, sample_initiative_data, mock_settings
    ):
        """Test handling of initiative with no tasks."""
        # Mock initiative response
        mock_initiative_response = Mock()
        mock_initiative_response.status_code = 200
        mock_initiative_response.json.return_value = [sample_initiative_data]

        # Mock empty tasks response
        mock_tasks_response = Mock()
        mock_tasks_response.status_code = 200
        mock_tasks_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.initiative_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.initiative_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [mock_initiative_response, mock_tasks_response]

            result = await get_initiative_details.fn("initiative-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative_details",
                        "initiative": sample_initiative_data,
                        "tasks": [],
                    }
                ),
            )
