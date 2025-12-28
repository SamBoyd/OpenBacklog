"""Unit tests for task_tools MCP tools."""

import uuid
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, is_

from src.initiative_management.task_controller import (
    TaskControllerError,
    TaskNotFoundError,
)
from src.mcp_server.task_tools import (
    TaskChecklistItem,
    create_task,
    get_initiative_tasks,
    get_task_details,
    search_tasks,
    update_task_description,
    update_task_status_done,
    update_task_status_inprogress,
    validate_context,
)
from src.models import ChecklistItem, Initiative, Task, TaskStatus, User, Workspace
from src.strategic_planning.exceptions import DomainException


class TestGetInitiativeTasks:
    """Test suite for get_initiative_tasks MCP tool."""

    @pytest.fixture
    def sample_tasks(self, user: User, workspace: Workspace):
        """Sample tasks for testing."""
        initiative_id = uuid.uuid4()
        return [
            Task(
                id=uuid.uuid4(),
                title="Task 1",
                description="Description 1",
                status=TaskStatus.TO_DO,
                initiative_id=initiative_id,
                workspace_id=workspace.id,
                user_id=user.id,
                identifier="T-001",
                type="CODING",
            ),
            Task(
                id=uuid.uuid4(),
                title="Task 2",
                description="Description 2",
                status=TaskStatus.IN_PROGRESS,
                initiative_id=initiative_id,
                workspace_id=workspace.id,
                user_id=user.id,
                identifier="T-002",
                type="CODING",
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_successful_retrieval(
        self, user: User, workspace: Workspace, session, sample_tasks
    ):
        """Test successful retrieval of initiative tasks."""
        initiative_id = str(sample_tasks[0].initiative_id)

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_initiative_tasks.return_value = sample_tasks

            result = await get_initiative_tasks.fn(initiative_id)

            # Verify controller was called correctly
            mock_controller.get_initiative_tasks.assert_called_once_with(
                user.id, uuid.UUID(initiative_id)
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task",
                        "message": f"Found 2 tasks for initiative {initiative_id}",
                        "initiative_id": initiative_id,
                    }
                ),
            )
            assert len(result["data"]) == 2
            assert result["data"][0]["title"] == "Task 1"
            assert result["data"][1]["title"] == "Task 2"

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_empty_response(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of empty task list."""
        initiative_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_initiative_tasks.return_value = []

            result = await get_initiative_tasks.fn(initiative_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task",
                        "message": f"Found 0 tasks for initiative {initiative_id}",
                        "data": [],
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_controller_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of controller error."""
        initiative_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_initiative_tasks.side_effect = TaskControllerError(
                "Controller error"
            )

            result = await get_initiative_tasks.fn(initiative_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_message": "Controller error",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_initiative_tasks_invalid_uuid(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of invalid UUID format."""
        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await get_initiative_tasks.fn("invalid-uuid")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_type": "validation_error",
                    }
                ),
            )


class TestGetTaskDetails:
    """Test suite for get_task_details MCP tool."""

    @pytest.fixture
    def sample_task(self, user: User, workspace: Workspace):
        """Sample task for testing."""
        initiative_id = uuid.uuid4()
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.TO_DO,
            initiative_id=initiative_id,
            workspace_id=workspace.id,
            user_id=user.id,
            identifier="T-123",
            type="CODING",
        )
        return task

    @pytest.fixture
    def sample_initiative(self, user: User, workspace: Workspace, sample_task):
        """Sample initiative for testing."""
        return Initiative(
            id=sample_task.initiative_id,
            title="User Authentication System",
            description="Implement secure user authentication",
            status=TaskStatus.IN_PROGRESS,
            identifier="I-001",
            user_id=user.id,
            workspace_id=workspace.id,
        )

    @pytest.mark.asyncio
    async def test_get_task_details_successful_retrieval(
        self, user: User, workspace: Workspace, session, sample_task, sample_initiative
    ):
        """Test successful retrieval of task details."""
        task_id = str(sample_task.id)
        user_id = user.id  # Cache user_id to avoid detached instance error

        # Add checklist items to the task
        sample_task.checklist_items = [
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=sample_task.id,
                title="First item",
                is_complete=False,
                order=1,
            ),
        ]

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = sample_task
            mock_controller.get_initiative_tasks.return_value = [sample_task]

            # Mock the Initiative query
            session.add(sample_initiative)
            session.commit()

            result = await get_task_details.fn(task_id)

            # Verify controller was called correctly
            mock_controller.get_task_details.assert_called_once_with(
                user_id, uuid.UUID(task_id)
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_details",
                        "message": f"Retrieved comprehensive task context for {sample_task.title}",
                    }
                ),
            )
            assert "task" in result
            assert "checklist_items" in result
            assert "task_context" in result
            assert len(result["checklist_items"]) == 1

    @pytest.mark.asyncio
    async def test_get_task_details_task_not_found(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling when task is not found."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = None

            result = await get_task_details.fn(task_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_details",
                        "error_message": f"Task {task_id} not found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_get_task_details_controller_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of controller error."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.side_effect = TaskNotFoundError(
                "Task not found"
            )

            result = await get_task_details.fn(task_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_details",
                        "error_type": "not_found",
                    }
                ),
            )


