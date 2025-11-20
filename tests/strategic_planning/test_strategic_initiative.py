"""Unit tests for StrategicInitiative aggregate.

Tests verify that StrategicInitiative aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.initiative_management.models import (
    StrategicInitiativeConflict,
    StrategicInitiativeHero,
    StrategicInitiativeVillain,
)
from src.models import Initiative, InitiativeStatus, User, Workspace
from src.narrative.aggregates.conflict import Conflict
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain, VillainType
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestStrategicInitiative:
    """Unit tests for StrategicInitiative aggregate."""

    @pytest.fixture
    def workspace(self, user: User, session: Session):
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
    def initiative(self, user: User, workspace: Workspace, session: Session):
        """Create an initiative for testing."""
        initiative = Initiative(
            id=uuid.uuid4(),
            title="Test Initiative",
            description="Test description",
            user_id=user.id,
            workspace_id=workspace.id,
            identifier="I-001",
            status=InitiativeStatus.BACKLOG,
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)
        return initiative

    @pytest.fixture
    def strategic_pillar(self, user: User, workspace: Workspace, session: Session):
        """Create a strategic pillar for testing."""
        pillar = StrategicPillar(
            id=uuid.uuid4(),
            user_id=user.id,
            workspace_id=workspace.id,
            name="Developer Experience",
            description="Make developers love our product",
            display_order=0,
        )
        session.add(pillar)
        session.commit()
        session.refresh(pillar)
        return pillar

    @pytest.fixture
    def roadmap_theme(self, user: User, workspace: Workspace, session: Session):
        """Create a roadmap theme for testing."""
        theme = RoadmapTheme(
            id=uuid.uuid4(),
            user_id=user.id,
            workspace_id=workspace.id,
            name="First Week Magic",
            description="Users fail to integrate in first week",
        )
        session.add(theme)
        session.commit()
        session.refresh(theme)
        return theme

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def hero(self, user: User, workspace: Workspace, session: Session):
        """Create a hero for testing."""
        hero = Hero(
            id=uuid.uuid4(),
            identifier="H-001",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Sarah, The Solo Developer",
            description="A solo developer who needs efficient tools",
            is_primary=True,
        )
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(self, user: User, workspace: Workspace, session: Session):
        """Create a villain for testing."""
        villain = Villain(
            id=uuid.uuid4(),
            identifier="V-001",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW.value,
            description="Jumping between tools breaks developer flow",
            severity=5,
        )
        session.add(villain)
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def conflict(
        self,
        user: User,
        workspace: Workspace,
        hero: Hero,
        villain: Villain,
        session: Session,
    ):
        """Create a conflict for testing."""
        conflict = Conflict(
            id=uuid.uuid4(),
            identifier="C-001",
            user_id=user.id,
            workspace_id=workspace.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah cannot access context without leaving IDE",
            status="OPEN",
        )
        session.add(conflict)
        session.commit()
        session.refresh(conflict)
        return conflict

    def test_define_strategic_context_validates_user_need_length(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() raises exception for user_need > 1000 chars."""
        long_user_need = "x" * 4001

        with pytest.raises(DomainException) as exc_info:
            StrategicInitiative.define_strategic_context(
                session=session,
                publisher=mock_publisher,
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,  # type: ignore
                pillar_id=None,
                theme_id=None,
                description=long_user_need,
                narrative_intent=None,
            )

        assert "4000 characters or less" in str(exc_info.value)
        assert "User need" in str(exc_info.value)
        assert "4001" in str(exc_info.value)

    def test_define_strategic_context_validates_connection_to_vision_length(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() raises exception for connection_to_vision > 1000 chars."""
        long_narrative_intent = "x" * 1001

        with pytest.raises(DomainException) as exc_info:
            StrategicInitiative.define_strategic_context(
                initiative_id=initiative.id,
                workspace_id=workspace.id,
                user_id=user.id,
                pillar_id=None,
                theme_id=None,
                description=None,
                narrative_intent=long_narrative_intent,
                session=session,
                publisher=mock_publisher,
            )

        assert "1000 characters or less" in str(exc_info.value)
        assert "Narrative intent" in str(exc_info.value)
        assert "1001" in str(exc_info.value)

    def test_define_strategic_context_accepts_valid_input(
        self,
        initiative: Initiative,
        workspace: Workspace,
        strategic_pillar: StrategicPillar,
        roadmap_theme: RoadmapTheme,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() accepts valid input."""
        description = "Users need to track their work efficiently"
        narrative_intent = "Enables productive solo development"

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=strategic_pillar.id,
            theme_id=roadmap_theme.id,
            description=description,
            narrative_intent=narrative_intent,
            session=session,
            publisher=mock_publisher,
        )

        assert strategic_init.initiative_id == initiative.id
        assert strategic_init.workspace_id == workspace.id
        assert strategic_init.pillar_id == strategic_pillar.id
        assert strategic_init.theme_id == roadmap_theme.id
        assert strategic_init.description == description
        assert strategic_init.narrative_intent == narrative_intent

    def test_define_strategic_context_accepts_none_for_optional_fields(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() accepts None for optional fields."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description=None,
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        assert strategic_init.pillar_id is None
        assert strategic_init.theme_id is None
        assert strategic_init.description is None
        assert strategic_init.narrative_intent is None

    def test_define_strategic_context_emits_strategic_context_completed_event(
        self,
        initiative: Initiative,
        workspace: Workspace,
        strategic_pillar: StrategicPillar,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() emits StrategicContextCompleted event."""
        description = "Users need to track their work"
        narrative_intent = "Enables productive development"

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=strategic_pillar.id,
            theme_id=None,
            description=description,
            narrative_intent=narrative_intent,
            session=session,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "StrategicContextCompleted"
        assert event.aggregate_id == strategic_init.id
        assert event.payload["workspace_id"] == str(workspace.id)
        assert event.payload["initiative_id"] == str(initiative.id)
        assert event.payload["pillar_id"] == str(strategic_pillar.id)
        assert event.payload["theme_id"] is None
        assert event.payload["description"] == description
        assert workspace_id_arg == str(workspace.id)

    def test_update_strategic_context_validates_fields(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that update_strategic_context() validates field lengths."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Valid",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Test description validation
        with pytest.raises(DomainException):
            strategic_init.update_strategic_context(
                publisher=mock_publisher,
                pillar_id=None,
                theme_id=None,
                description="x" * 4001,
                narrative_intent=None,
            )

        # Test narrative_intent validation
        with pytest.raises(DomainException):
            strategic_init.update_strategic_context(
                publisher=mock_publisher,
                pillar_id=None,
                theme_id=None,
                description="Valid",
                narrative_intent="x" * 1001,
            )

    def test_update_strategic_context_updates_fields_correctly(
        self,
        initiative: Initiative,
        workspace: Workspace,
        strategic_pillar: StrategicPillar,
        roadmap_theme: RoadmapTheme,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that update_strategic_context() updates fields correctly."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Original need",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        new_description = "Updated user need"
        new_narrative_intent = "Updated connection to vision"

        strategic_init.update_strategic_context(
            publisher=mock_publisher,
            pillar_id=strategic_pillar.id,
            theme_id=roadmap_theme.id,
            description=new_description,
            narrative_intent=new_narrative_intent,
        )

        assert strategic_init.pillar_id == strategic_pillar.id
        assert strategic_init.theme_id == roadmap_theme.id
        assert strategic_init.description == new_description
        assert strategic_init.narrative_intent == new_narrative_intent

    def test_update_strategic_context_emits_strategic_context_updated_event(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that update_strategic_context() emits StrategicContextUpdated event."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Original",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        new_description = "Updated user need"

        strategic_init.update_strategic_context(
            publisher=mock_publisher,
            pillar_id=None,
            theme_id=None,
            description=new_description,
            narrative_intent=None,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "StrategicContextUpdated"
        assert event.aggregate_id == strategic_init.id
        assert event.payload["description"] == new_description

    def test_unique_constraint_enforced_for_initiative_id(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
    ):
        """Test that unique constraint on initiative_id is enforced."""
        strategic_init1 = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description=None,
            narrative_intent=None,
        )
        session.add(strategic_init1)
        session.commit()

        strategic_init2 = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description=None,
            narrative_intent=None,
        )
        session.add(strategic_init2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_strategic_context_stores_correctly_in_database(
        self,
        initiative: Initiative,
        workspace: Workspace,
        strategic_pillar: StrategicPillar,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that strategic context is stored correctly in database."""
        description = "Users need to track their work"
        narrative_intent = "Enables productive solo development"

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=strategic_pillar.id,
            theme_id=None,
            description=description,
            narrative_intent=narrative_intent,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        saved_strategic_init = (
            session.query(StrategicInitiative)
            .filter(StrategicInitiative.id == strategic_init.id)
            .first()
        )

        assert saved_strategic_init is not None
        assert saved_strategic_init.initiative_id == initiative.id
        assert saved_strategic_init.workspace_id == workspace.id
        assert saved_strategic_init.pillar_id == strategic_pillar.id
        assert saved_strategic_init.description == description
        assert saved_strategic_init.narrative_intent == narrative_intent

    def test_cascade_delete_when_initiative_deleted(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that strategic context is deleted when initiative is deleted."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        strategic_init_id = strategic_init.id

        # Delete the initiative
        session.delete(initiative)
        session.commit()

        # Verify strategic context was also deleted
        saved_strategic_init = (
            session.query(StrategicInitiative)
            .filter(StrategicInitiative.id == strategic_init_id)
            .first()
        )

        assert saved_strategic_init is None

    def test_set_null_when_pillar_deleted(
        self,
        initiative: Initiative,
        workspace: Workspace,
        strategic_pillar: StrategicPillar,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that pillar_id is set to NULL when pillar is deleted."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=strategic_pillar.id,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        strategic_init_id = strategic_init.id

        # Delete the pillar
        session.delete(strategic_pillar)
        session.commit()

        # Verify strategic context still exists but pillar_id is NULL
        saved_strategic_init = (
            session.query(StrategicInitiative)
            .filter(StrategicInitiative.id == strategic_init_id)
            .first()
        )

        assert saved_strategic_init is not None
        assert saved_strategic_init.pillar_id is None

    def test_set_null_when_theme_deleted(
        self,
        initiative: Initiative,
        workspace: Workspace,
        roadmap_theme: RoadmapTheme,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that theme_id is set to NULL when theme is deleted."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=roadmap_theme.id,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        strategic_init_id = strategic_init.id

        # Delete the theme
        session.delete(roadmap_theme)
        session.commit()

        # Verify strategic context still exists but theme_id is NULL
        saved_strategic_init = (
            session.query(StrategicInitiative)
            .filter(StrategicInitiative.id == strategic_init_id)
            .first()
        )

        assert saved_strategic_init is not None
        assert saved_strategic_init.theme_id is None

    def test_link_heroes_creates_junction_table_entries(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_heroes() creates entries in junction table."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        strategic_init.link_heroes([hero.id], session)
        session.commit()

        links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )

        assert len(links) == 1
        assert links[0].hero_id == hero.id
        assert links[0].strategic_initiative_id == strategic_init.id

    def test_link_heroes_replaces_existing_links(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_heroes() replaces existing hero links."""
        hero1 = Hero(
            id=uuid.uuid4(),
            identifier="H-002",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Hero 1",
            description="First hero",
            is_primary=False,
        )
        hero2 = Hero(
            id=uuid.uuid4(),
            identifier="H-003",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Hero 2",
            description="Second hero",
            is_primary=False,
        )
        session.add(hero1)
        session.add(hero2)
        session.commit()

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Link first hero
        strategic_init.link_heroes([hero1.id], session)
        session.commit()

        # Verify first hero is linked
        links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].hero_id == hero1.id

        # Replace with second hero
        strategic_init.link_heroes([hero2.id], session)
        session.commit()

        # Verify only second hero is linked
        links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].hero_id == hero2.id

    def test_link_heroes_raises_exception_if_hero_does_not_exist(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_heroes() raises exception if hero doesn't exist."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        non_existent_hero_id = uuid.uuid4()

        with pytest.raises(DomainException) as exc_info:
            strategic_init.link_heroes([non_existent_hero_id], session)

        assert f"Hero with id {non_existent_hero_id} does not exist" in str(
            exc_info.value
        )

    def test_link_heroes_updates_updated_at(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_heroes() updates the updated_at timestamp."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        original_updated_at = strategic_init.updated_at

        # Wait a small amount to ensure timestamp difference
        import time

        time.sleep(0.01)

        strategic_init.link_heroes([hero.id], session)
        session.commit()
        session.refresh(strategic_init)

        assert strategic_init.updated_at > original_updated_at

    def test_link_villains_creates_junction_table_entries(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_villains() creates entries in junction table."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        strategic_init.link_villains([villain.id], session)
        session.commit()

        links = (
            session.query(StrategicInitiativeVillain)
            .filter(
                StrategicInitiativeVillain.strategic_initiative_id == strategic_init.id
            )
            .all()
        )

        assert len(links) == 1
        assert links[0].villain_id == villain.id
        assert links[0].strategic_initiative_id == strategic_init.id

    def test_link_villains_replaces_existing_links(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_villains() replaces existing villain links."""
        villain1 = Villain(
            id=uuid.uuid4(),
            identifier="V-002",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Villain 1",
            villain_type=VillainType.TECHNICAL.value,
            description="First villain",
            severity=3,
        )
        villain2 = Villain(
            id=uuid.uuid4(),
            identifier="V-003",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Villain 2",
            villain_type=VillainType.WORKFLOW.value,
            description="Second villain",
            severity=4,
        )
        session.add(villain1)
        session.add(villain2)
        session.commit()

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Link first villain
        strategic_init.link_villains([villain1.id], session)
        session.commit()

        # Verify first villain is linked
        links = (
            session.query(StrategicInitiativeVillain)
            .filter(
                StrategicInitiativeVillain.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].villain_id == villain1.id

        # Replace with second villain
        strategic_init.link_villains([villain2.id], session)
        session.commit()

        # Verify only second villain is linked
        links = (
            session.query(StrategicInitiativeVillain)
            .filter(
                StrategicInitiativeVillain.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].villain_id == villain2.id

    def test_link_villains_raises_exception_if_villain_does_not_exist(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_villains() raises exception if villain doesn't exist."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        non_existent_villain_id = uuid.uuid4()

        with pytest.raises(DomainException) as exc_info:
            strategic_init.link_villains([non_existent_villain_id], session)

        assert f"Villain with id {non_existent_villain_id} does not exist" in str(
            exc_info.value
        )

    def test_link_conflicts_creates_junction_table_entries(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        conflict: Conflict,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_conflicts() creates entries in junction table."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        strategic_init.link_conflicts([conflict.id], session)
        session.commit()

        links = (
            session.query(StrategicInitiativeConflict)
            .filter(
                StrategicInitiativeConflict.strategic_initiative_id == strategic_init.id
            )
            .all()
        )

        assert len(links) == 1
        assert links[0].conflict_id == conflict.id
        assert links[0].strategic_initiative_id == strategic_init.id

    def test_link_conflicts_replaces_existing_links(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_conflicts() replaces existing conflict links."""
        conflict1 = Conflict(
            id=uuid.uuid4(),
            identifier="C-002",
            user_id=user.id,
            workspace_id=workspace.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="First conflict",
            status="OPEN",
        )
        conflict2 = Conflict(
            id=uuid.uuid4(),
            identifier="C-003",
            user_id=user.id,
            workspace_id=workspace.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Second conflict",
            status="OPEN",
        )
        session.add(conflict1)
        session.add(conflict2)
        session.commit()

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Link first conflict
        strategic_init.link_conflicts([conflict1.id], session)
        session.commit()

        # Verify first conflict is linked
        links = (
            session.query(StrategicInitiativeConflict)
            .filter(
                StrategicInitiativeConflict.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].conflict_id == conflict1.id

        # Replace with second conflict
        strategic_init.link_conflicts([conflict2.id], session)
        session.commit()

        # Verify only second conflict is linked
        links = (
            session.query(StrategicInitiativeConflict)
            .filter(
                StrategicInitiativeConflict.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(links) == 1
        assert links[0].conflict_id == conflict2.id

    def test_link_conflicts_raises_exception_if_conflict_does_not_exist(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_conflicts() raises exception if conflict doesn't exist."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        non_existent_conflict_id = uuid.uuid4()

        with pytest.raises(DomainException) as exc_info:
            strategic_init.link_conflicts([non_existent_conflict_id], session)

        assert f"Conflict with id {non_existent_conflict_id} does not exist" in str(
            exc_info.value
        )

    def test_define_strategic_context_with_narrative_entities(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        conflict: Conflict,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_strategic_context() links heroes, villains, and conflicts."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent="Test narrative intent",
            hero_ids=[hero.id],
            villain_ids=[villain.id],
            conflict_ids=[conflict.id],
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        # Verify hero link
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(hero_links) == 1
        assert hero_links[0].hero_id == hero.id

        # Verify villain link
        villain_links = (
            session.query(StrategicInitiativeVillain)
            .filter(
                StrategicInitiativeVillain.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(villain_links) == 1
        assert villain_links[0].villain_id == villain.id

        # Verify conflict link
        conflict_links = (
            session.query(StrategicInitiativeConflict)
            .filter(
                StrategicInitiativeConflict.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(conflict_links) == 1
        assert conflict_links[0].conflict_id == conflict.id

    def test_update_strategic_context_with_narrative_entities(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that update_strategic_context() updates narrative entity links."""
        hero1 = Hero(
            id=uuid.uuid4(),
            identifier="H-004",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Hero 1",
            description="First hero",
            is_primary=False,
        )
        hero2 = Hero(
            id=uuid.uuid4(),
            identifier="H-005",
            user_id=user.id,
            workspace_id=workspace.id,
            name="Hero 2",
            description="Second hero",
            is_primary=False,
        )
        session.add(hero1)
        session.add(hero2)
        session.commit()

        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent="Test narrative intent",
            hero_ids=[hero1.id],
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        # Verify initial hero link
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(hero_links) == 1
        assert hero_links[0].hero_id == hero1.id

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        # Update with different hero
        strategic_init.update_strategic_context(
            publisher=mock_publisher,
            pillar_id=None,
            theme_id=None,
            description="Updated description",
            narrative_intent="Updated narrative intent",
            hero_ids=[hero2.id],
            session=session,
        )
        session.commit()

        # Verify hero link was replaced
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(hero_links) == 1
        assert hero_links[0].hero_id == hero2.id

    def test_update_strategic_context_can_clear_narrative_links(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that update_strategic_context() can clear narrative entity links."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent="Test narrative intent",
            hero_ids=[hero.id],
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        # Verify initial hero link exists
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(hero_links) == 1

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        # Update with empty hero list to clear links
        strategic_init.update_strategic_context(
            publisher=mock_publisher,
            pillar_id=None,
            theme_id=None,
            description="Updated description",
            narrative_intent="Updated narrative intent",
            hero_ids=[],
            session=session,
        )
        session.commit()

        # Verify hero links were cleared
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init.id
            )
            .all()
        )
        assert len(hero_links) == 0

    def test_cascade_delete_removes_narrative_links_when_strategic_initiative_deleted(
        self,
        initiative: Initiative,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        conflict: Conflict,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that deleting strategic initiative cascades to narrative junction tables."""
        strategic_init = StrategicInitiative.define_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
            description="Test description",
            narrative_intent="Test narrative intent",
            hero_ids=[hero.id],
            villain_ids=[villain.id],
            conflict_ids=[conflict.id],
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        strategic_init_id = strategic_init.id

        # Verify links exist
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init_id
            )
            .all()
        )
        assert len(hero_links) == 1

        # Delete the strategic initiative by deleting the parent initiative
        session.delete(initiative)
        session.commit()

        # Verify all links were deleted via cascade
        hero_links = (
            session.query(StrategicInitiativeHero)
            .filter(
                StrategicInitiativeHero.strategic_initiative_id == strategic_init_id
            )
            .all()
        )
        assert len(hero_links) == 0

        villain_links = (
            session.query(StrategicInitiativeVillain)
            .filter(
                StrategicInitiativeVillain.strategic_initiative_id == strategic_init_id
            )
            .all()
        )
        assert len(villain_links) == 0

        conflict_links = (
            session.query(StrategicInitiativeConflict)
            .filter(
                StrategicInitiativeConflict.strategic_initiative_id == strategic_init_id
            )
            .all()
        )
        assert len(conflict_links) == 0
