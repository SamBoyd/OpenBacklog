import json
import urllib.parse
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, is_
from starlette.requests import Request

from src.mcp_server.task_tools import (
    _generate_task_context,
    get_initiative_tasks,
    get_task_details,
    search_tasks,
    update_task_description,
    update_task_status_done,
    update_task_status_inprogress,
    validate_context,
)


class TestGetInitiativeTasks:
    """Test suite for get_initiative_tasks MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_tasks_data(self):
        """Sample task data for testing."""
        return [
            {
                "id": str(uuid.uuid4()),
                "title": "Task 1",
                "description": "Description 1",
                "status": "TODO",
                "initiative_id": "initiative-123",
                "workspace_id": "workspace-123",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Task 2",
                "description": "Description 2",
                "status": "IN_PROGRESS",
                "initiative_id": "initiative-123",
                "workspace_id": "workspace-123",
            },
        ]

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test get_initiative_tasks with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await get_initiative_tasks.fn("initiative-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_successful_retrieval(
        self, mock_request_with_auth, sample_tasks_data, mock_settings
    ):
        """Test successful retrieval of initiative tasks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_tasks_data

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_initiative_tasks.fn("initiative-123")

            # Verify correct URL construction
            expected_url = "https://api.test.com/task?initiative_id=eq.initiative-123&workspace_id=eq.workspace-123&select=*"
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
                        "type": "task",
                        "message": "Found 2 tasks for initiative initiative-123",
                        "initiative_id": "initiative-123",
                        "data": sample_tasks_data,
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_initiative_tasks.fn("initiative-123")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "Server error: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = Exception("Connection timeout")

            result = await get_initiative_tasks.fn("initiative-123")

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_empty_response(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of empty task list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await get_initiative_tasks.fn("initiative-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task",
                        "message": "Found 0 tasks for initiative initiative-123",
                        "data": [],
                    }
                ),
            )


