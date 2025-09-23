import logging
import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import ContextType, Group, Initiative, InitiativeGroup, InitiativeStatus
from src.services.ordering_service import (
    EntityNotFoundError,
    OrderingService,
    OrderingServiceError,
)

logger = logging.getLogger(__name__)


class InitiativeControllerError(Exception):
    pass


class InitiativeNotFoundError(InitiativeControllerError):
    pass


class InitiativeController:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ordering_service = OrderingService(db_session)

    def create_initiative(
        self,
        title: str,
        description: str,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        status: InitiativeStatus = InitiativeStatus.BACKLOG,
        initiative_type: Optional[str] = None,
    ) -> Initiative:
        try:
            initiative = Initiative(
                title=title,
                description=description,
                user_id=user_id,
                workspace_id=workspace_id,
                status=status,
                type=initiative_type,
            )

            self.db.add(initiative)
            self.db.flush()

            self.ordering_service.add_item(
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                item=initiative,
            )

            self.db.commit()
            self.db.refresh(initiative)

            logger.info(
                f"Created initiative {initiative.id} with title '{title}' for user {user_id}"
            )
            return initiative

        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to create initiative ordering: {e}")
            raise InitiativeControllerError(f"Failed to create initiative: {e}")
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating initiative: {e}")
            raise InitiativeControllerError(f"Failed to create initiative: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating initiative: {e}")
            raise InitiativeControllerError(f"Failed to create initiative: {e}")

    def delete_initiative(self, initiative_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )
            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            deleted_count = self.ordering_service.delete_all_orderings_for_entity(
                item=initiative
            )

            self.db.delete(initiative)
            self.db.commit()

            logger.info(
                f"Deleted initiative {initiative_id} for user {user_id} (removed {deleted_count} orderings)"
            )
            return True

        except InitiativeNotFoundError as e:
            raise e
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to remove initiative ordering: {e}")
            raise InitiativeControllerError(f"Failed to delete initiative: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error deleting initiative: {e}")
            raise InitiativeControllerError(f"Failed to delete initiative: {e}")

    def move_initiative(
        self,
        initiative_id: uuid.UUID,
        user_id: uuid.UUID,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Initiative:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )

            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            self.ordering_service.move_item(
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                item=initiative,
                after=after_id,
                before=before_id,
            )

            self.db.commit()
            self.db.refresh(initiative)

            logger.info(f"Moved initiative {initiative_id} for user {user_id}")
            return initiative

        except EntityNotFoundError as e:
            logger.error(f"Initiative ordering not found: {e}")
            raise InitiativeControllerError(f"Failed to move initiative: {e}")
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to move initiative: {e}")
            raise InitiativeControllerError(f"Failed to move initiative: {e}")
        except InitiativeNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error moving initiative: {e}")
            raise InitiativeControllerError(f"Failed to move initiative: {e}")

    def move_initiative_to_status(
        self,
        initiative_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: InitiativeStatus,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Initiative:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )

            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            old_status = initiative.status
            initiative.status = new_status

            if old_status != new_status:
                self.ordering_service.move_item_across_lists(
                    src_context_type=ContextType.STATUS_LIST,
                    src_context_id=None,
                    dest_context_type=ContextType.STATUS_LIST,
                    dest_context_id=None,
                    item=initiative,
                    after_id=after_id,
                    before_id=before_id,
                )

            self.db.commit()
            self.db.refresh(initiative)

            logger.info(
                f"Moved initiative {initiative_id} from {old_status} to {new_status} for user {user_id}"
            )
            return initiative

        except EntityNotFoundError as e:
            logger.error(f"Initiative ordering not found: {e}")
            raise InitiativeControllerError(f"Failed to move initiative to status: {e}")
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to move initiative to status: {e}")
            raise InitiativeControllerError(f"Failed to move initiative to status: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error moving initiative to status: {e}")
            raise InitiativeControllerError(f"Failed to move initiative to status: {e}")

    def add_initiative_to_group(
        self,
        initiative_id: uuid.UUID,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Initiative:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )

            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            # Validate that the group exists and belongs to the user
            group = (
                self.db.query(Group)
                .filter(Group.id == group_id, Group.user_id == user_id)
                .first()
            )
            if not group:
                raise InitiativeControllerError(
                    f"Group {group_id} not found for user {user_id}"
                )

            # Check if relationship already exists
            existing_relationship = (
                self.db.query(InitiativeGroup)
                .filter(
                    InitiativeGroup.initiative_id == initiative_id,
                    InitiativeGroup.group_id == group_id,
                )
                .first()
            )
            if existing_relationship:
                logger.warning(
                    f"Initiative {initiative_id} is already in group {group_id}"
                )
                return initiative

            # Add ordering first
            self.ordering_service.add_item(
                context_type=ContextType.GROUP,
                context_id=group_id,
                item=initiative,
                after=after_id,
                before=before_id,
            )

            # Create the actual relationship
            initiative_group = InitiativeGroup(
                initiative_id=initiative_id,
                group_id=group_id,
                user_id=user_id,
            )
            self.db.add(initiative_group)

            self.db.commit()
            self.db.refresh(initiative)

            logger.info(
                f"Added initiative {initiative_id} to group {group_id} for user {user_id}"
            )
            return initiative

        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to add initiative to group: {e}")
            raise InitiativeControllerError(f"Failed to add initiative to group: {e}")
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error adding initiative to group: {e}")
            raise InitiativeControllerError(f"Failed to add initiative to group: {e}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error adding initiative to group: {e}")
            raise InitiativeControllerError(f"Failed to add initiative to group: {e}")

    def remove_initiative_from_group(
        self, initiative_id: uuid.UUID, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> bool:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )

            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            # Check if the relationship exists
            initiative_group = (
                self.db.query(InitiativeGroup)
                .filter(
                    InitiativeGroup.initiative_id == initiative_id,
                    InitiativeGroup.group_id == group_id,
                    InitiativeGroup.user_id == user_id,
                )
                .first()
            )

            if not initiative_group:
                logger.warning(
                    f"Initiative {initiative_id} was not in group {group_id} for user {user_id}"
                )
                return False

            # Remove ordering first
            self.ordering_service.remove_item(
                context_type=ContextType.GROUP,
                context_id=group_id,
                item=initiative,
            )

            # Delete the actual relationship
            self.db.delete(initiative_group)

            self.db.commit()

            logger.info(
                f"Removed initiative {initiative_id} from group {group_id} for user {user_id}"
            )
            return True

        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to remove initiative from group: {e}")
            raise InitiativeControllerError(
                f"Failed to remove initiative from group: {e}"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error removing initiative from group: {e}")
            raise InitiativeControllerError(
                f"Failed to remove initiative from group: {e}"
            )

    def move_initiative_in_group(
        self,
        initiative_id: uuid.UUID,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Initiative:
        try:
            initiative = (
                self.db.query(Initiative)
                .filter(Initiative.id == initiative_id, Initiative.user_id == user_id)
                .first()
            )

            if not initiative:
                raise InitiativeNotFoundError(
                    f"Initiative {initiative_id} not found for user {user_id}"
                )

            # Validate that the group exists and belongs to the user
            group = (
                self.db.query(Group)
                .filter(Group.id == group_id, Group.user_id == user_id)
                .first()
            )
            if not group:
                raise InitiativeControllerError(
                    f"Group {group_id} not found for user {user_id}"
                )

            # Check if the relationship exists
            initiative_group = (
                self.db.query(InitiativeGroup)
                .filter(
                    InitiativeGroup.initiative_id == initiative_id,
                    InitiativeGroup.group_id == group_id,
                    InitiativeGroup.user_id == user_id,
                )
                .first()
            )

            if not initiative_group:
                raise InitiativeControllerError(
                    f"Initiative {initiative_id} is not in group {group_id}"
                )

            self.ordering_service.move_item(
                context_type=ContextType.GROUP,
                context_id=group_id,
                item=initiative,
                after=after_id,
                before=before_id,
            )

            self.db.commit()
            self.db.refresh(initiative)

            logger.info(
                f"Moved initiative {initiative_id} within group {group_id} for user {user_id}"
            )
            return initiative

        except EntityNotFoundError as e:
            logger.error(f"Initiative ordering not found in group: {e}")
            raise InitiativeControllerError(f"Failed to move initiative in group: {e}")
        except OrderingServiceError as e:
            self.db.rollback()
            logger.error(f"Failed to move initiative in group: {e}")
            raise InitiativeControllerError(f"Failed to move initiative in group: {e}")
        except InitiativeNotFoundError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error moving initiative in group: {e}")
            raise InitiativeControllerError(f"Failed to move initiative in group: {e}")
