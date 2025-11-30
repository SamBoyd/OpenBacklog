"""Unit tests for strategic initiative MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    greater_than,
    has_entries,
    has_key,
    has_length,
)
from sqlalchemy.orm.session import Session

from src.mcp_server.prompt_driven_tools.strategic_initiatives import (
    get_strategic_initiative,
    get_strategic_initiative_definition_framework,
    get_strategic_initiatives,
    submit_strategic_initiative,
)
from src.models import Workspace


class TestGetStrategicInitiativeDefinitionFramework:
    """Test suite for get_strategic_initiative_definition_framework tool."""

    @pytest.mark.asyncio
    async def test_returns_framework_structure(self, workspace: Workspace):
        """Test that framework returns expected structure."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
            ) as mock_get_workspace:
                mock_get_workspace.return_value = workspace.id

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.HeroService"
                ) as mock_hero_service:
                    mock_hero_service.return_value.get_heroes_for_workspace.return_value = (
                        []
                    )

                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_initiatives.VillainService"
                    ) as mock_villain_service:
                        mock_villain_service.return_value.get_villains_for_workspace.return_value = (
                            []
                        )

                        with patch(
                            "src.mcp_server.prompt_driven_tools.strategic_initiatives.strategic_controller"
                        ) as mock_strategic_controller:
                            mock_strategic_controller.get_strategic_pillars.return_value = (
                                []
                            )

                            mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
                                []
                            )
                            mock_session.query.return_value.filter_by.return_value.all.return_value = (
                                []
                            )

                            result = (
                                await get_strategic_initiative_definition_framework.fn()
                            )

        assert_that(result, has_key("entity_type"))
        assert_that(result["entity_type"], equal_to("strategic_initiative"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("questions_to_explore"))
        assert_that(result, has_key("anti_patterns"))
        assert_that(result, has_key("coaching_tips"))
        assert_that(result, has_key("current_state"))

    @pytest.mark.asyncio
    async def test_framework_includes_available_entities(
        self, workspace: Workspace, session: Session
    ):
        """Test that framework includes available heroes, villains, pillars, themes."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain, VillainType
        from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
        from src.strategic_planning.services.event_publisher import EventPublisher

        publisher = EventPublisher(session)

        Hero.define_hero(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Hero",
            description="A test hero",
            is_primary=True,
            session=session,
            publisher=publisher,
        )

        Villain.define_villain(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Villain",
            villain_type=VillainType.WORKFLOW,
            description="A test villain",
            severity=3,
            session=session,
            publisher=publisher,
        )

        StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
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
        assert_that(current_state["available_heroes"], has_length(1))
        assert_that(current_state["available_villains"], has_length(1))
        assert_that(current_state["available_pillars"], has_length(1))


class TestSubmitStrategicInitiativeDraftMode:
    """Test suite for submit_strategic_initiative draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace: Workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        title = "Smart Context Switching"
        description = "Auto-save and restore IDE context when switching between tasks."

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_initiatives.validate_strategic_initiative_constraints"
            ) as mock_validate:
                mock_validate.return_value = {
                    "valid_hero_ids": [],
                    "valid_villain_ids": [],
                    "valid_conflict_ids": [],
                    "valid_pillar_id": None,
                    "valid_theme_id": None,
                    "warnings": [],
                }

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (
                        str(uuid.uuid4()),
                        str(workspace.id),
                    )

                    result = await submit_strategic_initiative.fn(
                        title=title,
                        description=description,
                        draft_mode=True,
                    )

        assert_that(
            result, has_entries({"status": "success", "type": "strategic_initiative"})
        )
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data, has_key("initiative"))
        assert_that(data, has_key("strategic_context"))
        assert_that(data["initiative"]["title"], equal_to(title))
        assert_that(data["initiative"]["description"], equal_to(description))

        mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_mode_with_warnings_for_invalid_ids(self, workspace: Workspace):
        """Test that draft mode returns warnings for invalid narrative IDs."""
        title = "Test Initiative"
        description = "Test description for initiative"
        invalid_hero_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_initiatives.validate_strategic_initiative_constraints"
            ) as mock_validate:
                mock_validate.return_value = {
                    "valid_hero_ids": [],
                    "valid_villain_ids": [],
                    "valid_conflict_ids": [],
                    "valid_pillar_id": None,
                    "valid_theme_id": None,
                    "warnings": [f"Hero ID {invalid_hero_id} not found - skipped"],
                }

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (
                        str(uuid.uuid4()),
                        str(workspace.id),
                    )

                    result = await submit_strategic_initiative.fn(
                        title=title,
                        description=description,
                        hero_ids=[invalid_hero_id],
                        draft_mode=True,
                    )

        assert_that(result["status"], equal_to("success"))
        assert_that(result, has_key("warnings"))
        assert_that(result["warnings"], has_length(1))
        assert_that(result["warnings"][0], contains_string("Hero ID"))
        assert_that(result["warnings"][0], contains_string("not found"))


