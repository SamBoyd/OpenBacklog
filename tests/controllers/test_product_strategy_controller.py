"""Tests for product strategy controller."""

import uuid

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_length, not_none

from src.controllers import product_strategy_controller
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


def test_get_workspace_vision_not_found(workspace, session):
    """Test getting vision for workspace with no vision."""
    vision = product_strategy_controller.get_workspace_vision(workspace.id, session)
    assert_that(vision, equal_to(None))


def test_get_workspace_vision_exists(workspace, session, product_vision):
    """Test getting existing workspace vision."""
    vision = product_strategy_controller.get_workspace_vision(workspace.id, session)
    assert_that(vision, not_none())
    assert_that(vision.vision_text, equal_to(product_vision.vision_text))


def test_upsert_creates_new_vision(user, workspace, session):
    """Test creating new vision."""
    vision_text = "Build the best product"

    vision = product_strategy_controller.upsert_workspace_vision(
        workspace.id, user.id, vision_text, session
    )

    assert_that(vision.vision_text, equal_to(vision_text))
    assert_that(vision.workspace_id, equal_to(workspace.id))


def test_upsert_updates_existing_vision(user, workspace, session, product_vision):
    """Test updating existing vision."""
    new_text = "Updated vision text"

    vision = product_strategy_controller.upsert_workspace_vision(
        workspace.id, user.id, new_text, session
    )

    assert_that(vision.id, equal_to(product_vision.id))
    assert_that(vision.vision_text, equal_to(new_text))


def test_upsert_validates_vision_text_empty(user, workspace, session):
    """Test validation of empty vision text."""
    with pytest.raises(DomainException, match="at least 1 character"):
        product_strategy_controller.upsert_workspace_vision(
            workspace.id, user.id, "", session
        )


def test_upsert_validates_vision_text_too_long(user, workspace, session):
    """Test validation of vision text exceeding max length."""
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.upsert_workspace_vision(
            workspace.id, user.id, "A" * 1001, session
        )


def test_upsert_workspace_not_found(user, session):
    """Test upserting vision for non-existent workspace raises IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    fake_workspace_id = uuid.uuid4()
    with pytest.raises(IntegrityError):
        product_strategy_controller.upsert_workspace_vision(
            fake_workspace_id, user.id, "Some vision text", session
        )


# Strategic Pillar Tests


def test_get_strategic_pillars_empty(workspace, session):
    """Test getting pillars for workspace with no pillars."""
    pillars = product_strategy_controller.get_strategic_pillars(workspace.id, session)
    assert_that(pillars, has_length(0))


def test_get_strategic_pillars_returns_ordered_list(user, workspace, session):
    """Test getting pillars returns list ordered by display_order."""
    # Create 3 pillars
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )
    pillar3 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 3", None, None, session
    )

    pillars = product_strategy_controller.get_strategic_pillars(workspace.id, session)

    assert_that(pillars, has_length(3))
    assert_that(pillars[0].id, equal_to(pillar1.id))
    assert_that(pillars[1].id, equal_to(pillar2.id))
    assert_that(pillars[2].id, equal_to(pillar3.id))


def test_create_strategic_pillar_with_all_fields(user, workspace, session):
    """Test creating pillar with all fields."""
    name = "Developer Experience"
    description = "Make developers love our product"
    anti_strategy = "Not enterprise features"

    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, name, description, anti_strategy, session
    )

    assert_that(pillar.name, equal_to(name))
    assert_that(pillar.description, equal_to(description))
    assert_that(pillar.anti_strategy, equal_to(anti_strategy))
    assert_that(pillar.workspace_id, equal_to(workspace.id))
    assert_that(pillar.display_order, equal_to(0))


def test_create_strategic_pillar_with_only_name(user, workspace, session):
    """Test creating pillar with only required name field."""
    name = "Developer Experience"

    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, name, None, None, session
    )

    assert_that(pillar.name, equal_to(name))
    assert_that(pillar.description, equal_to(None))
    assert_that(pillar.anti_strategy, equal_to(None))


def test_create_strategic_pillar_assigns_display_order(user, workspace, session):
    """Test that display_order is assigned based on existing pillar count."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )

    assert_that(pillar1.display_order, equal_to(0))
    assert_that(pillar2.display_order, equal_to(1))


