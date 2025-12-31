"""Comprehensive tests for prompt-driven strategic initiative workflow MCP tools."""

import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm.session import Session

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.mcp_server.prompt_driven_tools.strategic_initiatives import (
    delete_strategic_initiative,
    get_strategic_initiative_definition_framework,
    query_strategic_initiatives,
    submit_strategic_initiative,
)
from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
    validate_strategic_initiative_constraints,
)
from src.models import Initiative, InitiativeStatus, User, Workspace
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain, VillainType
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


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
        assert_that(result, has_key("templates"))

        # Verify entity type
        assert_that(result["entity_type"], equal_to("strategic_initiative"))

    @pytest.mark.asyncio
    async def test_framework_includes_markdown_templates(self):
        """Test that framework includes markdown templates for description fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

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
                mock_villain_service.get_villains_for_workspace.return_value = []
                mock_villain_service_class.return_value = mock_villain_service

                mock_get_pillars.return_value = []

                mock_query = MagicMock()
                mock_query.filter_by.return_value.order_by.return_value.all.return_value = (
                    []
                )
                mock_session.query.return_value = mock_query

                result = await get_strategic_initiative_definition_framework.fn()

        # Verify templates are present
        assert_that(result, has_key("templates"))
        templates = result["templates"]

        # Verify all three description field templates exist
        assert_that(templates, has_key("implementation_description"))
        assert_that(templates, has_key("strategic_description"))
        assert_that(templates, has_key("narrative_intent"))

        # Verify templates contain expected markdown sections
        assert "## Technical Approach" in templates["implementation_description"]
        assert "## Scope" in templates["implementation_description"]

        assert "## Strategic Alignment" in templates["strategic_description"]
        assert "## Why Now" in templates["strategic_description"]
        assert "## Expected Impact" in templates["strategic_description"]

        assert "**[hero name]**" in templates["narrative_intent"]
        assert "**[villain name]**" in templates["narrative_intent"]

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

    @pytest.mark.asyncio
    async def test_framework_includes_available_entities_from_db(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that framework includes available heroes, villains, pillars, themes from database."""
        publisher = EventPublisher(session)

        Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Hero",
            description="A test hero",
            is_primary=True,
            session=session,
            publisher=publisher,
        )

        Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Villain",
            villain_type=VillainType.WORKFLOW,
            description="A test villain",
            severity=3,
            session=session,
            publisher=publisher,
        )

        StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Pillar",
            description="A test pillar",
            display_order=0,
            session=session,
            publisher=publisher,
        )

        session.commit()

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative_definition_framework.fn()

        current_state = result["current_state"]
        assert_that(current_state["hero_count"], equal_to(1))
        assert_that(current_state["villain_count"], equal_to(1))
        assert_that(current_state["pillar_count"], equal_to(1))
        assert len(current_state["available_heroes"]) == 1
        assert len(current_state["available_villains"]) == 1
        assert len(current_state["available_pillars"]) == 1