class TestSearchTasks:
    """Test suite for search_tasks MCP tool."""

    @pytest.fixture
    def sample_search_results(self, user: User, workspace: Workspace):
        """Sample search results for testing."""
        return [
            Task(
                id=uuid.uuid4(),
                title="Fix authentication bug",
                description="Authentication is not working correctly",
                identifier="AUTH-123",
                user_id=user.id,
                workspace_id=workspace.id,
                status=TaskStatus.TO_DO,
                type="CODING",
            ),
            Task(
                id=uuid.uuid4(),
                title="Add user authentication",
                description="Implement OAuth authentication",
                identifier="AUTH-124",
                user_id=user.id,
                workspace_id=workspace.id,
                status=TaskStatus.IN_PROGRESS,
                type="CODING",
            ),
        ]

    @pytest.mark.asyncio
    async def test_search_tasks_successful_search(
        self, user: User, workspace: Workspace, session, sample_search_results
    ):
        """Test successful task search."""
        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.search_tasks.return_value = sample_search_results

            result = await search_tasks.fn("authentication")

            # Verify controller was called correctly
            mock_controller.search_tasks.assert_called_once_with(
                user.id, workspace.id, "authentication"
            )

            # Verify successful result
            assert_that(result, has_entries({"status": "success", "type": "task"}))
            assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_search_tasks_empty_results(
        self, user: User, workspace: Workspace, session
    ):
        """Test search with no results."""
        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.search_tasks.return_value = []

            result = await search_tasks.fn("nonexistent")

            assert_that(
                result,
                has_entries({"status": "success", "type": "task", "data": []}),
            )

    @pytest.mark.asyncio
    async def test_search_tasks_controller_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of controller error during search."""
        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.search_tasks.side_effect = TaskControllerError(
                "Search failed"
            )

            result = await search_tasks.fn("test")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_type": "controller_error",
                    }
                ),
            )


class TestUpdateTaskDescription:
    """Test suite for update_task_description MCP tool."""

    @pytest.mark.asyncio
    async def test_update_task_description_successful_update(
        self, user: User, workspace: Workspace, session
    ):
        """Test successful task description update."""
        task_id = str(uuid.uuid4())
        description = "Updated description"

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_task = Mock()
            mock_controller.update_task_description.return_value = mock_task

            result = await update_task_description.fn(task_id, description)

            # Verify controller was called correctly
            mock_controller.update_task_description.assert_called_once_with(
                user.id, uuid.UUID(task_id), description
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_update",
                        "message": "Successfully updated task description",
                        "task_id": task_id,
                        "updated_description": description,
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_description_task_not_found(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling when task is not found."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.update_task_description.side_effect = TaskNotFoundError(
                "Task not found"
            )

            result = await update_task_description.fn(task_id, "New description")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_update",
                        "error_type": "not_found",
                    }
                ),
            )


class TestValidateContext:
    """Test suite for validate_context MCP tool."""

    @pytest.fixture
    def sample_task_with_checklist(self, user: User, workspace: Workspace):
        """Sample task with checklist for testing."""
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.IN_PROGRESS,
            user_id=user.id,
            workspace_id=workspace.id,
            identifier="T-123",
            type="CODING",
        )
        task.checklist_items = [
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=task.id,
                title="Item 1",
                is_complete=True,
                order=1,
            ),
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=task.id,
                title="Item 2",
                is_complete=False,
                order=2,
            ),
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=task.id,
                title="Item 3",
                is_complete=True,
                order=3,
            ),
        ]
        return task

    @pytest.mark.asyncio
    async def test_validate_context_successful_validation(
        self, user: User, workspace: Workspace, session, sample_task_with_checklist
    ):
        """Test successful context validation with checklist progress."""
        task_id = str(sample_task_with_checklist.id)

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = sample_task_with_checklist

            result = await validate_context.fn(task_id)

            # Verify controller was called correctly
            mock_controller.get_task_details.assert_called_once_with(
                user.id, uuid.UUID(task_id)
            )

            # Verify successful result with progress calculation
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "context_validation",
                        "message": "Task context is valid and up-to-date",
                        "task_id": task_id,
                    }
                ),
            )

            # Check checklist summary
            assert result["checklist_summary"]["total_items"] == 3
            assert result["checklist_summary"]["completed_items"] == 2
            completion_percentage = result["checklist_summary"]["completion_percentage"]
            assert 66.6 < completion_percentage < 66.7

    @pytest.mark.asyncio
    async def test_validate_context_task_not_found(
        self, user: User, workspace: Workspace, session
    ):
        """Test validation when task is not found."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = None

            result = await validate_context.fn(task_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "context_validation",
                        "error_message": f"Task {task_id} not found or access denied",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_validate_context_empty_checklist(
        self, user: User, workspace: Workspace, session
    ):
        """Test validation with empty checklist (0% completion)."""
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.IN_PROGRESS,
            user_id=user.id,
            workspace_id=workspace.id,
            identifier="T-123",
            type="CODING",
        )
        task.checklist_items = []
        task_id = str(task.id)

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = task

            result = await validate_context.fn(task_id)

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

    @pytest.mark.asyncio
    async def test_update_task_status_inprogress_successful_update(
        self, user: User, workspace: Workspace, session
    ):
        """Test successful task status update to IN_PROGRESS."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_task = Mock()
            mock_controller.move_task_to_status.return_value = mock_task

            result = await update_task_status_inprogress.fn(task_id)

            # Verify controller was called correctly
            mock_controller.move_task_to_status.assert_called_once_with(
                user.id, uuid.UUID(task_id), TaskStatus.IN_PROGRESS
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_status_update",
                        "message": "Successfully updated task status to IN_PROGRESS",
                        "task_id": task_id,
                        "new_status": "IN_PROGRESS",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_inprogress_task_not_found(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling when task is not found."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.move_task_to_status.side_effect = TaskNotFoundError(
                "Task not found"
            )

            result = await update_task_status_inprogress.fn(task_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_type": "not_found",
                    }
                ),
            )


class TestUpdateTaskStatusDone:
    """Test suite for update_task_status_done MCP tool."""

    @pytest.mark.asyncio
    async def test_update_task_status_done_successful_update(
        self, user: User, workspace: Workspace, session
    ):
        """Test successful task status update to DONE."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_task = Mock()
            mock_controller.move_task_to_status.return_value = mock_task

            result = await update_task_status_done.fn(task_id)

            # Verify controller was called correctly
            mock_controller.move_task_to_status.assert_called_once_with(
                user.id, uuid.UUID(task_id), TaskStatus.DONE
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task_status_update",
                        "message": "Successfully updated task status to DONE",
                        "task_id": task_id,
                        "new_status": "DONE",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_task_status_done_controller_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test handling of controller error."""
        task_id = str(uuid.uuid4())

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.move_task_to_status.side_effect = TaskControllerError(
                "Cannot update status"
            )

            result = await update_task_status_done.fn(task_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_id", ["invalid-uuid", "123", ""])
    async def test_update_task_status_done_invalid_uuid(
        self, user: User, workspace: Workspace, session, invalid_id
    ):
        """Test handling of invalid UUID formats."""
        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_task_status_done.fn(invalid_id)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task_status_update",
                        "error_type": "validation_error",
                    }
                ),
            )


class TestCreateTask:
    """Test suite for create_task MCP tool."""

    @pytest.fixture
    def sample_created_task(self, user: User, workspace: Workspace):
        """Sample task returned after creation."""
        task = Task(
            id=uuid.uuid4(),
            title="New Test Task",
            description="Task description",
            status=TaskStatus.TO_DO,
            initiative_id=uuid.uuid4(),
            workspace_id=workspace.id,
            user_id=user.id,
            identifier="TM-001",
            type="CODING",
        )
        task.checklist = []
        return task

    @pytest.mark.asyncio
    async def test_create_task_minimal_params(
        self, user: User, workspace: Workspace, session, sample_created_task
    ):
        """Test successful task creation with minimal parameters."""
        initiative_identifier = "I-012"
        initiative_id = sample_created_task.initiative_id

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.return_value = initiative_id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.create_task.return_value = sample_created_task

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
            )

            # Verify resolve was called
            mock_resolve.assert_called_once_with(
                initiative_identifier, workspace.id, session
            )

            # Verify controller was called correctly
            mock_controller.create_task.assert_called_once_with(
                title="New Test Task",
                user_id=user.id,
                workspace_id=workspace.id,
                initiative_id=initiative_id,
                status=TaskStatus.TO_DO,
                task_type=None,
                description=None,
                checklist=None,
            )

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "task",
                    }
                ),
            )
            assert "TM-001" in result["message"]
            assert result["data"]["identifier"] == "TM-001"
            assert result["data"]["initiative_identifier"] == initiative_identifier

    @pytest.mark.asyncio
    async def test_create_task_with_all_optional_params(
        self, user: User, workspace: Workspace, session, sample_created_task
    ):
        """Test task creation with all optional parameters."""
        initiative_identifier = "I-012"
        initiative_id = sample_created_task.initiative_id

        sample_created_task.status = TaskStatus.IN_PROGRESS
        sample_created_task.type = "TESTING"
        sample_created_task.description = "Detailed description"

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.return_value = initiative_id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.create_task.return_value = sample_created_task

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
                description="Detailed description",
                status="IN_PROGRESS",
                task_type="TESTING",
            )

            # Verify controller was called with all params
            mock_controller.create_task.assert_called_once_with(
                title="New Test Task",
                user_id=user.id,
                workspace_id=workspace.id,
                initiative_id=initiative_id,
                status=TaskStatus.IN_PROGRESS,
                task_type="TESTING",
                description="Detailed description",
                checklist=None,
            )

            # Verify successful result
            assert_that(result, has_entries({"status": "success", "type": "task"}))

    @pytest.mark.asyncio
    async def test_create_task_with_checklist(
        self, user: User, workspace: Workspace, session, sample_created_task
    ):
        """Test task creation with checklist items."""
        initiative_identifier = "I-012"
        initiative_id = sample_created_task.initiative_id

        # Add checklist items to the mock response
        sample_created_task.checklist = [
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=sample_created_task.id,
                title="Step 1",
                is_complete=False,
                order=0,
            ),
            ChecklistItem(
                id=uuid.uuid4(),
                task_id=sample_created_task.id,
                title="Step 2",
                is_complete=True,
                order=1,
            ),
        ]

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.return_value = initiative_id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.create_task.return_value = sample_created_task

            checklist_items = [
                TaskChecklistItem(title="Step 1", is_complete=False),
                TaskChecklistItem(title="Step 2", is_complete=True),
            ]

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
                checklist=checklist_items,
            )

            # Verify checklist was passed to controller
            call_args = mock_controller.create_task.call_args
            assert call_args.kwargs["checklist"] is not None
            assert len(call_args.kwargs["checklist"]) == 2
            assert call_args.kwargs["checklist"][0].title == "Step 1"
            assert call_args.kwargs["checklist"][1].title == "Step 2"

            # Verify successful result with checklist items
            assert_that(result, has_entries({"status": "success", "type": "task"}))
            assert len(result["data"]["checklist"]) == 2
            assert result["data"]["checklist"][0]["title"] == "Step 1"

    @pytest.mark.asyncio
    async def test_create_task_initiative_not_found(
        self, user: User, workspace: Workspace, session
    ):
        """Test error handling when initiative is not found."""
        initiative_identifier = "I-999"

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.side_effect = DomainException(
                f"Initiative with identifier '{initiative_identifier}' not found"
            )

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_type": "not_found",
                    }
                ),
            )
            assert initiative_identifier in result["error_message"]

    @pytest.mark.asyncio
    async def test_create_task_invalid_status(
        self, user: User, workspace: Workspace, session
    ):
        """Test error handling for invalid status value."""
        initiative_identifier = "I-012"
        initiative_id = uuid.uuid4()

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.return_value = initiative_id

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
                status="INVALID_STATUS",
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_type": "validation_error",
                    }
                ),
            )
            assert "INVALID_STATUS" in result["error_message"]

    @pytest.mark.asyncio
    async def test_create_task_controller_error(
        self, user: User, workspace: Workspace, session
    ):
        """Test error handling when controller fails."""
        initiative_identifier = "I-012"
        initiative_id = uuid.uuid4()

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_session_local.return_value = session
            mock_resolve.return_value = initiative_id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.create_task.side_effect = TaskControllerError(
                "Failed to create task"
            )

            result = await create_task.fn(
                initiative_identifier=initiative_identifier,
                title="New Test Task",
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "task",
                        "error_type": "controller_error",
                    }
                ),
            )
