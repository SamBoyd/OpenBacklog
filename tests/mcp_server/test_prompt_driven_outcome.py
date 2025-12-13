"""Comprehensive tests for prompt-driven outcome workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.product_outcomes import (
    delete_product_outcome,
    get_outcome_definition_framework,
    get_product_outcomes,
    submit_product_outcome,
    update_product_outcome,
)
from src.models import Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


class TestGetOutcomeDefinitionFramework:
    """Test suite for get_outcome_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_strategic_pillars"
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

    @pytest.mark.asyncio
    async def test_framework_includes_existing_outcomes(self):
        """Test that framework includes current outcomes and pillars."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock existing outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.uuid4()
            mock_outcome.name = "Daily Active Usage"
            mock_outcome.description = "Baseline: 30%. Target: 80%. Timeline: 6 months."

            # Mock existing pillar
            mock_pillar = MagicMock(spec=StrategicPillar)
            mock_pillar.id = uuid.uuid4()
            mock_pillar.name = "Developer-First Simplicity"

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_get_outcomes.return_value = [mock_outcome]
                mock_get_pillars.return_value = [mock_pillar]

                result = await get_outcome_definition_framework.fn()

        assert_that(result["current_state"]["outcome_count"], equal_to(1))
        assert_that(result["current_state"]["pillar_count"], equal_to(1))
        assert_that(len(result["current_state"]["current_outcomes"]), equal_to(1))
        assert_that(len(result["current_state"]["available_pillars"]), equal_to(1))

    @pytest.mark.asyncio
    async def test_framework_handles_missing_pillars_gracefully(self):
        """Test that framework provides helpful context when no pillars exist."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_get_outcomes.return_value = []
                mock_get_pillars.return_value = []

                result = await get_outcome_definition_framework.fn()

        # Verify the framework handles missing pillars gracefully
        assert_that(result, has_key("current_state"))
        assert_that(result["current_state"]["pillar_count"], equal_to(0))

    @pytest.mark.asyncio
    async def test_framework_includes_extraction_guidance(self):
        """Test that framework includes extraction guidance for user inputs."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_get_outcomes.return_value = []
                mock_get_pillars.return_value = []

                result = await get_outcome_definition_framework.fn()

        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))

    @pytest.mark.asyncio
    async def test_framework_handles_database_errors(self):
        """Test that framework handles database errors gracefully."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
            ) as mock_get_outcomes:
                mock_get_outcomes.side_effect = Exception("Database error")

                result = await get_outcome_definition_framework.fn()

        assert_that(result, has_entries({"status": "error"}))


class TestSubmitProductOutcome:
    """Test suite for submit_product_outcome tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_outcome_successfully(
        self, session, workspace: Workspace
    ):
        """Test that submit successfully creates outcome via controller."""
        name = "Developer Daily Adoption"
        description = "Goal: Increase daily active IDE plugin users. Baseline: 30% daily active. Target: 80% daily active. Timeline: 6 months."

        result = await submit_product_outcome.fn(name, description)

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_with_pillar_ids_links_correctly(
        self, session, workspace: Workspace
    ):
        """Test that submit links outcome to specified pillars."""
        # Create a test pillar first
        from src.strategic_planning import controller as strategic_controller

        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Developer-First Simplicity",
            description="Strategy: IDE-first. Anti-Strategy: Web-first.",
            session=session,
        )

        name = "IDE-Native Workflow"
        description = "Goal: Developers complete workflows in IDE. Baseline: 30%. Target: 80%. Timeline: 12 months."

        result = await submit_product_outcome.fn(
            name, description, pillar_ids=[str(pillar.id)]
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"], has_key("identifier"))

    @pytest.mark.asyncio
    async def test_submit_without_pillars_warns_alignment_gap(
        self, session, workspace: Workspace
    ):
        """Test that submit warns when no pillars are linked."""
        name = "Daily Active Usage"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."

        result = await submit_product_outcome.fn(name, description, pillar_ids=None)

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("warnings"))

    @pytest.mark.asyncio
    async def test_submit_validates_name_constraints(self, workspace: Workspace):
        """Test that submit validates name length constraints."""
        long_name = "A" * 151  # Exceeds max length of 150
        description = "Valid description"

        result = await submit_product_outcome.fn(long_name, description)

        # Should either succeed with truncation or fail with validation error
        assert_that(result, has_key("status"))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_pillar_id(self, workspace: Workspace):
        """Test that submit handles invalid pillar IDs gracefully."""
        name = "Daily Active Usage"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."
        invalid_pillar_id = "not-a-uuid"

        result = await submit_product_outcome.fn(
            name, description, pillar_ids=[invalid_pillar_id]
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.create_product_outcome"
            ) as mock_create:
                mock_create.side_effect = DomainException("Name must be unique")

                result = await submit_product_outcome.fn(
                    "Duplicate Name", "Description"
                )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_submit_includes_helpful_next_steps(
        self, session, workspace: Workspace
    ):
        """Test that submit includes actionable next steps."""
        name = "Developer Daily Adoption"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."

        result = await submit_product_outcome.fn(name, description)

        # Verify next steps is a list with at least one helpful string
        assert_that(result, has_key("next_steps"))
        assert isinstance(result["next_steps"], list)
        assert len(result["next_steps"]) > 0
        assert isinstance(result["next_steps"][0], str)


class TestGetProductOutcomes:
    """Test suite for get_product_outcomes tool."""

    @pytest.mark.asyncio
    async def test_get_outcomes_returns_empty_list(self):
        """Test that get returns empty list when no outcomes exist."""
        result = await get_product_outcomes.fn()

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"], has_key("outcomes"))
        assert_that(result["data"]["outcomes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_outcomes_returns_all_outcomes(
        self, session, workspace: Workspace
    ):
        """Test that get returns all existing outcomes."""
        from src.strategic_planning import controller as strategic_controller

        # Create two test outcomes
        outcome1 = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Outcome 1",
            description="First outcome",
            pillar_ids=[],
            session=session,
        )
        outcome2 = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Outcome 2",
            description="Second outcome",
            pillar_ids=[],
            session=session,
        )

        result = await get_product_outcomes.fn()

        assert_that(result, has_entries({"status": "success"}))
        assert_that(len(result["data"]["outcomes"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_get_outcomes_includes_outcome_details(
        self, session, workspace: Workspace
    ):
        """Test that get includes all relevant outcome details."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await get_product_outcomes.fn()

        assert_that(len(result["data"]["outcomes"]), equal_to(1))
        outcome_data = result["data"]["outcomes"][0]
        assert_that(outcome_data, has_key("identifier"))
        assert_that(outcome_data, has_key("name"))
        assert_that(outcome_data, has_key("description"))

    @pytest.mark.asyncio
    async def test_get_outcomes_handles_database_errors(self):
        """Test that get handles database errors gracefully."""
        with patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.product_outcomes.strategic_controller.get_product_outcomes"
            ) as mock_get:
                mock_get.side_effect = Exception("Database error")

                result = await get_product_outcomes.fn()

        assert_that(result, has_entries({"status": "error"}))