class TestSubmitStrategicInitiative:
    """Test suite for submit_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_initiative_successfully(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that submit successfully creates initiative."""
        title = "Smart Context Switching"
        impl_description = (
            "Auto-save and restore IDE context when switching between tasks"
        )

        result = await submit_strategic_initiative.fn(
            title=title,
            implementation_description=impl_description,
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
        assert initiative.description == impl_description
        assert initiative.status == InitiativeStatus.BACKLOG

    @pytest.mark.asyncio
    async def test_submit_with_narrative_connections(
        self, session: Session, user: User, workspace: Workspace
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
        impl_description = (
            "Auto-save and restore IDE context when switching between tasks"
        )

        result = await submit_strategic_initiative.fn(
            title=title,
            implementation_description=impl_description,
            hero_identifiers=[hero.identifier],
            villain_identifiers=[villain.identifier],
            pillar_identifier=pillar.identifier,
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
                implementation_description="Test description",
                status="INVALID_STATUS",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "Invalid status" in result["error_message"]

    @pytest.mark.asyncio
    async def test_submit_with_nonexistent_hero(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that submit gracefully handles invalid hero identifiers."""
        fake_hero_identifier = "H-9999"

        result = await submit_strategic_initiative.fn(
            title="Test Initiative",
            implementation_description="Test description",
            hero_identifiers=[fake_hero_identifier],
        )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "Hero with identifier" in result["error_message"]
        assert "not found" in result["error_message"]

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.validate_strategic_initiative_constraints"
        ) as mock_validate:
            mock_validate.side_effect = DomainException("Invalid title")

            result = await submit_strategic_initiative.fn(
                title="",
                implementation_description="Test description",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )


class TestQueryStrategicInitiativesList:
    """Test suite for query_strategic_initiatives tool in list mode."""

    @pytest.mark.asyncio
    async def test_query_empty_initiatives(self):
        """Test querying initiatives when none exist."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_query = MagicMock()
            mock_query.options.return_value.filter_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query

            result = await query_strategic_initiatives.fn()

        # Verify response structure
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result, has_key("data"))
        assert len(result["data"]["strategic_initiatives"]) == 0

    @pytest.mark.asyncio
    async def test_query_multiple_initiatives(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying multiple strategic initiatives."""
        # Create multiple initiatives
        initiatives: List[Initiative] = []
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

        result = await query_strategic_initiatives.fn()

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert len(result["data"]["strategic_initiatives"]) == 3

    @pytest.mark.asyncio
    async def test_returns_strategic_initiatives_with_narrative_summary(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that tool returns strategic initiatives with narrative summaries."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(user.id),
                str(workspace.id),
            )

            await submit_strategic_initiative.fn(
                title="Test Initiative for Retrieval",
                implementation_description="Testing retrieval functionality",
                narrative_intent="Test narrative intent",
            )

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await query_strategic_initiatives.fn()

        assert_that(result["status"], equal_to("success"))
        assert len(result["data"]["strategic_initiatives"]) > 0

        initiative_data = result["data"]["strategic_initiatives"][0]
        assert "initiative" in initiative_data
        assert "strategic_context" in initiative_data
        assert "narrative_summary" in initiative_data


class TestQueryStrategicInitiativesSingle:
    """Test suite for query_strategic_initiatives tool in single mode."""

    @pytest.mark.asyncio
    async def test_query_by_identifier(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying initiative by identifier."""
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

        result = await query_strategic_initiatives.fn(identifier=initiative.identifier)

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result["data"]["initiative"]["title"], equal_to("Test Initiative"))

    @pytest.mark.asyncio
    async def test_query_by_uuid(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying initiative by UUID."""
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

        result = await query_strategic_initiatives.fn(identifier=str(initiative.id))

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result["data"]["initiative"]["title"], equal_to("Test Initiative"))

    @pytest.mark.asyncio
    async def test_query_nonexistent_initiative(self):
        """Test querying nonexistent initiative."""
        fake_id = str(uuid.uuid4())

        result = await query_strategic_initiatives.fn(identifier=fake_id)

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )
        assert "not found" in result["error_message"]

    @pytest.mark.asyncio
    async def test_query_by_initiative_identifier(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test lookup by initiative identifier (e.g., I-1001)."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(user.id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative for Identifier Lookup",
                implementation_description="Testing lookup by initiative identifier",
            )

        initiative_identifier = create_result["data"]["initiative"]["identifier"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await query_strategic_initiatives.fn(
                identifier=initiative_identifier
            )

        assert_that(result["status"], equal_to("success"))
        assert_that(
            result["data"]["initiative"]["identifier"], equal_to(initiative_identifier)
        )
        assert_that(
            result["data"]["initiative"]["title"],
            equal_to("Initiative for Identifier Lookup"),
        )

    @pytest.mark.asyncio
    async def test_query_returns_narrative_summary(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that response includes narrative summary."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(user.id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative with Narrative",
                implementation_description="Testing narrative summary in response",
                narrative_intent="To prove the tool works",
            )

        initiative_id = create_result["data"]["initiative"]["id"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await query_strategic_initiatives.fn(identifier=initiative_id)

        assert_that(result["status"], equal_to("success"))
        assert "narrative_summary" in result["data"]
        assert "To prove the tool works" in result["data"]["narrative_summary"]


class TestQueryStrategicInitiativesFilters:
    """Test suite for query_strategic_initiatives tool with filters."""

    @pytest.mark.asyncio
    async def test_query_by_status_filter(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying initiatives filtered by status."""
        # Create initiatives with different statuses
        backlog_init = Initiative(
            title="Backlog Initiative",
            description="In backlog",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        in_progress_init = Initiative(
            title="In Progress Initiative",
            description="Currently in progress",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.IN_PROGRESS,
        )
        session.add(backlog_init)
        session.add(in_progress_init)
        session.commit()

        # Create strategic initiatives
        for initiative in [backlog_init, in_progress_init]:
            session.refresh(initiative)
            strategic_init = StrategicInitiative(
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                description="Strategic context",
            )
            session.add(strategic_init)

        session.commit()

        # Query for IN_PROGRESS only
        result = await query_strategic_initiatives.fn(status="IN_PROGRESS")

        assert_that(result["status"], equal_to("success"))
        assert len(result["data"]["strategic_initiatives"]) == 1
        assert (
            result["data"]["strategic_initiatives"][0]["initiative"]["status"]
            == "IN_PROGRESS"
        )

    @pytest.mark.asyncio
    async def test_query_by_search_filter(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying initiatives by search term."""
        # Create initiatives
        matching_init = Initiative(
            title="Context Switching Platform",
            description="Solve context switching issues",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        non_matching_init = Initiative(
            title="Performance Optimization",
            description="Make things faster",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(matching_init)
        session.add(non_matching_init)
        session.commit()

        # Create strategic initiatives
        for initiative in [matching_init, non_matching_init]:
            session.refresh(initiative)
            strategic_init = StrategicInitiative(
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                description="Strategic context",
            )
            session.add(strategic_init)

        session.commit()

        # Search for "context"
        result = await query_strategic_initiatives.fn(search="context")

        assert_that(result["status"], equal_to("success"))
        assert len(result["data"]["strategic_initiatives"]) >= 1
        # Verify matching initiative is in results
        found = False
        for init_data in result["data"]["strategic_initiatives"]:
            if "Context Switching" in init_data["initiative"]["title"]:
                found = True
                break
        assert found

    @pytest.mark.asyncio
    async def test_query_with_combined_filters(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test querying with multiple filters combined."""
        # Create initiatives
        matching_init = Initiative(
            title="Context Switching Solution",
            description="Solve context switching",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.IN_PROGRESS,
        )
        non_matching_status = Initiative(
            title="Context Switching Design",
            description="Design phase",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(matching_init)
        session.add(non_matching_status)
        session.commit()

        # Create strategic initiatives
        for initiative in [matching_init, non_matching_status]:
            session.refresh(initiative)
            strategic_init = StrategicInitiative(
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                description="Strategic context",
            )
            session.add(strategic_init)

        session.commit()

        # Query with both filters
        result = await query_strategic_initiatives.fn(
            search="context", status="IN_PROGRESS"
        )

        assert_that(result["status"], equal_to("success"))
        # Should only get the IN_PROGRESS initiative matching "context"
        assert len(result["data"]["strategic_initiatives"]) >= 1
        for init_data in result["data"]["strategic_initiatives"]:
            assert init_data["initiative"]["status"] == "IN_PROGRESS"


class TestQueryStrategicInitiativesWithTasks:
    """Test suite for query_strategic_initiatives with include_tasks parameter."""

    @pytest.mark.asyncio
    async def test_query_single_initiative_with_tasks(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that include_tasks returns tasks array when querying single initiative."""
        from src.models import ContextType, Task
        from src.services.ordering_service import OrderingService

        # Create initiative
        initiative = Initiative(
            title="Initiative With Tasks",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        # Create strategic initiative
        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        # Create tasks
        task1 = Task(
            title="Task 1",
            description="First task",
            user_id=user.id,
            initiative_id=initiative.id,
            workspace_id=workspace.id,
        )
        task2 = Task(
            title="Task 2",
            description="Second task",
            user_id=user.id,
            initiative_id=initiative.id,
            workspace_id=workspace.id,
        )
        session.add(task1)
        session.add(task2)
        session.commit()
        session.refresh(task1)
        session.refresh(task2)

        # Add to ordering
        ordering_service = OrderingService(session)
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task1,
        )
        ordering_service.add_item(
            context_type=ContextType.STATUS_LIST,
            context_id=None,
            item=task2,
        )

        # Query with include_tasks
        result = await query_strategic_initiatives.fn(
            identifier=initiative.identifier, include_tasks=True
        )

        assert_that(result["status"], equal_to("success"))
        assert "tasks" in result["data"]
        assert len(result["data"]["tasks"]) == 2
        task_titles = [t["title"] for t in result["data"]["tasks"]]
        assert "Task 1" in task_titles
        assert "Task 2" in task_titles

    @pytest.mark.asyncio
    async def test_query_without_include_tasks_no_tasks_array(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that tasks array is not included when include_tasks is False."""
        # Create initiative
        initiative = Initiative(
            title="Initiative Without Tasks Array",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

        # Create strategic initiative
        strategic_init = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            description="Strategic context",
        )
        session.add(strategic_init)
        session.commit()

        # Query without include_tasks
        result = await query_strategic_initiatives.fn(identifier=initiative.identifier)

        assert_that(result["status"], equal_to("success"))
        assert "tasks" not in result["data"]


class TestSubmitStrategicInitiativeUpsert:
    """Test suite for submit_strategic_initiative upsert functionality."""

    @pytest.mark.asyncio
    async def test_upsert_title_and_implementation_description(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test upsert (update) of initiative title and implementation description."""
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
        new_impl_description = "Updated implementation description"

        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
            title=new_title,
            implementation_description=new_impl_description,
        )

        # Verify response
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        # Verify updates in database
        session.refresh(initiative)
        assert initiative.title == new_title
        assert initiative.description == new_impl_description

    @pytest.mark.asyncio
    async def test_upsert_status(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test upsert (update) of initiative status."""
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

        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative_identifier,
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
    async def test_upsert_narrative_intent(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test upsert (update) of narrative intent."""
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

        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
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
    async def test_upsert_with_no_changes(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test upsert (update) with no fields provided."""
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

        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier
        )

        # Verify success - upsert should succeed even with no changes
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert initiative.title == "Test Initiative"

    @pytest.mark.asyncio
    async def test_upsert_nonexistent_initiative(self):
        """Test upserting nonexistent initiative."""
        fake_id = str(uuid.uuid4())

        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=fake_id,
            title="New Title",
        )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )

    @pytest.mark.asyncio
    async def test_upsert_can_modify_descriptions_independently(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that upsert can modify implementation and strategic descriptions independently."""
        initiative = Initiative(
            title="Initiative for Independent Updates",
            description="Original implementation description",
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
            description="Original strategic description",
        )
        session.add(strategic_init)
        session.commit()

        new_impl_desc = "Updated implementation description"
        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
            implementation_description=new_impl_desc,
        )

        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        session.refresh(initiative)
        session.refresh(strategic_init)
        assert initiative.description == new_impl_desc
        assert strategic_init.description == "Original strategic description"

        new_strategic_desc = "Updated strategic description"
        result = await submit_strategic_initiative.fn(
            strategic_initiative_identifier=initiative.identifier,
            strategic_description=new_strategic_desc,
        )

        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        session.refresh(initiative)
        session.refresh(strategic_init)
        assert initiative.description == new_impl_desc
        assert strategic_init.description == new_strategic_desc


class TestDeleteStrategicInitiative:
    """Test suite for delete_strategic_initiative tool."""

    @pytest.mark.asyncio
    async def test_delete_initiative_by_identifier(
        self, session: Session, user: User, workspace: Workspace
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
        self, session: Session, user: User, workspace: Workspace
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
        self, session: Session, user: User, workspace: Workspace
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

        result = await query_strategic_initiatives.fn(identifier=initiative.identifier)

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
    async def test_submit_with_mcp_context_error(
        self, user: User, workspace: Workspace
    ):
        """Test that submit handles authentication context errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_auth:
            from src.mcp_server.auth_utils import MCPContextError

            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await submit_strategic_initiative.fn(
                title="Test Initiative",
                implementation_description="Test description",
            )

        # Verify error response
        assert_that(
            result, has_entries({"status": "error", "type": "strategic_initiative"})
        )


class TestValidationConstraints:
    """Test suite for validate_strategic_initiative_constraints function."""

    def test_validates_title_required(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that empty title raises DomainException."""
        with pytest.raises(DomainException) as exc_info:
            validate_strategic_initiative_constraints(
                workspace_id=workspace.id,
                title="",
                description="Test description",
                hero_identifiers=[],
                villain_identifiers=[],
                conflict_identifiers=[],
                pillar_identifier=None,
                theme_identifier=None,
                narrative_intent=None,
                session=session,
            )

        assert "Title is required" in str(exc_info.value)

    def test_validates_description_required(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that empty description raises DomainException."""
        with pytest.raises(DomainException) as exc_info:
            validate_strategic_initiative_constraints(
                workspace_id=workspace.id,
                title="Test Title",
                description="",
                hero_identifiers=[],
                villain_identifiers=[],
                conflict_identifiers=[],
                pillar_identifier=None,
                theme_identifier=None,
                narrative_intent=None,
                session=session,
            )

        assert "Description is required" in str(exc_info.value)

    def test_returns_warnings_for_invalid_hero_identifiers(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that invalid hero identifiers result in warnings, not errors."""
        invalid_identifier = "H-9999"

        with pytest.raises(DomainException):
            validate_strategic_initiative_constraints(
                workspace_id=workspace.id,
                title="Test Title",
                description="Test description",
                hero_identifiers=[invalid_identifier],
                villain_identifiers=[],
                conflict_identifiers=[],
                pillar_identifier=None,
                theme_identifier=None,
                narrative_intent=None,
                session=session,
            )

    def test_validates_real_hero_identifiers(
        self, workspace: Workspace, session: Session, user: User
    ):
        """Test that valid hero identifiers are resolved to valid_hero_ids."""
        publisher = EventPublisher(session)
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Valid Hero",
            description="A valid hero for testing",
            is_primary=False,
            session=session,
            publisher=publisher,
        )
        session.commit()

        result = validate_strategic_initiative_constraints(
            workspace_id=workspace.id,
            title="Test Title",
            description="Test description",
            hero_identifiers=[hero.identifier],
            villain_identifiers=[],
            conflict_identifiers=[],
            pillar_identifier=None,
            theme_identifier=None,
            narrative_intent=None,
            session=session,
        )

        assert len(result["valid_hero_ids"]) == 1
        assert_that(result["valid_hero_ids"][0], equal_to(hero.id))
        assert len(result["warnings"]) == 0


class TestDescriptionFieldsSeparation:
    """Test suite for verifying implementation and strategic descriptions are stored independently."""

    @pytest.mark.asyncio
    async def test_submit_stores_both_descriptions_independently(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that submit stores implementation and strategic descriptions in separate fields."""
        title = "Test Initiative With Both Descriptions"
        impl_desc = "This describes how we will implement the feature"
        strategic_desc = "This explains how it connects to our strategy"

        result = await submit_strategic_initiative.fn(
            title=title,
            implementation_description=impl_desc,
            strategic_description=strategic_desc,
        )

        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        initiative = session.query(Initiative).filter_by(title=title).first()
        assert initiative is not None
        assert initiative.description == impl_desc

        strategic_init = (
            session.query(StrategicInitiative)
            .filter_by(initiative_id=initiative.id)
            .first()
        )
        assert strategic_init is not None
        assert strategic_init.description == strategic_desc

    @pytest.mark.asyncio
    async def test_submit_uses_impl_description_as_fallback_for_strategic(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that implementation_description is used as fallback when strategic_description is not provided."""
        title = "Test Initiative Fallback Description"
        impl_desc = "This is the implementation description"

        result = await submit_strategic_initiative.fn(
            title=title,
            implementation_description=impl_desc,
        )

        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )

        initiative = session.query(Initiative).filter_by(title=title).first()
        assert initiative is not None
        assert initiative.description == impl_desc

        strategic_init = (
            session.query(StrategicInitiative)
            .filter_by(initiative_id=initiative.id)
            .first()
        )
        assert strategic_init is not None
        assert strategic_init.description is None
