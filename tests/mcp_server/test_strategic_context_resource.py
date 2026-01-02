"""Tests for the strategic context summary MCP tool."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.utils.serializers import (
    serialize_hero,
    serialize_villain,
)
from src.mcp_server.strategic_context_resource import (
    _adapt_outcome_for_template,
    _adapt_theme_for_template,
    _adapt_villain_for_template,
    get_strategic_context_summary,
)
from src.models import User, Workspace
from src.narrative import Hero, Villain
from src.narrative.aggregates.villain import VillainType
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.services.event_publisher import EventPublisher


class TestAdaptOutcomeForTemplate:
    """Tests for _adapt_outcome_for_template helper."""

    def test_adapt_outcome_with_pillars(self):
        """Test outcome adaptation with linked pillars."""
        outcome = MagicMock()
        outcome.identifier = "O-001"
        outcome.name = "Developer Adoption"
        outcome.description = "Goal: 80% daily active users."
        outcome.display_order = 1
        outcome.created_at = datetime(2024, 1, 15)
        outcome.updated_at = datetime(2024, 1, 15)

        pillar1 = MagicMock()
        pillar1.name = "IDE Integration"
        pillar1.identifier = "P-001"
        pillar2 = MagicMock()
        pillar2.name = "AI Native"
        pillar2.identifier = "P-002"
        outcome.pillars = [pillar1, pillar2]

        result = _adapt_outcome_for_template(outcome)

        assert result["identifier"] == "O-001"
        assert result["name"] == "Developer Adoption"
        assert result["pillar_names"] == ["IDE Integration", "AI Native"]
        assert "pillar_identifiers" in result

    def test_adapt_outcome_without_pillars(self):
        """Test outcome adaptation without linked pillars."""
        outcome = MagicMock()
        outcome.identifier = "O-002"
        outcome.name = "Retention"
        outcome.description = "Keep users."
        outcome.display_order = 2
        outcome.created_at = datetime(2024, 1, 15)
        outcome.updated_at = datetime(2024, 1, 15)
        outcome.pillars = []

        result = _adapt_outcome_for_template(outcome)

        assert result["identifier"] == "O-002"
        assert result["pillar_names"] == []


class TestAdaptThemeForTemplate:
    @pytest.fixture
    def mock_publisher(self, session: Session) -> EventPublisher:
        """Create a real EventPublisher for testing."""
        return EventPublisher(session)

    @pytest.fixture
    def roadmap_theme(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: EventPublisher,
    ) -> RoadmapTheme:
        """Create a real RoadmapTheme from the database."""
        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Theme",
            description="A test theme for strategic context",
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(theme)
        return theme

    def test_adapt_real_theme_without_hero_or_villain(
        self,
        roadmap_theme: RoadmapTheme,
    ):
        """Test that _adapt_theme_for_template works with real RoadmapTheme model.

        This test surfaces the bug where _adapt_theme_for_template tries to access
        theme.hero_id and theme.primary_villain_id, which don't exist on the
        RoadmapTheme model (it uses many-to-many heroes/villains relationships instead).
        """
        result = _adapt_theme_for_template(roadmap_theme, prioritized_theme_ids=[])

        assert result["identifier"] == roadmap_theme.identifier
        assert result["name"] == "Test Theme"
        assert result["heroes"] == []
        assert result["villains"] == []
        assert result["outcomes"] == []
        assert result["is_prioritized"] is False
        assert result["priority_order"] is None

    def test_adapt_real_theme_with_hero_and_villain(
        self,
        roadmap_theme: RoadmapTheme,
        session: Session,
        user: User,
        workspace: Workspace,
    ):
        """Test that _adapt_theme_for_template works with RoadmapTheme model with heroes and villains."""

        hero = Hero(
            id=uuid.uuid4(),
            user_id=user.id,
            workspace_id=workspace.id,
            identifier="H-001",
            name="Alex",
            description="Solo dev.",
            is_primary=True,
        )
        session.add(hero)
        session.commit()
        session.refresh(hero)

        villain = Villain(
            id=uuid.uuid4(),
            user_id=user.id,
            workspace_id=workspace.id,
            identifier="V-001",
            name="Context Switching",
            description="Breaks developer flow.",
            villain_type=VillainType.WORKFLOW,
            severity=4,
            is_defeated=False,
        )
        session.add(villain)
        session.commit()
        session.refresh(villain)

        roadmap_theme.link_heroes([hero.id], session)
        roadmap_theme.link_villains([villain.id], session)
        session.commit()
        session.refresh(roadmap_theme)

        prioritized_ids = [str(roadmap_theme.id)]
        result = _adapt_theme_for_template(roadmap_theme, prioritized_ids)

        assert result["identifier"] == roadmap_theme.identifier
        assert result["heroes"] == [serialize_hero(hero, include_connections=False)]
        assert result["villains"] == [
            serialize_villain(villain, include_connections=False)
        ]
        assert result["outcomes"] == []
        assert result["is_prioritized"] is True
        assert result["priority_order"] == 0


class TestAdaptVillainForTemplate:
    """Tests for _adapt_villain_for_template helper."""

    @pytest.fixture
    def villain(self) -> Villain:
        """Create a test villain."""
        return Villain(
            id=uuid.uuid4(),
            identifier="V-001",
            name="Context Switching",
            description="Breaks developer flow.",
            villain_type=VillainType.WORKFLOW,
            severity=4,
            is_defeated=False,
            created_at=datetime(2024, 1, 15),
            updated_at=datetime(2024, 1, 15),
        )

    def test_adapt_villain_with_enum_type(self, villain: Villain):
        """Test villain adaptation with enum villain_type."""
        result = _adapt_villain_for_template(villain)

        assert result["identifier"] == "V-001"
        assert result["name"] == "Context Switching"
        assert result["villain_type"] == "WORKFLOW"
        assert result["severity"] == 4
        assert result["is_defeated"] is False


class TestTemplateRendering:
    """Tests for Jinja2 template rendering."""

    def test_template_renders_with_all_data(self):
        """Test that template renders correctly with all data present."""
        from jinja2 import Environment, FileSystemLoader

        templates_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)
        template = env.get_template("prompts/strategic_context_summary.jinja")

        vision = MagicMock()
        vision.vision_text = "Enable developers to manage tasks in IDE"
        vision.created_at = datetime(2024, 1, 15)

        rendered = template.render(
            vision=vision,
            pillars=[
                {
                    "identifier": "P-001",
                    "name": "IDE Integration",
                    "description": "Stay in IDE.",
                },
                {
                    "identifier": "P-002",
                    "name": "AI Native",
                    "description": "AI first.",
                },
            ],
            outcomes=[
                {
                    "identifier": "O-001",
                    "name": "Adoption",
                    "description": "80% daily active.",
                    "pillar_names": ["IDE Integration"],
                },
                {
                    "identifier": "O-002",
                    "name": "Retention",
                    "description": "Keep users.",
                    "pillar_names": [],
                },
            ],
            themes=[
                {
                    "identifier": "T-001",
                    "name": "MCP Focus",
                    "description": "Build MCP tools.",
                    "is_prioritized": True,
                    "priority_order": 0,
                    "hero_name": "Alex",
                    "primary_villain_name": "Context Switching",
                    "outcome_names": ["Adoption"],
                }
            ],
            heroes=[
                {
                    "identifier": "H-001",
                    "name": "Alex",
                    "description": "Solo dev.",
                    "is_primary": True,
                }
            ],
            villains=[
                {
                    "identifier": "V-001",
                    "name": "Context Switching",
                    "description": "Breaks flow.",
                    "villain_type": "WORKFLOW",
                    "severity": 4,
                    "is_defeated": False,
                }
            ],
        )

        assert "# Strategic Context Summary" in rendered
        assert "Enable developers to manage tasks in IDE" in rendered
        assert "P-001: IDE Integration" in rendered
        assert "O-001: Adoption" in rendered
        assert "T-001: MCP Focus" in rendered
        assert "⭐ Priority #1" in rendered
        assert "H-001: Alex" in rendered
        assert "👑 PRIMARY" in rendered
        assert "V-001: Context Switching" in rendered

    def test_template_renders_with_missing_data(self):
        """Test that template renders correctly with missing data (shows warnings)."""
        from jinja2 import Environment, FileSystemLoader

        templates_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)
        template = env.get_template("prompts/strategic_context_summary.jinja")

        rendered = template.render(
            vision=None,
            pillars=[],
            outcomes=[],
            themes=[],
            heroes=[],
            villains=[],
        )

        assert "# Strategic Context Summary" in rendered
        assert "⚠️ **No vision defined yet.**" in rendered
        assert "⚠️ **No strategic pillars defined.**" in rendered
        assert "⚠️ **No product outcomes defined.**" in rendered
        assert "⚠️ **No roadmap themes defined.**" in rendered
        assert "⚠️ **No heroes defined.**" in rendered
        assert "⚠️ **No villains defined.**" in rendered

    def test_template_shows_partial_warnings(self):
        """Test that template shows partial warnings for incomplete data."""
        from jinja2 import Environment, FileSystemLoader

        templates_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)
        template = env.get_template("prompts/strategic_context_summary.jinja")

        vision = MagicMock()
        vision.vision_text = "Test vision"
        vision.created_at = datetime(2024, 1, 15)

        rendered = template.render(
            vision=vision,
            pillars=[
                {
                    "identifier": "P-001",
                    "name": "One Pillar",
                    "description": "Only one.",
                }
            ],
            outcomes=[
                {
                    "identifier": "O-001",
                    "name": "One Outcome",
                    "description": "Only one.",
                    "pillar_names": [],
                }
            ],
            themes=[
                {
                    "identifier": "T-001",
                    "name": "Theme",
                    "description": "A theme.",
                    "is_prioritized": False,
                    "priority_order": None,
                    "hero_name": None,
                    "primary_villain_name": None,
                    "outcome_names": [],
                }
            ],
            heroes=[
                {
                    "identifier": "H-001",
                    "name": "Hero",
                    "description": "A hero.",
                    "is_primary": True,
                }
            ],
            villains=[
                {
                    "identifier": "V-001",
                    "name": "Villain",
                    "description": "A villain.",
                    "villain_type": "OTHER",
                    "severity": 3,
                    "is_defeated": False,
                }
            ],
        )

        assert "# Strategic Context Summary" in rendered
        assert "Test vision" in rendered
        assert "P-001: One Pillar" in rendered
        assert "O-001: One Outcome" in rendered
        assert "T-001: Theme" in rendered
        assert "H-001: Hero" in rendered
        assert "V-001: Villain" in rendered
        assert "⚠️ **Only 1 pillar(s) defined.**" in rendered
        assert "⚠️ **Only 1 outcome(s) defined.**" in rendered


class TestStrategicContextIntegration:
    """Integration-style tests that build full strategic context in database.

    These tests create all strategic entities (vision, pillars, outcomes,
    themes, heroes, villains) in the actual database and verify the full
    rendering pipeline works end-to-end without mocking.
    """

    @pytest.fixture
    def publisher(self, session: Session) -> EventPublisher:
        """Create a real EventPublisher for testing."""
        return EventPublisher(session)

    @pytest.fixture
    def vision(
        self,
        workspace: Workspace,
        session: Session,
    ) -> ProductVision:
        """Create and update the product vision."""
        from src.strategic_planning import controller as strategic_controller

        vision = strategic_controller.upsert_workspace_vision(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            vision_text="Enable developers to manage their product backlog without leaving their IDE, making strategic planning seamless and AI-native.",
            session=session,
        )
        return vision

    @pytest.fixture
    def pillars(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ) -> List[StrategicPillar]:
        """Create multiple strategic pillars."""
        from src.strategic_planning import controller as strategic_controller

        pillar1 = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Deep IDE Integration",
            description="Strategy: Make the IDE the primary interface for product planning. Anti-strategy: No separate web dashboards for daily workflow.",
            session=session,
        )
        pillar2 = strategic_controller.create_strategic_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="AI-Native Intelligence",
            description="Strategy: AI assists at every decision point. Anti-strategy: No manual-only workflows that could be automated.",
            session=session,
        )
        return [pillar1, pillar2]

    @pytest.fixture
    def outcomes(
        self,
        workspace: Workspace,
        user: User,
        pillars: List[StrategicPillar],
        session: Session,
    ) -> List[ProductOutcome]:
        """Create product outcomes linked to pillars."""
        from src.strategic_planning import controller as strategic_controller

        outcome1 = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Developer Daily Adoption",
            description="Goal: 80% of active developers use the MCP tools daily. Baseline: 0%. Target: 80% by Q2.",
            pillar_ids=[pillars[0].id],
            session=session,
        )
        outcome2 = strategic_controller.create_product_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Strategic Alignment",
            description="Goal: All initiatives trace to roadmap themes. Baseline: 20% alignment. Target: 100%.",
            pillar_ids=[pillars[0].id, pillars[1].id],
            session=session,
        )
        return [outcome1, outcome2]

    @pytest.fixture
    def hero(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        publisher: EventPublisher,
    ) -> Hero:
        """Create a primary hero."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer building SaaS products. She juggles coding, product management, and customer support. Her biggest pain is context switching between tools.",
            is_primary=True,
            session=session,
            publisher=publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        publisher: EventPublisher,
    ) -> Villain:
        """Create an active villain."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between IDE, project management tools, and documentation breaks flow state and wastes 20% of productive time.",
            severity=5,
            session=session,
            publisher=publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def defeated_villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        publisher: EventPublisher,
    ) -> Villain:
        """Create a defeated villain."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Manual Task Tracking",
            villain_type=VillainType.WORKFLOW,
            description="Manually updating task status in multiple systems.",
            severity=3,
            session=session,
            publisher=publisher,
        )
        villain.mark_defeated(publisher)
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def themes(
        self,
        workspace: Workspace,
        user: User,
        outcomes: List[ProductOutcome],
        hero: Hero,
        villain: Villain,
        session: Session,
        publisher: EventPublisher,
    ) -> List[RoadmapTheme]:
        """Create roadmap themes with connections."""
        from src.roadmap_intelligence import controller as roadmap_controller

        theme1 = roadmap_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="MCP-First Development",
            description="Make the MCP server the primary interface for AI assistants to interact with the product backlog.",
            outcome_ids=[outcomes[0].id],
            session=session,
        )
        theme1.link_heroes([hero.id], session)
        theme1.link_villains([villain.id], session)
        session.commit()

        theme2 = roadmap_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Strategic Context Everywhere",
            description="Ensure strategic context is available in every workflow decision.",
            outcome_ids=[outcomes[1].id],
            session=session,
        )
        session.commit()

        roadmap_controller.prioritize_roadmap_theme(
            theme_id=theme1.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        session.refresh(theme1)
        session.refresh(theme2)
        return [theme1, theme2]

    @pytest.fixture
    def full_strategic_context(
        self,
        vision: ProductVision,
        pillars: List[StrategicPillar],
        outcomes: List[ProductOutcome],
        hero: Hero,
        villain: Villain,
        defeated_villain: Villain,
        themes: List[RoadmapTheme],
        session: Session,
    ) -> Dict[str, Any]:
        """Fixture that ensures all strategic context is created."""
        return {
            "vision": vision,
            "pillars": pillars,
            "outcomes": outcomes,
            "hero": hero,
            "villain": villain,
            "defeated_villain": defeated_villain,
            "themes": themes,
        }

    @pytest.fixture
    def mock_get_workspace_id(
        self, workspace: Workspace
    ) -> Generator[MagicMock, None, None]:
        """Mock get_workspace_id_from_request to return workspace ID."""
        with patch(
            "src.mcp_server.strategic_context_resource.get_workspace_id_from_request"
        ) as mock:
            mock.return_value = workspace.id
            yield mock

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_returns_complete_context(
        self,
        full_strategic_context: Dict[str, Any],
        mock_get_workspace_id: MagicMock,
    ) -> None:
        """Test that get_strategic_context_summary returns complete strategic context.

        This integration test:
        1. Creates all strategic entities in the actual database
        2. Calls the real get_strategic_context_summary function
        3. Verifies all content appears in the returned markdown
        """
        result = await get_strategic_context_summary.fn()

        assert isinstance(result, str)
        assert "# Strategic Context Summary" in result
        assert "Enable developers to manage their product backlog" in result
        assert "P-001: Deep IDE Integration" in result
        assert "P-002: AI-Native Intelligence" in result
        assert "O-001: Developer Daily Adoption" in result
        assert "O-002: Strategic Alignment" in result
        assert "Linked Pillars:" in result
        assert "T-001: MCP-First Development" in result
        assert "T-002: Strategic Context Everywhere" in result
        assert "H-001: Sarah, The Solo Builder" in result
        assert "👑 PRIMARY" in result
        assert "V-001: Context Switching" in result
        assert "V-002: Manual Task Tracking" in result
        assert "Defeated Villains" in result
        assert "~~V-002: Manual Task Tracking~~" in result

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_shows_prioritized_themes(
        self,
        full_strategic_context: Dict[str, Any],
        mock_get_workspace_id: MagicMock,
    ) -> None:
        """Test that get_strategic_context_summary shows priority indicators for themes."""
        result = await get_strategic_context_summary.fn()

        assert "Prioritized Themes (Active Focus)" in result
        assert "⭐ Priority #1" in result
        assert "Backlog Themes (Not Yet Prioritized)" in result

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_includes_pillar_linkages(
        self,
        full_strategic_context: Dict[str, Any],
        mock_get_workspace_id: MagicMock,
    ) -> None:
        """Test that outcomes display their linked pillar names."""
        result = await get_strategic_context_summary.fn()

        assert "**Linked Pillars:**" in result
        assert "Deep IDE Integration" in result
        assert "AI-Native Intelligence" in result

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_shows_villain_severity(
        self,
        full_strategic_context: Dict[str, Any],
        mock_get_workspace_id: MagicMock,
    ) -> None:
        """Test that villains display severity indicators."""
        result = await get_strategic_context_summary.fn()

        assert "V-001: Context Switching" in result
        assert "🔴🔴🔴🔴🔴" in result

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_with_empty_workspace(
        self,
        workspace: Workspace,
        mock_get_workspace_id: MagicMock,
    ) -> None:
        """Test that get_strategic_context_summary shows warnings for empty workspace."""
        result = await get_strategic_context_summary.fn()

        assert "# Strategic Context Summary" in result
        assert "⚠️ **No vision defined yet.**" in result
        assert "⚠️ **No strategic pillars defined.**" in result
        assert "⚠️ **No product outcomes defined.**" in result
        assert "⚠️ **No roadmap themes defined.**" in result
        assert "⚠️ **No heroes defined.**" in result
        assert "⚠️ **No villains defined.**" in result

    @pytest.mark.asyncio
    async def test_get_strategic_context_summary_handles_validation_error(
        self,
        workspace: Workspace,
    ) -> None:
        """Test that get_strategic_context_summary handles workspace not found."""
        with patch(
            "src.mcp_server.strategic_context_resource.get_workspace_id_from_request"
        ) as mock:
            mock.side_effect = ValueError("Workspace not found")
            result = await get_strategic_context_summary.fn()

        assert "Error:" in result
        assert "Workspace not found" in result
