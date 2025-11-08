"""Unit tests for initiative_tools MCP tools."""

import uuid
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries

from src.initiative_management.initiative_controller import (
    InitiativeControllerError,
    InitiativeNotFoundError,
)
from src.mcp_server.initiative_tools import (
    get_active_initiatives,
    get_initiative_details,
    search_initiatives,
)
from src.models import Initiative, InitiativeStatus, Task, TaskStatus, User, Workspace


class TestGetActiveInitiatives:
    """Test suite for get_active_initiatives MCP tool."""

    @pytest.fixture
    def sample_initiatives(self, user: User, workspace: Workspace):
        """Sample initiative instances for testing."""
        return [
            Initiative(
                id=uuid.uuid4(),
                title="Initiative 1",
                description="Description 1",
                status=InitiativeStatus.IN_PROGRESS,
                identifier="INIT-001",
                workspace_id=workspace.id,
                user_id=user.id,
            ),
            Initiative(
                id=uuid.uuid4(),
                title="Initiative 2",
                description="Description 2",
                status=InitiativeStatus.IN_PROGRESS,
                identifier="INIT-002",
                workspace_id=workspace.id,
                user_id=user.id,
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_active_initiatives_successful_retrieval(
        self, session, user: User, workspace: Workspace, sample_initiatives
    ):
        """Test successful retrieval of active initiatives."""
        mock_controller = Mock()
        mock_controller.get_active_initiatives.return_value = sample_initiatives

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_active_initiatives.fn()

            # Verify controller was called correctly
            mock_controller.get_active_initiatives.assert_called_once_with(
                user.id, workspace.id
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative",
                        "message": "Found 2 active initiatives",
                    }
                ),
            )
            assert len(result["data"]) == 2
            assert_that(result["data"][0]["title"], equal_to("Initiative 1"))
            assert_that(result["data"][1]["title"], equal_to("Initiative 2"))

    @pytest.mark.asyncio
    async def test_get_active_initiatives_controller_error(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of controller error."""
        mock_controller = Mock()
        mock_controller.get_active_initiatives.side_effect = InitiativeControllerError(
            "Database error"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_active_initiatives.fn()

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Database error",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_active_initiatives_empty_response(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of empty initiative list."""
        mock_controller = Mock()
        mock_controller.get_active_initiatives.return_value = []

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

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
    async def test_get_active_initiatives_generic_exception(
        self, session, user: User, workspace: Workspace
    ):
        """Test exception handling during controller call."""
        mock_controller = Mock()
        mock_controller.get_active_initiatives.side_effect = Exception(
            "Unexpected error"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_active_initiatives.fn()

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: Unexpected error",
                        "error_type": "server_error",
                    }
                ),
            )


class TestSearchInitiatives:
    """Test suite for search_initiatives MCP tool."""

    @pytest.fixture
    def sample_search_results(self, user: User, workspace: Workspace):
        """Sample search results for testing."""
        return [
            Initiative(
                id=uuid.uuid4(),
                title="Fix authentication system",
                description="Authentication is not working correctly",
                identifier="AUTH-123",
                status=InitiativeStatus.IN_PROGRESS,
                workspace_id=workspace.id,
                user_id=user.id,
            ),
            Initiative(
                id=uuid.uuid4(),
                title="Add user authentication",
                description="Implement OAuth authentication",
                identifier="AUTH-124",
                status=InitiativeStatus.TO_DO,
                workspace_id=workspace.id,
                user_id=user.id,
            ),
        ]

    @pytest.mark.asyncio
    async def test_search_initiatives_successful_search(
        self, session, user: User, workspace: Workspace, sample_search_results
    ):
        """Test successful initiative search."""
        mock_controller = Mock()
        mock_controller.search_initiatives.return_value = sample_search_results

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await search_initiatives.fn("authentication")

            # Verify controller was called correctly
            mock_controller.search_initiatives.assert_called_once_with(
                user.id, workspace.id, "authentication"
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative",
                    }
                ),
            )
            assert len(result["data"]) == 2
            assert_that(
                result["data"][0]["title"], equal_to("Fix authentication system")
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_controller_error(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of controller error during search."""
        mock_controller = Mock()
        mock_controller.search_initiatives.side_effect = InitiativeControllerError(
            "Search failed"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await search_initiatives.fn("test")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Search failed",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_empty_results(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of empty search results."""
        mock_controller = Mock()
        mock_controller.search_initiatives.return_value = []

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await search_initiatives.fn("nonexistent")

            assert_that(
                result,
                has_entries({"status": "success", "type": "initiative", "data": []}),
            )

    @pytest.mark.asyncio
    async def test_search_initiatives_empty_query(
        self, session, user: User, workspace: Workspace
    ):
        """Test search with empty query string."""
        mock_controller = Mock()
        mock_controller.search_initiatives.return_value = []

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await search_initiatives.fn("")

            # Should still call the controller with empty query
            mock_controller.search_initiatives.assert_called_once_with(
                user.id, workspace.id, ""
            )
            assert_that(result["status"], equal_to("success"))

    @pytest.mark.asyncio
    async def test_search_initiatives_generic_exception(
        self, session, user: User, workspace: Workspace
    ):
        """Test exception handling during search."""
        mock_controller = Mock()
        mock_controller.search_initiatives.side_effect = Exception("Network error")

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await search_initiatives.fn("test")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative",
                        "error_message": "Server error: Network error",
                        "error_type": "server_error",
                    }
                ),
            )


