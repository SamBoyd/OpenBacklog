import uuid

import pytest
from hamcrest import assert_that, calling, equal_to, has_length, is_, not_none, raises

from src.initiative_management.task_controller import (
    ChecklistItemData,
    TaskController,
    TaskControllerError,
    TaskNotFoundError,
)
from src.models import ChecklistItem, ContextType, Ordering, Task, TaskStatus
from src.services.ordering_service import OrderingService


class TestTaskController:

    @pytest.fixture
    def controller(self, session):
        return TaskController(session)

    def test_create_task_success(
        self, controller, session, user, workspace, test_initiative
    ):
        title = "Test Task"

        result = controller.create_task(
            title=title,
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            status=TaskStatus.TO_DO,
            task_type="CODING",
        )

        # Verify task was created in database
        assert_that(result.title, equal_to(title))
        assert_that(result.user_id, equal_to(user.id))
        assert_that(result.workspace_id, equal_to(workspace.id))
        assert_that(result.initiative_id, equal_to(test_initiative.id))
        assert_that(result.status, equal_to(TaskStatus.TO_DO))
        assert_that(result.type, equal_to("CODING"))

        # Verify task exists in database
        db_task = session.query(Task).filter_by(id=result.id).first()
        assert_that(db_task, is_(not_none()))

        # Verify ordering was created
        ordering = session.query(Ordering).filter_by(task_id=result.id).first()
        assert_that(ordering, is_(not_none()))
        assert_that(ordering.context_type, equal_to(ContextType.STATUS_LIST))

    def test_create_task_with_checklist(
        self, controller, session, user, workspace, test_initiative
    ):
        checklist_items = [
            ChecklistItemData("Item 1", False, 0),
            ChecklistItemData("Item 2", True, 1),
        ]

        result = controller.create_task(
            title="Task with Checklist",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            checklist=checklist_items,
        )

        # Verify task was created
        assert_that(result.title, equal_to("Task with Checklist"))

        # Verify checklist items were created in database
        db_checklist = session.query(ChecklistItem).filter_by(task_id=result.id).all()
        assert_that(db_checklist, has_length(2))

        # Verify checklist item details
        item1 = next((item for item in db_checklist if item.title == "Item 1"), None)
        item2 = next((item for item in db_checklist if item.title == "Item 2"), None)

        assert_that(item1, is_(not_none()))
        assert_that(item1.is_complete, is_(False))
        assert_that(item1.order, equal_to(0))

        assert_that(item2, is_(not_none()))
        assert_that(item2.is_complete, is_(True))
        assert_that(item2.order, equal_to(1))

    def test_create_task_invalid_workspace(self, controller, user, test_initiative):
        fake_workspace_id = uuid.uuid4()

        assert_that(
            calling(controller.create_task).with_args(
                title="Test",
                user_id=user.id,
                workspace_id=fake_workspace_id,
                initiative_id=test_initiative.id,
            ),
            raises(TaskControllerError),
        )

    def test_delete_task_success(
        self, controller, session, user, workspace, test_initiative
    ):
        # Create a task first
        task = Task(
            title="Task to Delete",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add to ordering system
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task,
        )

        task_id = task.id
        result = controller.delete_task(task_id, user.id)

        assert_that(result, is_(True))

        # Verify task was deleted from database
        db_task = session.query(Task).filter_by(id=task_id).first()
        assert_that(db_task, is_(None))

        # Verify ordering was deleted
        ordering = session.query(Ordering).filter_by(task_id=task_id).first()
        assert_that(ordering, is_(None))

    def test_delete_task_not_found(self, controller, user):
        task_id = uuid.uuid4()

        assert_that(
            calling(controller.delete_task).with_args(task_id, user.id),
            raises(TaskNotFoundError),
        )

    def test_delete_task_wrong_user(
        self, controller, session, user, other_user, workspace, test_initiative
    ):
        # Create a task for one user
        task = Task(
            title="Task to Delete",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        session.add(task)
        session.commit()

        # Try to delete as different user
        assert_that(
            calling(controller.delete_task).with_args(task.id, other_user.id),
            raises(TaskNotFoundError),
        )

    def test_move_task_success(
        self, controller, session, user, workspace, test_initiative
    ):
        # Create two tasks
        task1 = Task(
            title="Task 1",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        task2 = Task(
            title="Task 2",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        session.add_all([task1, task2])
        session.commit()

        # Add both to ordering system
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task1,
        )
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task2,
        )

        # Move task1 after task2
        result = controller.move_task(
            task_id=task1.id,
            user_id=user.id,
            after_id=task2.id,
        )

        assert_that(result.id, equal_to(task1.id))

        # Verify ordering was updated in database
        ordering1 = session.query(Ordering).filter_by(task_id=task1.id).first()
        ordering2 = session.query(Ordering).filter_by(task_id=task2.id).first()

        assert_that(ordering1, is_(not_none()))
        assert_that(ordering2, is_(not_none()))

    def test_move_task_not_found(self, controller, user):
        task_id = uuid.uuid4()

        assert_that(
            calling(controller.move_task).with_args(task_id=task_id, user_id=user.id),
            raises(TaskNotFoundError),
        )

    def test_move_task_to_status_success(
        self, controller, session, user, workspace, test_initiative
    ):
        # Create a task
        task = Task(
            title="Task to Move",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add to ordering system
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task,
        )

        # Move to different status
        result = controller.move_task_to_status(
            task_id=task.id,
            user_id=user.id,
            new_status=TaskStatus.IN_PROGRESS,
        )

        assert_that(result.id, equal_to(task.id))
        assert_that(result.status, equal_to(TaskStatus.IN_PROGRESS))

        # Verify status was updated in database
        session.refresh(task)
        assert_that(task.status, equal_to(TaskStatus.IN_PROGRESS))

    def test_move_task_to_same_status_no_ordering_change(
        self, controller, session, user, workspace, test_initiative
    ):
        # Create a task
        task = Task(
            title="Task Same Status",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            status=TaskStatus.TO_DO,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add to ordering system
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task,
        )

        # Get original ordering
        original_ordering = session.query(Ordering).filter_by(task_id=task.id).first()
        original_position = original_ordering.position

        # Move to same status
        result = controller.move_task_to_status(
            task_id=task.id,
            user_id=user.id,
            new_status=TaskStatus.TO_DO,
        )

        assert_that(result.status, equal_to(TaskStatus.TO_DO))

        # Verify ordering didn't change (since it's the same status)
        session.refresh(original_ordering)
        assert_that(original_ordering.position, equal_to(original_position))

    def test_move_task_to_status_not_found(self, controller, user):
        task_id = uuid.uuid4()

        assert_that(
            calling(controller.move_task_to_status).with_args(
                task_id=task_id, user_id=user.id, new_status=TaskStatus.IN_PROGRESS
            ),
            raises(TaskNotFoundError),
        )

    def test_delete_task_with_multiple_orderings(
        self, controller, session, user, workspace, test_initiative
    ):
        """Test that deleting task removes all orderings (STATUS_LIST + potential GROUP orderings)."""
        # Create a task
        task = Task(
            title="Task with Multiple Orderings",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add to multiple ordering contexts
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task,
        )
        group_id1 = uuid.uuid4()
        group_id2 = uuid.uuid4()
        ordering_service.add_item(ContextType.GROUP, group_id1, task)
        ordering_service.add_item(ContextType.GROUP, group_id2, task)

        # Verify we have 3 orderings
        orderings_before = session.query(Ordering).filter_by(task_id=task.id).all()
        assert_that(orderings_before, has_length(3))

        # Delete the task
        task_id = task.id
        result = controller.delete_task(task_id, user.id)

        assert_that(result, is_(True))

        # Verify ALL orderings are deleted
        orderings_after = session.query(Ordering).filter_by(task_id=task_id).all()
        assert_that(orderings_after, has_length(0))

    def test_checklist_item_data_creation(self):
        item = ChecklistItemData("Test item", True, 1)
        assert_that(item.title, equal_to("Test item"))
        assert_that(item.is_complete, is_(True))
        assert_that(item.order, equal_to(1))

        # Test defaults
        item2 = ChecklistItemData("Another item")
        assert_that(item2.is_complete, is_(False))
        assert_that(item2.order, equal_to(0))
