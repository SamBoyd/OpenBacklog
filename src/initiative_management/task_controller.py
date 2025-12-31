import logging
import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import ChecklistItem, ContextType, EntityType, Task, TaskStatus
from src.services.ordering_service import (
    EntityNotFoundError,
    OrderingService,
    OrderingServiceError,
)

logger = logging.getLogger(__name__)


class TaskControllerError(Exception):
    pass


class TaskNotFoundError(TaskControllerError):
    pass


class ChecklistItemData:
    """Simple data class for checklist items."""

    def __init__(self, title: str, is_complete: bool = False, order: int = 0):
        self.title = title
        self.is_complete = is_complete
        self.order = order


class TaskController:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ordering_service = OrderingService(db_session)

    def create_task(
        self,
        title: str,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        initiative_id: uuid.UUID,
        status: TaskStatus = TaskStatus.TO_DO,
        task_type: Optional[str] = None,
        description: Optional[str] = None,
        checklist: Optional[List[ChecklistItemData]] = None,
    ) -> Task:
        try:
            task = Task(
                title=title,
                user_id=user_id,
                workspace_id=workspace_id,
                initiative_id=initiative_id,
                status=status,
                type=task_type,
                description=description,
            )

            self.db.add(task)
            self.db.flush()

            # Add checklist items if provided
            if checklist:
                for item_data in checklist:
                    checklist_item = ChecklistItem(
                        title=item_data.title,
                        is_complete=item_data.is_complete,
                        order=item_data.order,
                        user_id=user_id,
                        task_id=task.id,
                    )
                    self.db.add(checklist_item)

            # Add to ordering system
            self.ordering_service.add_item(
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                item=task,
            )

            self.db.commit()
            self.db.refresh(task)

            logger.info(
                f"Created task {task.id} with title '{title}' for user {user_id}"
            )
            return task

        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to create task ordering: {e}")
            raise TaskControllerError(f"Failed to create task: {e}")
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating task: {e}")
            raise TaskControllerError(f"Failed to create task: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating task: {e}")
            raise TaskControllerError(f"Failed to create task: {e}")

    def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        try:
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == user_id)
                .first()
            )
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            deleted_count = self.ordering_service.delete_all_orderings_for_entity(
                item=task
            )

            self.db.delete(task)
            self.db.commit()

            logger.info(
                f"Deleted task {task_id} for user {user_id} (removed {deleted_count} orderings)"
            )
            return True

        except TaskNotFoundError as e:
            raise e
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to remove task ordering: {e}")
            raise TaskControllerError(f"Failed to delete task: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error deleting task: {e}")
            raise TaskControllerError(f"Failed to delete task: {e}")

    def move_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Task:
        try:
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == user_id)
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            self.ordering_service.move_item(
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                item=task,
                after=after_id,
                before=before_id,
            )

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"Moved task {task_id} for user {user_id}")
            return task

        except EntityNotFoundError as e:
            logger.error(f"Task ordering not found: {e}")
            raise TaskControllerError(f"Failed to move task: {e}")
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to move task: {e}")
            raise TaskControllerError(f"Failed to move task: {e}")
        except TaskNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error moving task: {e}")
            raise TaskControllerError(f"Failed to move task: {e}")

    def move_task_to_status(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: TaskStatus,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Task:
        try:
            task = (
                self.db.query(Task)
                .filter(Task.id == task_id, Task.user_id == user_id)
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            old_status = task.status
            task.status = new_status

            if old_status != new_status:
                self.ordering_service.move_item_across_lists(
                    src_context_type=ContextType.STATUS_LIST,
                    src_context_id=None,
                    dest_context_type=ContextType.STATUS_LIST,
                    dest_context_id=None,
                    item=task,
                    after_id=after_id,
                    before_id=before_id,
                )

            self.db.commit()
            self.db.refresh(task)

            logger.info(
                f"Moved task {task_id} from {old_status} to {new_status} for user {user_id}"
            )
            return task

        except TaskNotFoundError as e:
            raise e
        except EntityNotFoundError as e:
            logger.error(f"Task ordering not found: {e}")
            raise TaskControllerError(f"Failed to move task to status: {e}")
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to move task to status: {e}")
            raise TaskControllerError(f"Failed to move task to status: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error moving task to status: {e}")
            raise TaskControllerError(f"Failed to move task to status: {e}")

    def get_initiative_tasks(
        self, user_id: uuid.UUID, initiative_id: uuid.UUID
    ) -> list[Task]:
        """
        Get all tasks for a specific initiative.

        Args:
            user_id: The user ID to verify ownership
            initiative_id: The initiative ID to get tasks for

        Returns:
            List of Task objects for the initiative
        """
        try:
            tasks = (
                self.db.query(Task)
                .filter(
                    Task.user_id == user_id,
                    Task.initiative_id == initiative_id,
                )
                .all()
            )

            logger.info(
                f"Retrieved {len(tasks)} tasks for initiative {initiative_id} for user {user_id}"
            )
            return tasks

        except Exception as e:
            logger.error(f"Unexpected error getting initiative tasks: {e}")
            raise TaskControllerError(f"Failed to get initiative tasks: {e}")

    def get_task_details(
        self, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> Optional[Task]:
        """
        Get task details with checklist items loaded.

        Args:
            user_id: The user ID to verify ownership
            task_id: The task ID to retrieve

        Returns:
            Task object with checklist relationship loaded

        Raises:
            TaskNotFoundError: If task not found or doesn't belong to user
        """
        try:
            task = (
                self.db.query(Task)
                .filter(
                    Task.id == task_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            # Access checklist items to trigger lazy loading
            _ = task.checklist

            logger.info(
                f"Retrieved task {task_id} with {len(task.checklist)} checklist items for user {user_id}"
            )
            return task

        except TaskNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"Unexpected error getting task details: {e}")
            raise TaskControllerError(f"Failed to get task details: {e}")

    def search_tasks(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, query: str
    ) -> list[Task]:
        """
        Search tasks by title, description, and identifier using LIKE operator.

        Args:
            user_id: The user ID to filter by
            workspace_id: The workspace ID to filter by
            query: The search query string

        Returns:
            List of Task objects matching the query
        """
        try:
            search_pattern = f"%{query}%"
            tasks = (
                self.db.query(Task)
                .filter(
                    Task.user_id == user_id,
                    Task.workspace_id == workspace_id,
                )
                .filter(
                    (Task.title.ilike(search_pattern))
                    | (Task.description.ilike(search_pattern))
                    | (Task.identifier.ilike(search_pattern))
                )
                .all()
            )

            logger.info(
                f"Found {len(tasks)} tasks matching query '{query}' for user {user_id}"
            )
            return tasks

        except Exception as e:
            logger.error(f"Unexpected error searching tasks: {e}")
            raise TaskControllerError(f"Failed to search tasks: {e}")

    def update_task_description(
        self, user_id: uuid.UUID, task_id: uuid.UUID, description: str
    ) -> Task:
        """
        Update a task's description.

        Args:
            user_id: The user ID to verify ownership
            task_id: The task ID to update
            description: The new description

        Returns:
            Updated Task object

        Raises:
            TaskNotFoundError: If task not found or doesn't belong to user
        """
        try:
            task = (
                self.db.query(Task)
                .filter(
                    Task.id == task_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            task.description = description
            self.db.commit()
            self.db.refresh(task)

            logger.info(f"Updated description for task {task_id} for user {user_id}")
            return task

        except TaskNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating task description: {e}")
            raise TaskControllerError(f"Failed to update task description: {e}")

    def update_checklist(
        self, user_id: uuid.UUID, task_id: uuid.UUID, items: List[ChecklistItemData]
    ) -> Task:
        """
        Replace the entire checklist for a task.

        Args:
            user_id: The user ID to verify ownership
            task_id: The task ID to update checklist for
            items: List of ChecklistItemData objects

        Returns:
            Updated Task object with new checklist

        Raises:
            TaskNotFoundError: If task not found or doesn't belong to user
        """
        try:
            task = (
                self.db.query(Task)
                .filter(
                    Task.id == task_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            # Delete existing checklist items
            self.db.query(ChecklistItem).filter(
                ChecklistItem.task_id == task_id
            ).delete()

            # Add new checklist items
            for item_data in items:
                checklist_item = ChecklistItem(
                    title=item_data.title,
                    is_complete=item_data.is_complete,
                    order=item_data.order,
                    user_id=user_id,
                    task_id=task_id,
                )
                self.db.add(checklist_item)

            self.db.commit()
            self.db.refresh(task)

            logger.info(
                f"Updated checklist for task {task_id} with {len(items)} items for user {user_id}"
            )
            return task

        except TaskNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating checklist: {e}")
            raise TaskControllerError(f"Failed to update checklist: {e}")

    def update_checklist_item(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        item_id: uuid.UUID,
        is_complete: bool,
    ) -> ChecklistItem:
        """
        Update a single checklist item's completion status.

        Args:
            user_id: The user ID to verify ownership
            task_id: The task ID for validation
            item_id: The checklist item ID to update
            is_complete: Whether the item is complete

        Returns:
            Updated ChecklistItem object

        Raises:
            TaskControllerError: If checklist item not found or doesn't belong to user
        """
        try:
            # Verify task ownership first
            task = (
                self.db.query(Task)
                .filter(
                    Task.id == task_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found for user {user_id}")

            # Get and update the checklist item
            checklist_item = (
                self.db.query(ChecklistItem)
                .filter(
                    ChecklistItem.id == item_id,
                    ChecklistItem.task_id == task_id,
                    ChecklistItem.user_id == user_id,
                )
                .first()
            )

            if not checklist_item:
                raise TaskControllerError(
                    f"Checklist item {item_id} not found for task {task_id} and user {user_id}"
                )

            checklist_item.is_complete = is_complete
            self.db.commit()
            self.db.refresh(checklist_item)

            logger.info(
                f"Updated checklist item {item_id} to complete={is_complete} for user {user_id}"
            )
            return checklist_item

        except TaskNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating checklist item: {e}")
            raise TaskControllerError(f"Failed to update checklist item: {e}")
