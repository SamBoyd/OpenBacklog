"""Comprehensive tests for prompt-driven strategic initiative workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm.session import Session

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.mcp_server.prompt_driven_tools.strategic_initiatives import (
    delete_strategic_initiative,
    get_strategic_initiative,
    get_strategic_initiative_definition_framework,
    get_strategic_initiatives,
    submit_strategic_initiative,
    update_strategic_initiative,
)
from src.models import Initiative, InitiativeStatus, Workspace
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


class TestGetStrategicInitiativeDefinitionFramework:
    """Test suite for get_strategic_initiative_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock all service calls
            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.HeroService"
                ) as mock_hero_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.VillainService"
                ) as mock_villain_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                # Mock service instances
                mock_hero_service = MagicMock()
                mock_hero_service.get_heroes_for_workspace.return_value = []
                mock_hero_service_class.return_value = mock_hero_service

                mock_villain_service = MagicMock()
                mock_villain_service.get_villains_for_workspace.return_value = []
                mock_villain_service_class.return_value = mock_villain_service

                mock_get_pillars.return_value = []

                # Mock the query for themes
                mock_query = MagicMock()
                mock_query.filter_by.return_value.order_by.return_value.all.return_value = (
                    []
                )
                mock_session.query.return_value = mock_query

                result = await get_strategic_initiative_definition_framework.fn()

        # Verify framework has required fields
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("questions_to_explore"))
        assert_that(result, has_key("anti_patterns"))
        assert_that(result, has_key("coaching_tips"))
        assert_that(result, has_key("current_state"))
        assert_that(result, has_key("conversation_guidelines"))
        assert_that(result, has_key("natural_questions"))
        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))

        # Verify entity type
        assert_that(result["entity_type"], equal_to("strategic_initiative"))

    @pytest.mark.asyncio
    async def test_framework_includes_available_heroes_villains(self):
        """Test that framework includes current heroes and villains."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock heroes and villains
            mock_hero = MagicMock(spec=Hero)
            mock_hero.id = uuid.uuid4()
            mock_hero.identifier = "H-1001"
            mock_hero.name = "Sarah, The Solo Builder"
            mock_hero.is_primary = True

            mock_villain = MagicMock(spec=Villain)
            mock_villain.id = uuid.uuid4()
            mock_villain.identifier = "V-1001"
            mock_villain.name = "Context Switching"
            mock_villain.villain_type = "WORKFLOW"
            mock_villain.is_defeated = False

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.HeroService"
                ) as mock_hero_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.VillainService"
                ) as mock_villain_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_hero_service = MagicMock()
                mock_hero_service.get_heroes_for_workspace.return_value = [mock_hero]
                mock_hero_service_class.return_value = mock_hero_service

                mock_villain_service = MagicMock()
                mock_villain_service.get_villains_for_workspace.return_value = [
                    mock_villain
                ]
                mock_villain_service_class.return_value = mock_villain_service

                mock_get_pillars.return_value = []

                mock_query = MagicMock()
                mock_query.filter_by.return_value.order_by.return_value.all.return_value = (
                    []
                )
                mock_session.query.return_value = mock_query

                result = await get_strategic_initiative_definition_framework.fn()

        # Verify heroes and villains are included
        assert_that(result["current_state"]["hero_count"], equal_to(1))
        assert_that(result["current_state"]["villain_count"], equal_to(1))
        assert len(result["current_state"]["available_heroes"]) == 1
        assert len(result["current_state"]["available_villains"]) == 1

    @pytest.mark.asyncio
    async def test_framework_filters_defeated_villains(self):
        """Test that framework excludes defeated villains."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_villain_active = MagicMock(spec=Villain)
            mock_villain_active.id = uuid.uuid4()
            mock_villain_active.identifier = "V-1001"
            mock_villain_active.name = "Context Switching"
            mock_villain_active.villain_type = "WORKFLOW"
            mock_villain_active.is_defeated = False

            mock_villain_defeated = MagicMock(spec=Villain)
            mock_villain_defeated.id = uuid.uuid4()
            mock_villain_defeated.identifier = "V-1002"
            mock_villain_defeated.name = "Legacy Code"
            mock_villain_defeated.villain_type = "TECHNICAL"
            mock_villain_defeated.is_defeated = True

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.HeroService"
                ) as mock_hero_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.VillainService"
                ) as mock_villain_service_class,
                patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
            ):
                mock_hero_service = MagicMock()
                mock_hero_service.get_heroes_for_workspace.return_value = []
                mock_hero_service_class.return_value = mock_hero_service

                mock_villain_service = MagicMock()
                mock_villain_service.get_villains_for_workspace.return_value = [
                    mock_villain_active,
                    mock_villain_defeated,
                ]
                mock_villain_service_class.return_value = mock_villain_service

                mock_get_pillars.return_value = []

                mock_query = MagicMock()
                mock_query.filter_by.return_value.order_by.return_value.all.return_value = (
                    []
                )
                mock_session.query.return_value = mock_query

                result = await get_strategic_initiative_definition_framework.fn()

        # Verify only active villains are included
        assert_that(result["current_state"]["villain_count"], equal_to(1))
        assert len(result["current_state"]["available_villains"]) == 1
        assert (
            result["current_state"]["available_villains"][0]["name"]
            == "Context Switching"
        )