class TestGetTaskDetails:
    """Test suite for get_task_details MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing."""
        return [
            {
                "id": "task-123",
                "title": "Test Task",
                "description": "Test Description",
                "status": "TODO",
                "initiative_id": "initiative-123",
                "workspace_id": "workspace-123",
            }
        ]

    @pytest.fixture
    def sample_checklist_data(self):
        """Sample checklist data for testing."""
        return [
            {
                "id": "checklist-1",
                "task_id": "task-123",
                "title": "First item",
                "is_complete": False,
                "order": 1,
            },
            {
                "id": "checklist-2",
                "task_id": "task-123",
                "title": "Second item",
                "is_complete": True,
                "order": 2,
            },
        ]

    @pytest.fixture
    def sample_initiative_data(self):
        """Sample initiative data for testing."""
        return [
            {
                "id": "initiative-123",
                "identifier": "I-001",
                "title": "User Authentication System",
                "description": "Implement secure user authentication with OAuth, 2FA, and session management.",
                "status": "IN_PROGRESS",
                "type": "FEATURE",
            }
        ]

    @pytest.fixture
    def sample_related_tasks_data(self):
        """Sample related tasks data for testing."""
        return [
            {
                "id": "task-456",
                "identifier": "T-001",
                "title": "Session Management System",
                "status": "TO_DO",
                "type": "CODING",
            },
            {
                "id": "task-789",
                "identifier": "T-002",
                "title": "Password Reset System",
                "status": "DONE",
                "type": "CODING",
            },
            {
                "id": "task-321",
                "identifier": "T-004",
                "title": "Two-Factor Authentication",
                "status": "BLOCKED",
                "type": "CODING",
            },
        ]

    @pytest.mark.asyncio
    async def test_get_task_details_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test get_task_details with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await get_task_details.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_details",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_task_details_successful_retrieval(
        self,
        mock_request_with_auth,
        sample_task_data,
        sample_checklist_data,
        sample_initiative_data,
        sample_related_tasks_data,
        mock_settings,
    ):
        """Test successful retrieval of task details with full context."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = sample_task_data

        checklist_response = Mock()
        checklist_response.status_code = 200
        checklist_response.json.return_value = sample_checklist_data

        initiative_response = Mock()
        initiative_response.status_code = 200
        initiative_response.json.return_value = sample_initiative_data

        related_tasks_response = Mock()
        related_tasks_response.status_code = 200
        related_tasks_response.json.return_value = sample_related_tasks_data

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [
                task_response,
                checklist_response,
                initiative_response,
                related_tasks_response,
            ]

            result = await get_task_details.fn("task-123")

            # Verify four API calls were made (task, checklist, initiative, related_tasks)
            assert mock_get.call_count == 4

            # Verify task API call
            task_call = mock_get.call_args_list[0]
            expected_task_url = "https://api.test.com/task?id=eq.task-123&workspace_id=eq.workspace-123&select=*"
            assert task_call[0][0] == expected_task_url

            # Verify checklist API call
            checklist_call = mock_get.call_args_list[1]
            expected_checklist_url = "https://api.test.com/checklist?task_id=eq.task-123&select=*&order=order"
            assert checklist_call[0][0] == expected_checklist_url

            # Verify initiative API call
            initiative_call = mock_get.call_args_list[2]
            expected_initiative_url = "https://api.test.com/initiative?id=eq.initiative-123&workspace_id=eq.workspace-123&select=*"
            assert initiative_call[0][0] == expected_initiative_url

            # Verify related tasks API call
            related_tasks_call = mock_get.call_args_list[3]
            expected_related_tasks_url = "https://api.test.com/task?initiative_id=eq.initiative-123&workspace_id=eq.workspace-123&id=neq.task-123&select=id,identifier,title,status,type&order=status,identifier"
            assert related_tasks_call[0][0] == expected_related_tasks_url

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_details",
                        "message": "Retrieved comprehensive task context for Test Task",
                        "task": sample_task_data[0],
                        "checklist_items": sample_checklist_data,
                    }
                ),
            )

            # Verify task_context field exists and contains expected content
            assert "task_context" in result
            task_context = result["task_context"]
            assert "INITIATIVE CONTEXT:" in task_context
            assert "User Authentication System" in task_context
            assert "TASK SCOPE:" in task_context
            assert "RELATED WORK IN THIS INITIATIVE:" in task_context

    @pytest.mark.asyncio
    async def test_get_task_details_task_not_found(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling when task is not found."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = []  # Empty array means not found

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = task_response

            result = await get_task_details.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_details",
                        "error_message": "Task task-123 not found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_task_details_checklist_fetch_fails(
        self,
        mock_request_with_auth,
        sample_task_data,
        sample_initiative_data,
        sample_related_tasks_data,
        mock_settings,
    ):
        """Test handling when checklist fetch fails but other calls succeed."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = sample_task_data

        checklist_response = Mock()
        checklist_response.status_code = 500

        initiative_response = Mock()
        initiative_response.status_code = 200
        initiative_response.json.return_value = sample_initiative_data

        related_tasks_response = Mock()
        related_tasks_response.status_code = 200
        related_tasks_response.json.return_value = sample_related_tasks_data

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [
                task_response,
                checklist_response,
                initiative_response,
                related_tasks_response,
            ]

            result = await get_task_details.fn("task-123")

            # Should log warning about checklist fetch failure
            mock_logger.warning.assert_called()

            # Should still return success with empty checklist but with task_context
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_details",
                        "task": sample_task_data[0],
                        "checklist_items": [],
                    }
                ),
            )

            # Should still have task_context field
            assert "task_context" in result


