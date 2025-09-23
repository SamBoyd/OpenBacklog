import json
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, is_
from starlette.requests import Request

from src.mcp_server.checklist_tools import (
    ChecklistItem,
    update_checklist,
    update_checklist_item,
)


class TestUpdateChecklist:
    """Test suite for update_checklist MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {}
        return request

    @pytest.fixture
    def sample_checklist_items(self):
        """Sample checklist items for testing."""
        return [
            ChecklistItem(title="First task", is_complete=False),
            ChecklistItem(title="Second task", is_complete=True),
            ChecklistItem(title="Third task", is_complete=False),
        ]

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.checklist_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_update_checklist_missing_authorization(
        self, mock_request_no_auth, sample_checklist_items, mock_settings
    ):
        """Test update_checklist with missing authorization header."""
        with patch(
            "src.mcp_server.checklist_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await update_checklist.fn("task-123", sample_checklist_items)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_update",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_successful_update(
        self, mock_request_with_auth, sample_checklist_items, mock_settings
    ):
        """Test successful checklist update with all items created."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200

        mock_create_response = Mock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = [
            {
                "id": str(uuid.uuid4()),
                "task_id": "task-123",
                "title": "Test item",
                "is_complete": False,
            }
        ]

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.requests.post") as mock_post,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.return_value = mock_delete_response
            mock_post.return_value = mock_create_response

            result = await update_checklist.fn("task-123", sample_checklist_items)

            # Verify delete was called correctly
            mock_delete.assert_called_once_with(
                "https://api.test.com/checklist?task_id=eq.task-123",
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json",
                },
            )

            # Verify post was called for each item
            assert mock_post.call_count == 3

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "checklist_update",
                        "task_id": "task-123",
                    }
                ),
            )

            # Verify created_items is a list with 3 items (one from each call)
            assert len(result["created_items"]) == 3

    @pytest.mark.asyncio
    async def test_update_checklist_delete_failure_continues(
        self, mock_request_with_auth, sample_checklist_items, mock_settings
    ):
        """Test that delete failure doesn't stop the creation process."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 500

        mock_create_response = Mock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = [{"id": "item-1"}]

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.requests.post") as mock_post,
            patch("src.mcp_server.checklist_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.return_value = mock_delete_response
            mock_post.return_value = mock_create_response

            result = await update_checklist.fn("task-123", sample_checklist_items)

            # Verify warning was logged for delete failure
            mock_logger.warning.assert_called_once()

            # Verify creation still proceeded
            assert mock_post.call_count == 3
            assert_that(result["status"], equal_to("success"))

    @pytest.mark.asyncio
    async def test_update_checklist_partial_create_failures(
        self, mock_request_with_auth, sample_checklist_items, mock_settings
    ):
        """Test handling of partial failures during item creation."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200

        # Mock responses: first succeeds, second fails, third succeeds
        mock_responses = []
        for i, status_code in enumerate([201, 500, 201]):
            response = Mock()
            response.status_code = status_code
            if status_code in [200, 201]:
                response.json.return_value = [{"id": f"item-{i}"}]
            mock_responses.append(response)

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.requests.post") as mock_post,
            patch("src.mcp_server.checklist_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.return_value = mock_delete_response
            mock_post.side_effect = mock_responses

            result = await update_checklist.fn("task-123", sample_checklist_items)

            # Verify warning was logged for create failure
            mock_logger.warning.assert_called()

            # Should still return success with partial results
            assert_that(result["status"], equal_to("success"))
            assert_that(
                result["message"],
                equal_to("Successfully updated checklist with 2 items"),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_empty_list(
        self, mock_request_with_auth, mock_settings
    ):
        """Test update_checklist with empty checklist items."""
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.requests.post") as mock_post,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.return_value = mock_delete_response

            result = await update_checklist.fn("task-123", [])

            # Should delete existing items but not create any new ones
            mock_delete.assert_called_once()
            mock_post.assert_not_called()

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "created_items": [],
                        "message": "Successfully updated checklist with 0 items",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_request_exception(
        self, mock_request_with_auth, sample_checklist_items, mock_settings
    ):
        """Test exception handling during HTTP requests."""
        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.side_effect = Exception("Network error")

            result = await update_checklist.fn("task-123", sample_checklist_items)

            # Should log the exception and return error
            mock_logger.exception.assert_called_once()
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_update",
                        "error_message": "Server error: Network error",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_validates_item_payload(
        self, mock_request_with_auth, mock_settings
    ):
        """Test that item payloads are constructed correctly."""
        checklist_items = [ChecklistItem(title="Test Task", is_complete=True)]

        mock_delete_response = Mock()
        mock_delete_response.status_code = 200

        mock_create_response = Mock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = [{"id": "created-item"}]

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.delete") as mock_delete,
            patch("src.mcp_server.checklist_tools.requests.post") as mock_post,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_delete.return_value = mock_delete_response
            mock_post.return_value = mock_create_response

            await update_checklist.fn("task-123", checklist_items)

            # Verify the payload sent to post
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            assert_that(
                payload,
                has_entries(
                    {
                        "task_id": "task-123",
                        "title": "Test Task",
                        "is_complete": False,  # Should always be False regardless of input
                    }
                ),
            )


class TestUpdateChecklistItem:
    """Test suite for update_checklist_item MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {}
        return request

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.mcp_server.checklist_tools.settings") as mock_settings:
            mock_settings.postgrest_domain = "https://api.test.com"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_update_checklist_item_missing_authorization(
        self, mock_request_no_auth, mock_settings
    ):
        """Test update_checklist_item with missing authorization header."""
        with patch(
            "src.mcp_server.checklist_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await update_checklist_item.fn("task-123", "item-456", True)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_successful_update_complete(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful update of checklist item to complete."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'[{"id": "item-456", "is_complete": true}]'
        mock_response.json.return_value = [{"id": "item-456", "is_complete": True}]

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_checklist_item.fn("task-123", "item-456", True)

            # Verify patch was called correctly
            mock_patch.assert_called_once_with(
                "https://api.test.com/checklist?id=eq.item-456&task_id=eq.task-123",
                json={"is_complete": True},
                headers={
                    "Authorization": "Bearer valid_token",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "checklist_item_update",
                        "message": "Successfully marked checklist item as complete",
                        "task_id": "task-123",
                        "item_id": "item-456",
                        "is_complete": True,
                        "updated_items": [{"id": "item-456", "is_complete": True}],
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_successful_update_incomplete(
        self, mock_request_with_auth, mock_settings
    ):
        """Test successful update of checklist item to incomplete."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_checklist_item.fn("task-123", "item-456", False)

            # Verify patch was called with correct payload
            call_args = mock_patch.call_args
            payload = call_args[1]["json"]
            assert_that(payload, equal_to({"is_complete": False}))

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "message": "Successfully marked checklist item as incomplete",
                        "is_complete": False,
                        "updated_items": [],
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_server_error(
        self, mock_request_with_auth, mock_settings
    ):
        """Test handling of server error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
            patch("src.mcp_server.checklist_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_checklist_item.fn("task-123", "item-456", True)

            # Should log the error
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_message": "Server error: 500",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_network_exception(
        self, mock_request_with_auth, mock_settings
    ):
        """Test exception handling during HTTP request."""
        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
            patch("src.mcp_server.checklist_tools.logger") as mock_logger,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.side_effect = Exception("Connection timeout")

            result = await update_checklist_item.fn("task-123", "item-456", True)

            # Should log the exception
            mock_logger.exception.assert_called_once()

            # Should return error response
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_message": "Server error: Connection timeout",
                        "error_type": "server_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    async def test_update_checklist_item_client_errors(
        self, mock_request_with_auth, mock_settings, status_code
    ):
        """Test handling of various client error status codes."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = f"Client error {status_code}"

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            result = await update_checklist_item.fn("task-123", "item-456", True)

            assert_that(
                result,
                has_entries(
                    {"status": "error", "error_message": f"Server error: {status_code}"}
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_validates_url_construction(
        self, mock_request_with_auth, mock_settings
    ):
        """Test that the update URL is constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"[]"
        mock_response.json.return_value = []

        with (
            patch(
                "src.mcp_server.checklist_tools.get_http_request"
            ) as mock_get_request,
            patch("src.mcp_server.checklist_tools.requests.patch") as mock_patch,
        ):

            mock_get_request.return_value = mock_request_with_auth
            mock_patch.return_value = mock_response

            await update_checklist_item.fn("task-123", "item-456", True)

            # Verify URL construction with proper query parameters
            expected_url = (
                "https://api.test.com/checklist?id=eq.item-456&task_id=eq.task-123"
            )
            call_args = mock_patch.call_args
            actual_url = call_args[0][0]

            assert_that(actual_url, equal_to(expected_url))