class TestSubmitStrategicInitiative:
    """Test suite for submit_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_initiative_successfully(
        self, session: Session, user, workspace: Workspace
    ):
        """Test that submit successfully creates initiative."""
        title = "Smart Context Switching"
        description = "Auto-save and restore IDE context when switching between tasks"

        result = await submit_strategic_initiative.fn(
            title=title,
            description=description,
            status="BACKLOG",
        )

        # Verify success response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

        # Verify initiative was created
        initiative = session.query(Initiative).filter_by(title=title).first()
        assert initiative is not None
        assert initiative.description == description
        assert initiative.status == InitiativeStatus.BACKLOG

    @pytest.mark.asyncio
    async def test_submit_with_narrative_connections(
        self, session: Session, user, workspace: Workspace
    ):
        """Test that submit creates initiative with narrative connections."""
        # Setup hero, villain, and pillar
        hero = Hero(
            name="Sarah, The Solo Builder",
            description="A solo developer working on multiple projects",
            is_primary=True,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(hero)

        villain = Villain(
            name="Context Switching",
            villain_type="WORKFLOW",
            description="Switching between tools breaks flow",
            severity=5,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(villain)

        pillar = StrategicPillar(
            name="Deep IDE Integration",
            description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile.",
            workspace_id=workspace.id,
            user_id=user.id,
            display_order=0,
        )
        session.add(pillar)

        session.commit()
        session.refresh(hero)
        session.refresh(villain)
        session.refresh(pillar)

        title = "Smart Context Switching"
        description = "Auto-save and restore IDE context when switching between tasks"

        result = await submit_strategic_initiative.fn(
            title=title,
            description=description,
            hero_ids=[str(hero.id)],
            villain_ids=[str(villain.id)],
            pillar_id=str(pillar.id),
            narrative_intent="Defeats context switching for Sarah",
            status="TO_DO",
        )

        # Verify success response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify narrative connections
        strategic_init = session.query(StrategicInitiative).first()
        assert strategic_init is not None
        assert len(strategic_init.heroes) == 1
        assert len(strategic_init.villains) == 1
        assert strategic_init.pillar_id == pillar.id
        assert strategic_init.narrative_intent == "Defeats context switching for Sarah"

    @pytest.mark.asyncio
    async def test_submit_with_invalid_status(self):
        """Test that submit handles invalid status."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await submit_strategic_initiative.fn(
                title="Test Initiative",
                description="Test description",
                status="INVALID_STATUS",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "Invalid status" in result["error_message"]

    @pytest.mark.asyncio
    async def test_submit_with_nonexistent_hero(
        self, session: Session, user, workspace: Workspace
    ):
        """Test that submit gracefully handles invalid hero IDs."""
        fake_hero_id = str(uuid.uuid4())

        result = await submit_strategic_initiative.fn(
            title="Test Initiative",
            description="Test description",
            hero_ids=[fake_hero_id],
        )

        # Should succeed with warning about invalid hero
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result, has_key("warnings"))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(
        self, session: Session, user, workspace: Workspace
    ):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.validate_strategic_initiative_constraints"
        ) as mock_validate:
            mock_validate.side_effect = DomainException("Invalid title")

            result = await submit_strategic_initiative.fn(
                title="",
                description="Test description",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )


