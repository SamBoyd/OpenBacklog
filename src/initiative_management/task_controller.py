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