def test_create_strategic_pillar_validates_name_empty(user, workspace, session):
    """Test validation of empty pillar name."""
    with pytest.raises(DomainException, match="at least 1 character"):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "", None, None, session
        )


def test_create_strategic_pillar_validates_name_too_long(user, workspace, session):
    """Test validation of pillar name exceeding max length."""
    long_name = "x" * 101
    with pytest.raises(DomainException, match="100 characters or less"):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, long_name, None, None, session
        )


def test_create_strategic_pillar_validates_description_too_long(
    user, workspace, session
):
    """Test validation of description exceeding max length."""
    long_description = "x" * 1001
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Valid Name", long_description, None, session
        )


def test_create_strategic_pillar_validates_anti_strategy_too_long(
    user, workspace, session
):
    """Test validation of anti_strategy exceeding max length."""
    long_anti_strategy = "x" * 1001
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Valid Name", None, long_anti_strategy, session
        )


def test_create_strategic_pillar_enforces_5_pillar_limit(user, workspace, session):
    """Test that creating 6th pillar raises DomainException."""
    # Create 5 pillars
    for i in range(5):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, f"Pillar {i}", None, None, session
        )

    # Attempt to create 6th pillar
    with pytest.raises(DomainException, match="maximum of 5 strategic pillars"):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 6", None, None, session
        )


def test_create_strategic_pillar_enforces_unique_name_per_workspace(
    user, workspace, session
):
    """Test that duplicate pillar names in same workspace raise IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Developer Experience", None, None, session
    )

    with pytest.raises(IntegrityError):
        product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Developer Experience", None, None, session
        )


def test_create_strategic_pillar_workspace_not_found(user, session):
    """Test creating pillar for non-existent workspace raises IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    fake_workspace_id = uuid.uuid4()
    with pytest.raises(IntegrityError):
        product_strategy_controller.create_strategic_pillar(
            fake_workspace_id, user.id, "Some pillar", None, None, session
        )


# Update Strategic Pillar Tests


def test_update_strategic_pillar_with_all_fields(user, workspace, session):
    """Test updating pillar with all fields."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id,
        user.id,
        "Original Name",
        "Original desc",
        "Original anti",
        session,
    )

    updated_name = "Updated Name"
    updated_description = "Updated description"
    updated_anti_strategy = "Updated anti-strategy"

    updated_pillar = product_strategy_controller.update_strategic_pillar(
        pillar.id,
        workspace.id,
        updated_name,
        updated_description,
        updated_anti_strategy,
        session,
    )

    assert_that(updated_pillar.id, equal_to(pillar.id))
    assert_that(updated_pillar.name, equal_to(updated_name))
    assert_that(updated_pillar.description, equal_to(updated_description))
    assert_that(updated_pillar.anti_strategy, equal_to(updated_anti_strategy))


def test_update_strategic_pillar_name_only(user, workspace, session):
    """Test updating only pillar name."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id,
        user.id,
        "Original Name",
        "Original desc",
        "Original anti",
        session,
    )

    updated_name = "Updated Name"

    updated_pillar = product_strategy_controller.update_strategic_pillar(
        pillar.id,
        workspace.id,
        updated_name,
        pillar.description,
        pillar.anti_strategy,
        session,
    )

    assert_that(updated_pillar.name, equal_to(updated_name))
    assert_that(updated_pillar.description, equal_to(pillar.description))
    assert_that(updated_pillar.anti_strategy, equal_to(pillar.anti_strategy))


