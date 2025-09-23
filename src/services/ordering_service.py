import uuid
from typing import Optional, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import ContextType, EntityType, Initiative, Ordering, Task
from src.utils.lexorank import LexoRank


class OrderingServiceError(Exception):
    """Base exception for ordering service errors."""

    pass


class InvalidContextError(OrderingServiceError):
    """Raised when context type or ID is invalid."""

    pass


class EntityNotFoundError(OrderingServiceError):
    """Raised when referenced entity is not found."""

    pass


class OrderingService:
    """
    Service for managing LexoRank ordering of tasks and initiatives.

    This is the single source of truth for all ordering operations,
    ensuring consistent position calculations and database mutations.
    """

    def __init__(self, db_session: Session):
        """
        Initialize the ordering service with a database session.

        Args:
            db_session: SQLAlchemy database session for operations
        """
        self.db = db_session

    def add_item(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        item: Union[Task, Initiative],
        after: Optional[Union[Task, Initiative, uuid.UUID]] = None,
        before: Optional[Union[Task, Initiative, uuid.UUID]] = None,
    ) -> Ordering:
        """
        Add an item to an ordered list with calculated position.

        Args:
            context_type: The context type for the ordering (GROUP, STATUS_LIST)
            context_id: Context identifier (group ID for GROUP context, None for STATUS_LIST)
            item: Task or Initiative to add to the list
            after: Item or ID to insert after (optional)
            before: Item or ID to insert before (optional)

        Returns:
            The created Ordering record

        Raises:
            InvalidContextError: When context validation fails
            EntityNotFoundError: When referenced entities don't exist
            OrderingServiceError: When position calculation fails
        """
        self._validate_context(context_type, context_id)

        entity_type = (
            EntityType.TASK if isinstance(item, Task) else EntityType.INITIATIVE
        )

        # Check if ordering already exists
        existing = self._get_entity_ordering(
            context_type, context_id, entity_type, item
        )
        if existing:
            raise OrderingServiceError(
                f"Item {item.id} already has ordering in this context"
            )

        # Calculate position
        position = self._calculate_position(
            context_type, context_id, entity_type, after, before
        )

        # Create ordering record
        ordering = Ordering(
            user_id=item.user_id,
            workspace_id=item.workspace_id,
            context_type=context_type,
            context_id=context_id,
            entity_type=entity_type,
            position=position,
        )

        # Set entity reference
        if entity_type == EntityType.TASK:
            ordering.task_id = item.id
        else:
            ordering.initiative_id = item.id

        try:
            self.db.add(ordering)
            self.db.flush()  # Flush to catch integrity errors before commit
            return ordering
        except IntegrityError as e:
            self.db.rollback()
            raise OrderingServiceError(f"Failed to create ordering: {e}")

    def move_item(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        item: Union[Task, Initiative, uuid.UUID],
        after: Optional[Union[Task, Initiative, uuid.UUID]] = None,
        before: Optional[Union[Task, Initiative, uuid.UUID]] = None,
    ) -> Ordering:
        """
        Move an item within the same ordered list.

        Args:
            context_type: The context type for the ordering
            context_id: Context identifier
            item: Item or ID to move
            after: Item or ID to move after (optional)
            before: Item or ID to move before (optional)

        Returns:
            The updated Ordering record

        Raises:
            EntityNotFoundError: When item ordering doesn't exist
            OrderingServiceError: When position calculation fails
        """
        self._validate_context(context_type, context_id)

        # Get existing ordering
        item_id = item.id if hasattr(item, "id") else item
        entity_type = self._determine_entity_type(item)

        ordering = self._get_ordering_by_item_id(
            context_type, context_id, entity_type, item_id
        )
        if not ordering:
            raise EntityNotFoundError(
                f"No ordering found for item {item_id} in this context"
            )

        # Calculate new position
        new_position = self._calculate_position(
            context_type, context_id, entity_type, after, before, exclude_item=item_id
        )

        # Update position
        ordering.position = new_position

        try:
            self.db.flush()
            return ordering
        except IntegrityError as e:
            self.db.rollback()
            raise OrderingServiceError(f"Failed to move item: {e}")

    def move_item_across_lists(
        self,
        src_context_type: ContextType,
        src_context_id: Optional[uuid.UUID],
        dest_context_type: ContextType,
        dest_context_id: Optional[uuid.UUID],
        item: Union[Task, Initiative, uuid.UUID],
        after_id: Optional[uuid.UUID] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Ordering:
        """
        Move an item from one ordered list to another.

        Args:
            src_context_type: Source context type
            src_context_id: Source context identifier
            dest_context_type: Destination context type
            dest_context_id: Destination context identifier
            item: Item or ID to move
            after_id: ID to move after in destination (optional)
            before_id: ID to move before in destination (optional)

        Returns:
            The updated Ordering record

        Raises:
            EntityNotFoundError: When item ordering doesn't exist
            OrderingServiceError: When operation fails
        """
        self._validate_context(src_context_type, src_context_id)
        self._validate_context(dest_context_type, dest_context_id)

        # Get existing ordering in source context
        item_id = item.id if hasattr(item, "id") else item
        entity_type = self._determine_entity_type(item)

        ordering = self._get_ordering_by_item_id(
            src_context_type, src_context_id, entity_type, item_id
        )
        if not ordering:
            raise EntityNotFoundError(
                f"No ordering found for item {item_id} in source context"
            )

        # Calculate position in destination context
        after_item = None
        before_item = None

        if after_id:
            after_item = after_id
        if before_id:
            before_item = before_id

        new_position = self._calculate_position(
            dest_context_type, dest_context_id, entity_type, after_item, before_item
        )

        # Update ordering to new context and position
        ordering.context_type = dest_context_type
        ordering.context_id = dest_context_id
        ordering.position = new_position

        try:
            self.db.flush()
            return ordering
        except IntegrityError as e:
            self.db.rollback()
            raise OrderingServiceError(f"Failed to move item across lists: {e}")

    def remove_item(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        item: Union[Task, Initiative, uuid.UUID],
    ) -> bool:
        """
        Remove an item from an ordered list.

        Args:
            context_type: The context type for the ordering
            context_id: Context identifier
            item: Item or ID to remove

        Returns:
            True if item was removed, False if not found

        Raises:
            OrderingServiceError: When removal fails
        """
        self._validate_context(context_type, context_id)

        # Find existing ordering
        item_id = item.id if hasattr(item, "id") else item
        entity_type = self._determine_entity_type(item)

        ordering = self._get_ordering_by_item_id(
            context_type, context_id, entity_type, item_id
        )
        if not ordering:
            return False

        try:
            self.db.delete(ordering)
            self.db.flush()
            return True
        except Exception as e:
            self.db.rollback()
            raise OrderingServiceError(f"Failed to remove item: {e}")

    def _validate_context(
        self, context_type: ContextType, context_id: Optional[uuid.UUID]
    ) -> None:
        """Validate context type and ID combination."""
        if context_type == ContextType.GROUP and context_id is None:
            raise InvalidContextError("GROUP context requires a context_id")

    def _determine_entity_type(
        self, item: Union[Task, Initiative, uuid.UUID]
    ) -> EntityType:
        """Determine entity type from item."""
        if isinstance(item, Task):
            return EntityType.TASK
        elif isinstance(item, Initiative):
            return EntityType.INITIATIVE
        elif isinstance(item, uuid.UUID):
            # Try to find in database to determine type
            task = self.db.query(Task).filter(Task.id == item).first()
            if task:
                return EntityType.TASK

            initiative = self.db.query(Initiative).filter(Initiative.id == item).first()
            if initiative:
                return EntityType.INITIATIVE

            raise EntityNotFoundError(f"No task or initiative found with ID {item}")
        else:
            raise OrderingServiceError(f"Invalid item type: {type(item)}")

    def _get_entity_ordering(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        entity_type: EntityType,
        item: Union[Task, Initiative],
    ) -> Optional[Ordering]:
        """Get existing ordering for an entity."""
        query = self.db.query(Ordering).filter(
            Ordering.context_type == context_type,
            Ordering.context_id == context_id,
            Ordering.entity_type == entity_type,
        )

        if entity_type == EntityType.TASK:
            query = query.filter(Ordering.task_id == item.id)
        else:
            query = query.filter(Ordering.initiative_id == item.id)

        return query.first()

    def _get_ordering_by_item_id(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        entity_type: EntityType,
        item_id: uuid.UUID,
    ) -> Optional[Ordering]:
        """Get ordering by item ID."""
        query = self.db.query(Ordering).filter(
            Ordering.context_type == context_type,
            Ordering.context_id == context_id,
            Ordering.entity_type == entity_type,
        )

        if entity_type == EntityType.TASK:
            query = query.filter(Ordering.task_id == item_id)
        else:
            query = query.filter(Ordering.initiative_id == item_id)

        return query.first()

    def _calculate_position(
        self,
        context_type: ContextType,
        context_id: Optional[uuid.UUID],
        entity_type: EntityType,
        after: Optional[Union[Task, Initiative, uuid.UUID]] = None,
        before: Optional[Union[Task, Initiative, uuid.UUID]] = None,
        exclude_item: Optional[uuid.UUID] = None,
    ) -> str:
        """
        Calculate LexoRank position for an item.

        Args:
            context_type: Context type for the list
            context_id: Context identifier
            entity_type: Type of entity being positioned
            after: Item to position after (optional)
            before: Item to position before (optional)
            exclude_item: Item ID to exclude from calculations (for moves)

        Returns:
            Calculated LexoRank position string
        """
        # Get all orderings in this context
        query = self.db.query(Ordering).filter(
            Ordering.context_type == context_type,
            Ordering.context_id == context_id,
            Ordering.entity_type == entity_type,
        )

        if exclude_item:
            if entity_type == EntityType.TASK:
                query = query.filter(Ordering.task_id != exclude_item)
            else:
                query = query.filter(Ordering.initiative_id != exclude_item)

        all_orderings = query.order_by(Ordering.position).all()

        # Handle empty list
        if not all_orderings:
            return LexoRank.middle()

        # Extract positions
        positions = [ordering.position for ordering in all_orderings]

        # Handle insertion at beginning or end
        if after is None and before is None:
            # Insert at end
            last_position = positions[-1]
            try:
                return LexoRank.gen_next(last_position)
            except ValueError:
                # Handle potential overflow
                return self._rebalance_and_insert(all_orderings, len(all_orderings))

        # Find reference positions
        after_position = None
        before_position = None

        if after is not None:
            after_id = after.id if hasattr(after, "id") else after
            after_ordering = self._get_ordering_by_item_id(
                context_type, context_id, entity_type, after_id
            )
            if after_ordering and after_ordering.id not in [
                o.id
                for o in all_orderings
                if exclude_item
                and (
                    (entity_type == EntityType.TASK and o.task_id == exclude_item)
                    or (
                        entity_type == EntityType.INITIATIVE
                        and o.initiative_id == exclude_item
                    )
                )
            ]:
                after_position = after_ordering.position

        if before is not None:
            before_id = before.id if hasattr(before, "id") else before
            before_ordering = self._get_ordering_by_item_id(
                context_type, context_id, entity_type, before_id
            )
            if before_ordering and before_ordering.id not in [
                o.id
                for o in all_orderings
                if exclude_item
                and (
                    (entity_type == EntityType.TASK and o.task_id == exclude_item)
                    or (
                        entity_type == EntityType.INITIATIVE
                        and o.initiative_id == exclude_item
                    )
                )
            ]:
                before_position = before_ordering.position

        # Calculate position between references
        try:
            return LexoRank.get_lexorank_in_between(
                after_position, before_position, len(all_orderings) + 1
            )
        except ValueError as e:
            if "Rebalancing Required" in str(e):
                return self._rebalance_and_insert(
                    all_orderings, len(all_orderings) // 2
                )
            raise OrderingServiceError(f"Failed to calculate position: {e}")

    def _rebalance_and_insert(
        self, orderings: list[Ordering], insert_index: int
    ) -> str:
        """
        Rebalance all positions and return position for new item.

        This method redistributes all positions evenly when LexoRank
        positions become too long or conflicts arise.

        Args:
            orderings: List of current orderings to rebalance
            insert_index: Index where new item should be inserted

        Returns:
            Position string for the new item
        """
        total_items = len(orderings) + 1

        # Generate new evenly distributed positions
        new_positions = []
        for i in range(total_items):
            # Create positions with adequate spacing
            rank_length = LexoRank.get_rank_length(total_items)
            step = LexoRank.get_rank_step(total_items)
            position_value = step * i

            # Convert to rank format
            rank_parts = []
            temp_value = position_value
            for _ in range(rank_length):
                rank_parts.insert(0, temp_value % LexoRank.base)
                temp_value //= LexoRank.base

            new_positions.append(LexoRank.format_rank(rank_parts))

        # Update existing orderings with new positions
        for i, ordering in enumerate(orderings):
            if i >= insert_index:
                ordering.position = new_positions[i + 1]
            else:
                ordering.position = new_positions[i]

        # Return position for new item
        return new_positions[insert_index]

    def delete_all_orderings_for_entity(
        self, item: Union[Task, Initiative, uuid.UUID]
    ) -> int:
        """
        Delete all orderings for a given entity across all contexts.

        This is useful when deleting an entity (Initiative or Task) to ensure
        all its ordering records are cleaned up from both STATUS_LIST and
        any GROUP contexts it may be part of.

        Args:
            item: Entity or ID to remove all orderings for

        Returns:
            Number of orderings deleted

        Raises:
            OrderingServiceError: When deletion fails
        """
        try:
            # Get entity ID and type
            item_id = item.id if hasattr(item, "id") else item
            entity_type = self._determine_entity_type(item)

            # Query all orderings for this entity
            if entity_type == EntityType.INITIATIVE:
                orderings = (
                    self.db.query(Ordering)
                    .filter(Ordering.initiative_id == item_id)
                    .all()
                )
            elif entity_type == EntityType.TASK:
                orderings = (
                    self.db.query(Ordering).filter(Ordering.task_id == item_id).all()
                )
            else:
                raise OrderingServiceError(f"Unknown entity type: {entity_type}")

            # Delete all found orderings
            count = len(orderings)
            for ordering in orderings:
                self.db.delete(ordering)

            # Flush changes (commit handled by caller)
            self.db.flush()

            return count

        except Exception as e:
            self.db.rollback()
            raise OrderingServiceError(
                f"Failed to delete all orderings for entity: {e}"
            )
