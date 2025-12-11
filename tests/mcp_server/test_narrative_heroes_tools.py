"""Unit tests for narrative hero MCP tools.

Tests verify that hero definition, submission, retrieval, update, and deletion
tools work correctly, handle errors appropriately, and emit domain events when expected.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entries, has_key

from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.prompt_driven_tools.narrative_heroes import (
    delete_hero,
    get_hero_definition_framework,
    get_hero_details,
    get_heroes,
    submit_hero,
    update_hero,
)
from src.models import Workspace
from src.narrative.aggregates.hero import Hero
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestGetHeroDefinitionFramework:
    """Test suite for get_hero_definition_framework MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def existing_hero(self, workspace, user, session, mock_publisher):
        """Create an existing hero for testing framework state."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.mark.asyncio
    async def test_get_framework_without_existing_heroes(self, session, workspace):
        """Test framework retrieval with no existing heroes."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_definition_framework.fn()

        # Verify framework structure
        assert_that(result, has_entries({"entity_type": "hero"}))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("questions_to_explore"))
        assert_that(result, has_key("anti_patterns"))
        assert_that(result, has_key("coaching_tips"))
        assert_that(result, has_key("current_state"))

        # Verify current state shows no heroes
        assert_that(result["current_state"]["hero_count"], equal_to(0))
        assert_that(result["current_state"]["has_primary_hero"], equal_to(False))

    @pytest.mark.asyncio
    async def test_get_framework_with_existing_heroes(
        self, session, workspace, existing_hero
    ):
        """Test framework retrieval includes current state with existing heroes."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_definition_framework.fn()

        # Verify current state reflects existing heroes
        assert_that(result["current_state"]["hero_count"], equal_to(1))
        assert_that(result["current_state"]["has_primary_hero"], equal_to(True))
        assert_that(result["current_state"], has_key("primary_hero"))
        assert_that(
            result["current_state"]["primary_hero"]["name"],
            equal_to(existing_hero.name),
        )

    @pytest.mark.asyncio
    async def test_get_framework_includes_coaching_content(self, session, workspace):
        """Test framework includes all required coaching and guidance content."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_definition_framework.fn()

        # Verify coaching and natural questions
        assert_that(result, has_key("conversation_guidelines"))
        assert_that(result, has_key("natural_questions"))
        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))


class TestSubmitHero:
    """Test suite for submit_hero MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.mark.asyncio
    async def test_submit_hero_success(self, session, user, workspace):
        """Test successfully submitting a new hero."""
        hero_name = "Sarah, The Solo Builder"
        hero_description = "Sarah is a solo developer building SaaS products."

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_hero.fn(
                name=hero_name,
                description=hero_description,
                is_primary=False,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["name"], equal_to(hero_name))
        assert_that(result["data"]["description"], equal_to(hero_description))
        assert_that(result["data"]["is_primary"], equal_to(False))

    @pytest.mark.asyncio
    async def test_submit_hero_as_primary(self, session, user, workspace):
        """Test submitting a hero as primary."""
        hero_name = "Sarah, The Solo Builder"
        hero_description = "Sarah is a solo developer."

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_hero.fn(
                name=hero_name,
                description=hero_description,
                is_primary=True,
            )

        # Verify response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["is_primary"], equal_to(True))

    @pytest.mark.asyncio
    async def test_submit_hero_without_description(self, session, user, workspace):
        """Test submitting a hero without a description."""
        hero_name = "Sarah, The Solo Builder"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_hero.fn(
                name=hero_name,
                description=None,
                is_primary=False,
            )

        # Verify success - description is optional
        assert_that(result, has_entries({"status": "success", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_submit_hero_mcp_context_error(self, session, user, workspace):
        """Test handling of MCPContextError during submission."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await submit_hero.fn(
                name="Sarah, The Solo Builder",
                description="Description",
                is_primary=False,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_submit_hero_domain_exception(self, session, user, workspace):
        """Test handling of domain validation errors."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.validate_hero_constraints"
            ) as mock_validate,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))
            mock_validate.side_effect = DomainException("Hero name must be unique")

            result = await submit_hero.fn(
                name="Sarah, The Solo Builder",
                description="Description",
                is_primary=False,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))
        assert_that(
            result.get("error_message", ""), contains_string("Hero name must be unique")
        )

    @pytest.mark.asyncio
    async def test_submit_hero_includes_next_steps(self, session, user, workspace):
        """Test that submit_hero includes helpful next steps."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_hero.fn(
                name="Sarah, The Solo Builder",
                description="Description",
                is_primary=False,
            )

        # Verify next_steps are included
        assert_that(result, has_key("next_steps"))
        # Check that one of the next_steps contains "villain"
        steps_text = " ".join(result.get("next_steps", []))
        assert_that(steps_text, contains_string("villain"))


