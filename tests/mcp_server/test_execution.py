"""Unit tests for execution MCP server tools.

Tests verify that the execution-mode tools work correctly:
- query_strategic_initiatives
- submit_strategic_initiative (update-only)
- query_tasks
- submit_task (update-only)
- get_strategic_context_summary

The execution server only supports updates, not creation of new entities.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, has_key
from sqlalchemy.orm import Session

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.initiative_management.initiative_controller import InitiativeController
from src.initiative_management.task_controller import TaskController
from src.mcp_server.execution import (
    get_strategic_context_summary,
    query_strategic_initiatives,
    query_tasks,
    submit_strategic_initiative,
    submit_task,
)
from src.mcp_server.task_tools import TaskChecklistItem
from src.models import Initiative, InitiativeStatus, Task, TaskStatus, User, Workspace


@pytest.fixture
def initiative(user: User, workspace: Workspace, session: Session) -> Initiative:
    """Sample initiative for testing."""
    controller = InitiativeController(session)
    initiative = controller.create_initiative(
        user_id=user.id,
        workspace_id=workspace.id,
        title="User Authentication System",
        description="Implement secure user authentication",
        status=InitiativeStatus.IN_PROGRESS,
    )

    session.add(initiative)
    session.commit()

    return initiative


@pytest.fixture
def strategic_initiative(
    user: User, workspace: Workspace, initiative: Initiative, session: Session
) -> StrategicInitiative:
    """Sample strategic initiative for testing."""
    strategic_initiative = StrategicInitiative.define_strategic_context(
        session=session,
        publisher=MagicMock(),
        initiative_id=initiative.id,
        workspace_id=workspace.id,
        user_id=user.id,
        pillar_id=None,
        theme_id=None,
        description="Test Description",
        narrative_intent="Test Narrative Intent",
    )
    session.add(strategic_initiative)
    session.commit()
    return strategic_initiative


@pytest.fixture
def task(
    user: User, workspace: Workspace, initiative: Initiative, session: Session
) -> Task:
    """Sample task for testing."""
    controller = TaskController(session)
    task = controller.create_task(
        title="Test Task",
        description="Test Description",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=initiative.id,
        status=TaskStatus.TO_DO,
        task_type="CODING",
    )
    return task


@pytest.fixture
def mock_get_auth_context(user: User, workspace: Workspace):
    """Mock get_auth_context for execution MCP tools."""
    with (
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_auth_initiatives,
        patch("src.mcp_server.task_tools.get_auth_context") as mock_auth_tasks,
    ):
        mock_auth_initiatives.return_value = (str(user.id), str(workspace.id))
        mock_auth_tasks.return_value = (str(user.id), str(workspace.id))
        yield


class TestQueryStrategicInitiatives:
    """Test suite for query_strategic_initiatives tool."""

    @pytest.mark.asyncio
    async def test_query_all_initiatives(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        strategic_initiative: StrategicInitiative,
        mock_get_auth_context: MagicMock,
    ):
        """Test querying all initiatives."""
        result = await query_strategic_initiatives.fn()

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("strategic_initiatives"))

    @pytest.mark.asyncio
    async def test_query_single_initiative(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        strategic_initiative: StrategicInitiative,
        mock_get_auth_context: MagicMock,
    ):
        """Test querying a single initiative by identifier."""
        result = await query_strategic_initiatives.fn(identifier=initiative.identifier)

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("initiative"))

    @pytest.mark.asyncio
    async def test_query_by_status(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        strategic_initiative: StrategicInitiative,
        mock_get_auth_context: MagicMock,
    ):
        """Test querying initiatives by status."""
        result = await query_strategic_initiatives.fn(status="IN_PROGRESS")

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))


class TestSubmitStrategicInitiative:
    """Test suite for submit_strategic_initiative tool (update-only)."""

    @pytest.mark.asyncio
    async def test_update_initiative_status(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        strategic_initiative: StrategicInitiative,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating initiative status."""
        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
            status="TO_DO",
        )

        assert_that(result, has_key("status"))
        # Verify the update was successful
        session.refresh(initiative)
        assert initiative.status == InitiativeStatus.TO_DO

    @pytest.mark.asyncio
    async def test_update_initiative_title(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        strategic_initiative: StrategicInitiative,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating initiative title."""
        new_title = "Updated Initiative Title"
        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
            title=new_title,
        )

        assert_that(result, has_key("status"))
        session.refresh(initiative)
        assert initiative.title == new_title

    @pytest.mark.asyncio
    async def test_update_nonexistent_initiative(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating a non-existent initiative returns error."""
        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier="I-99999",
            status="TO_DO",
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "error"
        assert_that(result, has_key("error_message"))


class TestQueryTasks:
    """Test suite for query_tasks tool."""

    @pytest.mark.asyncio
    async def test_query_tasks_by_initiative(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        initiative: Initiative,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test querying tasks by initiative identifier."""
        result = await query_tasks.fn(initiative_identifier=initiative.identifier)

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("tasks"))
        assert len(result["data"]["tasks"]) >= 1

    @pytest.mark.asyncio
    async def test_query_single_task(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test querying a single task by identifier."""
        result = await query_tasks.fn(identifier=task.identifier)

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("task"))
        assert result["data"]["task"]["identifier"] == task.identifier

    @pytest.mark.asyncio
    async def test_query_tasks_search(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test searching tasks by text."""
        result = await query_tasks.fn(search="Test")

        assert_that(result, has_key("status"))
        assert_that(result, has_key("data"))


class TestSubmitTask:
    """Test suite for submit_task tool (update-only)."""

    @pytest.mark.asyncio
    async def test_update_task_status(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating task status."""
        result = await submit_task.fn(
            task_identifier=task.identifier,
            status="IN_PROGRESS",
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "success"
        session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_task_title(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating task title."""
        new_title = "Updated Task Title"
        result = await submit_task.fn(
            task_identifier=task.identifier,
            title=new_title,
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "success"
        session.refresh(task)
        assert task.title == new_title

    @pytest.mark.asyncio
    async def test_update_task_description(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating task description."""
        new_description = "Updated task description"
        result = await submit_task.fn(
            task_identifier=task.identifier,
            description=new_description,
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_update_task_checklist(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating task checklist."""
        checklist = [
            TaskChecklistItem(title="Item 1", is_complete=False),
            TaskChecklistItem(title="Item 2", is_complete=True),
        ]
        result = await submit_task.fn(
            task_identifier=task.identifier,
            checklist=checklist,
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating a non-existent task returns error."""
        result = await submit_task.fn(
            task_identifier="T-99999",
            status="IN_PROGRESS",
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "error"
        assert_that(result, has_key("error_type"))
        assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_update_task_invalid_status(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        task: Task,
        mock_get_auth_context: MagicMock,
    ):
        """Test updating task with invalid status returns error."""
        result = await submit_task.fn(
            task_identifier=task.identifier,
            status="INVALID_STATUS",
        )

        assert_that(result, has_key("status"))
        assert result["status"] == "error"
        assert_that(result, has_key("error_type"))


class TestGetStrategicContextSummary:
    """Test suite for get_strategic_context_summary tool."""

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
        mock_get_auth_context: MagicMock,
    ):
        """Test retrieving strategic context summary."""
        with patch(
            "src.mcp_server.execution._get_strategic_context_summary_impl"
        ) as mock_impl:
            mock_impl.return_value = "# Strategic Context\n\nThis is a test summary."
            result = await get_strategic_context_summary.fn()

            assert isinstance(result, str)
            assert "Strategic Context" in result
            mock_impl.assert_called_once()