class TestSubmitStrategicInitiativePersistMode:
    """Test suite for submit_strategic_initiative persist mode functionality."""

    @pytest.mark.asyncio
    async def test_persist_mode_creates_initiative_and_strategic_context(
        self, workspace: Workspace, session: Session
    ):
        """Test that draft_mode=False creates both Initiative and StrategicInitiative."""
        from src.initiative_management.aggregates.strategic_initiative import (
            StrategicInitiative,
        )
        from src.models import Initiative

        title = "Full Strategic Initiative Test"
        description = "Testing full creation with strategic context"

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            result = await submit_strategic_initiative.fn(
                title=title,
                description=description,
                narrative_intent="This is a test narrative intent",
                draft_mode=False,
            )

        assert_that(result["status"], equal_to("success"))
        assert_that(result["type"], equal_to("strategic_initiative"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("initiative"))
        assert_that(result["data"], has_key("strategic_context"))

        initiative_id = result["data"]["initiative"]["id"]
        initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        assert initiative is not None
        assert_that(initiative.title, equal_to(title))

        strategic_context = (
            session.query(StrategicInitiative)
            .filter_by(initiative_id=initiative_id)
            .first()
        )
        assert strategic_context is not None
        assert_that(
            strategic_context.narrative_intent,
            equal_to("This is a test narrative intent"),
        )

    @pytest.mark.asyncio
    async def test_persist_mode_links_valid_heroes_and_villains(
        self, workspace: Workspace, session: Session
    ):
        """Test that persist mode properly links valid heroes and villains."""
        from src.initiative_management.aggregates.strategic_initiative import (
            StrategicInitiative,
        )
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain, VillainType
        from src.strategic_planning.services.event_publisher import EventPublisher

        publisher = EventPublisher(session)

        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Hero for Link",
            description="A test hero for linking",
            is_primary=False,
            session=session,
            publisher=publisher,
        )

        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Villain for Link",
            villain_type=VillainType.TECHNICAL,
            description="A test villain for linking",
            severity=4,
            session=session,
            publisher=publisher,
        )

        session.commit()

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            result = await submit_strategic_initiative.fn(
                title="Initiative with Links",
                description="Testing hero and villain linking",
                hero_ids=[str(hero.id)],
                villain_ids=[str(villain.id)],
                draft_mode=False,
            )

        assert_that(result["status"], equal_to("success"))

        strategic_context_id = result["data"]["strategic_context"]["id"]
        strategic_context = (
            session.query(StrategicInitiative)
            .filter_by(id=strategic_context_id)
            .first()
        )
        assert strategic_context is not None
        session.refresh(strategic_context)

        assert_that(strategic_context.heroes, has_length(1))
        assert_that(strategic_context.villains, has_length(1))
        assert_that(strategic_context.heroes[0].id, equal_to(hero.id))
        assert_that(strategic_context.villains[0].id, equal_to(villain.id))


class TestGetStrategicInitiatives:
    """Test suite for get_strategic_initiatives retrieval tool."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_strategic_initiatives(
        self, workspace: Workspace
    ):
        """Test that tool returns empty list when no strategic initiatives exist."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
            ) as mock_get_workspace:
                mock_get_workspace.return_value = workspace.id

                mock_query = MagicMock()
                mock_session.query.return_value = mock_query
                mock_query.options.return_value = mock_query
                mock_query.filter_by.return_value = mock_query
                mock_query.all.return_value = []

                result = await get_strategic_initiatives.fn()

        assert_that(result["status"], equal_to("success"))
        assert_that(result["type"], equal_to("strategic_initiative"))
        assert_that(result["data"]["strategic_initiatives"], has_length(0))

    @pytest.mark.asyncio
    async def test_returns_strategic_initiatives_with_narrative_summary(
        self, workspace: Workspace, session: Session
    ):
        """Test that tool returns strategic initiatives with narrative summaries."""

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            await submit_strategic_initiative.fn(
                title="Test Initiative for Retrieval",
                description="Testing retrieval functionality",
                narrative_intent="Test narrative intent",
                draft_mode=False,
            )

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiatives.fn()

        assert_that(result["status"], equal_to("success"))
        assert_that(
            result["data"]["strategic_initiatives"], has_length(greater_than(0))
        )

        initiative_data = result["data"]["strategic_initiatives"][0]
        assert_that(initiative_data, has_key("initiative"))
        assert_that(initiative_data, has_key("strategic_context"))
        assert_that(initiative_data, has_key("narrative_summary"))