def test_update_strategic_pillar_validates_name_empty(user, workspace, session):
    """Test validation of empty name when updating."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Original Name", None, None, session
    )

    with pytest.raises(DomainException, match="at least 1 character"):
        product_strategy_controller.update_strategic_pillar(
            pillar.id, workspace.id, "", None, None, session
        )


def test_update_strategic_pillar_validates_name_too_long(user, workspace, session):
    """Test validation of name exceeding max length when updating."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Original Name", None, None, session
    )

    long_name = "x" * 101
    with pytest.raises(DomainException, match="100 characters or less"):
        product_strategy_controller.update_strategic_pillar(
            pillar.id, workspace.id, long_name, None, None, session
        )


def test_update_strategic_pillar_validates_description_too_long(
    user, workspace, session
):
    """Test validation of description exceeding max length when updating."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Original Name", None, None, session
    )

    long_description = "x" * 1001
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.update_strategic_pillar(
            pillar.id, workspace.id, "Valid Name", long_description, None, session
        )


def test_update_strategic_pillar_validates_anti_strategy_too_long(
    user, workspace, session
):
    """Test validation of anti_strategy exceeding max length when updating."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Original Name", None, None, session
    )

    long_anti_strategy = "x" * 1001
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.update_strategic_pillar(
            pillar.id, workspace.id, "Valid Name", None, long_anti_strategy, session
        )


def test_update_strategic_pillar_enforces_unique_name(user, workspace, session):
    """Test that updating to duplicate name raises IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )

    with pytest.raises(IntegrityError):
        product_strategy_controller.update_strategic_pillar(
            pillar2.id, workspace.id, "Pillar 1", None, None, session
        )


def test_update_strategic_pillar_not_found(user, workspace, session):
    """Test updating non-existent pillar raises DomainException."""
    fake_pillar_id = uuid.uuid4()

    with pytest.raises(DomainException, match="not found"):
        product_strategy_controller.update_strategic_pillar(
            fake_pillar_id, workspace.id, "Some name", None, None, session
        )


# Delete Strategic Pillar Tests


def test_delete_strategic_pillar_success(user, workspace, session):
    """Test successfully deleting a pillar."""
    pillar = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar to Delete", None, None, session
    )

    product_strategy_controller.delete_strategic_pillar(
        pillar.id, workspace.id, user.id, session
    )

    # Verify pillar is deleted
    pillars = product_strategy_controller.get_strategic_pillars(workspace.id, session)
    assert_that(pillars, has_length(0))


def test_delete_strategic_pillar_not_found(user, workspace, session):
    """Test deleting non-existent pillar raises DomainException."""
    fake_pillar_id = uuid.uuid4()

    with pytest.raises(DomainException, match="not found"):
        product_strategy_controller.delete_strategic_pillar(
            fake_pillar_id, workspace.id, user.id, session
        )


# Reorder Strategic Pillars Tests


def test_reorder_strategic_pillars_success(user, workspace, session):
    """Test successfully reordering pillars."""
    # Create 3 pillars (display_order will be 0, 1, 2)
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )
    pillar3 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 3", None, None, session
    )

    # Reorder: swap pillar1 and pillar3 (0 -> 2, 2 -> 0)
    pillar_orders = {
        pillar1.id: 2,  # Move pillar1 to end
        pillar2.id: 1,  # Keep pillar2 in middle
        pillar3.id: 0,  # Move pillar3 to start
    }

    result = product_strategy_controller.reorder_strategic_pillars(
        workspace.id, pillar_orders, session
    )

    # Verify result is ordered correctly
    assert_that(result, has_length(3))
    assert_that(result[0].id, equal_to(pillar3.id))
    assert_that(result[0].display_order, equal_to(0))
    assert_that(result[1].id, equal_to(pillar2.id))
    assert_that(result[1].display_order, equal_to(1))
    assert_that(result[2].id, equal_to(pillar1.id))
    assert_that(result[2].display_order, equal_to(2))


def test_reorder_strategic_pillars_requires_all_pillars(user, workspace, session):
    """Test that partial reordering (not including all pillars) raises error."""
    # Create 3 pillars
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )
    pillar3 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 3", None, None, session
    )

    # Try to reorder only pillar1 and pillar2 (missing pillar3)
    pillar_orders = {
        pillar1.id: 1,
        pillar2.id: 0,
    }

    with pytest.raises(
        DomainException, match="Must provide display order for all 3 pillars"
    ):
        product_strategy_controller.reorder_strategic_pillars(
            workspace.id, pillar_orders, session
        )


def test_reorder_strategic_pillars_validates_incomplete_sequence(
    user, workspace, session
):
    """Test that display orders must form complete sequence [0,1,2,...]."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )
    pillar3 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 3", None, None, session
    )

    # Try to set display orders with gaps: [0, 1, 5]
    pillar_orders = {
        pillar1.id: 0,
        pillar2.id: 1,
        pillar3.id: 5,
    }

    with pytest.raises(DomainException, match="Display orders must be"):
        product_strategy_controller.reorder_strategic_pillars(
            workspace.id, pillar_orders, session
        )


