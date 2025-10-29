"""Minimal tests for prompt-driven utility tools (Phase 3)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.utilities import (
    connect_outcome_to_pillars,
    review_strategic_foundation,
)
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar


class TestReviewStrategicFoundation:
    """Test suite for review_strategic_foundation tool."""

    @pytest.mark.asyncio
    async def test_review_foundation_healthy(self):
        """Test that review returns healthy status when all elements present."""
        workspace_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock healthy foundation
            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.id = uuid.uuid4()
            mock_vision.workspace_id = uuid.UUID(workspace_id)
            mock_vision.vision_text = "Test vision"
            mock_vision.created_at = None
            mock_vision.updated_at = None

            mock_pillar1 = MagicMock(spec=StrategicPillar)
            mock_pillar1.id = uuid.uuid4()
            mock_pillar1.name = "Pillar 1"
            mock_pillar1.outcomes = [MagicMock()]  # Has outcomes

            mock_pillar2 = MagicMock(spec=StrategicPillar)
            mock_pillar2.id = uuid.uuid4()
            mock_pillar2.name = "Pillar 2"
            mock_pillar2.outcomes = [MagicMock()]

            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.uuid4()
            mock_outcome.name = "Outcome 1"
            mock_outcome.pillars = [mock_pillar1]  # Linked

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_workspace_vision"
                ) as mock_get_vision,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
            ):
                mock_get_vision.return_value = mock_vision
                mock_get_pillars.return_value = [mock_pillar1, mock_pillar2]
                mock_get_outcomes.return_value = [mock_outcome]

                result = await review_strategic_foundation.fn(workspace_id)

        # Verify healthy status
        assert_that(result, has_key("status"))
        assert_that(result["status"], equal_to("healthy"))
        assert_that(result, has_key("vision"))
        assert_that(result["vision"]["exists"], equal_to(True))
        assert_that(result, has_key("pillars"))
        assert_that(result["pillars"]["count"], equal_to(2))
        assert_that(result, has_key("outcomes"))
        assert_that(result["outcomes"]["count"], equal_to(1))

    @pytest.mark.asyncio
    async def test_review_foundation_partial(self):
        """Test that review identifies gaps in foundation."""
        workspace_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock partial foundation - vision and one pillar, no outcomes
            mock_vision = MagicMock(spec=ProductVision)
            mock_vision.id = uuid.uuid4()
            mock_vision.vision_text = "Test vision"
            mock_vision.created_at = None
            mock_vision.updated_at = None

            mock_pillar = MagicMock(spec=StrategicPillar)
            mock_pillar.id = uuid.uuid4()
            mock_pillar.name = "Pillar 1"
            mock_pillar.outcomes = []

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_workspace_vision"
                ) as mock_get_vision,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
            ):
                mock_get_vision.return_value = mock_vision
                mock_get_pillars.return_value = [mock_pillar]
                mock_get_outcomes.return_value = []

                result = await review_strategic_foundation.fn(workspace_id)

        # Verify partial status and gaps identified
        assert_that(result["status"], equal_to("partial"))
        assert_that(result, has_key("gaps"))
        assert_that(len(result["gaps"]) > 0, equal_to(True))

    @pytest.mark.asyncio
    async def test_review_foundation_missing(self):
        """Test that review returns missing status when nothing defined."""
        workspace_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_workspace_vision"
                ) as mock_get_vision,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
                patch(
                    "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
            ):
                mock_get_vision.return_value = None
                mock_get_pillars.return_value = []
                mock_get_outcomes.return_value = []

                result = await review_strategic_foundation.fn(workspace_id)

        # Verify missing status
        assert_that(result["status"], equal_to("missing"))
        assert_that(result["vision"]["exists"], equal_to(False))

    @pytest.mark.asyncio
    async def test_review_handles_invalid_uuid(self):
        """Test that review handles invalid workspace_id."""
        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await review_strategic_foundation.fn("not-a-uuid")

        # Verify error response
        assert_that(
            result,
            has_entries({"status": "error", "type": "strategic_foundation_review"}),
        )


class TestConnectOutcomeToPillars:
    """Test suite for connect_outcome_to_pillars tool."""

    @patch("src.mcp_server.prompt_driven_tools.utilities.get_user_id_from_request")
    @pytest.mark.asyncio
    async def test_connect_outcome_to_pillars_success(self, mock_get_user_id):
        """Test that connect successfully links outcome to pillars."""
        workspace_id = str(uuid.uuid4())
        outcome_id = str(uuid.uuid4())
        pillar_id1 = str(uuid.uuid4())
        pillar_id2 = str(uuid.uuid4())

        mock_get_user_id.return_value = uuid.uuid4()

        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.UUID(outcome_id)
            mock_outcome.name = "Test Outcome"
            mock_outcome.description = None
            mock_outcome.metrics = None
            mock_outcome.time_horizon_months = None
            mock_outcome.display_order = 0
            mock_outcome.pillars = []
            mock_outcome.created_at = None
            mock_outcome.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_product_outcomes"
            ) as mock_get_outcomes:
                mock_get_outcomes.return_value = [mock_outcome]

                result = await connect_outcome_to_pillars.fn(
                    workspace_id, outcome_id, [pillar_id1, pillar_id2]
                )

        # Verify success response
        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

        # Verify link_to_pillars was called
        mock_outcome.link_to_pillars.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_outcome_not_found(self):
        """Test that connect handles outcome not found error."""
        workspace_id = str(uuid.uuid4())
        outcome_id = str(uuid.uuid4())
        pillar_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.utilities.strategic_controller.get_product_outcomes"
            ) as mock_get_outcomes:
                mock_get_outcomes.return_value = []  # No outcomes

                result = await connect_outcome_to_pillars.fn(
                    workspace_id, outcome_id, [pillar_id]
                )

        # Verify error response
        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_connect_outcome_handles_invalid_uuid(self):
        """Test that connect handles invalid UUIDs."""
        with patch(
            "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await connect_outcome_to_pillars.fn(
                "not-a-uuid", "also-not-uuid", ["still-not-uuid"]
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "outcome_pillar_link"})
        )
