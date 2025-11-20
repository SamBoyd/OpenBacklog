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
from src.models import Initiative, InitiativeStatus, User, Workspace
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
        description = "Users need to track their work efficiently. Enables productive solo development. Success: 80% adoption within 30 days. Out of scope: Team collaboration features"
        narrative_intent = "We want to help developers be more productive"

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
        description = "Users need to track their work. Enables productive development"
        narrative_intent = "We want to help developers be more productive"

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
            description="Original description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        new_description = "Updated description"
        new_narrative_intent = "Updated narrative intent"

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
            description="Original description",
            narrative_intent=None,
            session=session,
            publisher=mock_publisher,
        )

        # Reset mock to clear the creation event
        mock_publisher.reset_mock()

        new_description = "Updated description"

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
        )
        session.add(strategic_init1)
        session.commit()

        strategic_init2 = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=workspace.id,
            user_id=user.id,
            pillar_id=None,
            theme_id=None,
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
        description = "Users need to track their work. Enables productive solo development. Success: 80% adoption within 30 days. Out of scope: Team collaboration features"
        narrative_intent = "We want to help developers be more productive"

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