def test_reorder_strategic_pillars_validates_duplicate_display_order(
    user, workspace, session
):
    """Test that duplicate display_order values raise DomainException."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )
    pillar3 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 3", None, None, session
    )

    # Try to set two pillars to same display_order
    pillar_orders = {
        pillar1.id: 0,
        pillar2.id: 1,
        pillar3.id: 1,
    }

    with pytest.raises(DomainException, match="Display orders must be"):
        product_strategy_controller.reorder_strategic_pillars(
            workspace.id, pillar_orders, session
        )


def test_reorder_strategic_pillars_missing_pillar(user, workspace, session):
    """Test that missing a pillar raises DomainException."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )

    # Only include pillar1, missing pillar2
    pillar_orders = {
        pillar1.id: 0,
    }

    with pytest.raises(
        DomainException, match="Must provide display order for all 2 pillars"
    ):
        product_strategy_controller.reorder_strategic_pillars(
            workspace.id, pillar_orders, session
        )


def test_reorder_strategic_pillars_unknown_pillar(user, workspace, session):
    """Test that unknown pillar ID raises DomainException."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )

    product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )

    fake_pillar_id = uuid.uuid4()
    pillar_orders = {
        pillar1.id: 0,
        fake_pillar_id: 1,
    }

    with pytest.raises(
        DomainException, match="Strategic pillar not found: " + str(fake_pillar_id)
    ):
        product_strategy_controller.reorder_strategic_pillars(
            workspace.id, pillar_orders, session
        )


# Product Outcome Tests


def test_get_product_outcomes_empty(workspace, session):
    """Test getting outcomes for workspace with no outcomes."""
    outcomes = product_strategy_controller.get_product_outcomes(workspace.id, session)
    assert_that(outcomes, has_length(0))


def test_get_product_outcomes_returns_ordered_list(user, workspace, session):
    """Test getting outcomes returns list ordered by display_order."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Outcome 1",
        None,
        None,
        None,
        [],
        session,
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Outcome 2",
        None,
        None,
        None,
        [],
        session,
    )
    outcome3 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Outcome 3",
        None,
        None,
        None,
        [],
        session,
    )

    outcomes = product_strategy_controller.get_product_outcomes(workspace.id, session)

    assert_that(outcomes, has_length(3))
    assert_that(outcomes[0].id, equal_to(outcome1.id))
    assert_that(outcomes[1].id, equal_to(outcome2.id))
    assert_that(outcomes[2].id, equal_to(outcome3.id))
    assert_that(outcomes[0].display_order, equal_to(0))
    assert_that(outcomes[1].display_order, equal_to(1))
    assert_that(outcomes[2].display_order, equal_to(2))


def test_create_product_outcome_minimal(user, workspace, session):
    """Test creating outcome with only required fields."""
    outcome = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "80% weekly AI usage",
        None,
        None,
        None,
        [],
        session,
    )

    assert_that(outcome.name, equal_to("80% weekly AI usage"))
    assert_that(outcome.workspace_id, equal_to(workspace.id))
    assert_that(outcome.description, equal_to(None))
    assert_that(outcome.metrics, equal_to(None))
    assert_that(outcome.time_horizon_months, equal_to(None))
    assert_that(outcome.display_order, equal_to(0))


