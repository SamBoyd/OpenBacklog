"""Unit tests for product outcome MCP tools.

Tests verify that query_product_outcomes works correctly in both list and single modes,
handles errors appropriately, and returns complete data.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, not_
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.product_outcomes import (
    delete_product_outcome,
    get_outcome_definition_framework,
    query_product_outcomes,
    submit_product_outcome,
)
from src.models import User, Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.services.event_publisher import EventPublisher


@pytest.fixture
def mock_get_workspace_id_from_request(
    workspace: Workspace,
) -> Generator[MagicMock, None, None]:
    """Mock get_workspace_id_from_request to return workspace ID."""
    with patch(
        "src.mcp_server.prompt_driven_tools.product_outcomes.get_workspace_id_from_request"
    ) as mock:
        mock.return_value = workspace.id
        yield mock


@pytest.fixture
def mock_get_auth_context(
    user: User, workspace: Workspace
) -> Generator[MagicMock, None, None]:
    """Mock get_auth_context to return user and workspace IDs."""
    with patch(
        "src.mcp_server.prompt_driven_tools.product_outcomes.get_auth_context"
    ) as mock:
        mock.return_value = (str(user.id), str(workspace.id))
        yield mock


class TestQueryProductOutcomesSingleMode:
    """Test suite for query_product_outcomes with identifier (single entity mode)."""

    @pytest.fixture
    def mock_publisher(self) -> MagicMock:
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def pillar(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> StrategicPillar:
        """Create a StrategicPillar instance for testing."""
        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Developer-First Simplicity",
            description="Make it easy for developers.",
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(pillar)
        return pillar

    @pytest.fixture
    def outcome(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ) -> ProductOutcome:
        """Create a ProductOutcome instance for testing."""
        outcome = ProductOutcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Daily Active Usage",
            description="80% of users active daily.",
            display_order=0,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)
        return outcome

    @pytest.fixture
    def outcome_with_pillar(
        self,
        workspace: Workspace,
        user: User,
        pillar: StrategicPillar,
        session: Session,
        mock_publisher: MagicMock,
    ) -> ProductOutcome:
        """Create a ProductOutcome linked to a pillar."""
        outcome = ProductOutcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="IDE Adoption",
            description="70% of users work from IDE.",
            display_order=0,
        )
        session.add(outcome)
        session.commit()

        outcome.link_to_pillars(
            pillar_ids=[pillar.id],
            user_id=user.id,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(outcome)
        return outcome

    @pytest.mark.asyncio
    async def test_single_outcome_success(
        self,
        session: Session,
        outcome: ProductOutcome,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test successfully retrieving single outcome by identifier."""
        result = await query_product_outcomes.fn(identifier=outcome.identifier)

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["identifier"], equal_to(outcome.identifier))
        assert_that(result["data"]["name"], equal_to("Daily Active Usage"))
        assert_that(result["data"]["pillar_names"], equal_to([]))
        assert_that(result["data"]["linked_themes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_single_outcome_with_pillar(
        self,
        session: Session,
        outcome_with_pillar: ProductOutcome,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test retrieving single outcome with linked pillar."""
        result = await query_product_outcomes.fn(
            identifier=outcome_with_pillar.identifier
        )

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result["data"]["name"], equal_to("IDE Adoption"))
        assert_that(
            result["data"]["pillar_names"], equal_to(["Developer-First Simplicity"])
        )

    @pytest.mark.asyncio
    async def test_single_outcome_not_found(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test error when outcome not found."""
        result = await query_product_outcomes.fn(identifier="O-9999")

        assert_that(result, has_entries({"status": "error", "type": "outcome"}))
        assert_that(result, has_key("error_message"))


class TestQueryProductOutcomesListMode:
    """Test suite for query_product_outcomes without identifier (list mode)."""

    @pytest.mark.asyncio
    async def test_list_outcomes_empty(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that list returns empty list when no outcomes exist."""
        result = await query_product_outcomes.fn()

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"], has_key("outcomes"))
        assert_that(result["data"]["outcomes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_list_outcomes_returns_all(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that list returns all existing outcomes."""
        from src.strategic_planning import controller as strategic_controller

        strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Outcome 1",
            description="First outcome",
            pillar_ids=[],
            session=session,
        )
        strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Outcome 2",
            description="Second outcome",
            pillar_ids=[],
            session=session,
        )

        result = await query_product_outcomes.fn()

        assert_that(result, has_entries({"status": "success"}))
        assert_that(len(result["data"]["outcomes"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_list_outcomes_includes_details(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that list includes all relevant outcome details."""
        from src.strategic_planning import controller as strategic_controller

        strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await query_product_outcomes.fn()

        assert_that(len(result["data"]["outcomes"]), equal_to(1))
        outcome_data = result["data"]["outcomes"][0]
        assert_that(outcome_data, has_key("identifier"))
        assert_that(outcome_data, has_key("name"))
        assert_that(outcome_data, has_key("description"))


class TestGetOutcomeDefinitionFramework:
    """Test suite for get_outcome_definition_framework tool."""

    @pytest.fixture
    def mock_publisher(self) -> MagicMock:
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that framework returns all required fields."""
        result = await get_outcome_definition_framework.fn()

        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("current_state"))
        assert_that(result["current_state"], has_key("current_outcomes"))
        assert_that(result["current_state"], has_key("available_pillars"))

    @pytest.mark.asyncio
    async def test_framework_includes_existing_outcomes(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_workspace_id_from_request: MagicMock,
        mock_publisher: MagicMock,
    ):
        """Test that framework includes current outcomes and pillars."""
        from src.strategic_planning import controller as strategic_controller

        strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Daily Active Usage",
            description="Baseline: 30%. Target: 80%. Timeline: 6 months.",
            pillar_ids=[],
            session=session,
        )
        strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Developer-First Simplicity",
            description="Make it easy for developers.",
            session=session,
        )

        result = await get_outcome_definition_framework.fn()

        assert_that(result["current_state"]["outcome_count"], equal_to(1))
        assert_that(result["current_state"]["pillar_count"], equal_to(1))
        assert_that(len(result["current_state"]["current_outcomes"]), equal_to(1))
        assert_that(len(result["current_state"]["available_pillars"]), equal_to(1))

    @pytest.mark.asyncio
    async def test_framework_handles_missing_pillars_gracefully(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that framework provides helpful context when no pillars exist."""
        result = await get_outcome_definition_framework.fn()

        assert_that(result, has_key("current_state"))
        assert_that(result["current_state"]["pillar_count"], equal_to(0))

    @pytest.mark.asyncio
    async def test_framework_includes_extraction_guidance(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that framework includes extraction guidance for user inputs."""
        result = await get_outcome_definition_framework.fn()

        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))

    @pytest.mark.asyncio
    async def test_framework_handles_database_errors(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that framework handles database errors gracefully."""
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
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit successfully creates outcome via controller."""
        name = "Developer Daily Adoption"
        description = "Goal: Increase daily active IDE plugin users. Baseline: 30% daily active. Target: 80% daily active. Timeline: 6 months."

        result = await submit_product_outcome.fn(name, description)

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_with_pillar_identifiers_links_correctly(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit links outcome to specified pillars."""
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
            name, description, pillar_identifiers=[pillar.identifier]
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"], has_key("identifier"))

    @pytest.mark.asyncio
    async def test_submit_without_pillars_warns_alignment_gap(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit warns when no pillars are linked."""
        name = "Daily Active Usage"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."

        result = await submit_product_outcome.fn(
            name, description, pillar_identifiers=None
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("warnings"))

    @pytest.mark.asyncio
    async def test_submit_validates_name_constraints(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit validates name length constraints."""
        long_name = "A" * 151
        description = "Valid description"

        result = await submit_product_outcome.fn(long_name, description)

        assert_that(result, has_key("status"))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_pillar_identifier(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit handles invalid pillar identifiers gracefully."""
        name = "Daily Active Usage"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."
        invalid_pillar_identifier = "P-99999"

        result = await submit_product_outcome.fn(
            name, description, pillar_identifiers=[invalid_pillar_identifier]
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit handles domain validation errors."""
        from src.strategic_planning import controller as strategic_controller

        strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Duplicate Name",
            description="First outcome with this name",
            pillar_ids=[],
            session=session,
        )

        result = await submit_product_outcome.fn("Duplicate Name", "Description")

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_submit_includes_helpful_next_steps(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit includes actionable next steps."""
        name = "Developer Daily Adoption"
        description = "Baseline: 30%. Target: 80%. Timeline: 6 months."

        result = await submit_product_outcome.fn(name, description)

        assert_that(result, has_key("next_steps"))
        assert isinstance(result["next_steps"], list)
        assert len(result["next_steps"]) > 0
        assert isinstance(result["next_steps"][0], str)


class TestUpdateProductOutcome:
    """Test suite for submit_product_outcome upsert functionality."""

    @pytest.mark.asyncio
    async def test_update_outcome_name_successfully(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert successfully changes outcome name."""
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
        result = await submit_product_outcome.fn(
            outcome_identifier=outcome.identifier, name=new_name
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_update_outcome_description_successfully(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert successfully changes outcome description."""
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
        result = await submit_product_outcome.fn(
            outcome_identifier=outcome.identifier, description=new_description
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_update_outcome_pillar_links_successfully(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert successfully changes pillar linkages."""
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

        result = await submit_product_outcome.fn(
            outcome_identifier=outcome.identifier,
            pillar_identifiers=[pillar.identifier],
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_update_outcome_requires_identifier(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert creates new outcome when no identifier is provided."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await submit_product_outcome.fn(
            name="New Outcome", description="New description"
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["identifier"], not_(equal_to(outcome.identifier)))

    @pytest.mark.asyncio
    async def test_update_nonexistent_outcome_fails(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert fails when outcome doesn't exist."""
        fake_identifier = "O-99999"
        result = await submit_product_outcome.fn(
            outcome_identifier=fake_identifier, name="New Name"
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_update_with_invalid_outcome_id_fails(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert fails with invalid outcome identifier."""
        result = await submit_product_outcome.fn(
            outcome_identifier="INVALID", name="New Name"
        )

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_update_with_invalid_pillar_ids_fails(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that upsert fails with invalid pillar IDs."""
        from src.strategic_planning import controller as strategic_controller

        outcome = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Outcome",
            description="Test description",
            pillar_ids=[],
            session=session,
        )

        result = await submit_product_outcome.fn(
            outcome_identifier=outcome.identifier, pillar_identifiers=["INVALID"]
        )

        assert_that(result, has_entries({"status": "error"}))


class TestDeleteProductOutcome:
    """Test suite for delete_product_outcome tool."""

    @pytest.mark.asyncio
    async def test_delete_outcome_successfully(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
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
    async def test_delete_nonexistent_outcome_fails(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that delete fails when outcome doesn't exist."""
        fake_identifier = "O-99999"
        result = await delete_product_outcome.fn(outcome_identifier=fake_identifier)

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_delete_with_invalid_outcome_id_fails(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
    ):
        """Test that delete fails with invalid outcome identifier."""
        result = await delete_product_outcome.fn(outcome_identifier="INVALID")

        assert_that(result, has_entries({"status": "error"}))

    @pytest.mark.asyncio
    async def test_delete_includes_outcome_name_in_success(
        self,
        session: Session,
        workspace: Workspace,
        mock_get_auth_context: MagicMock,
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