class TestValidationConstraints:
    """Test suite for validate_strategic_initiative_constraints function."""

    def test_validates_title_required(self, workspace: Workspace, session: Session):
        """Test that empty title raises DomainException."""
        from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
            validate_strategic_initiative_constraints,
        )
        from src.strategic_planning.exceptions import DomainException

        with pytest.raises(DomainException) as exc_info:
            validate_strategic_initiative_constraints(
                workspace_id=workspace.id,
                title="",
                description="Test description",
                hero_ids=[],
                villain_ids=[],
                conflict_ids=[],
                pillar_id=None,
                theme_id=None,
                narrative_intent=None,
                session=session,
            )

        assert "Title is required" in str(exc_info.value)

    def test_validates_description_required(
        self, workspace: Workspace, session: Session
    ):
        """Test that empty description raises DomainException."""
        from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
            validate_strategic_initiative_constraints,
        )
        from src.strategic_planning.exceptions import DomainException

        with pytest.raises(DomainException) as exc_info:
            validate_strategic_initiative_constraints(
                workspace_id=workspace.id,
                title="Test Title",
                description="",
                hero_ids=[],
                villain_ids=[],
                conflict_ids=[],
                pillar_id=None,
                theme_id=None,
                narrative_intent=None,
                session=session,
            )

        assert "Description is required" in str(exc_info.value)

    def test_returns_warnings_for_invalid_hero_ids(
        self, workspace: Workspace, session: Session
    ):
        """Test that invalid hero IDs result in warnings, not errors."""
        from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
            validate_strategic_initiative_constraints,
        )

        invalid_id = str(uuid.uuid4())

        result = validate_strategic_initiative_constraints(
            workspace_id=workspace.id,
            title="Test Title",
            description="Test description",
            hero_ids=[invalid_id],
            villain_ids=[],
            conflict_ids=[],
            pillar_id=None,
            theme_id=None,
            narrative_intent=None,
            session=session,
        )

        assert_that(result["valid_hero_ids"], has_length(0))
        assert_that(result["warnings"], has_length(1))
        assert_that(result["warnings"][0], contains_string("Hero ID"))
        assert_that(result["warnings"][0], contains_string("not found"))

    def test_validates_real_hero_ids(self, workspace: Workspace, session: Session):
        """Test that valid hero IDs are returned in valid_hero_ids."""
        from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
            validate_strategic_initiative_constraints,
        )
        from src.narrative.aggregates.hero import Hero
        from src.strategic_planning.services.event_publisher import EventPublisher

        publisher = EventPublisher(session)
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
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
            hero_ids=[str(hero.id)],
            villain_ids=[],
            conflict_ids=[],
            pillar_id=None,
            theme_id=None,
            narrative_intent=None,
            session=session,
        )

        assert_that(result["valid_hero_ids"], has_length(1))
        assert_that(result["valid_hero_ids"][0], equal_to(hero.id))
        assert_that(result["warnings"], has_length(0))


class TestGetStrategicInitiative:
    """Test suite for get_strategic_initiative retrieval tool."""

    @pytest.mark.asyncio
    async def test_finds_by_strategic_initiative_id(
        self, workspace: Workspace, session: Session
    ):
        """Test lookup by strategic initiative UUID."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative for ID Lookup",
                description="Testing lookup by strategic initiative ID",
                draft_mode=False,
            )

        strategic_initiative_id = create_result["data"]["strategic_context"]["id"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative.fn(query=strategic_initiative_id)

        assert_that(result["status"], equal_to("success"))
        assert_that(result["data"]["id"], equal_to(strategic_initiative_id))
        assert_that(
            result["data"]["initiative"]["title"], equal_to("Initiative for ID Lookup")
        )

    @pytest.mark.asyncio
    async def test_finds_by_initiative_id(self, workspace: Workspace, session: Session):
        """Test lookup by initiative UUID."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative for Initiative ID Lookup",
                description="Testing lookup by initiative ID",
                draft_mode=False,
            )

        initiative_id = create_result["data"]["initiative"]["id"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative.fn(query=initiative_id)

        assert_that(result["status"], equal_to("success"))
        assert_that(result["data"]["initiative"]["id"], equal_to(initiative_id))

    @pytest.mark.asyncio
    async def test_finds_by_initiative_identifier(
        self, workspace: Workspace, session: Session
    ):
        """Test lookup by initiative identifier (e.g., 'I-1001')."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative for Identifier Lookup",
                description="Testing lookup by identifier",
                draft_mode=False,
            )

        initiative_identifier = create_result["data"]["initiative"]["identifier"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative.fn(query=initiative_identifier)

        assert_that(result["status"], equal_to("success"))
        assert_that(
            result["data"]["initiative"]["identifier"], equal_to(initiative_identifier)
        )

    @pytest.mark.asyncio
    async def test_returns_error_for_not_found(self, workspace: Workspace):
        """Test that not found query returns error response."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative.fn(query="nonexistent-identifier")

        assert_that(result["status"], equal_to("error"))
        assert_that(result["error_message"], contains_string("not found"))

    @pytest.mark.asyncio
    async def test_returns_narrative_summary(
        self, workspace: Workspace, session: Session
    ):
        """Test that response includes narrative summary."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ) as mock_get_auth:
            mock_get_auth.return_value = (
                str(workspace.user_id),
                str(workspace.id),
            )

            create_result = await submit_strategic_initiative.fn(
                title="Initiative with Narrative",
                description="Testing narrative summary in response",
                narrative_intent="To prove the tool works",
                draft_mode=False,
            )

        initiative_id = create_result["data"]["initiative"]["id"]

        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ) as mock_get_workspace:
            mock_get_workspace.return_value = workspace.id

            result = await get_strategic_initiative.fn(query=initiative_id)

        assert_that(result["status"], equal_to("success"))
        assert_that(result["data"], has_key("narrative_summary"))
        assert_that(
            result["data"]["narrative_summary"],
            contains_string("To prove the tool works"),
        )
