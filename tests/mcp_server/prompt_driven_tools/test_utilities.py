"""Minimal tests for prompt-driven utility tools (Phase 3)."""

import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, has_length
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.utilities import connect_outcome_to_pillars
from src.models import Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar


class TestConnectOutcomeToPillars:
    """Test suite for connect_outcome_to_pillars tool."""

    @pytest.mark.asyncio
    async def test_connect_outcome_to_pillars_success(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: List[MagicMock],
    ):
        """Test that connect successfully links outcome to pillars."""
        outcome_identifier = "O-001"
        pillar_identifiers = ["P-001", "P-002"]

        outcome = ProductOutcome(
            user_id=workspace.user_id,
            workspace_id=workspace.id,
            identifier=outcome_identifier,
            name="Test Outcome",
            description=None,
            display_order=0,
            pillars=[],
        )

        pillar1 = StrategicPillar(
            identifier="P-001",
            name="Pillar 1",
            description=None,
            display_order=0,
            user_id=workspace.user_id,
            workspace_id=workspace.id,
        )
        pillar2 = StrategicPillar(
            identifier="P-002",
            name="Pillar 2",
            description=None,
            display_order=1,
            user_id=workspace.user_id,
            workspace_id=workspace.id,
        )
        session.add(pillar1)
        session.add(pillar2)
        session.add(outcome)
        session.commit()
        session.refresh(outcome)

        result = await connect_outcome_to_pillars.fn(
            outcome_identifier, pillar_identifiers
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

        assert_that(outcome.pillars, has_length(2))
        assert_that(outcome.pillars[0].id, equal_to(pillar1.id))
        assert_that(outcome.pillars[1].id, equal_to(pillar2.id))

    @pytest.mark.asyncio
    async def test_connect_outcome_not_found(self):
        """Test that connect handles outcome not found error."""
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

                result = await connect_outcome_to_pillars.fn(outcome_id, [pillar_id])

        # Verify error response
        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_connect_outcome_handles_invalid_uuid(self):
        """Test that connect handles invalid UUIDs."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.utilities.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.utilities.get_workspace_id_from_request"
            ) as mock_get_workspace_id,
        ):
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            # Mock get_workspace_id_from_request to raise ValueError
            mock_get_workspace_id.side_effect = ValueError("Invalid workspace ID")

            result = await connect_outcome_to_pillars.fn(
                "also-not-uuid", ["still-not-uuid"]
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "outcome_pillar_link"})
        )