class TestSearchTasks:
    """Test suite for search_tasks MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "id": "task-1",
                "title": "Fix authentication bug",
                "description": "Authentication is not working correctly",
                "identifier": "AUTH-123",
            },
            {
                "id": "task-2",
                "title": "Add user authentication",
                "description": "Implement OAuth authentication",
                "identifier": "AUTH-124",
            },
        ]

    @pytest.mark.asyncio
    async def test_search_tasks_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test search_tasks with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await search_tasks.fn("authentication")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_tasks_successful_search(
        self, mock_request_with_auth, sample_search_results, mock_settings
    ):
        """Test successful task search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_results

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = "authentication"

            result = await search_tasks.fn("authentication")

            # Verify URL encoding was called
            mock_quote.assert_called_once_with("authentication")

            # Verify correct API call
            expected_url = "https://api.test.com/task?or(title.plfts(authentication),description.plfts(authentication),identifier.plfts(authentication))&workspace_id=eq.workspace-123"
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
                    {"status": "success", "type": "task", "data": sample_search_results}
                ),
            )

    @pytest.mark.asyncio
    async def test_search_tasks_with_special_characters(
        self, mock_request_with_auth, mock_settings
    ):
        """Test search with special characters that need URL encoding."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.urllib.parse.quote") as mock_quote,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response
            mock_quote.return_value = "oauth%202.0"

            result = await search_tasks.fn("oauth 2.0")

            # Verify URL encoding was called with special characters
            mock_quote.assert_called_once_with("oauth 2.0")

            # Verify encoded query was used in URL
            expected_url = "https://api.test.com/task?or(title.plfts(oauth%202.0),description.plfts(oauth%202.0),identifier.plfts(oauth%202.0))&workspace_id=eq.workspace-123"
            assert mock_get.call_args[0][0] == expected_url

    @pytest.mark.asyncio
    async def test_search_tasks_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error during search."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = mock_response

            result = await search_tasks.fn("test")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "Server error: 500",
                    }
                ),
            )


class TestUpdateTaskDescription:
    """Test suite for update_task_description MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_update_task_description_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test update_task_description with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await update_task_description.fn("task-123", "New description")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_update",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_description_successful_update(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful task description update."""
        mock_response = Mock()
        mock_response.status_code = 200

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_description.fn("task-123", "Updated description")

            # Verify patch was called correctly
            expected_url = (
                "https://api.test.com/task?id=eq.task-123&workspace_id=eq.workspace-123"
            )
            mock_patch.assert_called_once_with(
                expected_url,
                json={"description": "Updated description"},
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
                        "type": "task_update",
                        "message": "Successfully updated task description",
                        "task_id": "task-123",
                        "updated_description": "Updated description",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_description_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error during update."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_description.fn("task-123", "New description")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_update",
                        "error_message": "Server error: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_description_status_204(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful update with 204 No Content response."""
        mock_response = Mock()
        mock_response.status_code = 204

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_description.fn("task-123", "New description")

            # Should still return success for 204
            assert_that(
                result, has_entries({"status": "success", "type": "task_update"})
            )


class TestValidateContext:
    """Test suite for validate_context MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing."""
        return [
            {
                "id": "task-123",
                "title": "Test Task",
                "description": "Test Description",
                "status": "IN_PROGRESS",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]

    @pytest.fixture
    def sample_checklist_data(self):
        """Sample checklist data for testing."""
        return [
            {"id": "item-1", "is_complete": True},
            {"id": "item-2", "is_complete": False},
            {"id": "item-3", "is_complete": True},
        ]

    @pytest.mark.asyncio
    async def test_validate_context_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test validate_context with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await validate_context.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "context_validation",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_validate_context_successful_validation(
        self,
        mock_request_with_auth,
        sample_task_data,
        sample_checklist_data,
        mock_settings,
    ):
        """Test successful context validation with checklist progress calculation."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = sample_task_data

        checklist_response = Mock()
        checklist_response.status_code = 200
        checklist_response.json.return_value = sample_checklist_data

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [task_response, checklist_response]

            result = await validate_context.fn("task-123")

            # Verify two API calls were made
            assert mock_get.call_count == 2

            # Verify successful result with progress calculation
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "context_validation",
                        "message": "Task context is valid and up-to-date",
                        "task_id": "task-123",
                        "task": has_entries(
                            {
                                "id": "task-123",
                                "title": "Test Task",
                                "description": "Test Description",
                                "status": "IN_PROGRESS",
                            }
                        ),
                        "checklist_summary": has_entries(
                            {"total_items": 3, "completed_items": 2}
                        ),
                    }
                ),
            )

            # Check completion percentage separately due to floating point precision
            completion_percentage = result["checklist_summary"]["completion_percentage"]
            assert (
                66.6 < completion_percentage < 66.7
            )  # More lenient floating point check

    @pytest.mark.asyncio
    async def test_validate_context_task_not_found(
        self, mock_request_with_auth, mock_settings
    ):
        """Test validation when task is not found."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = []  # Empty array means not found

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.return_value = task_response

            result = await validate_context.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "context_validation",
                        "error_message": "Task task-123 not found or access denied",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_validate_context_empty_checklist(
        self, mock_request_with_auth, sample_task_data, mock_settings
    ):
        """Test validation with empty checklist (0% completion)."""
        task_response = Mock()
        task_response.status_code = 200
        task_response.json.return_value = sample_task_data

        checklist_response = Mock()
        checklist_response.status_code = 200
        checklist_response.json.return_value = []

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.get") as mock_get,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_get.side_effect = [task_response, checklist_response]

            result = await validate_context.fn("task-123")

            # Should handle empty checklist with 0% completion
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "checklist_summary": has_entries(
                            {
                                "total_items": 0,
                                "completed_items": 0,
                                "completion_percentage": 0,
                            }
                        ),
                    }
                ),
            )


