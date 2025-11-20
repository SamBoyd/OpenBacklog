"""Tests for product strategy controller."""

import uuid

import pytest
from hamcrest import assert_that, equal_to, has_length
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.strategic_planning import controller as product_strategy_controller
from src.strategic_planning.exceptions import DomainException


class TestProductOutcome:
    def test_get_product_outcomes_empty(self, workspace: Workspace, session: Session):
        """Test getting outcomes for workspace with no outcomes."""
        outcomes = product_strategy_controller.get_product_outcomes(
            workspace.id, session
        )
        assert_that(outcomes, has_length(0))

    def test_get_product_outcomes_returns_ordered_list(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test getting outcomes returns list ordered by display_order."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 1",
            None,
            [],
            session,
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 2",
            None,
            [],
            session,
        )
        outcome3 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 3",
            None,
            [],
            session,
        )

        outcomes = product_strategy_controller.get_product_outcomes(
            workspace.id, session
        )

        assert_that(outcomes, has_length(3))
        assert_that(outcomes[0].id, equal_to(outcome1.id))
        assert_that(outcomes[1].id, equal_to(outcome2.id))
        assert_that(outcomes[2].id, equal_to(outcome3.id))
        assert_that(outcomes[0].display_order, equal_to(0))
        assert_that(outcomes[1].display_order, equal_to(1))
        assert_that(outcomes[2].display_order, equal_to(2))

    def test_create_product_outcome_minimal(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test creating outcome with only required fields."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "80% weekly AI usage",
            None,
            [],
            session,
        )

        assert_that(outcome.name, equal_to("80% weekly AI usage"))
        assert_that(outcome.workspace_id, equal_to(workspace.id))
        assert_that(outcome.description, equal_to(None))
        assert_that(outcome.display_order, equal_to(0))

    def test_create_product_outcome_full_details(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test creating outcome with all fields."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "80% weekly AI usage",
            "Measure AI adoption",
            [],
            session,
        )

        assert_that(outcome.name, equal_to("80% weekly AI usage"))
        assert_that(outcome.description, equal_to("Measure AI adoption"))

    def test_create_product_outcome_with_pillar_links(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test creating outcome linked to pillars."""
        pillar1 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 1", None, session
        )
        pillar2 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 2", None, session
        )

        outcome = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Outcome",
            description=None,
            pillar_ids=[pillar1.id, pillar2.id],
            session=session,
        )

        session.refresh(outcome)
        assert_that(outcome.pillars, has_length(2))
        pillar_ids = {p.id for p in outcome.pillars}
        assert pillar1.id in pillar_ids
        assert pillar2.id in pillar_ids

    def test_create_product_outcome_validates_name_empty(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of empty outcome name."""
        with pytest.raises(DomainException, match="at least 1 character"):
            product_strategy_controller.create_product_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                description=None,
                pillar_ids=[],
                session=session,
            )

    def test_create_product_outcome_validates_name_too_long(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of outcome name exceeding max length."""
        with pytest.raises(DomainException, match="150 characters or less"):
            product_strategy_controller.create_product_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="A" * 151,
                description=None,
                pillar_ids=[],
                session=session,
            )

    def test_create_product_outcome_validates_description_too_long(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of outcome description exceeding max length."""
        with pytest.raises(DomainException, match="3000 characters or less"):
            product_strategy_controller.create_product_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid name",
                description="D" * 3001,
                pillar_ids=[],
                session=session,
            )

    def test_create_product_outcome_enforces_max_limit(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that workspace cannot exceed 10 outcome limit."""
        for i in range(10):
            product_strategy_controller.create_product_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name=f"Outcome {i}",
                description=None,
                pillar_ids=[],
                session=session,
            )

        with pytest.raises(DomainException, match="maximum of 10 product outcomes"):
            product_strategy_controller.create_product_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Outcome 11",
                description=None,
                pillar_ids=[],
                session=session,
            )

    def test_create_product_outcome_display_order_increments(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that display_order increments for each new outcome."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="First",
            description=None,
            pillar_ids=[],
            session=session,
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Second",
            description=None,
            pillar_ids=[],
            session=session,
        )
        outcome3 = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Third",
            description=None,
            pillar_ids=[],
            session=session,
        )

        assert_that(outcome1.display_order, equal_to(0))
        assert_that(outcome2.display_order, equal_to(1))
        assert_that(outcome3.display_order, equal_to(2))

    # Update Product Outcome Tests

    def test_update_product_outcome_with_all_fields(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating outcome with all fields."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Original Name",
            description="Original desc",
            pillar_ids=[],
            session=session,
        )

        updated_name = "Updated Name"
        updated_description = "Updated description"

        updated_outcome = product_strategy_controller.update_product_outcome(
            outcome_id=outcome.id,
            workspace_id=workspace.id,
            name=updated_name,
            description=updated_description,
            pillar_ids=[],
            session=session,
        )

        assert_that(updated_outcome.id, equal_to(outcome.id))
        assert_that(updated_outcome.name, equal_to(updated_name))
        assert_that(updated_outcome.description, equal_to(updated_description))

    def test_update_product_outcome_name_only(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating only outcome name."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Original Name",
            "Original desc",
            [],
            session,
        )

        updated_name = "Updated Name"

        updated_outcome = product_strategy_controller.update_product_outcome(
            outcome.id,
            workspace.id,
            updated_name,
            outcome.description,
            [],
            session,
        )

        assert_that(updated_outcome.name, equal_to(updated_name))
        assert_that(updated_outcome.description, equal_to(outcome.description))

    def test_update_product_outcome_pillar_links(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating outcome pillar linkages."""
        pillar1 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 1", None, session
        )
        pillar2 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 2", None, session
        )
        pillar3 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 3", None, session
        )

        # Create outcome with pillar1 and pillar2
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Test Outcome",
            None,
            [pillar1.id, pillar2.id],
            session,
        )

        session.refresh(outcome)
        assert_that(outcome.pillars, has_length(2))

        # Update to link pillar2 and pillar3 (remove pillar1, add pillar3)
        updated_outcome = product_strategy_controller.update_product_outcome(
            outcome.id,
            workspace.id,
            outcome.name,
            outcome.description,
            [pillar2.id, pillar3.id],
            session,
        )

        session.refresh(updated_outcome)
        assert_that(updated_outcome.pillars, has_length(2))
        pillar_ids = {p.id for p in updated_outcome.pillars}
        assert pillar2.id in pillar_ids
        assert pillar3.id in pillar_ids
        assert pillar1.id not in pillar_ids

    def test_update_product_outcome_validates_name_empty(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of empty name when updating."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Original Name", None, [], session
        )

        with pytest.raises(DomainException, match="at least 1 character"):
            product_strategy_controller.update_product_outcome(
                outcome_id=outcome.id,
                workspace_id=workspace.id,
                name="",
                description=None,
                pillar_ids=[],
                session=session,
            )

    def test_update_product_outcome_validates_name_too_long(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of name exceeding max length when updating."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Original Name", None, [], session
        )

        long_name = "x" * 151
        with pytest.raises(DomainException, match="150 characters or less"):
            product_strategy_controller.update_product_outcome(
                outcome_id=outcome.id,
                workspace_id=workspace.id,
                name=long_name,
                description=None,
                pillar_ids=[],
                session=session,
            )

    def test_update_product_outcome_validates_description_too_long(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test validation of description exceeding max length when updating."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Original Name", None, [], session
        )

        long_description = "x" * 3001
        with pytest.raises(DomainException, match="3000 characters or less"):
            product_strategy_controller.update_product_outcome(
                outcome_id=outcome.id,
                workspace_id=workspace.id,
                name="Valid Name",
                description=long_description,
                pillar_ids=[],
                session=session,
            )

    def test_update_product_outcome_not_found(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test updating non-existent outcome raises DomainException."""
        fake_outcome_id = uuid.uuid4()

        with pytest.raises(DomainException, match="not found"):
            product_strategy_controller.update_product_outcome(
                outcome_id=fake_outcome_id,
                workspace_id=workspace.id,
                name="Some name",
                description=None,
                pillar_ids=[],
                session=session,
            )

    # Delete Product Outcome Tests

    def test_delete_product_outcome_success(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test successfully deleting an outcome."""
        outcome = product_strategy_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Outcome to Delete",
            description=None,
            pillar_ids=[],
            session=session,
        )

        product_strategy_controller.delete_product_outcome(
            outcome_id=outcome.id,
            workspace_id=workspace.id,
            user_id=user.id,
            session=session,
        )

        # Verify outcome is deleted
        outcomes = product_strategy_controller.get_product_outcomes(
            workspace_id=workspace.id,
            session=session,
        )
        assert_that(outcomes, has_length(0))

    def test_delete_product_outcome_not_found(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test deleting non-existent outcome raises DomainException."""
        fake_outcome_id = uuid.uuid4()

        with pytest.raises(DomainException, match="not found"):
            product_strategy_controller.delete_product_outcome(
                outcome_id=fake_outcome_id,
                workspace_id=workspace.id,
                user_id=user.id,
                session=session,
            )

    # Reorder Product Outcomes Tests

    def test_reorder_product_outcomes_success(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test successfully reordering outcomes."""
        # Create 3 outcomes (display_order will be 0, 1, 2)
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 1",
            None,
            [],
            session,
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 2",
            None,
            [],
            session,
        )
        outcome3 = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 3",
            None,
            [],
            session,
        )

        # Reorder: swap outcome1 and outcome3 (0 -> 2, 2 -> 0)
        outcome_orders = {
            outcome1.id: 2,  # Move outcome1 to end
            outcome2.id: 1,  # Keep outcome2 in middle
            outcome3.id: 0,  # Move outcome3 to start
        }

        result = product_strategy_controller.reorder_product_outcomes(
            workspace.id, outcome_orders, session
        )

        # Verify result is ordered correctly
        assert_that(result, has_length(3))
        assert_that(result[0].id, equal_to(outcome3.id))
        assert_that(result[0].display_order, equal_to(0))
        assert_that(result[1].id, equal_to(outcome2.id))
        assert_that(result[1].display_order, equal_to(1))
        assert_that(result[2].id, equal_to(outcome1.id))
        assert_that(result[2].display_order, equal_to(2))

    def test_reorder_product_outcomes_requires_all_outcomes(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that partial reordering (not including all outcomes) raises error."""
        # Create 3 outcomes
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 1", None, [], session
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 2", None, [], session
        )
        # outcome3
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 3", None, [], session
        )

        # Try to reorder only outcome1 and outcome2 (missing outcome3)
        outcome_orders = {
            outcome1.id: 1,
            outcome2.id: 0,
        }

        with pytest.raises(
            DomainException, match="Must provide display order for all 3 outcomes"
        ):
            product_strategy_controller.reorder_product_outcomes(
                workspace.id, outcome_orders, session
            )

    def test_reorder_product_outcomes_validates_incomplete_sequence(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that display orders must form complete sequence [0,1,2,...]."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 1", None, [], session
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 2", None, [], session
        )
        outcome3 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 3", None, [], session
        )

        # Try to set display orders with gaps: [0, 1, 5]
        outcome_orders = {
            outcome1.id: 0,
            outcome2.id: 1,
            outcome3.id: 5,
        }

        with pytest.raises(DomainException, match="Display orders must be"):
            product_strategy_controller.reorder_product_outcomes(
                workspace.id, outcome_orders, session
            )

    def test_reorder_product_outcomes_validates_duplicate_display_order(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that duplicate display_order values raise DomainException."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 1", None, [], session
        )
        outcome2 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 2", None, [], session
        )
        outcome3 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 3", None, [], session
        )

        # Try to set two outcomes to same display_order
        outcome_orders = {
            outcome1.id: 0,
            outcome2.id: 1,
            outcome3.id: 1,
        }

        with pytest.raises(DomainException, match="Display orders must be"):
            product_strategy_controller.reorder_product_outcomes(
                workspace.id, outcome_orders, session
            )

    def test_reorder_product_outcomes_missing_outcome(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that missing an outcome raises DomainException."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 1", None, [], session
        )

        # outcome2
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 2", None, [], session
        )

        # Only include outcome1, missing outcome2
        outcome_orders = {
            outcome1.id: 0,
        }

        with pytest.raises(
            DomainException, match="Must provide display order for all 2 outcomes"
        ):
            product_strategy_controller.reorder_product_outcomes(
                workspace.id, outcome_orders, session
            )

    def test_reorder_product_outcomes_unknown_outcome(
        self, user: User, workspace: Workspace, session: Session
    ):
        """Test that unknown outcome ID raises DomainException."""
        outcome1 = product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 1", None, [], session
        )

        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Outcome 2", None, [], session
        )

        fake_outcome_id = uuid.uuid4()
        outcome_orders = {
            outcome1.id: 0,
            fake_outcome_id: 1,
        }

        with pytest.raises(
            DomainException, match="Product outcome not found: " + str(fake_outcome_id)
        ):
            product_strategy_controller.reorder_product_outcomes(
                workspace.id, outcome_orders, session
            )
