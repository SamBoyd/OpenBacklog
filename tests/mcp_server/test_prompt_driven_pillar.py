"""Minimal tests for prompt-driven pillar workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.strategic_pillars import (
    get_pillar_definition_framework,
    get_strategic_pillar_details,
    submit_strategic_pillar,
)
from src.models import Workspace
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestGetStrategicPillarDetails:
    """Test suite for get_strategic_pillar_details tool."""

    @pytest.fixture
    def pillar(self, workspace, user, session):
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
    async def test_get_strategic_pillar_details_success(
        self, session, user, workspace, pillar
    ):
        """Test successfully retrieving a strategic pillar."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await get_strategic_pillar_details.fn(pillar_id=str(pillar.id))

        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        assert_that(result["data"]["name"], equal_to(pillar.name))
        assert_that(result["data"]["id"], equal_to(str(pillar.id)))

    @pytest.mark.asyncio
    async def test_get_strategic_pillar_details_includes_linked_outcomes(
        self, session, user, workspace, pillar
    ):
        """Test that pillar details include linked outcomes."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await get_strategic_pillar_details.fn(pillar_id=str(pillar.id))

        assert_that(result["data"], has_key("linked_outcomes"))
        assert isinstance(result["data"]["linked_outcomes"], list)

    @pytest.mark.asyncio
    async def test_get_strategic_pillar_details_not_found(
        self, session, user, workspace
    ):
        """Test error when pillar not found."""
        fake_id = str(uuid.uuid4())

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await get_strategic_pillar_details.fn(pillar_id=fake_id)

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
        assert "not found" in result["error_message"]

    @pytest.mark.asyncio
    async def test_get_strategic_pillar_details_invalid_uuid(
        self, session, user, workspace
    ):
        """Test error when invalid UUID provided."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await get_strategic_pillar_details.fn(pillar_id="invalid-uuid")

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))

    @pytest.mark.asyncio
    async def test_get_strategic_pillar_details_mcp_context_error(
        self, session, pillar
    ):
        """Test handling of MCPContextError."""
        from src.mcp_server.auth_utils import MCPContextError

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await get_strategic_pillar_details.fn(pillar_id=str(pillar.id))

        assert_that(result, has_entries({"status": "error", "type": "pillar"}))


class TestGetPillarDefinitionFramework:
    """Test suite for get_pillar_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

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
    async def test_framework_includes_existing_pillars(self):
        """Test that framework includes current pillars."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
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
                "src.mcp_server.prompt_driven_tools.strategic_pillars.strategic_controller.get_strategic_pillars"
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
    async def test_submit_creates_pillar_successfully(
        self, session: Session, workspace: Workspace
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
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_pillars.strategic_controller.create_strategic_pillar"
            ) as mock_create:
                mock_create.side_effect = DomainException("Pillar limit exceeded")

                result = await submit_strategic_pillar.fn(
                    "Pillar Name", "Strategy: X. Anti-Strategy: Y."
                )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
