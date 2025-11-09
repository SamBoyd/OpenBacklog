import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
from hamcrest import assert_that, calling, equal_to, is_, is_not, raises
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.initiative_management.initiative_controller import (
    InitiativeController,
    InitiativeControllerError,
    InitiativeNotFoundError,
)
from src.models import (
    ContextType,
    Group,
    GroupType,
    Initiative,
    InitiativeGroup,
    InitiativeStatus,
    User,
    Workspace,
)
from src.services.ordering_service import OrderingServiceError


class TestInitiativeController:

    @pytest.fixture
    def controller(self, session):
        controller = InitiativeController(session)
        return controller

    @pytest.fixture
    def test_initiative(
        self, session: Session, user: User, workspace: Workspace
    ) -> Initiative:
        initiative = Initiative(
            title="Test Initiative",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            type="FEATURE",
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)
        return initiative

    @pytest.fixture
    def test_group(self, session: Session, user: User, workspace: Workspace) -> Group:
        group = Group(
            name="Test Group",
            description="A test group for testing",
            user_id=user.id,
            workspace_id=workspace.id,
            group_type=GroupType.EXPLICIT,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        return group

    def test_create_initiative_success(self, controller, user, workspace, session):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        title = "Test Initiative"

        result: Initiative = controller.create_initiative(
            title=title,
            description=None,
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            initiative_type="FEATURE",
        )

        # Verify initiative was created in database
        assert_that(result.title, equal_to(title))
        assert_that(result.user_id, equal_to(user.id))
        assert_that(result.workspace_id, equal_to(workspace.id))
        assert_that(result.status, equal_to(InitiativeStatus.BACKLOG))
        assert_that(result.type, equal_to("FEATURE"))

        # Verify initiative exists in database
        db_initiative = session.query(Initiative).filter_by(id=result.id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.title, equal_to(title))

        mock_ordering_service.add_item.assert_called_once()
        call_args = mock_ordering_service.add_item.call_args
        assert_that(call_args.kwargs["context_type"], equal_to(ContextType.STATUS_LIST))
        assert_that(call_args.kwargs["context_id"], is_(None))

    def test_create_initiative_ordering_service_error(
        self, controller, user, workspace, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service
        mock_ordering_service.add_item.side_effect = OrderingServiceError("Test error")

        # Count initiatives before the failed operation
        initial_count = session.query(Initiative).count()

        assert_that(
            calling(controller.create_initiative).with_args(
                title="Test",
                description=None,
                user_id=user.id,
                workspace_id=workspace.id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify no initiative was persisted due to rollback
        final_count = session.query(Initiative).count()
        assert_that(final_count, equal_to(initial_count))

    def test_create_initiative_integrity_error(
        self, controller, user, workspace, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        # Create a duplicate initiative to trigger an integrity error
        # Assuming title+user_id+workspace_id combination should be unique
        existing_initiative = Initiative(
            title="Duplicate Title",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(existing_initiative)
        session.commit()

        # Try to create another initiative with same combination to trigger integrity error
        # Mock the session.flush to raise IntegrityError
        original_flush = session.flush

        def mock_flush():
            raise IntegrityError("statement", "params", "orig")

        session.flush = mock_flush

        # Count initiatives before the failed operation
        initial_count = session.query(Initiative).count()

        try:
            assert_that(
                calling(controller.create_initiative).with_args(
                    title="Duplicate Title",
                    description=None,
                    user_id=user.id,
                    workspace_id=workspace.id,
                ),
                raises(InitiativeControllerError),
            )

            # Verify no additional initiative was persisted due to rollback
            final_count = session.query(Initiative).count()
            assert_that(final_count, equal_to(initial_count))
        finally:
            # Restore original flush method
            session.flush = original_flush

    def test_delete_initiative_success(self, controller, test_initiative, session):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id

        result = controller.delete_initiative(initiative_id, user_id)

        assert_that(result, is_(True))
        mock_ordering_service.delete_all_orderings_for_entity.assert_called_once_with(
            item=test_initiative,
        )

        # Verify initiative was deleted from database
        deleted_initiative = (
            session.query(Initiative).filter_by(id=initiative_id).first()
        )
        assert_that(deleted_initiative, is_(None))

    def test_delete_initiative_not_found(self, controller, user, session):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        non_existent_id = uuid.uuid4()
        user_id = user.id

        assert_that(
            calling(controller.delete_initiative).with_args(non_existent_id, user_id),
            raises(InitiativeNotFoundError),
        )

    def test_delete_initiative_no_ordering_but_initiative_exists(
        self, controller, test_initiative, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id

        result = controller.delete_initiative(initiative_id, user_id)

        assert_that(result, is_(True))

        # Verify initiative was deleted from database
        deleted_initiative = (
            session.query(Initiative).filter_by(id=initiative_id).first()
        )
        assert_that(deleted_initiative, is_(None))

    def test_move_initiative_success(self, controller, test_initiative, session):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        after_id = uuid.uuid4()

        result = controller.move_initiative(
            initiative_id=initiative_id, user_id=user_id, after_id=after_id
        )

        assert_that(result, equal_to(test_initiative))
        mock_ordering_service.move_item.assert_called_once_with(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=test_initiative,
            after=after_id,
            before=None,
        )

        # Verify initiative still exists and is refreshed
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.id, equal_to(initiative_id))

    def test_move_initiative_not_found(self, controller, user):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        non_existent_id = uuid.uuid4()
        user_id = user.id

        assert_that(
            calling(controller.move_initiative).with_args(
                initiative_id=non_existent_id, user_id=user_id
            ),
            raises(InitiativeNotFoundError),
        )

    def test_move_initiative_to_status_success(
        self, controller, test_initiative, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        # Set initial status
        test_initiative.status = InitiativeStatus.BACKLOG
        session.commit()

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        new_status = InitiativeStatus.IN_PROGRESS

        result = controller.move_initiative_to_status(
            initiative_id=initiative_id,
            user_id=user_id,
            new_status=new_status,
        )

        assert_that(result, equal_to(test_initiative))
        assert_that(test_initiative.status, equal_to(new_status))
        mock_ordering_service.move_item_across_lists.assert_called_once()

        # Verify status was updated in database
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative.status, equal_to(new_status))

    def test_move_initiative_to_same_status_no_ordering_change(
        self, controller, test_initiative, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        current_status = InitiativeStatus.BACKLOG
        test_initiative.status = current_status
        session.commit()

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id

        result = controller.move_initiative_to_status(
            initiative_id=initiative_id,
            user_id=user_id,
            new_status=current_status,
        )

        assert_that(result, equal_to(test_initiative))
        mock_ordering_service.move_item_across_lists.assert_not_called()

        # Verify status remains unchanged
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative.status, equal_to(current_status))

    def test_add_initiative_to_group_success(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        result = controller.add_initiative_to_group(
            initiative_id=initiative_id,
            user_id=user_id,
            group_id=group_id,
        )

        assert_that(result, equal_to(test_initiative))
        mock_ordering_service.add_item.assert_called_once_with(
            context_type=ContextType.GROUP,
            context_id=group_id,
            item=test_initiative,
            after=None,
            before=None,
        )

        # Verify initiative still exists and is refreshed
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.id, equal_to(initiative_id))

        # Verify InitiativeGroup relationship was created
        initiative_group = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == group_id,
            )
            .first()
        )
        assert_that(initiative_group, is_not(None))
        assert_that(initiative_group.user_id, equal_to(user_id))

    def test_remove_initiative_from_group_success(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service
        mock_ordering_service.remove_item.return_value = True

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        # First create the relationship that we'll remove
        initiative_group = InitiativeGroup(
            initiative_id=initiative_id,
            group_id=group_id,
            user_id=user_id,
        )
        session.add(initiative_group)
        session.commit()

        # Verify the relationship exists before removal
        existing_relationship = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == group_id,
            )
            .first()
        )
        assert_that(existing_relationship, is_not(None))

        result = controller.remove_initiative_from_group(
            initiative_id=initiative_id,
            user_id=user_id,
            group_id=group_id,
        )

        assert_that(result, is_(True))
        mock_ordering_service.remove_item.assert_called_once_with(
            context_type=ContextType.GROUP,
            context_id=group_id,
            item=test_initiative,
        )

        # Verify initiative still exists
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.id, equal_to(initiative_id))

        # Verify InitiativeGroup relationship was deleted
        removed_relationship = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == group_id,
            )
            .first()
        )
        assert_that(removed_relationship, is_(None))

    def test_remove_initiative_from_group_not_in_group(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        # Don't create any relationship - initiative is not in group

        result = controller.remove_initiative_from_group(
            initiative_id=initiative_id,
            user_id=user_id,
            group_id=group_id,
        )

        assert_that(result, is_(False))

        # Verify ordering service was not called since no relationship exists
        mock_ordering_service.remove_item.assert_not_called()

        # Verify initiative still exists
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.id, equal_to(initiative_id))

    def test_add_initiative_to_nonexistent_group(
        self, controller, test_initiative, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        nonexistent_group_id = uuid.uuid4()

        assert_that(
            calling(controller.add_initiative_to_group).with_args(
                initiative_id=initiative_id,
                user_id=user_id,
                group_id=nonexistent_group_id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify no relationship was created
        initiative_group = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == nonexistent_group_id,
            )
            .first()
        )
        assert_that(initiative_group, is_(None))

        # Verify ordering service was not called
        mock_ordering_service.add_item.assert_not_called()

    def test_add_initiative_to_group_owned_by_different_user(
        self, controller, test_initiative, session, other_user, workspace
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        # Create a group owned by a different user
        other_group = Group(
            name="Other User's Group",
            description="A group owned by another user",
            user_id=other_user.id,
            workspace_id=workspace.id,
            group_type=GroupType.EXPLICIT,
        )
        session.add(other_group)
        session.commit()
        session.refresh(other_group)

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id  # Original user
        group_id = other_group.id

        assert_that(
            calling(controller.add_initiative_to_group).with_args(
                initiative_id=initiative_id,
                user_id=user_id,
                group_id=group_id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify no relationship was created
        initiative_group = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == group_id,
            )
            .first()
        )
        assert_that(initiative_group, is_(None))

        # Verify ordering service was not called
        mock_ordering_service.add_item.assert_not_called()

    def test_add_initiative_to_group_already_in_group(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        # First create the relationship
        initiative_group = InitiativeGroup(
            initiative_id=initiative_id,
            group_id=group_id,
            user_id=user_id,
        )
        session.add(initiative_group)
        session.commit()

        # Try to add again - should handle gracefully
        result = controller.add_initiative_to_group(
            initiative_id=initiative_id,
            user_id=user_id,
            group_id=group_id,
        )

        assert_that(result, equal_to(test_initiative))

        # Verify ordering service was not called since relationship already exists
        mock_ordering_service.add_item.assert_not_called()

        # Verify only one relationship exists
        relationship_count = (
            session.query(InitiativeGroup)
            .filter(
                InitiativeGroup.initiative_id == initiative_id,
                InitiativeGroup.group_id == group_id,
            )
            .count()
        )
        assert_that(relationship_count, equal_to(1))

    def test_delete_initiative_with_multiple_orderings(
        self, controller, test_initiative, session
    ):
        """Test deleting initiative that has both STATUS_LIST and GROUP orderings."""
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service
        mock_ordering_service.delete_all_orderings_for_entity.return_value = 3

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id

        result = controller.delete_initiative(initiative_id, user_id)

        assert_that(result, is_(True))

        # Verify the new method was called instead of the old remove_item
        mock_ordering_service.delete_all_orderings_for_entity.assert_called_once_with(
            item=test_initiative
        )

        # Verify old method was not called
        mock_ordering_service.remove_item.assert_not_called()

        # Verify initiative was deleted from database
        deleted_initiative = (
            session.query(Initiative).filter_by(id=initiative_id).first()
        )
        assert_that(deleted_initiative, is_(None))

    def test_move_initiative_in_group_success(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        # Create the relationship first
        initiative_group = InitiativeGroup(
            initiative_id=initiative_id,
            group_id=group_id,
            user_id=user_id,
        )
        session.add(initiative_group)
        session.commit()

        after_id = uuid.uuid4()
        before_id = uuid.uuid4()

        result = controller.move_initiative_in_group(
            initiative_id=initiative_id,
            user_id=user_id,
            group_id=group_id,
            after_id=after_id,
            before_id=before_id,
        )

        assert_that(result, equal_to(test_initiative))
        mock_ordering_service.move_item.assert_called_once_with(
            context_type=ContextType.GROUP,
            context_id=group_id,
            item=test_initiative,
            after=after_id,
            before=before_id,
        )

        # Verify initiative still exists and is refreshed
        db_initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert_that(db_initiative, is_not(None))
        assert_that(db_initiative.id, equal_to(initiative_id))

    def test_move_initiative_in_group_not_found(self, controller, user, test_group):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        non_existent_id = uuid.uuid4()
        user_id = user.id
        group_id = test_group.id

        assert_that(
            calling(controller.move_initiative_in_group).with_args(
                initiative_id=non_existent_id,
                user_id=user_id,
                group_id=group_id,
            ),
            raises(InitiativeNotFoundError),
        )

        # Verify ordering service was not called
        mock_ordering_service.move_item.assert_not_called()

    def test_move_initiative_in_group_group_not_found(
        self, controller, test_initiative, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        nonexistent_group_id = uuid.uuid4()

        assert_that(
            calling(controller.move_initiative_in_group).with_args(
                initiative_id=initiative_id,
                user_id=user_id,
                group_id=nonexistent_group_id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify ordering service was not called
        mock_ordering_service.move_item.assert_not_called()

    def test_move_initiative_in_group_not_in_group(
        self, controller, test_initiative, test_group, session
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id
        group_id = test_group.id

        # Don't create the relationship - initiative is not in group

        assert_that(
            calling(controller.move_initiative_in_group).with_args(
                initiative_id=initiative_id,
                user_id=user_id,
                group_id=group_id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify ordering service was not called
        mock_ordering_service.move_item.assert_not_called()

    def test_move_initiative_in_group_different_user(
        self, controller, test_initiative, session, other_user, workspace
    ):
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        # Create a group owned by a different user
        other_group = Group(
            name="Other User's Group",
            description="A group owned by another user",
            user_id=other_user.id,
            workspace_id=workspace.id,
            group_type=GroupType.EXPLICIT,
        )
        session.add(other_group)
        session.commit()
        session.refresh(other_group)

        initiative_id = test_initiative.id
        user_id = test_initiative.user_id  # Original user
        group_id = other_group.id

        assert_that(
            calling(controller.move_initiative_in_group).with_args(
                initiative_id=initiative_id,
                user_id=user_id,
                group_id=group_id,
            ),
            raises(InitiativeControllerError),
        )

        # Verify ordering service was not called
        mock_ordering_service.move_item.assert_not_called()

    def test_complete_onboarding_if_first_initiative_calls_complete_onboarding(
        self, controller, user, workspace, session, monkeypatch
    ):
        """Test that onboarding is completed when user has exactly one initiative."""
        from src.accounting.models import UserAccountStatus

        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        mock_complete_onboarding = Mock(return_value=user.account_details)
        monkeypatch.setattr(
            "src.accounting.accounting_controller.complete_onboarding",
            mock_complete_onboarding,
        )

        account_details = user.account_details
        account_details.status = UserAccountStatus.NEW
        account_details.onboarding_completed = False
        session.add(account_details)
        session.commit()

        controller.create_initiative(
            title="First Initiative",
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            initiative_type="FEATURE",
        )

        controller.complete_onboarding_if_first_initiative(user.id)

        mock_complete_onboarding.assert_called_once_with(user, session)

    def test_complete_onboarding_if_first_initiative_not_called_for_multiple_initiatives(
        self, controller, user, workspace, session, monkeypatch
    ):
        """Test that onboarding is NOT completed when user has more than one initiative."""
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        mock_complete_onboarding = Mock()
        monkeypatch.setattr(
            "src.accounting.accounting_controller.complete_onboarding",
            mock_complete_onboarding,
        )

        controller.create_initiative(
            title="First Initiative",
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            initiative_type="FEATURE",
        )

        controller.create_initiative(
            title="Second Initiative",
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            initiative_type="FEATURE",
        )

        controller.complete_onboarding_if_first_initiative(user.id)

        mock_complete_onboarding.assert_not_called()

    def test_complete_onboarding_if_first_initiative_handles_errors_gracefully(
        self, controller, user, workspace, session, monkeypatch
    ):
        """Test that errors during onboarding completion are handled gracefully."""
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        mock_complete_onboarding = Mock(side_effect=Exception("Onboarding error"))
        monkeypatch.setattr(
            "src.accounting.accounting_controller.complete_onboarding",
            mock_complete_onboarding,
        )

        controller.create_initiative(
            title="First Initiative",
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            initiative_type="FEATURE",
        )

        controller.complete_onboarding_if_first_initiative(user.id)

        mock_complete_onboarding.assert_called_once()

    def test_complete_onboarding_if_first_initiative_handles_nonexistent_user(
        self, controller, session, monkeypatch
    ):
        """Test that method handles nonexistent user gracefully."""
        mock_ordering_service = Mock()
        controller.ordering_service = mock_ordering_service

        mock_complete_onboarding = Mock()
        monkeypatch.setattr(
            "src.accounting.accounting_controller.complete_onboarding",
            mock_complete_onboarding,
        )

        nonexistent_user_id = uuid.uuid4()

        controller.complete_onboarding_if_first_initiative(nonexistent_user_id)

        mock_complete_onboarding.assert_not_called()

    def test_complete_onboarding_if_first_initiative_not_called_for_zero_initiatives(
        self, controller, user, session, monkeypatch
    ):
        """Test that onboarding is NOT completed when user has zero initiatives."""
        mock_complete_onboarding = Mock()
        monkeypatch.setattr(
            "src.accounting.accounting_controller.complete_onboarding",
            mock_complete_onboarding,
        )

        controller.complete_onboarding_if_first_initiative(user.id)

        mock_complete_onboarding.assert_not_called()
