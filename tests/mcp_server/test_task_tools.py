"""Unit tests for task_tools MCP tools."""

import uuid
from typing import List
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, has_entries, has_key
from sqlalchemy.orm import Session

from src.initiative_management.task_controller import TaskControllerError
from src.mcp_server.task_tools import (
    TaskChecklistItem,
    query_tasks,
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


@pytest.fixture
def mock_get_auth_context(user: User, workspace: Workspace):
    """Mock get_auth_context for MCP tools."""
    with patch("src.mcp_server.task_tools.get_auth_context") as mock_auth:
        mock_auth.return_value = (str(user.id), str(workspace.id))
        yield mock_auth


class TestQueryTasksByInitiative:
    """Test suite for query_tasks with initiative_identifier filter."""

    @pytest.fixture
    def sample_tasks(
        self, user: User, workspace: Workspace, initiative: Initiative, session: Session
    ) -> List[Task]:
        """Sample tasks for testing."""
        tasks = [
            Task(
                id=uuid.uuid4(),
                title="Task 1",
                description="Description 1",
                status=TaskStatus.TO_DO,
                initiative_id=initiative.id,
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
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                identifier="T-002",
                type="CODING",
            ),
        ]
        for task in tasks:
            session.add(task)
        session.commit()
        return tasks

    @pytest.mark.asyncio
    async def test_query_tasks_by_initiative_successful_retrieval(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_tasks: List[Task],
        mock_get_auth_context,
    ):
        """Test successful retrieval of initiative tasks."""
        result = await query_tasks.fn(initiative_identifier=initiative.identifier)

        assert_that(
            result,
            has_entries(
                {
                    "status": "success",
                    "type": "task",
                }
            ),
        )
        assert_that(result["data"], has_key("tasks"))
        assert len(result["data"]["tasks"]) == 2
        assert result["data"]["tasks"][0]["title"] == "Task 1"
        assert result["data"]["tasks"][1]["title"] == "Task 2"

    @pytest.mark.asyncio
    async def test_query_tasks_by_initiative_empty_response(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context,
    ):
        """Test handling of empty task list."""
        result = await query_tasks.fn(initiative_identifier=initiative.identifier)

        assert_that(
            result,
            has_entries(
                {
                    "status": "success",
                    "type": "task",
                }
            ),
        )
        assert_that(result["data"], has_key("tasks"))
        assert len(result["data"]["tasks"]) == 0

    @pytest.mark.asyncio
    async def test_query_tasks_by_initiative_not_found(
        self, user: User, workspace: Workspace, session: Session, mock_get_auth_context
    ):
        """Test handling when initiative is not found."""
        result = await query_tasks.fn(initiative_identifier="I-99999")

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

    @pytest.mark.asyncio
    async def test_query_tasks_by_initiative_controller_error(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context,
    ):
        """Test handling of controller error."""
        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_initiative_tasks.side_effect = TaskControllerError(
                "Controller error"
            )

            result = await query_tasks.fn(initiative_identifier=initiative.identifier)

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


class TestQueryTasksSingle:
    """Test suite for query_tasks with identifier filter (single task lookup)."""

    @pytest.fixture
    def sample_task(
        self, user: User, workspace: Workspace, initiative: Initiative, session: Session
    ) -> Task:
        """Sample task for testing."""
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.TO_DO,
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            identifier="T-123",
            type="CODING",
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @pytest.mark.asyncio
    async def test_query_tasks_single_successful_retrieval(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_task: Task,
        mock_get_auth_context,
    ):
        """Test successful retrieval of task details."""
        result = await query_tasks.fn(identifier=sample_task.identifier)

        assert_that(
            result,
            has_entries(
                {
                    "status": "success",
                    "type": "task",
                }
            ),
        )
        assert_that(result["data"], has_key("task"))
        assert_that(result["data"], has_key("checklist_items"))
        assert_that(result["data"], has_key("task_context"))
        assert result["data"]["task"]["identifier"] == sample_task.identifier

    @pytest.mark.asyncio
    async def test_query_tasks_single_includes_checklist(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_task: Task,
        mock_get_auth_context,
    ):
        """Test that task details include checklist items."""
        checklist_item = ChecklistItem(
            id=uuid.uuid4(),
            user_id=user.id,
            task_id=sample_task.id,
            title="First item",
            is_complete=False,
            order=1,
        )
        session.add(checklist_item)
        session.commit()

        result = await query_tasks.fn(identifier=sample_task.identifier)

        assert_that(result["data"], has_key("checklist_items"))
        assert len(result["data"]["checklist_items"]) == 1
        assert result["data"]["checklist_items"][0]["title"] == "First item"

    @pytest.mark.asyncio
    async def test_query_tasks_single_not_found(
        self, user: User, workspace: Workspace, session: Session, mock_get_auth_context
    ):
        """Test handling when task is not found."""
        result = await query_tasks.fn(identifier="T-99999")

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
        assert "not found" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_query_tasks_single_includes_initiative_context(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_task: Task,
        mock_get_auth_context,
    ):
        """Test that task details include initiative context."""
        result = await query_tasks.fn(identifier=sample_task.identifier)

        assert_that(result["data"], has_key("task_context"))
        assert initiative.title in result["data"]["task_context"]


class TestQueryTasksSearch:
    """Test suite for query_tasks with search filter."""

    @pytest.fixture
    def sample_search_results(
        self, user: User, workspace: Workspace, initiative: Initiative, session: Session
    ) -> List[Task]:
        """Sample search results for testing."""
        tasks = [
            Task(
                id=uuid.uuid4(),
                title="Fix authentication bug",
                description="Authentication is not working correctly",
                identifier="AUTH-123",
                user_id=user.id,
                workspace_id=workspace.id,
                initiative_id=initiative.id,
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
                initiative_id=initiative.id,
                status=TaskStatus.IN_PROGRESS,
                type="CODING",
            ),
        ]
        for task in tasks:
            session.add(task)
        session.commit()
        return tasks

    @pytest.mark.asyncio
    async def test_query_tasks_search_successful(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_search_results: List[Task],
        mock_get_auth_context,
    ):
        """Test successful task search."""
        result = await query_tasks.fn(search="authentication")

        assert_that(result, has_entries({"status": "success", "type": "task"}))
        assert_that(result["data"], has_key("tasks"))
        assert len(result["data"]["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_query_tasks_search_empty_results(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context,
    ):
        """Test search with no results."""
        result = await query_tasks.fn(search="nonexistent")

        assert_that(
            result,
            has_entries({"status": "success", "type": "task"}),
        )
        assert_that(result["data"], has_key("tasks"))
        assert len(result["data"]["tasks"]) == 0

    @pytest.mark.asyncio
    async def test_query_tasks_search_controller_error(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context,
    ):
        """Test handling of controller error during search."""
        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.search_tasks.side_effect = TaskControllerError(
                "Search failed"
            )

            result = await query_tasks.fn(search="test")

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


class TestQueryTasksNoParams:
    """Test suite for query_tasks with no parameters."""

    @pytest.mark.asyncio
    async def test_query_tasks_no_params_returns_error(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context,
    ):
        """Test that query_tasks with no params returns validation error."""
        result = await query_tasks.fn()

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
        assert "at least one filter required" in result["error_message"].lower()


class TestValidateContext:
    """Test suite for validate_context MCP tool."""

    @pytest.fixture
    def sample_task_with_checklist(
        self, user: User, workspace: Workspace, initiative: Initiative, session: Session
    ) -> Task:
        """Sample task with checklist for testing."""
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.IN_PROGRESS,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            identifier="T-123",
            type="CODING",
        )
        session.add(task)
        session.commit()

        checklist_items = [
            ChecklistItem(
                id=uuid.uuid4(),
                user_id=user.id,
                task_id=task.id,
                title="Item 1",
                is_complete=True,
                order=1,
            ),
            ChecklistItem(
                id=uuid.uuid4(),
                user_id=user.id,
                task_id=task.id,
                title="Item 2",
                is_complete=False,
                order=2,
            ),
            ChecklistItem(
                id=uuid.uuid4(),
                user_id=user.id,
                task_id=task.id,
                title="Item 3",
                is_complete=True,
                order=3,
            ),
        ]
        for item in checklist_items:
            session.add(item)
        session.commit()
        session.refresh(task)
        return task

    @pytest.mark.asyncio
    async def test_validate_context_successful_validation(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        sample_task_with_checklist: Task,
        mock_get_auth_context,
    ):
        """Test successful context validation with checklist progress."""
        task_id = str(sample_task_with_checklist.id)

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = sample_task_with_checklist

            result = await validate_context.fn(task_id)

            mock_controller.get_task_details.assert_called_once_with(
                user.id, uuid.UUID(task_id)
            )

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

            assert result["checklist_summary"]["total_items"] == 3
            assert result["checklist_summary"]["completed_items"] == 2
            completion_percentage = result["checklist_summary"]["completion_percentage"]
            assert 66.6 < completion_percentage < 66.7

    @pytest.mark.asyncio
    async def test_validate_context_task_not_found(
        self, user: User, workspace: Workspace, session: Session, mock_get_auth_context
    ):
        """Test validation when task is not found."""
        task_id = str(uuid.uuid4())

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context,
    ):
        """Test validation with empty checklist (0% completion)."""
        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.IN_PROGRESS,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
            identifier="T-EMPTY",
            type="CODING",
        )
        session.add(task)
        session.commit()
        task_id = str(task.id)

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_controller.get_task_details.return_value = task

            result = await validate_context.fn(task_id)

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

    @pytest.fixture
    def mock_get_auth_context_for_submit(self, user: User, workspace: Workspace):
        """Mock get_auth_context for submit_task tests."""
        with patch("src.mcp_server.task_tools.get_auth_context") as mock_auth:
            mock_auth.return_value = (str(user.id), str(workspace.id))
            yield mock_auth

    @pytest.mark.asyncio
    async def test_submit_task_create_minimal(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
    ):
        """Test creating task with only required fields."""
        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller

            mock_task = Mock()
            mock_task.identifier = "T-001"
            mock_task.title = "Test Task"
            mock_task.description = None
            mock_task.status.value = "TO_DO"
            mock_task.type = "CODING"
            mock_task.initiative = initiative
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
    ):
        """Test error when title is missing for create."""
        result = await submit_task.fn(initiative_identifier="I-001", title=None)

        assert result["status"] == "error"
        assert "title is required" in result["error_message"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_update_task_not_found(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test error when task_identifier doesn't exist."""
        result = await submit_task.fn(task_identifier="T-999", status="DONE")

        assert result["status"] == "error"
        assert "not found" in result["error_message"]
        assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_submit_task_create_missing_initiative_identifier(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
    ):
        """Test error when initiative_identifier is missing for create."""
        result = await submit_task.fn(title="New Task")

        assert result["status"] == "error"
        assert "initiative_identifier is required" in result["error_message"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_create_with_all_optional_params(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
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
            mock_task.title = "Test Task"
            mock_task.description = "Detailed description"
            mock_task.status.value = "IN_PROGRESS"
            mock_task.type = "TESTING"
            mock_task.initiative = initiative
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
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
            mock_task.title = "Task with Checklist"
            mock_task.description = None
            mock_task.status.value = "TO_DO"
            mock_task.type = None
            mock_task.initiative = initiative
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        mock_get_auth_context_for_submit,
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

    @pytest.mark.asyncio
    async def test_submit_task_update_status_to_in_progress(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test updating task status to IN_PROGRESS."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-STAT",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-STAT-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test error when invalid status is provided during update."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-INVSTAT",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-INVSTAT-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        result = await submit_task.fn(
            task_identifier="T-INVSTAT-001", status="INVALID_STATUS"
        )

        assert result["status"] == "error"
        assert "Invalid status" in result["error_message"]
        assert "INVALID_STATUS" in result["error_message"]
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_submit_task_update_status_controller_error(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test handling of controller error during status update."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-ERR",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-ERR-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test updating task title only."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-TITLE",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Old Title",
            identifier="T-TITLE-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        result = await submit_task.fn(
            task_identifier="T-TITLE-001", title="Updated Title"
        )

        assert result["status"] == "success"
        assert result["data"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_submit_task_update_type(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test updating task type only."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-TYPE",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-TYPE-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
            type="CODING",
        )
        session.add(task)
        session.commit()

        result = await submit_task.fn(task_identifier="T-TYPE-001", task_type="TESTING")

        assert result["status"] == "success"
        assert result["data"]["type"] == "TESTING"

    @pytest.mark.asyncio
    async def test_submit_task_update_checklist(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test replacing task checklist."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-CHECK",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Test Task",
            identifier="T-CHECK-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
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
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test updating multiple fields simultaneously."""
        local_initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            identifier="I-UPD-MULTI",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(local_initiative)
        session.commit()

        task = Task(
            id=uuid.uuid4(),
            title="Old Title",
            identifier="T-MULTI-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=local_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()

        with patch("src.mcp_server.task_tools.TaskController") as mock_controller_class:
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
    async def test_submit_task_update_invalid_identifier(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test handling of invalid identifier - treated as not found."""
        result = await submit_task.fn(task_identifier="invalid-uuid", status="DONE")

        assert result["status"] == "error"
        assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_submit_task_update_nonexistent_task(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context_for_submit,
    ):
        """Test handling when task doesn't exist."""
        result = await submit_task.fn(task_identifier="T-NONEXISTENT", status="DONE")

        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
