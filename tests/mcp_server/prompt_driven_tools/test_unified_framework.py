"""Tests for unified framework tool."""

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, raises

from src.mcp_server.prompt_driven_tools.unified_framework import get_framework


class TestGetFramework:
    """Test suite for unified get_framework tool."""

    @pytest.mark.asyncio
    async def test_get_framework_hero(self):
        """Test routing to hero framework."""
        expected_framework = {
            "entity_type": "hero",
            "purpose": "Define who you're building for",
            "criteria": ["Specific person with a name"],
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_hero_definition_framework"
        ) as mock_hero_framework:
            mock_hero_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="hero")

        assert_that(result, equal_to(expected_framework))
        mock_hero_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_villain(self):
        """Test routing to villain framework."""
        expected_framework = {
            "entity_type": "villain",
            "purpose": "Define problems blocking your hero",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_villain_definition_framework"
        ) as mock_villain_framework:
            mock_villain_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="villain")

        assert_that(result, equal_to(expected_framework))
        mock_villain_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_conflict(self):
        """Test routing to conflict framework."""
        expected_framework = {
            "entity_type": "conflict",
            "purpose": "Create conflict between hero and villain",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_conflict_creation_framework"
        ) as mock_conflict_framework:
            mock_conflict_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="conflict")

        assert_that(result, equal_to(expected_framework))
        mock_conflict_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_vision(self):
        """Test routing to vision framework."""
        expected_framework = {
            "entity_type": "vision",
            "purpose": "Define the change you want to make",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_vision_definition_framework"
        ) as mock_vision_framework:
            mock_vision_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="vision")

        assert_that(result, equal_to(expected_framework))
        mock_vision_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_pillar(self):
        """Test routing to pillar framework."""
        expected_framework = {
            "entity_type": "pillar",
            "purpose": "Define strategic pillars",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_pillar_definition_framework"
        ) as mock_pillar_framework:
            mock_pillar_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="pillar")

        assert_that(result, equal_to(expected_framework))
        mock_pillar_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_outcome(self):
        """Test routing to outcome framework."""
        expected_framework = {
            "entity_type": "outcome",
            "purpose": "Define product outcomes",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_outcome_definition_framework"
        ) as mock_outcome_framework:
            mock_outcome_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="outcome")

        assert_that(result, equal_to(expected_framework))
        mock_outcome_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_theme(self):
        """Test routing to theme framework."""
        expected_framework = {
            "entity_type": "theme",
            "purpose": "Define roadmap themes",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_theme_exploration_framework"
        ) as mock_theme_framework:
            mock_theme_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="theme")

        assert_that(result, equal_to(expected_framework))
        mock_theme_framework.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_framework_initiative(self):
        """Test routing to initiative framework."""
        expected_framework = {
            "entity_type": "initiative",
            "purpose": "Define strategic initiatives",
        }

        with patch(
            "src.mcp_server.prompt_driven_tools.unified_framework.get_strategic_initiative_definition_framework"
        ) as mock_initiative_framework:
            mock_initiative_framework.return_value = expected_framework

            result = await get_framework.fn(entity_type="initiative")

        assert_that(result, equal_to(expected_framework))
        mock_initiative_framework.assert_called_once()
