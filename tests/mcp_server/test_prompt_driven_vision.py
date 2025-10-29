"""Minimal tests for prompt-driven vision workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.strategic_foundation import (
    get_vision_definition_framework,
    submit_product_vision,
)
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.exceptions import DomainException


class TestGetVisionDefinitionFramework:
    """Test suite for get_vision_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        workspace_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock get_workspace_vision to return None (no existing vision)
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn(workspace_id)

        # Verify framework has required fields
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("questions_to_explore"))
        assert_that(result, has_key("anti_patterns"))
        assert_that(result, has_key("coaching_tips"))
        assert_that(result, has_key("current_state"))

        # Verify current state shows no vision
        assert_that(result["current_state"]["has_vision"], equal_to(False))

    @pytest.mark.asyncio
    async def test_framework_includes_existing_vision(self):
        """Test that framework includes current vision if exists."""
        workspace_id = str(uuid.uuid4())
        existing_vision = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock existing vision
            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.vision_text = existing_vision
            mock_vision.created_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = mock_vision

                result = await get_vision_definition_framework.fn(workspace_id)

        # Verify current state shows existing vision
        assert_that(result["current_state"]["has_vision"], equal_to(True))
        assert_that(
            result["current_state"]["current_vision"], equal_to(existing_vision)
        )

    @pytest.mark.asyncio
    async def test_framework_handles_invalid_uuid(self):
        """Test that framework handles invalid workspace_id."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await get_vision_definition_framework.fn("not-a-uuid")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))


class TestSubmitProductVision:
    """Test suite for submit_product_vision tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_vision_successfully(self):
        """Test that submit successfully creates vision via controller."""
        workspace_id = str(uuid.uuid4())
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock user ID
            mock_user_id = uuid.uuid4()
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.get_user_id_from_request"
            ) as mock_get_user:
                mock_get_user.return_value = mock_user_id

                # Mock controller upsert
                mock_vision = MagicMock(spec=ProductVision)
                mock_vision.id = uuid.uuid4()
                mock_vision.workspace_id = uuid.UUID(workspace_id)
                mock_vision.vision_text = vision_text
                mock_vision.created_at = None
                mock_vision.updated_at = None

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.upsert_workspace_vision"
                ) as mock_upsert:
                    mock_upsert.return_value = mock_vision

                    result = await submit_product_vision.fn(workspace_id, vision_text)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "vision"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

        # Verify controller was called correctly
        mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        workspace_id = str(uuid.uuid4())
        vision_text = ""  # Invalid: too short

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_user_id = uuid.uuid4()
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.get_user_id_from_request"
            ) as mock_get_user:
                mock_get_user.return_value = mock_user_id

                # Mock controller to raise DomainException
                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.upsert_workspace_vision"
                ) as mock_upsert:
                    mock_upsert.side_effect = DomainException(
                        "Vision text must be 1-1000 characters"
                    )

                    result = await submit_product_vision.fn(workspace_id, vision_text)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_uuid(self):
        """Test that submit handles invalid workspace_id."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await submit_product_vision.fn("not-a-uuid", "Some vision text")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
