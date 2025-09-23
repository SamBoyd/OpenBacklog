import random
import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, calling, equal_to, raises
from sqlalchemy.exc import IntegrityError

from src.models import ContextType, EntityType, Initiative, Ordering, Task
from src.services.ordering_service import (
    EntityNotFoundError,
    InvalidContextError,
    OrderingService,
    OrderingServiceError,
)
from src.utils.lexorank import LexoRank


class TestOrderingService:
    """Unit tests for OrderingService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def ordering_service(self, mock_db_session):
        """OrderingService instance with mocked dependencies."""
        return OrderingService(mock_db_session)

    @pytest.fixture
    def mock_task(self):
        """Mock Task instance."""
        task = Mock(spec=Task)
        task.id = uuid.uuid4()
        task.user_id = uuid.uuid4()
        task.workspace_id = uuid.uuid4()
        return task

    @pytest.fixture
    def mock_initiative(self):
        """Mock Initiative instance."""
        initiative = Mock(spec=Initiative)
        initiative.id = uuid.uuid4()
        initiative.user_id = uuid.uuid4()
        initiative.workspace_id = uuid.uuid4()
        return initiative

    def test_init(self, mock_db_session):
        """Test OrderingService initialization."""
        service = OrderingService(mock_db_session)
        assert service.db == mock_db_session

    def test_validate_context_group_with_id(self, ordering_service):
        """Test context validation passes for GROUP with context_id."""
        context_id = uuid.uuid4()
        # Should not raise
        ordering_service._validate_context(ContextType.GROUP, context_id)

    def test_validate_context_group_without_id_raises_error(self, ordering_service):
        """Test context validation fails for GROUP without context_id."""
        with pytest.raises(
            InvalidContextError, match="GROUP context requires a context_id"
        ):
            ordering_service._validate_context(ContextType.GROUP, None)

    def test_validate_context_status_list_with_none(self, ordering_service):
        """Test context validation passes for STATUS_LIST with None context_id."""
        # Should not raise
        ordering_service._validate_context(ContextType.STATUS_LIST, None)

    def test_determine_entity_type_task(self, ordering_service, mock_task):
        """Test entity type determination for Task."""
        entity_type = ordering_service._determine_entity_type(mock_task)
        assert entity_type == EntityType.TASK

    def test_determine_entity_type_initiative(self, ordering_service, mock_initiative):
        """Test entity type determination for Initiative."""
        entity_type = ordering_service._determine_entity_type(mock_initiative)
        assert entity_type == EntityType.INITIATIVE

    def test_determine_entity_type_uuid_task(
        self, ordering_service, mock_db_session, mock_task
    ):
        """Test entity type determination for UUID that resolves to Task."""
        task_id = uuid.uuid4()

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task,  # Task query returns task
            None,  # Initiative query returns None
        ]

        entity_type = ordering_service._determine_entity_type(task_id)
        assert entity_type == EntityType.TASK

    def test_determine_entity_type_uuid_initiative(
        self, ordering_service, mock_db_session, mock_initiative
    ):
        """Test entity type determination for UUID that resolves to Initiative."""
        initiative_id = uuid.uuid4()

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            None,  # Task query returns None
            mock_initiative,  # Initiative query returns initiative
        ]

        entity_type = ordering_service._determine_entity_type(initiative_id)
        assert entity_type == EntityType.INITIATIVE

    def test_determine_entity_type_uuid_not_found_raises_error(
        self, ordering_service, mock_db_session
    ):
        """Test entity type determination for UUID that doesn't exist."""
        unknown_id = uuid.uuid4()

        # Mock query results - both return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(
            EntityNotFoundError,
            match=f"No task or initiative found with ID {unknown_id}",
        ):
            ordering_service._determine_entity_type(unknown_id)

    def test_determine_entity_type_invalid_type_raises_error(self, ordering_service):
        """Test entity type determination for invalid type."""
        with pytest.raises(OrderingServiceError, match="Invalid item type"):
            ordering_service._determine_entity_type("invalid")

    @patch("src.services.ordering_service.LexoRank")
    def test_calculate_position_empty_list(
        self, mock_lexorank, ordering_service, mock_db_session
    ):
        """Test position calculation for empty list."""
        # Mock empty query result
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        # Mock LexoRank.middle() to return string directly
        mock_lexorank.middle.return_value = "middle_position"

        position = ordering_service._calculate_position(
            ContextType.STATUS_LIST, None, EntityType.TASK
        )

        assert position == "middle_position"
        mock_lexorank.middle.assert_called_once()

    @patch("src.services.ordering_service.LexoRank")
    def test_calculate_position_insert_at_end(
        self, mock_lexorank, ordering_service, mock_db_session
    ):
        """Test position calculation for insertion at end."""
        # Mock existing orderings
        mock_ordering = Mock()
        mock_ordering.position = "existing_position"
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_ordering
        ]

        # Mock LexoRank.gen_next() to return string directly
        mock_lexorank.gen_next.return_value = "next_position"

        position = ordering_service._calculate_position(
            ContextType.STATUS_LIST, None, EntityType.TASK
        )

        assert position == "next_position"
        mock_lexorank.gen_next.assert_called_once_with("existing_position")

    def test_get_entity_ordering_task(
        self, ordering_service, mock_db_session, mock_task
    ):
        """Test getting entity ordering for task."""
        mock_ordering = Mock()
        # Mock the query chain properly
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ordering

        result = ordering_service._get_entity_ordering(
            ContextType.STATUS_LIST, None, EntityType.TASK, mock_task
        )

        assert result == mock_ordering

    def test_get_entity_ordering_initiative(
        self, ordering_service, mock_db_session, mock_initiative
    ):
        """Test getting entity ordering for initiative."""
        mock_ordering = Mock()
        # Mock the query chain properly
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ordering

        result = ordering_service._get_entity_ordering(
            ContextType.STATUS_LIST, None, EntityType.INITIATIVE, mock_initiative
        )

        assert result == mock_ordering

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_get_entity_ordering")
    @patch.object(OrderingService, "_calculate_position")
    def test_add_item_success_task(
        self,
        mock_calculate_position,
        mock_get_entity_ordering,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test successful addition of task item."""
        # Setup mocks
        mock_get_entity_ordering.return_value = None  # No existing ordering
        mock_calculate_position.return_value = "calculated_position"

        # Execute
        result = ordering_service.add_item(ContextType.STATUS_LIST, None, mock_task)

        # Verify
        mock_validate_context.assert_called_once_with(ContextType.STATUS_LIST, None)
        mock_get_entity_ordering.assert_called_once_with(
            ContextType.STATUS_LIST, None, EntityType.TASK, mock_task
        )
        mock_calculate_position.assert_called_once_with(
            ContextType.STATUS_LIST, None, EntityType.TASK, None, None
        )

        # Verify ordering creation
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

        # Verify ordering properties
        added_ordering = mock_db_session.add.call_args[0][0]
        assert added_ordering.user_id == mock_task.user_id
        assert added_ordering.workspace_id == mock_task.workspace_id
        assert added_ordering.context_type == ContextType.STATUS_LIST
        assert added_ordering.context_id is None
        assert added_ordering.entity_type == EntityType.TASK
        assert added_ordering.position == "calculated_position"
        assert added_ordering.task_id == mock_task.id

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_get_entity_ordering")
    def test_add_item_already_exists_raises_error(
        self,
        mock_get_entity_ordering,
        mock_validate_context,
        ordering_service,
        mock_task,
    ):
        """Test adding item that already has ordering raises error."""
        # Setup mocks
        mock_get_entity_ordering.return_value = Mock()  # Existing ordering

        # Execute and verify
        with pytest.raises(
            OrderingServiceError,
            match=f"Item {mock_task.id} already has ordering in this context",
        ):
            ordering_service.add_item(ContextType.STATUS_LIST, None, mock_task)

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_get_entity_ordering")
    @patch.object(OrderingService, "_calculate_position")
    def test_add_item_integrity_error_raises_service_error(
        self,
        mock_calculate_position,
        mock_get_entity_ordering,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test adding item with database integrity error."""
        # Setup mocks
        mock_get_entity_ordering.return_value = None
        mock_calculate_position.return_value = "position"
        mock_db_session.flush.side_effect = IntegrityError(
            "statement", "params", "orig"
        )

        # Execute and verify
        with pytest.raises(OrderingServiceError, match="Failed to create ordering"):
            ordering_service.add_item(ContextType.STATUS_LIST, None, mock_task)

        mock_db_session.rollback.assert_called_once()

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    @patch.object(OrderingService, "_calculate_position")
    def test_move_item_success(
        self,
        mock_calculate_position,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test successful item move."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_ordering = Mock()
        mock_get_ordering_by_item_id.return_value = mock_ordering
        mock_calculate_position.return_value = "new_position"

        # Execute
        result = ordering_service.move_item(
            ContextType.STATUS_LIST, None, mock_task, after=uuid.uuid4()
        )

        # Verify
        mock_validate_context.assert_called_once_with(ContextType.STATUS_LIST, None)
        mock_determine_entity_type.assert_called_once_with(mock_task)
        mock_get_ordering_by_item_id.assert_called_once_with(
            ContextType.STATUS_LIST, None, EntityType.TASK, mock_task.id
        )
        mock_calculate_position.assert_called_once()

        assert mock_ordering.position == "new_position"
        mock_db_session.flush.assert_called_once()
        assert result == mock_ordering

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    def test_move_item_not_found_raises_error(
        self,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_task,
    ):
        """Test moving item that doesn't exist raises error."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_get_ordering_by_item_id.return_value = None

        # Execute and verify
        with pytest.raises(
            EntityNotFoundError, match=f"No ordering found for item {mock_task.id}"
        ):
            ordering_service.move_item(ContextType.STATUS_LIST, None, mock_task)

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    @patch.object(OrderingService, "_calculate_position")
    def test_move_item_across_lists_success(
        self,
        mock_calculate_position,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test successful item move across lists."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_ordering = Mock()
        mock_get_ordering_by_item_id.return_value = mock_ordering
        mock_calculate_position.return_value = "dest_position"

        dest_context_id = uuid.uuid4()

        # Execute
        result = ordering_service.move_item_across_lists(
            ContextType.STATUS_LIST, None, ContextType.GROUP, dest_context_id, mock_task
        )

        # Verify context validation called for both contexts
        assert mock_validate_context.call_count == 2
        mock_validate_context.assert_any_call(ContextType.STATUS_LIST, None)
        mock_validate_context.assert_any_call(ContextType.GROUP, dest_context_id)

        # Verify ordering updated
        assert mock_ordering.context_type == ContextType.GROUP
        assert mock_ordering.context_id == dest_context_id
        assert mock_ordering.position == "dest_position"

        mock_db_session.flush.assert_called_once()
        assert result == mock_ordering

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    def test_remove_item_success(
        self,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test successful item removal."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_ordering = Mock()
        mock_get_ordering_by_item_id.return_value = mock_ordering

        # Execute
        result = ordering_service.remove_item(ContextType.STATUS_LIST, None, mock_task)

        # Verify
        mock_validate_context.assert_called_once_with(ContextType.STATUS_LIST, None)
        mock_determine_entity_type.assert_called_once_with(mock_task)
        mock_get_ordering_by_item_id.assert_called_once_with(
            ContextType.STATUS_LIST, None, EntityType.TASK, mock_task.id
        )

        mock_db_session.delete.assert_called_once_with(mock_ordering)
        mock_db_session.flush.assert_called_once()
        assert result is True

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    def test_remove_item_not_found(
        self,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_task,
    ):
        """Test removing item that doesn't exist."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_get_ordering_by_item_id.return_value = None

        # Execute
        result = ordering_service.remove_item(ContextType.STATUS_LIST, None, mock_task)

        # Verify
        assert result is False

    @patch.object(OrderingService, "_validate_context")
    @patch.object(OrderingService, "_determine_entity_type")
    @patch.object(OrderingService, "_get_ordering_by_item_id")
    def test_remove_item_database_error_raises_service_error(
        self,
        mock_get_ordering_by_item_id,
        mock_determine_entity_type,
        mock_validate_context,
        ordering_service,
        mock_db_session,
        mock_task,
    ):
        """Test removing item with database error."""
        # Setup mocks
        mock_determine_entity_type.return_value = EntityType.TASK
        mock_ordering = Mock()
        mock_get_ordering_by_item_id.return_value = mock_ordering
        mock_db_session.delete.side_effect = Exception("Database error")

        # Execute and verify
        with pytest.raises(OrderingServiceError, match="Failed to remove item"):
            ordering_service.remove_item(ContextType.STATUS_LIST, None, mock_task)

        mock_db_session.rollback.assert_called_once()

    def test_delete_all_orderings_for_entity_success(
        self, mock_db_session, mock_initiative
    ):
        """Test successful deletion of all orderings for an entity."""
        service = OrderingService(mock_db_session)

        # Mock orderings for the initiative
        mock_ordering1 = Mock()
        mock_ordering1.id = uuid.uuid4()
        mock_ordering2 = Mock()
        mock_ordering2.id = uuid.uuid4()
        mock_ordering3 = Mock()
        mock_ordering3.id = uuid.uuid4()

        mock_orderings = [mock_ordering1, mock_ordering2, mock_ordering3]

        # Setup query mock
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_orderings

        result = service.delete_all_orderings_for_entity(mock_initiative)

        assert_that(result, equal_to(3))

        # Verify query was called correctly
        mock_db_session.query.assert_called_once_with(Ordering)
        mock_query.filter.assert_called_once()

        # Verify all orderings were deleted
        assert_that(mock_db_session.delete.call_count, equal_to(3))
        mock_db_session.delete.assert_any_call(mock_ordering1)
        mock_db_session.delete.assert_any_call(mock_ordering2)
        mock_db_session.delete.assert_any_call(mock_ordering3)

        # Verify flush was called
        mock_db_session.flush.assert_called_once()

    def test_delete_all_orderings_for_entity_no_orderings(
        self, mock_db_session, mock_initiative
    ):
        """Test deletion when no orderings exist for entity."""
        service = OrderingService(mock_db_session)

        # Setup query mock to return empty list
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = service.delete_all_orderings_for_entity(mock_initiative)

        assert_that(result, equal_to(0))

        # Verify no delete calls were made
        mock_db_session.delete.assert_not_called()

        # Verify flush was still called
        mock_db_session.flush.assert_called_once()

    def test_delete_all_orderings_for_entity_with_uuid(self, mock_db_session):
        """Test deletion using UUID instead of entity object."""
        service = OrderingService(mock_db_session)

        initiative_id = uuid.uuid4()
        mock_ordering = Mock()

        # Mock the entity lookup
        mock_initiative = Mock()
        mock_initiative.id = initiative_id

        mock_initiative_query = Mock()
        mock_db_session.query.return_value = mock_initiative_query
        mock_initiative_query.filter.return_value = mock_initiative_query
        # First call for entity lookup, second for orderings lookup
        mock_initiative_query.first.return_value = mock_initiative
        mock_initiative_query.all.return_value = [mock_ordering]

        result = service.delete_all_orderings_for_entity(initiative_id)

        assert_that(result, equal_to(1))
        mock_db_session.delete.assert_called_once_with(mock_ordering)

    def test_delete_all_orderings_for_entity_database_error(
        self, mock_db_session, mock_initiative
    ):
        """Test handling of database errors during deletion."""
        service = OrderingService(mock_db_session)

        mock_ordering = Mock()

        # Setup query mock
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_ordering]

        # Make flush raise an exception
        mock_db_session.flush.side_effect = Exception("Database error")

        assert_that(
            calling(service.delete_all_orderings_for_entity).with_args(mock_initiative),
            raises(OrderingServiceError),
        )

        mock_db_session.rollback.assert_called_once()

    def test_delete_all_orderings_for_entity_full_integration(
        self, session, user, workspace, test_initiative
    ):
        """Test delete_all_orderings_for_entity with real database."""
        service = OrderingService(session)
        group_id1 = uuid.uuid4()
        group_id2 = uuid.uuid4()

        # Add initiative to STATUS_LIST and two groups
        # status_ordering = service.add_item(ContextType.STATUS_LIST, None, test_initiative)
        # session.commit()

        group_ordering1 = service.add_item(
            ContextType.GROUP, group_id1, test_initiative
        )
        session.commit()

        group_ordering2 = service.add_item(
            ContextType.GROUP, group_id2, test_initiative
        )
        session.commit()

        # Verify orderings exist
        db_orderings = (
            session.query(Ordering).filter_by(initiative_id=test_initiative.id).all()
        )
        assert_that(len(db_orderings), equal_to(3))

        # Delete all orderings
        deleted_count = service.delete_all_orderings_for_entity(test_initiative)
        session.commit()

        assert_that(deleted_count, equal_to(3))

        # Verify all orderings are gone
        db_orderings = (
            session.query(Ordering).filter_by(initiative_id=test_initiative.id).all()
        )
        assert_that(len(db_orderings), equal_to(0))


class TestOrderingServiceIntegration:
    """Integration tests using real database session."""

    @pytest.fixture
    def test_task(self, session, workspace, user, test_initiative):
        test_task = Task(
            title="Test Task E2E",
            description="This is the initial description for E2E testing.",
            user_id=user.id,
            initiative_id=test_initiative.id,
            identifier="E2E-TASK-"
            + random.choice(
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            ),  # Unique identifier
            workspace_id=workspace.id,
        )
        test_initiative.tasks = [test_task]

        session.add(test_task)
        session.commit()

        return test_task

    def test_add_item_full_integration(self, session, user, workspace, test_task):
        """Test adding item with real database session."""
        service = OrderingService(session)

        # Execute
        ordering = service.add_item(ContextType.STATUS_LIST, None, test_task)

        session.commit()

        # Verify
        assert ordering.id is not None
        assert ordering.user_id == test_task.user_id
        assert ordering.workspace_id == test_task.workspace_id
        assert ordering.context_type == ContextType.STATUS_LIST
        assert ordering.context_id is None
        assert ordering.entity_type == EntityType.TASK
        assert ordering.task_id == test_task.id
        assert ordering.position is not None

        # Verify ordering exists in database
        db_ordering = session.query(Ordering).filter_by(id=ordering.id).first()
        assert db_ordering is not None

    def test_move_item_full_integration(self, session, user, workspace, test_task):
        """Test moving item with real database session."""
        service = OrderingService(session)

        # Add item first
        ordering = service.add_item(ContextType.STATUS_LIST, None, test_task)
        original_position = ordering.position
        session.commit()

        # Create another task to move relative to
        task2 = Task(
            title="Task 2",
            identifier="T-002",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_task.initiative_id,
        )
        session.add(task2)
        session.commit()

        # Add second task to ordering
        ordering2 = service.add_item(ContextType.STATUS_LIST, None, task2)
        session.commit()

        # Move first item after second item
        moved_ordering = service.move_item(
            ContextType.STATUS_LIST, None, test_task, after=task2
        )
        session.commit()

        # Verify position changed
        assert moved_ordering.position != original_position
        assert moved_ordering.position > ordering2.position

    def test_move_item_across_lists_full_integration(
        self, session, user, workspace, test_task
    ):
        """Test moving item across lists with real database session."""
        service = OrderingService(session)
        group_id = uuid.uuid4()

        # Add item to STATUS_LIST
        ordering = service.add_item(ContextType.STATUS_LIST, None, test_task)
        session.commit()

        # Move to GROUP
        moved_ordering = service.move_item_across_lists(
            ContextType.STATUS_LIST, None, ContextType.GROUP, group_id, test_task
        )
        session.commit()

        # Verify
        assert moved_ordering.context_type == ContextType.GROUP
        assert moved_ordering.context_id == group_id

    def test_remove_item_full_integration(self, session, user, workspace, test_task):
        """Test removing item with real database session."""
        service = OrderingService(session)

        # Add item first
        ordering = service.add_item(ContextType.STATUS_LIST, None, test_task)
        ordering_id = ordering.id
        session.commit()

        # Remove item
        result = service.remove_item(ContextType.STATUS_LIST, None, test_task)
        session.commit()

        # Verify
        assert result is True

        # Verify ordering no longer exists
        db_ordering = session.query(Ordering).filter_by(id=ordering_id).first()
        assert db_ordering is None

    def test_multiple_items_ordering(self, session, user, workspace, test_initiative):
        """Test ordering multiple items maintains correct sequence."""
        service = OrderingService(session)

        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = Task(
                title=f"Task {i}",
                identifier=f"T-{i:03d}",
                user_id=user.id,
                workspace_id=workspace.id,
                initiative_id=test_initiative.id,
            )
            session.add(task)
            tasks.append(task)

        session.commit()

        # Add tasks to ordering
        orderings = []
        for task in tasks:
            ordering = service.add_item(ContextType.STATUS_LIST, None, task)
            orderings.append(ordering)

        session.commit()

        # Verify positions are in ascending order
        positions = [ordering.position for ordering in orderings]
        sorted_positions = sorted(positions)
        assert positions == sorted_positions

    def test_lexorank_position_calculations(
        self, session, user, workspace, test_initiative
    ):
        """Test LexoRank position calculations work correctly."""
        service = OrderingService(session)

        # Create tasks
        task1 = Task(
            title="Task 1",
            identifier="T-001",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        task2 = Task(
            title="Task 2",
            identifier="T-002",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )
        task3 = Task(
            title="Task 3",
            identifier="T-003",
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
        )

        session.add_all([task1, task2, task3])
        session.commit()

        # Add first task
        ordering1 = service.add_item(ContextType.STATUS_LIST, None, task1)
        session.commit()

        # Add second task after first
        ordering2 = service.add_item(ContextType.STATUS_LIST, None, task2, after=task1)
        session.commit()

        # Add third task between first and second
        ordering3 = service.add_item(
            ContextType.STATUS_LIST, None, task3, after=task1, before=task2
        )
        session.commit()

        # Verify ordering: task1 < task3 < task2
        assert ordering1.position < ordering3.position < ordering2.position
