"""Tests for product strategy controller."""

import uuid

import pytest
from hamcrest import assert_that, equal_to, has_entries, not_none

from src.controllers import product_strategy_controller
from src.strategic_planning.aggregates.product_vision import ProductVision
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
