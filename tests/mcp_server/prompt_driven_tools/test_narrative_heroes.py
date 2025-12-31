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
    query_heroes,
    submit_hero,
)
from src.models import User, Workspace
from src.narrative.aggregates.hero import Hero
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


@pytest.fixture
def mock_get_workspace_id_from_request(workspace: Workspace) -> MagicMock:
    """Mock get_workspace_id_from_request to return workspace ID."""
    with patch(
        "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
    ) as mock:
        mock.return_value = str(workspace.id)
        yield mock


@pytest.fixture
def mock_get_auth_context(user: User, workspace: Workspace) -> MagicMock:
    """Mock get_auth_context to return user and workspace IDs."""
    with patch(
        "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
    ) as mock:
        mock.return_value = (str(user.id), str(workspace.id))
        yield mock


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
    async def test_get_framework_without_existing_heroes(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test framework retrieval with no existing heroes."""
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
        self, session, workspace, existing_hero, mock_get_workspace_id_from_request
    ):
        """Test framework retrieval includes current state with existing heroes."""
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
    async def test_get_framework_includes_coaching_content(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test framework includes all required coaching and guidance content."""
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
    async def test_submit_hero_success(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test successfully submitting a new hero."""
        hero_name = "Sarah, The Solo Builder"
        hero_description = "Sarah is a solo developer building SaaS products."

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
    async def test_submit_hero_as_primary(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test submitting a hero as primary."""
        hero_name = "Sarah, The Solo Builder"
        hero_description = "Sarah is a solo developer."

        result = await submit_hero.fn(
            name=hero_name,
            description=hero_description,
            is_primary=True,
        )

        # Verify response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["is_primary"], equal_to(True))

    @pytest.mark.asyncio
    async def test_submit_hero_without_description(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test submitting a hero without a description."""
        hero_name = "Sarah, The Solo Builder"

        result = await submit_hero.fn(
            name=hero_name,
            description=None,
            is_primary=False,
        )

        # Verify success - description is optional
        assert_that(result, has_entries({"status": "success", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_submit_hero_mcp_context_error(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test handling of MCPContextError during submission."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await submit_hero.fn(
            name="Sarah, The Solo Builder",
            description="Description",
            is_primary=False,
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_submit_hero_domain_exception(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test handling of domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_heroes.validate_hero_constraints"
        ) as mock_validate:
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
    async def test_submit_hero_includes_next_steps(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test that submit_hero includes helpful next steps."""
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


class TestQueryHeroesListMode:
    """Test suite for query_heroes MCP tool in list mode (no identifier)."""

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
    async def test_get_heroes_empty_workspace(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test retrieving heroes from workspace with no heroes."""
        result = await query_heroes.fn()

        # Verify success response with empty list
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["heroes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_heroes_multiple_heroes(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
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

        result = await query_heroes.fn()

        # Verify response contains both heroes
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(len(result["data"]["heroes"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_get_heroes_success_response_structure(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test query_heroes returns correctly structured response."""
        result = await query_heroes.fn()

        # Verify response structure
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result, has_key("message"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("heroes"))


class TestQueryHeroesSingleMode:
    """Test suite for query_heroes MCP tool in single mode (with identifier)."""

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
    async def test_get_hero_details_success(
        self, session, workspace, hero, mock_get_workspace_id_from_request
    ):
        """Test successfully retrieving hero details."""
        result = await query_heroes.fn(identifier=hero.identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to(hero.name))
        assert_that(result["data"]["identifier"], equal_to(hero.identifier))

    @pytest.mark.asyncio
    async def test_get_hero_details_includes_journey_summary(
        self, session, workspace, hero, mock_get_workspace_id_from_request
    ):
        """Test that hero details include journey summary."""
        result = await query_heroes.fn(identifier=hero.identifier)

        # Verify journey summary is included
        assert_that(result["data"], has_key("journey_summary"))

    @pytest.mark.asyncio
    async def test_get_hero_details_not_found(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test error when hero not found."""
        fake_identifier = "H-9999"

        result = await query_heroes.fn(identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))


class TestSubmitHeroUpsert:
    """Test suite for submit_hero upsert MCP tool (create and update)."""

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
    async def test_submit_hero_update_name_success(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test successfully updating hero's name via upsert."""
        new_name = "Sarah, The Senior Builder"

        result = await submit_hero.fn(
            hero_identifier=hero.identifier,
            name=new_name,
            description=hero.description,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_submit_hero_update_description_success(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test successfully updating hero's description via upsert."""
        new_description = "Sarah is now a senior developer with a team."

        result = await submit_hero.fn(
            hero_identifier=hero.identifier,
            name=hero.name,
            description=new_description,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_submit_hero_update_set_as_primary(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test setting a hero as primary via upsert."""
        result = await submit_hero.fn(
            hero_identifier=hero.identifier,
            name=hero.name,
            description=hero.description,
            is_primary=True,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["is_primary"], equal_to(True))

    @pytest.mark.asyncio
    async def test_submit_hero_update_all_fields_success(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test updating all fields at once via upsert."""
        new_name = "Sarah, The Team Lead"
        new_description = "Sarah now leads a growing team."

        result = await submit_hero.fn(
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
    async def test_submit_hero_update_partial_preserves_values(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test that omitted parameters preserve existing values during update."""
        original_description = hero.description

        result = await submit_hero.fn(
            hero_identifier=hero.identifier,
            name="New Name",
            description=None,
            is_primary=False,
        )

        # Verify name changed but description preserved
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result["data"]["name"], equal_to("New Name"))
        assert_that(result["data"]["description"], equal_to(original_description))

    @pytest.mark.asyncio
    async def test_submit_hero_update_mcp_context_error(
        self, session, hero, mock_get_auth_context
    ):
        """Test handling of MCPContextError during update."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await submit_hero.fn(
            hero_identifier=hero.identifier,
            name="New Name",
            description="New description",
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_submit_hero_update_not_found(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test error when hero not found during update."""
        fake_identifier = "H-9999"

        result = await submit_hero.fn(
            hero_identifier=fake_identifier,
            name="New Name",
            description="New description",
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
    async def test_delete_hero_success(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test successfully deleting a hero."""
        hero_id = hero.id
        hero_identifier = hero.identifier

        result = await delete_hero.fn(hero_identifier=hero_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(
            result["message"], contains_string(f"Deleted hero {hero_identifier}")
        )
        assert_that(result["data"]["deleted_identifier"], equal_to(hero_identifier))
        assert_that(result["data"]["deleted_id"], equal_to(str(hero_id)))

    @pytest.mark.asyncio
    async def test_delete_hero_not_found(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test error when hero not found."""
        fake_identifier = "H-9999"

        result = await delete_hero.fn(hero_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_mcp_context_error(
        self, session, hero, mock_get_auth_context
    ):
        """Test handling of MCPContextError."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_domain_exception(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test handling of domain exceptions during deletion."""
        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_heroes.HeroService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_hero_by_identifier.side_effect = DomainException(
                "Hero validation failed"
            )

            result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "hero"}))

    @pytest.mark.asyncio
    async def test_delete_hero_generic_exception(
        self, session, user, workspace, hero, mock_get_auth_context
    ):
        """Test handling of generic exceptions during deletion."""
        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_heroes.HeroService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_hero_by_identifier.side_effect = RuntimeError(
                "Unexpected database error"
            )

            result = await delete_hero.fn(hero_identifier=hero.identifier)

        # Verify error response includes server error message
        assert_that(result, has_entries({"status": "error", "type": "hero"}))
        assert_that(result.get("error_message", ""), contains_string("Server error"))
