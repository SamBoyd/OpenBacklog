"""Unit tests for task_tools MCP tools."""

import uuid
from typing import List
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, is_
from sqlalchemy.orm import Session

from src.initiative_management.task_controller import (
    TaskControllerError,
    TaskNotFoundError,
)
from src.mcp_server.task_tools import (
    TaskChecklistItem,
    get_initiative_tasks,
    get_task_details,
    search_tasks,
    submit_task,
    validate_context,
)
from src.models import ChecklistItem, Initiative, Task, TaskStatus, User, Workspace
from src.strategic_planning.exceptions import DomainException


@pytest.fixture
def initiative(user: User, workspace: Workspace, session: Session) -> Initiative:
    """Sample initiative for testing."""
    initiative = Initiative(
        id=uuid.uuid4(),
        user_id=user.id,
        workspace_id=workspace.id,
        title="User Authentication System",
        description="Implement secure user authentication",
        status=TaskStatus.IN_PROGRESS,
        identifier="I-001",
    )

    session.add(initiative)
    session.commit()

    return initiative


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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        sample_tasks: List[Task],
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
        self, user: User, workspace: Workspace, session: Session
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
        self, user: User, workspace: Workspace, session: Session
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
        self, user: User, workspace: Workspace, session: Session
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
    def sample_initiative(self, user: User, workspace: Workspace, sample_task: Task):
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        sample_task: Task,
        sample_initiative: Initiative,
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
        self, user: User, workspace: Workspace, session: Session
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
        self, user: User, workspace: Workspace, session: Session
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        sample_search_results: List[Task],
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
        self, user: User, workspace: Workspace, session: Session
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
        self, user: User, workspace: Workspace, session: Session
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        sample_task_with_checklist: Task,
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
        self, user: User, workspace: Workspace, session: Session
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
        self, user: User, workspace: Workspace, session: Session
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