class TestGetStrategicInitiatives:
    """Test suite for get_strategic_initiatives tool."""

    @pytest.mark.asyncio
    async def test_get_empty_initiatives(self):
        """Test getting initiatives when none exist."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_query = MagicMock()
            mock_query.options.return_value.filter_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query

            result = await get_strategic_initiatives.fn()

        # Verify response structure
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result, has_key("data"))
        assert len(result["data"]["strategic_initiatives"]) == 0

    @pytest.mark.asyncio
    async def test_get_multiple_initiatives(
        self, session: Session, user, workspace: Workspace
    ):
        """Test getting multiple strategic initiatives."""
        # Create multiple initiatives
        initiatives = []
        for i in range(3):
            initiative = Initiative(
                title=f"Initiative {i}",
                description=f"Description {i}",
                user_id=user.id,
                workspace_id=workspace.id,
                status=InitiativeStatus.BACKLOG,
            )
            session.add(initiative)
            initiatives.append(initiative)

        session.commit()

        # Refresh to get IDs
        for initiative in initiatives:
            session.refresh(initiative)

        # Now create strategic initiatives
        for i, initiative in enumerate(initiatives):
            strategic_init = StrategicInitiative(
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                description=f"Strategic context {i}",
            )
            session.add(strategic_init)

        session.commit()

        result = await get_strategic_initiatives.fn()

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert len(result["data"]["strategic_initiatives"]) == 3


class TestGetStrategicInitiative:
    """Test suite for get_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_get_by_identifier(
        self, session: Session, user, workspace: Workspace
    ):
        """Test getting initiative by identifier."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await get_strategic_initiative.fn(initiative.identifier)

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result["data"]["initiative"]["title"], equal_to("Test Initiative"))

    @pytest.mark.asyncio
    async def test_get_by_uuid(self, session: Session, user, workspace: Workspace):
        """Test getting initiative by UUID."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await get_strategic_initiative.fn(str(initiative.id))

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result["data"]["initiative"]["title"], equal_to("Test Initiative"))

    @pytest.mark.asyncio
    async def test_get_nonexistent_initiative(self):
        """Test getting nonexistent initiative."""
        fake_id = str(uuid.uuid4())

        result = await get_strategic_initiative.fn(fake_id)

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "not found" in result["error_message"]


