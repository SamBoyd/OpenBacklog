"""Tests for product strategy controller."""

import uuid

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_length, not_none

from src.strategic_planning import controller as product_strategy_controller
from src.strategic_planning.exceptions import DomainException


class TestWorkspaceVision:
    def test_get_workspace_vision_exists(self, workspace, session, product_vision):
        """Test getting existing workspace vision."""
        vision = product_strategy_controller.get_workspace_vision(workspace.id, session)
        assert_that(vision, not_none())
        assert_that(vision.vision_text, equal_to(product_vision.vision_text))

    def test_upsert_refines_existing_vision(self, user, workspace, session):
        """Test refining existing vision."""
        refined_text = "Build the very best product for developers"

        vision = product_strategy_controller.upsert_workspace_vision(
            workspace.id, user.id, refined_text, session
        )

        assert_that(vision.vision_text, equal_to(refined_text))
        assert_that(vision.workspace_id, equal_to(workspace.id))

    def test_upsert_validates_vision_text_empty(self, user, workspace, session):
        """Test validation of empty vision text."""
        with pytest.raises(DomainException, match="at least 1 character"):
            product_strategy_controller.upsert_workspace_vision(
                workspace.id, user.id, "", session
            )

    def test_upsert_validates_vision_text_too_long(self, user, workspace, session):
        """Test validation of vision text exceeding max length."""
        with pytest.raises(DomainException, match="1000 characters or less"):
            product_strategy_controller.upsert_workspace_vision(
                workspace.id, user.id, "A" * 1001, session
            )