class TestSubmitTask:
    """Test suite for submit_task MCP tool (upsert pattern)."""

    @pytest.mark.asyncio
    async def test_submit_task_create_minimal(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test creating task with only required fields."""
        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            mock_task = Mock()
            mock_task.identifier = "T-001"
            mock_controller.create_task.return_value = mock_task

            result = await submit_task.fn(
                initiative_identifier="I-001", title="Test Task"
            )

            mock_controller.create_task.assert_called_once()
            call_args = mock_controller.create_task.call_args
            assert call_args.kwargs["title"] == "Test Task"
            assert call_args.kwargs["initiative_id"] == initiative.id
            assert call_args.kwargs["user_id"] == user.id
            assert call_args.kwargs["workspace_id"] == workspace.id
            assert call_args.kwargs["status"] == TaskStatus.TO_DO
            assert call_args.kwargs["description"] is None
            assert call_args.kwargs["checklist"] is None

            assert result["status"] == "success"
            assert result["message"] == "Created task T-001"

    @pytest.mark.asyncio
    async def test_submit_task_create_missing_title(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test error when title is missing for create."""
        result = await submit_task.fn(initiative_identifier="I-001", title=None)

        assert result["status"] == "error"
        assert "title is required" in result["error_message"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_update_task_not_found(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test error when task_identifier doesn't exist."""
        result = await submit_task.fn(task_identifier="T-999", status="DONE")

        assert result["status"] == "error"
        assert "not found" in result["error_message"]
        assert result["error_type"] == "not_found"

    # === CREATE PATH: Additional Tests ===

    @pytest.mark.asyncio
    async def test_submit_task_create_missing_initiative_identifier(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test error when initiative_identifier is missing for create."""

        result = await submit_task.fn(title="New Task")

        assert result["status"] == "error"
        assert "initiative_identifier is required" in result["error_message"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_create_with_all_optional_params(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test creating task with all optional parameters."""
        with (
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_resolve.return_value = initiative.id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            mock_task = Mock()
            mock_task.identifier = "T-002"
            mock_controller.create_task.return_value = mock_task

            result = await submit_task.fn(
                initiative_identifier="I-001",
                title="Test Task",
                description="Detailed description",
                status="IN_PROGRESS",
                task_type="TESTING",
            )

            assert result["status"] == "success"
            mock_controller.create_task.assert_called_once()
            call_args = mock_controller.create_task.call_args
            assert call_args.kwargs["description"] == "Detailed description"
            assert call_args.kwargs["status"] == TaskStatus.IN_PROGRESS
            assert call_args.kwargs["task_type"] == "TESTING"

    @pytest.mark.asyncio
    async def test_submit_task_create_with_checklist(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test creating task with checklist items."""

        with (
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_resolve.return_value = initiative.id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            mock_task = Mock()
            mock_task.identifier = "T-003"
            mock_controller.create_task.return_value = mock_task

            checklist_items = [
                TaskChecklistItem(title="Step 1", is_complete=False),
                TaskChecklistItem(title="Step 2", is_complete=True),
            ]

            result = await submit_task.fn(
                initiative_identifier="I-001",
                title="Task with Checklist",
                checklist=checklist_items,
            )

            assert result["status"] == "success"
            call_args = mock_controller.create_task.call_args
            assert call_args.kwargs["checklist"] is not None
            assert len(call_args.kwargs["checklist"]) == 2

    @pytest.mark.asyncio
    async def test_submit_task_create_initiative_not_found(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test error when initiative doesn't exist."""
        with (
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_resolve.side_effect = DomainException(
                "Initiative with identifier 'I-999' not found"
            )

            result = await submit_task.fn(
                initiative_identifier="I-999",
                title="New Task",
            )

            assert result["status"] == "error"
            assert "not found" in result["error_message"]
            assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_submit_task_create_invalid_status(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test error when invalid status is provided during create."""
        with (
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_resolve.return_value = initiative.id

            result = await submit_task.fn(
                initiative_identifier="I-001",
                title="Test Task",
                status="INVALID_STATUS",
            )

            assert result["status"] == "error"
            assert "Invalid status" in result["error_message"]
            assert "INVALID_STATUS" in result["error_message"]
            assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_create_controller_error(
        self, user: User, workspace: Workspace, session: Session, initiative: Initiative
    ):
        """Test handling of controller error during creation."""
        with (
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
            patch(
                "src.mcp_server.task_tools.resolve_initiative_identifier"
            ) as mock_resolve,
        ):
            mock_resolve.return_value = initiative.id
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.create_task.side_effect = TaskControllerError(
                "Failed to create task"
            )

            result = await submit_task.fn(
                initiative_identifier="I-001",
                title="Test Task",
            )

            assert result["status"] == "error"
            assert "Failed to create task" in result["error_message"]
            assert result["error_type"] == "controller_error"

    # === UPDATE PATH: Additional Tests ===

    @pytest.mark.asyncio
    async def test_submit_task_update_status_to_in_progress(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating task status to IN_PROGRESS."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-STAT",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-STAT-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with (
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            result = await submit_task.fn(
                task_identifier="T-STAT-001", status="IN_PROGRESS"
            )

            assert result["status"] == "success"
            mock_controller.move_task_to_status.assert_called_once()
            call_args = mock_controller.move_task_to_status.call_args
            assert call_args[0][2] == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_submit_task_update_invalid_status(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test error when invalid status is provided during update."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-INVSTAT",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-INVSTAT-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await submit_task.fn(
                task_identifier="T-INVSTAT-001", status="INVALID_STATUS"
            )

            assert result["status"] == "error"
            assert "Invalid status" in result["error_message"]
            assert "INVALID_STATUS" in result["error_message"]
            assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_update_status_controller_error(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test handling of controller error during status update."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-ERR",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-ERR-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

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

            result = await submit_task.fn(task_identifier="T-ERR-001", status="DONE")

            assert result["status"] == "error"
            assert "Cannot update status" in result["error_message"]
            assert result["error_type"] == "controller_error"

    @pytest.mark.asyncio
    async def test_submit_task_update_title(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating task title only."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-TITLE",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Old Title",
            identifier="T-TITLE-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await submit_task.fn(
                task_identifier="T-TITLE-001", title="Updated Title"
            )

            assert result["status"] == "success"
            assert result["data"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_submit_task_update_type(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating task type only."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-TYPE",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-TYPE-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
            type="CODING",
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await submit_task.fn(
                task_identifier="T-TYPE-001", task_type="TESTING"
            )

            assert result["status"] == "success"
            assert result["data"]["type"] == "TESTING"

    @pytest.mark.asyncio
    async def test_submit_task_update_checklist(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test replacing task checklist."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-CHECK",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-CHECK-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with (
            patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_session_local.return_value = session
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            checklist_items = [
                TaskChecklistItem(title="Item 1", is_complete=False),
                TaskChecklistItem(title="Item 2", is_complete=True),
            ]

            result = await submit_task.fn(
                task_identifier="T-CHECK-001", checklist=checklist_items
            )

            assert result["status"] == "success"
            mock_controller.update_checklist.assert_called_once()
            call_args = mock_controller.update_checklist.call_args
            assert call_args[0][2] is not None
            assert len(call_args[0][2]) == 2

    @pytest.mark.asyncio
    async def test_submit_task_update_multiple_fields(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating multiple fields simultaneously."""
        # Create real task in database
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-MULTI",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Old Title",
            identifier="T-MULTI-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with (
            patch("src.mcp_server.task_tools.TaskController") as mock_controller_class,
        ):
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            result = await submit_task.fn(
                task_identifier="T-MULTI-001",
                description="New description",
                status="IN_PROGRESS",
                title="Updated Title",
            )

            assert result["status"] == "success"
            mock_controller.update_task_description.assert_called_once()
            mock_controller.move_task_to_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_task_update_invalid_uuid(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test handling of invalid UUID formats - treated as not found."""

        # Any invalid identifier (including invalid-uuid, 123, etc) returns not_found
        result = await submit_task.fn(task_identifier="invalid-uuid", status="DONE")

        assert result["status"] == "error"
        # Invalid identifiers are treated as "not found" since they don't match any task
        assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_submit_task_update_nonexistent_task(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test handling when task doesn't exist (task not found vs validation error)."""
        with patch("src.mcp_server.task_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            # "123" is a valid string but not a valid UUID, so it returns not_found
            result = await submit_task.fn(task_identifier="123", status="DONE")

            assert result["status"] == "error"
            # When task isn't found, the error is "not_found" not "validation_error"
            assert result["error_type"] == "not_found"