class TestUpdateStrategicInitiative:
    """Test suite for update_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_update_title_and_description(
        self, session: Session, user, workspace: Workspace
    ):
        """Test updating initiative title and description."""
        initiative = Initiative(
            title="Original Title",
            description="Original description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        new_title = "Updated Title"
        new_description = "Updated description"

        result = await update_strategic_initiative.fn(
            query=initiative.identifier,
            title=new_title,
            description=new_description,
        )

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify updates in database
        session.refresh(initiative)
        assert initiative.title == new_title
        assert initiative.description == new_description

    @pytest.mark.asyncio
    async def test_update_status(self, session: Session, user, workspace: Workspace):
        """Test updating initiative status."""
        from src.models import ContextType
        from src.services.ordering_service import OrderingService

        initiative = Initiative(
            title="Test Initiative For Update Status",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        # Add to ordering service so it can be updated
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=initiative,
        )

        initiative_id = initiative.id
        initiative_identifier = initiative.identifier

        strategic_init = StrategicInitiative(
            initiative_id=initiative_id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await update_strategic_initiative.fn(
            query=initiative_identifier,
            status="IN_PROGRESS",
        )

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify status updated in database with a fresh query
        updated_initiative = (
            session.query(Initiative).filter_by(id=initiative_id).first()
        )
        assert updated_initiative is not None
        assert updated_initiative.status == InitiativeStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_narrative_intent(
        self, session: Session, user, workspace: Workspace
    ):
        """Test updating narrative intent."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
            narrative_intent="Original intent",
        )
        session.add(strategic_init)
        session.commit()

        new_intent = "Updated narrative intent"

        result = await update_strategic_initiative.fn(
            query=initiative.identifier,
            narrative_intent=new_intent,
        )

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify intent updated
        session.refresh(strategic_init)
        assert strategic_init.narrative_intent == new_intent

    @pytest.mark.asyncio
    async def test_update_with_no_changes(
        self, session: Session, user, workspace: Workspace
    ):
        """Test update with no fields provided."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await update_strategic_initiative.fn(query=initiative.identifier)

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "must be provided" in result["error_message"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_initiative(self):
        """Test updating nonexistent initiative."""
        fake_id = str(uuid.uuid4())

        result = await update_strategic_initiative.fn(
            query=fake_id,
            title="New Title",
        )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )


class TestDeleteStrategicInitiative:
    """Test suite for delete_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_delete_initiative_by_identifier(
        self, session: Session, user, workspace: Workspace
    ):
        """Test deleting initiative by identifier."""
        initiative = Initiative(
            title="Test Initiative For Delete By ID",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        identifier = initiative.identifier
        initiative_id = initiative.id

        strategic_init = StrategicInitiative(
            initiative_id=initiative_id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await delete_strategic_initiative.fn(query=identifier)

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert result["data"]["deleted_identifier"] == identifier

        # Verify initiative was deleted with a fresh query
        deleted_initiative = (
            session.query(Initiative).filter_by(id=initiative_id).first()
        )
        assert deleted_initiative is None

    @pytest.mark.asyncio
    async def test_delete_initiative_by_uuid(
        self, session: Session, user, workspace: Workspace
    ):
        """Test deleting initiative by UUID."""
        initiative = Initiative(
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        result = await delete_strategic_initiative.fn(query=str(initiative.id))

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify initiative was deleted
        deleted_initiative = (
            session.query(Initiative).filter_by(id=initiative.id).first()
        )
        assert deleted_initiative is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_initiative(self):
        """Test deleting nonexistent initiative."""
        fake_id = str(uuid.uuid4())

        result = await delete_strategic_initiative.fn(query=fake_id)

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )


class TestStrategicInitiativeNarrativeSummary:
    """Test suite for narrative summary generation."""

    @pytest.mark.asyncio
    async def test_narrative_summary_with_all_connections(
        self, session: Session, user, workspace: Workspace
    ):
        """Test that narrative summary includes all connections."""
        # Create strategic entities
        pillar = StrategicPillar(
            name="Deep IDE Integration",
            description="Seamless developer workflow",
            workspace_id=workspace.id,
            user_id=user.id,
            display_order=0,
        )
        session.add(pillar)

        theme = RoadmapTheme(
            name="IDE Excellence",
            description="Problem: context switching",
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(theme)

        session.commit()
        session.refresh(pillar)
        session.refresh(theme)

        # Create initiative with strategic connections
        initiative = Initiative(
            title="Smart Context Switching",
            description="Auto-save and restore IDE context",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
            pillar_id=pillar.id,
            theme_id=theme.id,
            narrative_intent="Defeats context switching for Sarah",
        )
        session.add(strategic_init)
        session.commit()

        result = await get_strategic_initiative.fn(initiative.identifier)

        # Verify narrative summary includes strategic elements
        narrative_summary = result["data"]["narrative_summary"]
        assert "Deep IDE Integration" in narrative_summary
        assert "IDE Excellence" in narrative_summary
        assert "Defeats context switching for Sarah" in narrative_summary


class TestStrategicInitiativeErrors:
    """Test suite for error handling in strategic initiatives."""

    @pytest.mark.asyncio
    async def test_framework_handles_error_gracefully(self):
        """Test that framework handles unexpected errors gracefully."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace_id:
            mock_get_workspace_id.side_effect = Exception("Database connection error")

            result = await get_strategic_initiative_definition_framework.fn()

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )

    @pytest.mark.asyncio
    async def test_submit_with_mcp_context_error(self, user, workspace: Workspace):
        """Test that submit handles authentication context errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_auth:
            from src.mcp_server.auth_utils import MCPContextError

            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await submit_strategic_initiative.fn(
                title="Test Initiative",
                description="Test description",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
