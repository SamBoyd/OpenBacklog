"""Minimal tests for prompt-driven pillar workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.strategic_pillars import (
    get_pillar_definition_framework,
    query_strategic_pillars,
    submit_strategic_pillar,
)
from src.models import User, Workspace
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


@pytest.fixture
def mock_get_workspace_id_from_request(workspace: Workspace):
    """Fixture that patches get_workspace_id_from_request and returns workspace ID."""
    with patch(
        "src.mcp_server.prompt_driven_tools.strategic_pillars.get_workspace_id_from_request"
    ) as mock:
        mock.return_value = str(workspace.id)
        yield mock


@pytest.fixture
def mock_get_auth_context(user: User, workspace: Workspace):
    """Mock get_auth_context for MCP tools."""
    with patch(
        "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
    ) as mock_auth:
        mock_auth.return_value = (str(user.id), str(workspace.id))
        yield mock_auth


class TestQueryStrategicPillars:
    """Test suite for query_strategic_pillars tool."""

    @pytest.fixture
    def pillar(self, workspace: Workspace, user: User, session: Session):
        """Create a pillar for testing."""
        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Deep IDE Integration",
            description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile.",
            session=session,
        )
        session.commit()
        session.refresh(pillar)
        return pillar

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_single_success(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        pillar: StrategicPillar,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test successfully retrieving a single strategic pillar."""
        result = await query_strategic_pillars.fn(identifier=pillar.identifier)

        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"]["name"], equal_to(pillar.name))
        assert_that(result["data"]["identifier"], equal_to(pillar.identifier))

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_includes_linked_outcomes(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        pillar: StrategicPillar,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test that pillar details include linked outcomes."""
        result = await query_strategic_pillars.fn(identifier=pillar.identifier)

        assert_that(result["data"], has_key("linked_outcomes"))
        assert isinstance(result["data"]["linked_outcomes"], list)

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_single_not_found(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test error when pillar not found."""
        fake_identifier = "P-99999"

        result = await query_strategic_pillars.fn(identifier=fake_identifier)

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
        assert "not found" in result["error_message"]

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_single_invalid_identifier(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test error when invalid identifier provided."""
        result = await query_strategic_pillars.fn(identifier="INVALID")

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_single_mcp_context_error(
        self,
        session: Session,
        pillar: StrategicPillar,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test handling of MCPContextError."""
        from src.mcp_server.auth_utils import MCPContextError

        mock_get_workspace_id_from_request.side_effect = MCPContextError(
            "No workspace in context"
        )

        result = await query_strategic_pillars.fn(identifier=pillar.identifier)

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_list_returns_all_pillars(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        pillar: StrategicPillar,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test retrieving all strategic pillars without identifier."""
        result = await query_strategic_pillars.fn()

        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"], has_key("pillars"))
        assert isinstance(result["data"]["pillars"], list)
        # Should include the pillar we created
        assert len(result["data"]["pillars"]) >= 1
        assert any(
            p["identifier"] == pillar.identifier for p in result["data"]["pillars"]
        )

    @pytest.mark.asyncio
    async def test_query_strategic_pillars_list_empty(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        mock_get_workspace_id_from_request: MagicMock,
    ):
        """Test retrieving all pillars when none exist."""
        result = await query_strategic_pillars.fn()

        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"], has_key("pillars"))
        assert isinstance(result["data"]["pillars"], list)
        assert len(result["data"]["pillars"]) == 0


class TestGetPillarDefinitionFramework:
    """Test suite for get_pillar_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(
        self, mock_get_workspace_id_from_request: MagicMock
    ):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.strategic_controller.get_strategic_pillars"
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
    async def test_framework_includes_existing_pillars(
        self, mock_get_workspace_id_from_request: MagicMock
    ):
        """Test that framework includes current pillars."""
        # Mock existing pillars
        mock_pillar = MagicMock(spec=StrategicPillar)
        mock_pillar.id = uuid.uuid4()
        mock_pillar.name = "Deep IDE Integration"
        mock_pillar.description = "Seamless IDE experience"
        mock_pillar.anti_strategy = "No web-first"

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.strategic_controller.get_strategic_pillars"
        ) as mock_get_pillars:
            mock_get_pillars.return_value = [mock_pillar]

            result = await get_pillar_definition_framework.fn()

        # Verify current state shows existing pillar
        assert_that(result["current_state"]["pillar_count"], equal_to(1))
        assert_that(result["current_state"]["remaining"], equal_to(4))
        assert_that(len(result["current_state"]["current_pillars"]), equal_to(1))


class TestSubmitStrategicPillar:
    """Test suite for submit_strategic_pillar tool (create and update)."""

    @pytest.fixture
    def pillar(self, workspace: Workspace, user: User, session: Session):
        """Create a pillar for testing updates."""
        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Deep IDE Integration",
            description="Strategy: Seamless IDE experience. Anti-Strategy: No web-first",
            session=session,
        )
        session.commit()
        session.refresh(pillar)
        return pillar

    @pytest.mark.asyncio
    async def test_submit_creates_pillar_successfully(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit successfully creates pillar via controller."""
        name = "Deep IDE Integration"
        description = "Strategy: Seamless IDE experience. Anti-Strategy: No web-first"

        result = await submit_strategic_pillar.fn(name, description)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_updates_pillar_name(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        pillar: StrategicPillar,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit updates pillar name via upsert."""
        new_name = "Deep IDE Integration (Updated)"

        result = await submit_strategic_pillar.fn(
            name=new_name,
            description=pillar.description,
            pillar_identifier=pillar.identifier,
        )

        # Verify success response and updated name
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_submit_updates_pillar_description(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        pillar: StrategicPillar,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit updates pillar description via upsert."""
        new_description = (
            "Updated strategy: Enhanced experience. Anti-Strategy: No distractions."
        )

        result = await submit_strategic_pillar.fn(
            name=pillar.name,
            description=new_description,
            pillar_identifier=pillar.identifier,
        )

        # Verify success response and updated description
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_submit_updates_both_fields(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        pillar: StrategicPillar,
        mock_get_auth_context: MagicMock,
    ):
        """Test that submit updates both name and description via upsert."""
        new_name = "AI-Native Guidance"
        new_description = (
            "Strategy: Infuse AI into all workflows. Anti-Strategy: No bolted-on AI."
        )

        result = await submit_strategic_pillar.fn(
            name=new_name,
            description=new_description,
            pillar_identifier=pillar.identifier,
        )

        # Verify both fields updated
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"]["name"], equal_to(new_name))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_submit_update_pillar_not_found(
        self,
        session: Session,
        workspace: Workspace,
        user: User,
        mock_get_auth_context: MagicMock,
    ):
        """Test error when pillar not found during update."""
        fake_identifier = "P-9999"

        result = await submit_strategic_pillar.fn(
            name="New Name",
            description="New description",
            pillar_identifier=fake_identifier,
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.strategic_controller.create_strategic_pillar"
        ) as mock_create:
            mock_create.side_effect = DomainException("Pillar limit exceeded")

            result = await submit_strategic_pillar.fn(
                "Pillar Name", "Strategy: X. Anti-Strategy: Y."
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
