"""Unit tests for checklist_tools MCP tools."""

import uuid
from unittest.mock import patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.initiative_management.task_controller import (
    ChecklistItemData,
    TaskNotFoundError,
)
from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.checklist_tools import (
    ChecklistItem,
    update_checklist,
    update_checklist_item,
)
from src.models import ChecklistItem as ChecklistItemModel
from src.models import Initiative, Task, User, Workspace


class TestUpdateChecklist:
    """Test suite for update_checklist MCP tool."""

    @pytest.fixture
    def initiative(self, session, user: User, workspace: Workspace):
        """Create a test initiative."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)
        yield initiative

    @pytest.fixture
    def task(self, session, user: User, workspace: Workspace, initiative: Initiative):
        """Create a test task."""
        task = Task(
            title="Test Task",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        yield task

    @pytest.fixture
    def sample_checklist_items(self):
        """Sample checklist items for testing."""
        return [
            ChecklistItem(title="First task", is_complete=False),
            ChecklistItem(title="Second task", is_complete=True),
            ChecklistItem(title="Third task", is_complete=False),
        ]

    @pytest.mark.asyncio
    async def test_update_checklist_successful(
        self, session, user: User, task: Task, sample_checklist_items
    ):
        """Test successful checklist update with all items created."""
        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist.fn(str(task.id), sample_checklist_items)

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "checklist_update",
                        "task_id": str(task.id),
                    }
                ),
            )

            # Verify created_items is a list with 3 items
            assert len(result["created_items"]) == 3

            # Verify items were actually created in database
            items = (
                session.query(ChecklistItemModel)
                .filter(ChecklistItemModel.task_id == task.id)
                .order_by(ChecklistItemModel.order)
                .all()
            )
            assert len(items) == 3
            assert items[0].title == "First task"
            assert items[1].title == "Second task"
            assert items[2].title == "Third task"

    @pytest.mark.asyncio
    async def test_update_checklist_replaces_existing_items(
        self, session, user: User, task: Task
    ):
        """Test that update_checklist replaces existing checklist items."""
        # Create initial checklist items
        initial_items = [
            ChecklistItemModel(
                title="Old item 1",
                is_complete=False,
                order=0,
                user_id=user.id,
                task_id=task.id,
            ),
            ChecklistItemModel(
                title="Old item 2",
                is_complete=True,
                order=1,
                user_id=user.id,
                task_id=task.id,
            ),
        ]
        for item in initial_items:
            session.add(item)
        session.commit()

        # Update with new items
        new_items = [
            ChecklistItem(title="New item 1", is_complete=False),
            ChecklistItem(title="New item 2", is_complete=False),
            ChecklistItem(title="New item 3", is_complete=False),
        ]

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist.fn(str(task.id), new_items)

            assert_that(result["status"], equal_to("success"))
            assert len(result["created_items"]) == 3

            # Verify old items were deleted and new ones created
            items = (
                session.query(ChecklistItemModel)
                .filter(ChecklistItemModel.task_id == task.id)
                .all()
            )
            assert len(items) == 3
            titles = [item.title for item in items]
            assert "Old item 1" not in titles
            assert "Old item 2" not in titles
            assert "New item 1" in titles
            assert "New item 2" in titles
            assert "New item 3" in titles

    @pytest.mark.asyncio
    async def test_update_checklist_empty_list(self, session, user: User, task: Task):
        """Test update_checklist with empty checklist items."""
        # Create initial items
        initial_item = ChecklistItemModel(
            title="Old item",
            is_complete=False,
            order=0,
            user_id=user.id,
            task_id=task.id,
        )
        session.add(initial_item)
        session.commit()

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist.fn(str(task.id), [])

            # Should delete existing items and create no new ones
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

            # Verify all items were deleted
            items = (
                session.query(ChecklistItemModel)
                .filter(ChecklistItemModel.task_id == task.id)
                .all()
            )
            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_update_checklist_task_not_found(self, session, user: User):
        """Test update_checklist with non-existent task."""
        non_existent_task_id = str(uuid.uuid4())
        items = [ChecklistItem(title="Test", is_complete=False)]

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist.fn(non_existent_task_id, items)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_update",
                        "error_type": "not_found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_wrong_user(
        self, session, user: User, other_user: User, workspace: Workspace
    ):
        """Test update_checklist fails when task belongs to different user."""
        # Create initiative for other_user
        other_initiative = Initiative(
            title="Other User's Initiative",
            description="Test",
            user_id=other_user.id,
            workspace_id=workspace.id,
        )
        session.add(other_initiative)
        session.commit()
        session.refresh(other_initiative)

        # Create task belonging to other_user
        other_task = Task(
            title="Other User's Task",
            description="Test",
            user_id=other_user.id,
            workspace_id=workspace.id,
            initiative_id=other_initiative.id,
        )
        session.add(other_task)
        session.commit()
        session.refresh(other_task)

        items = [ChecklistItem(title="Test", is_complete=False)]

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            # user fixture from conftest is mocked in get_auth_context
            result = await update_checklist.fn(str(other_task.id), items)

            # Should fail because task belongs to other_user
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "error_type": "not_found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_invalid_task_id(self, session, user: User):
        """Test update_checklist with invalid UUID format."""
        items = [ChecklistItem(title="Test", is_complete=False)]

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist.fn("not-a-uuid", items)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_update",
                        "error_type": "validation_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_auth_error(self, session, task: Task):
        """Test update_checklist with authentication error."""
        items = [ChecklistItem(title="Test", is_complete=False)]

        with (
            patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.checklist_tools.get_auth_context") as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError(
                "No access token found", error_type="auth_error"
            )

            result = await update_checklist.fn(str(task.id), items)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_update",
                        "error_type": "auth_error",
                    }
                ),
            )


class TestUpdateChecklistItem:
    """Test suite for update_checklist_item MCP tool."""

    @pytest.fixture
    def initiative(self, session, user: User, workspace: Workspace):
        """Create a test initiative."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)
        yield initiative

    @pytest.fixture
    def task(self, session, user: User, workspace: Workspace, initiative: Initiative):
        """Create a test task."""
        task = Task(
            title="Test Task",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=initiative.id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        yield task

    @pytest.fixture
    def checklist_item(self, session, user: User, task: Task):
        """Create a test checklist item."""
        item = ChecklistItemModel(
            title="Test Item",
            is_complete=False,
            order=0,
            user_id=user.id,
            task_id=task.id,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        yield item

    @pytest.mark.asyncio
    async def test_update_checklist_item_mark_complete(
        self, session, user: User, task: Task, checklist_item: ChecklistItemModel
    ):
        """Test marking a checklist item as complete."""
        task_id = str(task.id)
        item_id = str(checklist_item.id)

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(task_id, item_id, True)

            # Verify successful result
            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "type": "checklist_item_update",
                        "message": "Successfully marked checklist item as complete",
                        "task_id": task_id,
                        "item_id": item_id,
                        "is_complete": True,
                    }
                ),
            )

            # Verify item was updated in database
            updated_item = (
                session.query(ChecklistItemModel)
                .filter(ChecklistItemModel.id == checklist_item.id)
                .first()
            )
            assert updated_item.is_complete is True

    @pytest.mark.asyncio
    async def test_update_checklist_item_mark_incomplete(
        self, session, user: User, task: Task, checklist_item: ChecklistItemModel
    ):
        """Test marking a completed item as incomplete."""
        # Set item as complete first
        checklist_item.is_complete = True
        session.commit()

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(
                str(task.id), str(checklist_item.id), False
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "success",
                        "message": "Successfully marked checklist item as incomplete",
                        "is_complete": False,
                    }
                ),
            )

            # Verify item was updated
            updated_item = (
                session.query(ChecklistItemModel)
                .filter(ChecklistItemModel.id == checklist_item.id)
                .first()
            )
            assert updated_item.is_complete is False

    @pytest.mark.asyncio
    async def test_update_checklist_item_not_found(
        self, session, user: User, task: Task
    ):
        """Test updating non-existent checklist item."""
        non_existent_item_id = str(uuid.uuid4())

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(
                str(task.id), non_existent_item_id, True
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_type": "controller_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_task_not_found(
        self, session, user: User, checklist_item: ChecklistItemModel
    ):
        """Test updating checklist item with non-existent task."""
        non_existent_task_id = str(uuid.uuid4())

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(
                non_existent_task_id, str(checklist_item.id), True
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_type": "not_found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_wrong_user(
        self, session, user: User, other_user: User, workspace: Workspace
    ):
        """Test update_checklist_item fails when task belongs to different user."""
        # Create initiative for other_user
        other_initiative = Initiative(
            title="Other User's Initiative",
            description="Test",
            user_id=other_user.id,
            workspace_id=workspace.id,
        )
        session.add(other_initiative)
        session.commit()
        session.refresh(other_initiative)

        # Create task and item belonging to other_user
        other_task = Task(
            title="Other User's Task",
            description="Test",
            user_id=other_user.id,
            workspace_id=workspace.id,
            initiative_id=other_initiative.id,
        )
        session.add(other_task)
        session.commit()
        session.refresh(other_task)

        other_item = ChecklistItemModel(
            title="Other User's Item",
            is_complete=False,
            order=0,
            user_id=other_user.id,
            task_id=other_task.id,
        )
        session.add(other_item)
        session.commit()
        session.refresh(other_item)

        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            # user fixture from conftest is mocked in get_auth_context
            result = await update_checklist_item.fn(
                str(other_task.id), str(other_item.id), True
            )

            # Should fail because task belongs to other_user
            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "error_type": "not_found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_invalid_task_id(
        self, session, user: User, checklist_item: ChecklistItemModel
    ):
        """Test update_checklist_item with invalid task UUID format."""
        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(
                "not-a-uuid", str(checklist_item.id), True
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_type": "validation_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_invalid_item_id(
        self, session, user: User, task: Task
    ):
        """Test update_checklist_item with invalid item UUID format."""
        with patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await update_checklist_item.fn(str(task.id), "not-a-uuid", True)

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_type": "validation_error",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_update_checklist_item_auth_error(
        self, session, task: Task, checklist_item: ChecklistItemModel
    ):
        """Test update_checklist_item with authentication error."""
        with (
            patch("src.mcp_server.checklist_tools.SessionLocal") as mock_session_local,
            patch("src.mcp_server.checklist_tools.get_auth_context") as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError(
                "No access token found", error_type="auth_error"
            )

            result = await update_checklist_item.fn(
                str(task.id), str(checklist_item.id), True
            )

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "checklist_item_update",
                        "error_type": "auth_error",
                    }
                ),
            )