class TestGetInitiativeDetails:
    """Test suite for get_initiative_details MCP tool."""

    @pytest.fixture
    def sample_initiative_with_tasks(self, user: User, workspace: Workspace):
        """Sample initiative with tasks for testing."""
        initiative = Initiative(
            id=uuid.uuid4(),
            title="User Authentication System",
            description="Implement comprehensive user authentication",
            status=InitiativeStatus.IN_PROGRESS,
            identifier="AUTH-001",
            workspace_id=workspace.id,
            user_id=user.id,
        )

        task1 = Task(
            id=uuid.uuid4(),
            title="Implement OAuth login",
            description="Add OAuth 2.0 authentication",
            status=TaskStatus.IN_PROGRESS,
            identifier="AUTH-001-T1",
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
        )

        task2 = Task(
            id=uuid.uuid4(),
            title="Add session management",
            description="Implement secure session handling",
            status=TaskStatus.TO_DO,
            identifier="AUTH-001-T2",
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
        )

        initiative.tasks = [task1, task2]
        return initiative

    @pytest.mark.asyncio
    async def test_get_initiative_details_successful_retrieval(
        self, session, user: User, workspace: Workspace, sample_initiative_with_tasks
    ):
        """Test successful retrieval of initiative details with tasks."""
        mock_controller = Mock()
        mock_controller.get_initiative_details.return_value = (
            sample_initiative_with_tasks
        )

        initiative_id = str(sample_initiative_with_tasks.id)

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn(initiative_id)

            # Verify controller was called correctly
            mock_controller.get_initiative_details.assert_called_once_with(
                user.id, sample_initiative_with_tasks.id
            )

            # Verify successful result structure
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative_details",
                        "message": "Retrieved comprehensive initiative context for User Authentication System",
                    }
                ),
            )
            assert_that(
                result["initiative"]["title"],
                equal_to("User Authentication System"),
            )
            assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_get_initiative_details_initiative_not_found(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling when initiative is not found."""
        mock_controller = Mock()
        mock_controller.get_initiative_details.return_value = None

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            initiative_id = str(uuid.uuid4())
            result = await get_initiative_details.fn(initiative_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": f"Initiative {initiative_id} not found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_controller_not_found_error(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of InitiativeNotFoundError from controller."""
        mock_controller = Mock()
        mock_controller.get_initiative_details.side_effect = InitiativeNotFoundError(
            "Initiative does not exist"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn(str(uuid.uuid4()))

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Initiative does not exist",
                        "error_type": "not_found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_controller_error(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of controller error."""
        mock_controller = Mock()
        mock_controller.get_initiative_details.side_effect = InitiativeControllerError(
            "Database error"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn(str(uuid.uuid4()))

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Database error",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_invalid_uuid(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of invalid UUID format."""
        mock_controller = Mock()

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn("invalid-uuid")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_type": "validation_error",
                    }
                ),
            )
            assert "Invalid initiative ID format" in result["error_message"]

    @pytest.mark.asyncio
    async def test_get_initiative_details_empty_tasks(
        self, session, user: User, workspace: Workspace
    ):
        """Test handling of initiative with no tasks."""
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Empty Initiative",
            description="No tasks yet",
            status=InitiativeStatus.TO_DO,
            identifier="EMPTY-001",
            workspace_id=workspace.id,
            user_id=user.id,
        )
        initiative.tasks = []

        mock_controller = Mock()
        mock_controller.get_initiative_details.return_value = initiative

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn(str(initiative.id))

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "initiative_details",
                        "tasks": [],
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_details_generic_exception(
        self, session, user: User, workspace: Workspace
    ):
        """Test exception handling during controller call."""
        mock_controller = Mock()
        mock_controller.get_initiative_details.side_effect = Exception(
            "Unexpected error"
        )

        with (
            patch("src.mcp_server.initiative_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.initiative_tools.InitiativeController"
            ) as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller_class.return_value = mock_controller

            result = await get_initiative_details.fn(str(uuid.uuid4()))

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "initiative_details",
                        "error_message": "Server error: Unexpected error",
                        "error_type": "server_error",
                    }
                ),
            )