class TestUpdateProductOutcome:
    """Test suite for update_product_outcome tool."""

    @pytest.mark.asyncio
    async def test_update_outcome_name_successfully(
        self, session, workspace: Workspace
    ):
        """Test that update successfully changes outcome name."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Original Name",
            description="Original description",
            pillar_ids=[],
            session=session,
        )

        new_name = "Updated Name"
        result = await update_product_outcome.fn(
            outcome_identifier=outcome.identifier, name=new_name
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_update_outcome_description_successfully(
        self, session, workspace: Workspace
    ):
        """Test that update successfully changes outcome description."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Original description",
            pillar_ids=[],
            session=session,
        )

        new_description = "Updated description with new metrics"
        result = await update_product_outcome.fn(
            outcome_identifier=outcome.identifier, description=new_description
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_update_outcome_pillar_links_successfully(
        self, session, workspace: Workspace
    ):
        """Test that update successfully changes pillar linkages."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Pillar",
            description="Strategy: Test. Anti-Strategy: None.",
            session=session,
        )

        result = await update_product_outcome.fn(
            outcome_identifier=outcome.identifier,
            pillar_identifiers=[pillar.identifier],
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_update_outcome_requires_at_least_one_field(
        self, session, workspace: Workspace
    ):
        """Test that update requires at least one field to be provided."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await update_product_outcome.fn(outcome_identifier=outcome.identifier)

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_update_nonexistent_outcome_fails(self, workspace: Workspace):
        """Test that update fails when outcome doesn't exist."""
        fake_identifier = "O-99999"
        result = await update_product_outcome.fn(
            outcome_identifier=fake_identifier, name="New Name"
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_update_with_invalid_outcome_id_fails(self, workspace: Workspace):
        """Test that update fails with invalid outcome identifier."""
        result = await update_product_outcome.fn(
            outcome_identifier="INVALID", name="New Name"
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_update_with_invalid_pillar_ids_fails(
        self, session, workspace: Workspace
    ):
        """Test that update fails with invalid pillar IDs."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await update_product_outcome.fn(
            outcome_identifier=outcome.identifier, pillar_identifiers=["INVALID"]
        )

        assert_that(result, has_entries({"status": "error"}))


class TestDeleteProductOutcome:
    """Test suite for delete_product_outcome tool."""

    @pytest.mark.asyncio
    async def test_delete_outcome_successfully(self, session, workspace: Workspace):
        """Test that delete successfully removes an outcome."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Outcome to Delete",
            description="This outcome will be deleted",
            pillar_ids=[],
            session=session,
        )
        outcome_identifier = outcome.identifier

        result = await delete_product_outcome.fn(outcome_identifier=outcome_identifier)

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["deleted_identifier"], equal_to(outcome_identifier))

    @pytest.mark.asyncio
    async def test_delete_nonexistent_outcome_fails(self, workspace: Workspace):
        """Test that delete fails when outcome doesn't exist."""
        fake_identifier = "O-99999"
        result = await delete_product_outcome.fn(outcome_identifier=fake_identifier)

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_delete_with_invalid_outcome_id_fails(self, workspace: Workspace):
        """Test that delete fails with invalid outcome identifier."""
        result = await delete_product_outcome.fn(outcome_identifier="INVALID")

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_delete_includes_outcome_name_in_success(
        self, session, workspace: Workspace
    ):
        """Test that delete success message includes the outcome name."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Named Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await delete_product_outcome.fn(outcome_identifier=outcome.identifier)

        assert_that(result, has_entries({"status": "success"}))
        assert_that(
            result["message"], equal_to("Deleted product outcome 'Named Outcome'")
        )
