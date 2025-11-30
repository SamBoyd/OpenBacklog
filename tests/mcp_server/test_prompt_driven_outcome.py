"""Minimal tests for prompt-driven outcome workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.strategic_foundation import (
    get_outcome_definition_framework,
    submit_product_outcome,
)
from src.models import Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome


class TestGetOutcomeDefinitionFramework:
    """Test suite for get_outcome_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_get_outcomes.return_value = []
                mock_get_pillars.return_value = []

                result = await get_outcome_definition_framework.fn()

        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("current_state"))
        assert_that(result["current_state"], has_key("current_outcomes"))
        assert_that(result["current_state"], has_key("available_pillars"))


class TestSubmitProductOutcome:
    """Test suite for submit_product_outcome tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_outcome_successfully(self, workspace: Workspace):
        """Test that submit successfully creates outcome via controller."""
        name = "Developer Daily Adoption"
        description = "Goal: Increase daily active IDE plugin users. Baseline: 30% daily active. Target: 80% daily active. Timeline: 6 months."

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.uuid4()
            mock_outcome.workspace_id = workspace.id
            mock_outcome.name = name
            mock_outcome.description = description
            mock_outcome.display_order = 0
            mock_outcome.pillars = []
            mock_outcome.created_at = None
            mock_outcome.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.create_product_outcome"
            ) as mock_create:
                mock_create.return_value = mock_outcome

                result = await submit_product_outcome.fn(
                    name, description, draft_mode=False
                )

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))


class TestSubmitProductOutcomeDraftMode:
    """Test suite for submit_product_outcome draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace: Workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        name = "Developer Daily Adoption"
        description = "Goal: Increase daily active IDE plugin users. Baseline: 30% daily active. Target: 80% daily active. Timeline: 6 months."

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to prevent DB queries
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.validate_outcome_constraints"
            ) as mock_validate:
                mock_validate.return_value = None  # Validation passes

                # Mock get_auth_context
                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    # Mock get_product_outcomes to return empty list for display_order calculation
                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_product_outcomes"
                    ) as mock_get_outcomes:
                        mock_get_outcomes.return_value = []

                        # Call tool with draft_mode=True
                        result = await submit_product_outcome.fn(
                            name, description, draft_mode=True
                        )

        # Assert draft response structure
        assert_that(
            result, has_entries({"status": "success", "type": "product_outcome"})
        )
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["name"], equal_to(name))
        assert_that(data["description"], equal_to(description))
        assert_that(data["display_order"], equal_to(0))  # First outcome
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))

        # Verify validation was called
        mock_validate.assert_called_once()
