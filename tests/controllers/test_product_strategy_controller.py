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