class TestGetHeroes:
    """Test suite for get_heroes MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.mark.asyncio
    async def test_get_heroes_empty_workspace(self, session, workspace):
        """Test retrieving heroes from workspace with no heroes."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_heroes.fn()

        # Verify success response with empty list
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["heroes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_heroes_multiple_heroes(
        self, session, workspace, user, mock_publisher
    ):
        """Test retrieving multiple heroes from workspace."""
        # Create multiple heroes
        hero1 = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        hero2 = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Alex, The Team Lead",
            description="Alex leads a small team.",
            is_primary=False,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_heroes.fn()

        # Verify response contains both heroes
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(len(result["data"]["heroes"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_get_heroes_success_response_structure(self, session, workspace):
        """Test get_heroes returns correctly structured response."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_heroes.fn()

        # Verify response structure
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result, has_key("message"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("heroes"))


class TestGetHeroDetails:
    """Test suite for get_hero_details MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def hero(self, workspace, user, session, mock_publisher):
        """Create a hero for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.mark.asyncio
    async def test_get_hero_details_success(self, session, workspace, hero):
        """Test successfully retrieving hero details."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_details.fn(hero_identifier=hero.identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to(hero.name))
        assert_that(result["data"]["identifier"], equal_to(hero.identifier))

    @pytest.mark.asyncio
    async def test_get_hero_details_includes_journey_summary(
        self, session, workspace, hero
    ):
        """Test that hero details include journey summary."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_details.fn(hero_identifier=hero.identifier)

        # Verify journey summary is included
        assert_that(result["data"], has_key("journey_summary"))

    @pytest.mark.asyncio
    async def test_get_hero_details_not_found(self, session, workspace):
        """Test error when hero not found."""
        fake_identifier = "H-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_hero_details.fn(hero_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))


class TestUpdateHero:
    """Test suite for update_hero MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def hero(self, workspace, user, session, mock_publisher):
        """Create a hero for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=False,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.mark.asyncio
    async def test_update_hero_name_success(self, session, user, workspace, hero):
        """Test successfully updating hero's name."""
        new_name = "Sarah, The Senior Builder"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
                name=new_name,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_update_hero_description_success(
        self, session, user, workspace, hero
    ):
        """Test successfully updating hero's description."""
        new_description = "Sarah is now a senior developer with a team."

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
                description=new_description,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_update_hero_set_as_primary(self, session, user, workspace, hero):
        """Test setting a hero as primary."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
                is_primary=True,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["is_primary"], equal_to(True))

    @pytest.mark.asyncio
    async def test_update_hero_no_fields_error(self, session, user, workspace, hero):
        """Test error when no fields provided for update."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))
        assert_that(
            result.get("error_message", ""), contains_string("At least one field")
        )

    @pytest.mark.asyncio
    async def test_update_hero_all_fields_success(self, session, user, workspace, hero):
        """Test updating all fields at once."""
        new_name = "Sarah, The Team Lead"
        new_description = "Sarah now leads a growing team."

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
                name=new_name,
                description=new_description,
                is_primary=True,
            )

        # Verify all fields updated
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to(new_name))
        assert_that(result["data"]["description"], equal_to(new_description))
        assert_that(result["data"]["is_primary"], equal_to(True))

    @pytest.mark.asyncio
    async def test_update_hero_mcp_context_error(self, session, hero):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await update_hero.fn(
                hero_identifier=hero.identifier,
                name="New Name",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_update_hero_not_found(self, session, user, workspace):
        """Test error when hero not found."""
        fake_identifier = "H-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_hero.fn(
                hero_identifier=fake_identifier,
                name="New Name",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))


class TestDeleteHero:
    """Test suite for delete_hero MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def hero(self, workspace, user, session, mock_publisher):
        """Create a hero for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=False,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.mark.asyncio
    async def test_delete_hero_success(self, session, user, workspace, hero):
        """Test successfully deleting a hero."""
        hero_id = hero.id
        hero_identifier = hero.identifier

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await delete_hero.fn(hero_identifier=hero_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(
            result["message"], contains_string(f"Deleted hero {hero_identifier}")
        )
        assert_that(result["data"]["deleted_identifier"], equal_to(hero_identifier))
        assert_that(result["data"]["deleted_id"], equal_to(str(hero_id)))

    @pytest.mark.asyncio
    async def test_delete_hero_not_found(self, session, user, workspace):
        """Test error when hero not found."""
        fake_identifier = "H-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await delete_hero.fn(hero_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_mcp_context_error(self, session, hero):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_domain_exception(self, session, user, workspace, hero):
        """Test handling of domain exceptions during deletion."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.HeroService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_hero_by_identifier.side_effect = DomainException(
                "Hero validation failed"
            )

            result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_generic_exception(self, session, user, workspace, hero):
        """Test handling of generic exceptions during deletion."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.HeroService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_hero_by_identifier.side_effect = RuntimeError(
                "Unexpected database error"
            )

            result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response includes server error message
        assert_that(result, has_entries({"status": "error", "type": "hero"}))
        assert_that(result.get("error_message", ""), contains_string("Server error"))
