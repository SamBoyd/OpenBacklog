"""Minimal tests for prompt-driven vision workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.product_vision import (
    get_vision_definition_framework,
    get_vision_details,
    submit_product_vision,
)
from src.models import Workspace
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.exceptions import DomainException


class TestGetVisionDetails:
    """Test suite for get_vision_details tool."""

    @pytest.mark.asyncio
    async def test_get_vision_details_success(self):
        """Test that get_vision_details returns vision when exists."""
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.id = uuid.uuid4()
            mock_vision.vision_text = vision_text
            mock_vision.created_at = None
            mock_vision.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = mock_vision

                result = await get_vision_details.fn()

        assert_that(result, has_entries({"status": "success", "type": "vision"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["vision_text"], equal_to(vision_text))

    @pytest.mark.asyncio
    async def test_get_vision_details_not_found(self):
        """Test that get_vision_details returns error when no vision defined."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_details.fn()

        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))
        assert "No vision defined" in result["error_message"]

    @pytest.mark.asyncio
    async def test_get_vision_details_handles_workspace_error(self):
        """Test that get_vision_details handles invalid workspace."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.get_workspace_id_from_request"
            ) as mock_get_workspace_id,
        ):
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_get_workspace_id.side_effect = ValueError("Invalid workspace ID")

            result = await get_vision_details.fn()

        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_get_vision_details_handles_generic_exception(self):
        """Test that get_vision_details handles unexpected exceptions gracefully."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.side_effect = Exception("Unexpected database error")

                result = await get_vision_details.fn()

        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))
        assert "Server error" in result["error_message"]


class TestGetVisionDefinitionFramework:
    """Test suite for get_vision_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock get_workspace_vision to return None (no existing vision)
            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

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
        existing_vision = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock existing vision
            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.vision_text = existing_vision
            mock_vision.created_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = mock_vision

                result = await get_vision_definition_framework.fn()

        # Verify current state shows existing vision
        assert_that(result["current_state"]["has_vision"], equal_to(True))
        assert_that(
            result["current_state"]["current_vision"], equal_to(existing_vision)
        )

    @pytest.mark.asyncio
    async def test_framework_handles_invalid_uuid(self):
        """Test that framework handles invalid workspace_id."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.get_workspace_id_from_request"
            ) as mock_get_workspace_id,
        ):
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            # Mock get_workspace_id_from_request to raise ValueError
            mock_get_workspace_id.side_effect = ValueError("Invalid workspace ID")

            result = await get_vision_definition_framework.fn()

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))


class TestSubmitProductVision:
    """Test suite for submit_product_vision tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_vision_successfully(self, workspace: Workspace):
        """Test that submit successfully creates vision via controller."""
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock controller upsert
            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.id = uuid.uuid4()
            mock_vision.workspace_id = workspace.id
            mock_vision.vision_text = vision_text
            mock_vision.created_at = None
            mock_vision.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.upsert_workspace_vision"
            ) as mock_upsert:
                mock_upsert.return_value = mock_vision

                result = await submit_product_vision.fn(vision_text)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "vision"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

        # Verify controller was called correctly
        mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        vision_text = ""  # Invalid: too short

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock controller to raise DomainException
            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.upsert_workspace_vision"
            ) as mock_upsert:
                mock_upsert.side_effect = DomainException(
                    "Vision text must be 1-1000 characters"
                )

                result = await submit_product_vision.fn(vision_text)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_uuid(self):
        """Test that submit handles invalid workspace_id."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.product_vision.get_workspace_id_from_request"
            ) as mock_get_workspace_id,
        ):
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            # Mock get_workspace_id_from_request to raise ValueError
            mock_get_workspace_id.side_effect = ValueError("Invalid workspace ID")

            result = await submit_product_vision.fn("Some vision text")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))