class TestUpdateTaskStatusInProgress:
    """Test suite for update_task_status_inprogress MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_update_task_status_inprogress_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test update_task_status_inprogress with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await update_task_status_inprogress.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_inprogress_successful_update(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful task status update to IN_PROGRESS."""
        mock_response = Mock()
        mock_response.status_code = 200

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_status_inprogress.fn("task-123")

            # Verify patch was called correctly
            expected_url = (
                "https://api.test.com/task?id=eq.task-123&workspace_id=eq.workspace-123"
            )
            mock_patch.assert_called_once_with(
                expected_url,
                json={"status": "IN_PROGRESS"},
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
                        "type": "task_status_update",
                        "message": "Successfully updated task status to IN_PROGRESS",
                        "task_id": "task-123",
                        "new_status": "IN_PROGRESS",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_inprogress_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error during status update."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_status_inprogress.fn("task-123")

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_message": "Server error: 500",
                    }
                ),
            )


class TestUpdateTaskStatusDone:
    """Test suite for update_task_status_done MCP tool."""

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
        with patch("src.mcp_server.task_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_update_task_status_done_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test update_task_status_done with missing authorization header."""
        with patch("src.mcp_server.task_tools.get_http_request") as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await update_task_status_done.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_done_successful_update(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful task status update to DONE."""
        mock_response = Mock()
        mock_response.status_code = 200

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_status_done.fn("task-123")

            # Verify patch was called correctly
            expected_url = (
                "https://api.test.com/task?id=eq.task-123&workspace_id=eq.workspace-123"
            )
            mock_patch.assert_called_once_with(
                expected_url,
                json={"status": "DONE"},
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
                        "type": "task_status_update",
                        "message": "Successfully updated task status to DONE",
                        "task_id": "task-123",
                        "new_status": "DONE",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_done_status_204(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful update with 204 No Content response."""
        mock_response = Mock()
        mock_response.status_code = 204

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_status_done.fn("task-123")

            # Should still return success for 204
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_status_update",
                        "new_status": "DONE",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_done_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
            patch("src.mcp_server.task_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.side_effect = Exception("Connection timeout")

            result = await update_task_status_done.fn("task-123")

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    async def test_update_task_status_done_client_errors(
        self, mock_request_with_auth, mock_settings, status_code
    ):
        """Test handling of various client error status codes."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = f"Client error {status_code}"

        with (
            patch("src.mcp_server.task_tools.get_http_request") as mock_get_request,
            patch("src.mcp_server.task_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_task_status_done.fn("task-123")

            assert_that(
                result,
                has_entries(
                    {"status": "error", "error_message": f"Server error: {status_code}"}
                ),
            )
