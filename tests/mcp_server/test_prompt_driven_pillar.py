"""Minimal tests for prompt-driven pillar workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.strategic_foundation import (
    get_pillar_definition_framework,
    submit_strategic_pillar,
)
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


class TestGetPillarDefinitionFramework:
    """Test suite for get_pillar_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
            ) as mock_get_pillars:
                mock_get_pillars.return_value = []

                result = await get_pillar_definition_framework.fn()

        # Verify framework structure
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("current_state"))

        # Verify pillar limit info
        assert_that(result["current_state"]["pillar_count"], equal_to(0))
        assert_that(result["current_state"]["max_pillars"], equal_to(5))
        assert_that(result["current_state"]["remaining"], equal_to(5))

    @pytest.mark.asyncio
    async def test_framework_includes_existing_pillars(self):
        """Test that framework includes current pillars."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock existing pillars
            mock_pillar = MagicMock(spec=StrategicPillar)
            mock_pillar.id = uuid.uuid4()
            mock_pillar.name = "Deep IDE Integration"
            mock_pillar.description = "Seamless IDE experience"
            mock_pillar.anti_strategy = "No web-first"

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
            ) as mock_get_pillars:
                mock_get_pillars.return_value = [mock_pillar]

                result = await get_pillar_definition_framework.fn()

        # Verify current state shows existing pillar
        assert_that(result["current_state"]["pillar_count"], equal_to(1))
        assert_that(result["current_state"]["remaining"], equal_to(4))
        assert_that(len(result["current_state"]["current_pillars"]), equal_to(1))


class TestSubmitStrategicPillar:
    """Test suite for submit_strategic_pillar tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_pillar_successfully(self, workspace):
        """Test that submit successfully creates pillar via controller."""
        name = "Deep IDE Integration"
        description = "Strategy: Seamless IDE experience. Anti-Strategy: No web-first"

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock controller create
            mock_pillar = MagicMock(spec=StrategicPillar)
            mock_pillar.id = uuid.uuid4()
            mock_pillar.workspace_id = workspace.id
            mock_pillar.name = name
            mock_pillar.description = description
            mock_pillar.display_order = 0
            mock_pillar.outcomes = []
            mock_pillar.created_at = None
            mock_pillar.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.create_strategic_pillar"
            ) as mock_create:
                mock_create.return_value = mock_pillar

                # Mock get_strategic_pillars for counting
                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars:
                    mock_get_pillars.return_value = [mock_pillar]

                    result = await submit_strategic_pillar.fn(name, description)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.create_strategic_pillar"
            ) as mock_create:
                mock_create.side_effect = DomainException("Pillar limit exceeded")

                result = await submit_strategic_pillar.fn(
                    "Pillar Name", "Strategy: X. Anti-Strategy: Y."
                )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