class TestVisionFrameworkNaturalLanguageMapping:
    """Test suite for natural language mapping in vision framework."""

    @pytest.mark.asyncio
    async def test_framework_includes_conversation_guidelines(self):
        """Test that vision framework includes conversation guidelines."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("conversation_guidelines"))
        guidelines = result["conversation_guidelines"]
        assert_that(guidelines, has_key("say_this"))
        assert_that(guidelines, has_key("not_this"))
        assert_that(guidelines, has_key("example_question"))

    @pytest.mark.asyncio
    async def test_framework_includes_natural_questions(self):
        """Test that vision framework includes natural question mappings."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("natural_questions"))
        assert isinstance(result["natural_questions"], list)
        assert len(result["natural_questions"]) > 0

        first_question = result["natural_questions"][0]
        assert_that(first_question, has_key("framework_term"))
        assert_that(first_question, has_key("natural_question"))

    @pytest.mark.asyncio
    async def test_framework_includes_extraction_guidance(self):
        """Test that vision framework includes extraction guidance."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("extraction_guidance"))
        assert isinstance(result["extraction_guidance"], list)
        assert len(result["extraction_guidance"]) > 0

        first_guidance = result["extraction_guidance"][0]
        assert_that(first_guidance, has_key("from_input"))
        assert_that(first_guidance, has_key("extractions"))

    @pytest.mark.asyncio
    async def test_framework_includes_inference_examples(self):
        """Test that vision framework includes inference examples."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("inference_examples"))
        assert isinstance(result["inference_examples"], list)
        assert len(result["inference_examples"]) > 0

        first_example = result["inference_examples"][0]
        assert_that(first_example, has_key("user_says"))
        assert_that(first_example, has_key("inferences"))


class TestSubmitProductVisionAdditional:
    """Additional test cases for submit_product_vision error handling."""

    @pytest.mark.asyncio
    async def test_submit_handles_validation_error(self):
        """Test that submit handles validation constraint errors."""
        vision_text = "Too short"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.validate_vision_constraints"
            ) as mock_validate:
                mock_validate.side_effect = ValueError(
                    "Vision text must be 50+ characters"
                )

                result = await submit_product_vision.fn(vision_text)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_submit_handles_mcp_context_error(self):
        """Test that submit handles authentication context errors."""
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.get_auth_context"
            ) as mock_auth:
                from src.mcp_server.auth_utils import MCPContextError

                mock_auth.side_effect = MCPContextError("No workspace in context")

                result = await submit_product_vision.fn(vision_text)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_submit_handles_generic_exception(self):
        """Test that submit handles unexpected exceptions gracefully."""
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.upsert_workspace_vision"
            ) as mock_upsert:
                mock_upsert.side_effect = Exception("Unexpected database error")

                result = await submit_product_vision.fn(vision_text)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "vision"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_submit_response_includes_next_steps(self):
        """Test that successful submit response includes next_steps guidance."""
        vision_text = "Enable developers to manage tasks without leaving their IDE"

        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.id = uuid.uuid4()
            mock_vision.vision_text = vision_text
            mock_vision.created_at = None
            mock_vision.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.upsert_workspace_vision"
            ) as mock_upsert:
                mock_upsert.return_value = mock_vision

                result = await submit_product_vision.fn(vision_text)

        # Verify next_steps are present and guide to pillars
        assert_that(result, has_key("next_steps"))
        assert isinstance(result["next_steps"], list)
        assert len(result["next_steps"]) > 0

        # Verify that next steps mention pillars (the natural next workflow step)
        next_steps_text = " ".join(result["next_steps"])
        assert "pillar" in next_steps_text.lower()


class TestVisionFrameworkContent:
    """Test suite for vision framework content quality."""

    @pytest.mark.asyncio
    async def test_framework_includes_criteria(self):
        """Test that vision framework includes well-defined criteria."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("criteria"))
        assert isinstance(result["criteria"], list)
        assert len(result["criteria"]) > 0

    @pytest.mark.asyncio
    async def test_framework_includes_examples(self):
        """Test that vision framework includes concrete examples."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("examples"))
        assert isinstance(result["examples"], list)
        assert len(result["examples"]) > 0

        # Verify example structure
        first_example = result["examples"][0]
        assert_that(first_example, has_key("text"))
        assert_that(first_example, has_key("why_good"))

    @pytest.mark.asyncio
    async def test_framework_includes_anti_patterns(self):
        """Test that vision framework includes anti-patterns for guidance."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result, has_key("anti_patterns"))
        assert isinstance(result["anti_patterns"], list)
        assert len(result["anti_patterns"]) > 0

        # Verify anti-pattern structure
        first_pattern = result["anti_patterns"][0]
        assert_that(first_pattern, has_key("example"))
        assert_that(first_pattern, has_key("why_bad"))
        assert_that(first_pattern, has_key("better"))

    @pytest.mark.asyncio
    async def test_framework_entity_type_is_vision(self):
        """Test that framework correctly identifies itself as vision type."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_vision.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_vision.strategic_controller.get_workspace_vision"
            ) as mock_get_vision:
                mock_get_vision.return_value = None

                result = await get_vision_definition_framework.fn()

        assert_that(result["entity_type"], equal_to("vision"))
