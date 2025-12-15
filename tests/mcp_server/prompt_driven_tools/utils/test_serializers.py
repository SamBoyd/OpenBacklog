"""Tests for MCP serializer functions.

Tests the serialization behavior with include_connections=True (full objects)
and include_connections=False (identifiers only).

Uses user and workspace fixtures from root conftest.py.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.utils.serializers import (
    serialize_conflict,
    serialize_hero,
    serialize_initiative_summary,
    serialize_outcome,
    serialize_pillar,
    serialize_theme,
    serialize_villain,
)
from src.models import User, Workspace
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar


class TestSerializeHero:
    """Tests for serialize_hero()."""

    @pytest.fixture
    def hero(self, workspace: Workspace, user: User, session: Session) -> Hero:
        """Create a test hero."""
        hero = Hero(
            id=uuid.uuid4(),
            identifier="H-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Developer",
            description="A solo developer building products",
            is_primary=True,
        )
        session.add(hero)
        session.commit()
        return hero

    def test_serialize_hero_includes_core_fields(self, hero: Hero):
        """Test that hero serialization includes all core fields."""
        result = serialize_hero(hero)

        assert result["identifier"] == "H-001"
        assert result["name"] == "Sarah, The Developer"
        assert result["description"] == "A solo developer building products"
        assert result["is_primary"] is True
        assert "created_at" in result
        assert "updated_at" in result

    def test_serialize_hero_excludes_uuid_fields(self, hero: Hero):
        """Test that hero serialization excludes UUID fields."""
        result = serialize_hero(hero)

        assert "id" not in result
        assert "workspace_id" not in result

    def test_serialize_hero_include_connections_parameter_accepted(self, hero: Hero):
        """Test that include_connections parameter is accepted."""
        result_true = serialize_hero(hero, include_connections=True)
        result_false = serialize_hero(hero, include_connections=False)

        assert result_true["identifier"] == result_false["identifier"]


class TestSerializeVillain:
    """Tests for serialize_villain()."""

    @pytest.fixture
    def villain(self, workspace: Workspace, user: User, session: Session) -> Villain:
        """Create a test villain."""
        villain = Villain(
            id=uuid.uuid4(),
            identifier="V-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            description="The productivity killer",
            villain_type="INTERNAL",
            severity=2,
            is_defeated=False,
        )
        session.add(villain)
        session.commit()
        return villain

    def test_serialize_villain_includes_core_fields(self, villain: Villain):
        """Test that villain serialization includes all core fields."""
        result = serialize_villain(villain)

        assert result["identifier"] == "V-001"
        assert result["name"] == "Context Switching"
        assert result["description"] == "The productivity killer"
        assert result["villain_type"] == "INTERNAL"
        assert result["severity"] == 2
        assert result["is_defeated"] is False

    def test_serialize_villain_excludes_uuid_fields(self, villain: Villain):
        """Test that villain serialization excludes UUID fields."""
        result = serialize_villain(villain)

        assert "id" not in result
        assert "workspace_id" not in result


class TestSerializeConflict:
    """Tests for serialize_conflict()."""

    @pytest.fixture
    def hero(self, workspace: Workspace, user: User, session: Session) -> Hero:
        """Create a test hero."""
        hero = Hero(
            id=uuid.uuid4(),
            identifier="H-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah",
            description="Developer",
            is_primary=True,
        )
        session.add(hero)
        session.commit()
        return hero

    @pytest.fixture
    def villain(self, workspace: Workspace, user: User, session: Session) -> Villain:
        """Create a test villain."""
        villain = Villain(
            id=uuid.uuid4(),
            identifier="V-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            description="Productivity killer",
            villain_type="INTERNAL",
            severity=2,
            is_defeated=False,
        )
        session.add(villain)
        session.commit()
        return villain

    @pytest.fixture
    def conflict(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
    ) -> Conflict:
        """Create a test conflict."""
        conflict = Conflict(
            id=uuid.uuid4(),
            identifier="C-001",
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah battles context switching",
            status=ConflictStatus.OPEN.value,
        )
        session.add(conflict)
        session.commit()
        session.refresh(conflict)
        return conflict

    def test_serialize_conflict_with_connections_includes_full_objects(
        self, conflict: Conflict
    ):
        """Test that include_connections=True returns full hero/villain objects."""
        result = serialize_conflict(conflict, include_connections=True)

        assert result["identifier"] == "C-001"
        assert result["description"] == "Sarah battles context switching"
        assert result["status"] == "OPEN"
        assert isinstance(result["hero"], dict)
        assert result["hero"]["name"] == "Sarah"
        assert result["hero"]["identifier"] == "H-001"
        assert isinstance(result["villain"], dict)
        assert result["villain"]["name"] == "Context Switching"
        assert result["villain"]["identifier"] == "V-001"

    def test_serialize_conflict_without_connections_returns_identifiers(
        self, conflict: Conflict
    ):
        """Test that include_connections=False returns identifiers only."""
        result = serialize_conflict(conflict, include_connections=False)

        assert result["identifier"] == "C-001"
        assert result["hero_identifier"] == "H-001"
        assert result["villain_identifier"] == "V-001"
        assert "hero" not in result
        assert "villain" not in result


class TestSerializePillar:
    """Tests for serialize_pillar()."""

    @pytest.fixture
    def outcome(self, workspace: Workspace, user: User, session: Session):
        """Create a test outcome."""
        outcome = ProductOutcome(
            id=uuid.uuid4(),
            identifier="O-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Increased Productivity",
            description="Users are more productive",
            display_order=0,
        )
        session.add(outcome)
        session.commit()
        return outcome

    @pytest.fixture
    def pillar(
        self,
        workspace: Workspace,
        user: User,
        outcome: ProductOutcome,
        session: Session,
    ) -> StrategicPillar:
        """Create a test pillar with linked outcome."""
        pillar = StrategicPillar(
            id=uuid.uuid4(),
            identifier="P-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Deep Work",
            description="Enable focused work",
            display_order=0,
        )

        session.add(pillar)
        session.commit()
        session.refresh(pillar)

        outcome.link_to_pillars([pillar.id], user.id, session, MagicMock())
        session.commit()

        return pillar

    def test_serialize_pillar_with_connections_includes_full_outcomes(
        self, pillar: StrategicPillar
    ):
        """Test that include_connections=True returns full outcome objects."""
        result = serialize_pillar(pillar, include_connections=True)

        assert result["identifier"] == "P-001"
        assert result["name"] == "Deep Work"
        assert "outcomes" in result
        assert len(result["outcomes"]) == 1
        assert result["outcomes"][0]["identifier"] == "O-001"
        assert result["outcomes"][0]["name"] == "Increased Productivity"

    def test_serialize_pillar_without_connections_returns_identifiers(
        self, pillar: StrategicPillar
    ):
        """Test that include_connections=False returns outcome identifiers only."""
        result = serialize_pillar(pillar, include_connections=False)

        assert result["identifier"] == "P-001"
        assert "outcome_identifiers" in result
        assert result["outcome_identifiers"] == ["O-001"]
        assert "outcomes" not in result


class TestSerializeOutcome:
    """Tests for serialize_outcome()."""

    @pytest.fixture
    def pillar(self, workspace: Workspace, user: User, session: Session):
        """Create a test pillar."""
        pillar = StrategicPillar(
            id=uuid.uuid4(),
            identifier="P-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Deep Work",
            description="Enable focused work",
            display_order=0,
        )
        session.add(pillar)
        session.commit()
        return pillar

    @pytest.fixture
    def outcome(
        self, workspace: Workspace, user: User, pillar, session: Session
    ) -> ProductOutcome:
        """Create a test outcome with linked pillar."""
        outcome = ProductOutcome(
            id=uuid.uuid4(),
            identifier="O-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Increased Productivity",
            description="Users are more productive",
            display_order=0,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)

        outcome.link_to_pillars([pillar.id], user.id, session, MagicMock())
        session.commit()
        session.refresh(outcome)

        return outcome

    def test_serialize_outcome_with_connections_includes_full_pillars(
        self, outcome: ProductOutcome
    ):
        """Test that include_connections=True returns full pillar objects."""
        result = serialize_outcome(outcome, include_connections=True)

        assert result["identifier"] == "O-001"
        assert result["name"] == "Increased Productivity"
        assert "pillars" in result
        assert len(result["pillars"]) == 1
        assert result["pillars"][0]["identifier"] == "P-001"
        assert result["pillars"][0]["name"] == "Deep Work"

    def test_serialize_outcome_without_connections_returns_identifiers(
        self, outcome: ProductOutcome
    ):
        """Test that include_connections=False returns pillar identifiers only."""
        result = serialize_outcome(outcome, include_connections=False)

        assert result["identifier"] == "O-001"
        assert "pillar_identifiers" in result
        assert result["pillar_identifiers"] == ["P-001"]
        assert "pillars" not in result


class TestSerializeTheme:
    """Tests for serialize_theme()."""

    @pytest.fixture
    def hero(self, workspace: Workspace, user: User, session: Session) -> Hero:
        """Create a test hero."""
        hero = Hero(
            id=uuid.uuid4(),
            identifier="H-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah",
            description="Developer",
            is_primary=True,
        )
        session.add(hero)
        session.commit()
        return hero

    @pytest.fixture
    def villain(self, workspace: Workspace, user: User, session: Session) -> Villain:
        """Create a test villain."""
        villain = Villain(
            id=uuid.uuid4(),
            identifier="V-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            description="Productivity killer",
            villain_type="INTERNAL",
            severity=2,
            is_defeated=False,
        )
        session.add(villain)
        session.commit()
        return villain

    @pytest.fixture
    def theme(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
    ) -> RoadmapTheme:
        """Create a test theme with linked hero and villain."""
        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Focus Mode",
            description="Enable deep work",
        )
        theme.link_heroes([hero.id], session)
        theme.link_villains([villain.id], session)
        session.add(theme)
        session.commit()
        session.refresh(theme)
        return theme

    def test_serialize_theme_with_connections_includes_full_objects(
        self, theme: RoadmapTheme
    ):
        """Test that include_connections=True returns full nested objects."""
        result = serialize_theme(theme, include_connections=True)

        assert result["identifier"] == "T-001"
        assert result["name"] == "Focus Mode"
        assert "heroes" in result
        assert len(result["heroes"]) == 1
        assert result["heroes"][0]["name"] == "Sarah"
        assert "villains" in result
        assert len(result["villains"]) == 1
        assert result["villains"][0]["name"] == "Context Switching"

    def test_serialize_theme_without_connections_returns_identifiers(
        self, theme: RoadmapTheme
    ):
        """Test that include_connections=False returns identifiers only."""
        result = serialize_theme(theme, include_connections=False)

        assert result["identifier"] == "T-001"
        assert "hero_identifiers" in result
        assert result["hero_identifiers"] == ["H-001"]
        assert "villain_identifiers" in result
        assert result["villain_identifiers"] == ["V-001"]
        assert "heroes" not in result
        assert "villains" not in result


class TestSerializeInitiativeSummary:
    """Tests for serialize_initiative_summary()."""

    def test_serialize_initiative_summary_returns_minimal_fields(self):
        """Test that initiative summary returns only identifier, title, status."""
        from unittest.mock import MagicMock

        mock_initiative = MagicMock()
        mock_initiative.identifier = "I-1001"
        mock_initiative.title = "Test Initiative"
        mock_initiative.status.value = "IN_PROGRESS"

        result = serialize_initiative_summary(mock_initiative)

        assert result == {
            "identifier": "I-1001",
            "title": "Test Initiative",
            "status": "IN_PROGRESS",
        }
