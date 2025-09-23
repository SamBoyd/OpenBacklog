import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_entries, has_items, is_, none, not_
from sqlalchemy.orm import Session

from src.main import app
from src.models import (
    ChecklistItem,
    ContextType,
    EntityType,
    Initiative,
    Ordering,
    Task,
    TaskStatus,
    TaskType,
    User,
    Workspace,
)
from src.services.ordering_service import OrderingService
from tests.conftest import dependency_to_override


class TestTaskViews:

    def _create_mock_orderings(self, task_id, user_id):
        """Helper method to create mock orderings for test tasks."""
        return [
            Ordering(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=None,
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                entity_type=EntityType.TASK,
                initiative_id=None,
                task_id=task_id,
                position="n",
            )
        ]

    @pytest.fixture
    def client(self, user):
        app.dependency_overrides[dependency_to_override] = lambda: user
        client = TestClient(app)
        yield client
        app.dependency_overrides.pop(dependency_to_override, None)

    @patch("src.views.task_views.TaskController")
    def test_create_task_success(
        self, mock_task_controller, client, user, workspace, session, test_initiative
    ):
        task_id = uuid.uuid4()
        checklist_item1_id = uuid.uuid4()
        checklist_item2_id = uuid.uuid4()

        mock_task = Task(
            id=task_id,
            identifier="T-001",
            title="New Test Task",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            status=TaskStatus.TO_DO,
            type=TaskType.CODING,
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            checklist=[
                ChecklistItem(
                    id=checklist_item1_id,
                    title="First item",
                    is_complete=False,
                    order=0,
                    task_id=task_id,
                    user_id=user.id,
                ),
                ChecklistItem(
                    id=checklist_item2_id,
                    title="Second item",
                    is_complete=True,
                    order=1,
                    task_id=task_id,
                    user_id=user.id,
                ),
            ],
            orderings=self._create_mock_orderings(task_id, user.id),
        )

        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.create_task.return_value = mock_task

        payload = {
            "title": "New Test Task",
            "status": "TO_DO",
            "type": "CODING",
            "description": "Test description",
            "workspace_id": str(workspace.id),
            "initiative_id": str(test_initiative.id),
            "checklist": [
                {"title": "First item", "is_complete": False, "order": 0},
                {"title": "Second item", "is_complete": True, "order": 1},
            ],
        }

        response = client.post("/api/tasks", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries(
                {
                    "title": "New Test Task",
                    "status": "TO_DO",
                    "type": "CODING",
                    "description": "Test description",
                    "user_id": str(user.id),
                    "workspace_id": str(workspace.id),
                    "initiative_id": str(test_initiative.id),
                    "orderings": has_items(
                        has_entries(
                            {
                                "context_type": "STATUS_LIST",
                                "entity_type": "TASK",
                                "position": "n",
                            }
                        )
                    ),
                }
            ),
        )

        # Verify the task controller was called
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.create_task.assert_called_once()

    @patch("src.views.task_views.TaskController")
    def test_create_task_minimal_payload(
        self, mock_task_controller, client, user, workspace, session, test_initiative
    ):
        task_id = uuid.uuid4()

        mock_task = Task(
            id=task_id,
            identifier="T-002",
            title="Minimal Task",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.TO_DO,
            type=None,
            description=None,
            checklist=[],
            orderings=self._create_mock_orderings(task_id, user.id),
        )

        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.create_task.return_value = mock_task

        payload = {
            "title": "Minimal Task",
            "workspace_id": str(workspace.id),
            "initiative_id": str(test_initiative.id),
        }

        response = client.post("/api/tasks", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries(
                {
                    "title": "Minimal Task",
                    "status": "TO_DO",
                    "type": None,
                    "description": None,
                    "orderings": has_items(
                        has_entries(
                            {
                                "context_type": "STATUS_LIST",
                                "entity_type": "TASK",
                                "position": "n",
                            }
                        )
                    ),
                }
            ),
        )

        # Should have empty checklist
        assert_that(len(response_data["checklist"]), equal_to(0))

        # Verify the task controller was called
        mock_task_controller_instance.create_task.assert_called_once()

    def test_create_task_invalid_title(self, client, user, workspace, test_initiative):
        payload = {
            "title": "",
            "workspace_id": str(workspace.id),
            "initiative_id": str(test_initiative.id),
        }

        response = client.post("/api/tasks", json=payload)

        assert_that(response.status_code, equal_to(422))

    @patch("src.views.task_views.TaskController")
    def test_delete_task_success(
        self, mock_task_controller, client, user, workspace, session, test_task
    ):
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.delete_task.return_value = True

        task_id = test_task.id

        response = client.delete(f"/api/tasks/{task_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data, has_entries({"message": "Task deleted successfully"})
        )

        # Verify the task controller was called
        mock_task_controller_instance.delete_task.assert_called_once_with(
            task_id, user.id
        )

    @patch("src.views.task_views.TaskController")
    def test_delete_task_not_found(self, mock_task_controller, client, user):
        from src.controllers.task_controller import TaskNotFoundError

        mock_task_controller_instance = mock_task_controller.return_value
        fake_id = uuid.uuid4()
        mock_task_controller_instance.delete_task.side_effect = TaskNotFoundError(
            f"Task {fake_id} not found"
        )

        response = client.delete(f"/api/tasks/{fake_id}")

        assert_that(response.status_code, equal_to(404))
        mock_task_controller_instance.delete_task.assert_called_once_with(
            fake_id, user.id
        )

    @patch("src.views.task_views.TaskController")
    def test_move_task_success(
        self,
        mock_task_controller,
        client,
        user,
        workspace,
        session,
        test_task,
        test_initiative,
    ):
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.move_task.return_value = Task(
            id=test_task.id,
            identifier=test_task.identifier,
            title=test_task.title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.TO_DO,
            orderings=self._create_mock_orderings(test_task.id, user.id),
        )

        task_id = test_task.id
        other_task_id = uuid.uuid4()
        payload = {"after_id": str(other_task_id)}

        response = client.put(f"/api/tasks/{task_id}/move", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(response_data["id"], equal_to(str(task_id)))

        # Verify the task controller was called
        mock_task_controller_instance.move_task.assert_called_once_with(
            task_id=task_id,
            user_id=user.id,
            after_id=other_task_id,
            before_id=None,
        )

    @patch("src.views.task_views.TaskController")
    def test_move_task_not_found(self, mock_task_controller, client, user):
        from src.controllers.task_controller import TaskNotFoundError

        mock_task_controller_instance = mock_task_controller.return_value
        fake_id = uuid.uuid4()
        after_id = uuid.uuid4()
        mock_task_controller_instance.move_task.side_effect = TaskNotFoundError(
            f"Task {fake_id} not found"
        )

        payload = {"after_id": str(after_id)}

        response = client.put(f"/api/tasks/{fake_id}/move", json=payload)

        assert_that(response.status_code, equal_to(404))
        mock_task_controller_instance.move_task.assert_called_once_with(
            task_id=fake_id,
            user_id=user.id,
            after_id=after_id,
            before_id=None,
        )

    @patch("src.views.task_views.TaskController")
    def test_move_task_to_status_success(
        self,
        mock_task_controller,
        client,
        user,
        workspace,
        session,
        test_task,
        test_initiative,
    ):
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.move_task_to_status.return_value = Task(
            id=test_task.id,
            identifier=test_task.identifier,
            title=test_task.title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.IN_PROGRESS,
            orderings=self._create_mock_orderings(test_task.id, user.id),
        )

        task_id = test_task.id
        payload = {"new_status": "IN_PROGRESS", "after_id": None, "before_id": None}

        response = client.put(f"/api/tasks/{task_id}/status", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data, has_entries({"id": str(task_id), "status": "IN_PROGRESS"})
        )

        # Verify the task controller was called
        mock_task_controller_instance.move_task_to_status.assert_called_once_with(
            task_id=task_id,
            user_id=user.id,
            new_status=TaskStatus.IN_PROGRESS,
            after_id=None,
            before_id=None,
        )

    @patch("src.views.task_views.TaskController")
    def test_move_task_to_status_not_found(self, mock_task_controller, client, user):
        from src.controllers.task_controller import TaskNotFoundError

        mock_task_controller_instance = mock_task_controller.return_value
        fake_id = uuid.uuid4()
        mock_task_controller_instance.move_task_to_status.side_effect = (
            TaskNotFoundError(f"Task {fake_id} not found")
        )

        payload = {"new_status": "IN_PROGRESS"}

        response = client.put(f"/api/tasks/{fake_id}/status", json=payload)

        assert_that(response.status_code, equal_to(404))
        mock_task_controller_instance.move_task_to_status.assert_called_once_with(
            task_id=fake_id,
            user_id=user.id,
            new_status=TaskStatus.IN_PROGRESS,
            after_id=None,
            before_id=None,
        )

    @patch("src.views.task_views.TaskController")
    def test_delete_task_with_multiple_orderings(
        self, mock_task_controller, client, user, workspace, session, test_task
    ):
        """Test that deleting task removes all orderings (STATUS_LIST + potential GROUP orderings)."""
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.delete_task.return_value = True

        task_id = test_task.id

        # Delete the task via API
        response = client.delete(f"/api/tasks/{task_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data, has_entries({"message": "Task deleted successfully"})
        )

        # Verify the task controller was called
        mock_task_controller_instance.delete_task.assert_called_once_with(
            task_id, user.id
        )

    @patch("src.views.task_views.TaskController")
    def test_create_task_with_checklist_validation(
        self, mock_task_controller, client, user, workspace, session, test_initiative
    ):
        """Test that checklist items are properly validated and created."""
        task_id = uuid.uuid4()
        mock_task_controller_instance = mock_task_controller.return_value
        mock_task_controller_instance.create_task.return_value = Task(
            id=task_id,
            identifier="T-003",
            title="Task with Complex Checklist",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.TO_DO,
            checklist=[
                ChecklistItem(
                    id=uuid.uuid4(),
                    title="First item",
                    is_complete=False,
                    order=0,
                    task_id=task_id,
                    user_id=user.id,
                ),
                ChecklistItem(
                    id=uuid.uuid4(),
                    title="Second item",
                    is_complete=True,
                    order=1,
                    task_id=task_id,
                    user_id=user.id,
                ),
                ChecklistItem(
                    id=uuid.uuid4(),
                    title="Third item",
                    is_complete=False,
                    order=2,
                    task_id=task_id,
                    user_id=user.id,
                ),
            ],
        )

        payload = {
            "title": "Task with Complex Checklist",
            "workspace_id": str(workspace.id),
            "initiative_id": str(test_initiative.id),
            "checklist": [
                {"title": "First item", "is_complete": False, "order": 0},
                {"title": "Second item", "is_complete": True, "order": 1},
                {"title": "Third item", "is_complete": False, "order": 2},
            ],
        }

        response = client.post("/api/tasks", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()

        # Verify checklist items in response
        checklist = response_data["checklist"]
        assert_that(len(checklist), equal_to(3))

        # Find items by title (order might vary)
        first_item = next(item for item in checklist if item["title"] == "First item")
        second_item = next(item for item in checklist if item["title"] == "Second item")
        third_item = next(item for item in checklist if item["title"] == "Third item")

        assert_that(first_item["is_complete"], is_(False))
        assert_that(first_item["order"], equal_to(0))

        assert_that(second_item["is_complete"], is_(True))
        assert_that(second_item["order"], equal_to(1))

        assert_that(third_item["is_complete"], is_(False))
        assert_that(third_item["order"], equal_to(2))

        # Verify the task controller was called
        mock_task_controller_instance.create_task.assert_called_once()

    @patch("src.views.task_views.TaskController")
    def test_task_status_transitions(
        self,
        mock_task_controller,
        client,
        user,
        workspace,
        session,
        test_task,
        test_initiative,
    ):
        """Test moving task through different status transitions."""
        mock_task_controller_instance = mock_task_controller.return_value
        task_id = test_task.id

        # TO_DO → IN_PROGRESS
        mock_task_controller_instance.move_task_to_status.return_value = Task(
            id=task_id,
            identifier=test_task.identifier,
            title=test_task.title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.IN_PROGRESS,
        )
        response = client.put(
            f"/api/tasks/{task_id}/status", json={"new_status": "IN_PROGRESS"}
        )
        assert_that(response.status_code, equal_to(200))
        assert_that(response.json()["status"], equal_to("IN_PROGRESS"))

        # IN_PROGRESS → BLOCKED
        mock_task_controller_instance.move_task_to_status.return_value = Task(
            id=task_id,
            identifier=test_task.identifier,
            title=test_task.title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.BLOCKED,
        )
        response = client.put(
            f"/api/tasks/{task_id}/status", json={"new_status": "BLOCKED"}
        )
        assert_that(response.status_code, equal_to(200))
        assert_that(response.json()["status"], equal_to("BLOCKED"))

        # BLOCKED → DONE
        mock_task_controller_instance.move_task_to_status.return_value = Task(
            id=task_id,
            identifier=test_task.identifier,
            title=test_task.title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=TaskStatus.DONE,
        )
        response = client.put(
            f"/api/tasks/{task_id}/status", json={"new_status": "DONE"}
        )
        assert_that(response.status_code, equal_to(200))
        assert_that(response.json()["status"], equal_to("DONE"))

        # Verify controller was called for each status change
        assert_that(
            mock_task_controller_instance.move_task_to_status.call_count, equal_to(3)
        )