def test_create_product_outcome_full_details(user, workspace, session):
    """Test creating outcome with all fields."""
    outcome = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "80% weekly AI usage",
        "Measure AI adoption",
        "Weekly active users using AI features",
        12,
        [],
        session,
    )

    assert_that(outcome.name, equal_to("80% weekly AI usage"))
    assert_that(outcome.description, equal_to("Measure AI adoption"))
    assert_that(outcome.metrics, equal_to("Weekly active users using AI features"))
    assert_that(outcome.time_horizon_months, equal_to(12))


def test_create_product_outcome_with_pillar_links(user, workspace, session):
    """Test creating outcome linked to pillars."""
    pillar1 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 1", None, None, session
    )
    pillar2 = product_strategy_controller.create_strategic_pillar(
        workspace.id, user.id, "Pillar 2", None, None, session
    )

    outcome = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Test Outcome",
        None,
        None,
        None,
        [pillar1.id, pillar2.id],
        session,
    )

    session.refresh(outcome)
    assert_that(outcome.pillars, has_length(2))
    pillar_ids = {p.id for p in outcome.pillars}
    assert pillar1.id in pillar_ids
    assert pillar2.id in pillar_ids


def test_create_product_outcome_validates_name_empty(user, workspace, session):
    """Test validation of empty outcome name."""
    with pytest.raises(DomainException, match="at least 1 character"):
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "", None, None, None, [], session
        )


def test_create_product_outcome_validates_name_too_long(user, workspace, session):
    """Test validation of outcome name exceeding max length."""
    with pytest.raises(DomainException, match="150 characters or less"):
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "A" * 151, None, None, None, [], session
        )


def test_create_product_outcome_validates_description_too_long(
    user, workspace, session
):
    """Test validation of outcome description exceeding max length."""
    with pytest.raises(DomainException, match="1500 characters or less"):
        product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Valid name",
            "D" * 1501,
            None,
            None,
            [],
            session,
        )


def test_create_product_outcome_validates_metrics_too_long(user, workspace, session):
    """Test validation of outcome metrics exceeding max length."""
    with pytest.raises(DomainException, match="1000 characters or less"):
        product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Valid name",
            None,
            "M" * 1001,
            None,
            [],
            session,
        )


def test_create_product_outcome_validates_time_horizon_too_low(
    user, workspace, session
):
    """Test validation of time horizon below minimum."""
    with pytest.raises(DomainException, match="between 6-36 months"):
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Valid name", None, None, 5, [], session
        )


def test_create_product_outcome_validates_time_horizon_too_high(
    user, workspace, session
):
    """Test validation of time horizon above maximum."""
    with pytest.raises(DomainException, match="between 6-36 months"):
        product_strategy_controller.create_product_outcome(
            workspace.id, user.id, "Valid name", None, None, 37, [], session
        )


def test_create_product_outcome_enforces_max_limit(user, workspace, session):
    """Test that workspace cannot exceed 10 outcome limit."""
    for i in range(10):
        product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            f"Outcome {i}",
            None,
            None,
            None,
            [],
            session,
        )

    with pytest.raises(DomainException, match="maximum of 10 product outcomes"):
        product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome 11",
            None,
            None,
            None,
            [],
            session,
        )


def test_create_product_outcome_display_order_increments(user, workspace, session):
    """Test that display_order increments for each new outcome."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "First",
        None,
        None,
        None,
        [],
        session,
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Second",
        None,
        None,
        None,
        [],
        session,
    )
    outcome3 = product_strategy_controller.create_product_outcome(
        workspace.id,
        user.id,
        "Third",
        None,
        None,
        None,
        [],
        session,
    )

    assert_that(outcome1.display_order, equal_to(0))
    assert_that(outcome2.display_order, equal_to(1))
    assert_that(outcome3.display_order, equal_to(2))
