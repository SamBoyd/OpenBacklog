"""Unit tests for Hero aggregate.

Tests verify that Hero aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import Workspace
from src.narrative.aggregates.hero import Hero
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestHero:
    """Unit tests for Hero aggregate."""

    @pytest.fixture
    def workspace(self, user, session: Session):
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
    def hero(
        self, workspace: Workspace, user, session: Session, mock_publisher: MagicMock
    ):
        """Create a Hero instance for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer building a SaaS product.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    def test_define_hero_success(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_hero() creates hero successfully."""
        name = "Sarah, The Solo Builder"
        description = "Sarah is a solo developer building a SaaS product."

        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(hero)

        assert hero.id is not None
        assert hero.identifier is not None
        assert hero.identifier.startswith("H-")
        assert hero.name == name
        assert hero.description == description
        assert hero.is_primary is True
        assert hero.workspace_id == workspace.id

    def test_define_hero_name_too_short(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_hero() raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            Hero.define_hero(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                description="Some description",
                is_primary=False,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_hero_name_too_long(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_hero() raises exception for name > 100 chars."""
        long_name = "x" * 101

        with pytest.raises(DomainException) as exc_info:
            Hero.define_hero(
                workspace_id=workspace.id,
                user_id=user.id,
                name=long_name,
                description="Some description",
                is_primary=False,
                session=session,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_define_hero_description_too_long(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_hero() raises exception for description > 2000 chars."""
        long_description = "x" * 2001

        with pytest.raises(DomainException) as exc_info:
            Hero.define_hero(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description=long_description,
                is_primary=False,
                session=session,
                publisher=mock_publisher,
            )

        assert "2000 characters or less" in str(exc_info.value)
        assert "2001" in str(exc_info.value)

    def test_define_hero_emits_hero_defined_event(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_hero() emits HeroDefined event."""
        name = "Sarah, The Solo Builder"
        description = "Sarah is a solo developer building a SaaS product."
        is_primary = True

        mock_publisher.reset_mock()

        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            is_primary=is_primary,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(hero)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "HeroDefined"
        assert event.aggregate_id == hero.id
        assert event.payload["name"] == name
        assert event.payload["description"] == description
        assert event.payload["is_primary"] == is_primary
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_update_hero_validates_fields(
        self,
        hero: Hero,
        mock_publisher: MagicMock,
    ):
        """Test that update_hero() validates field lengths."""
        with pytest.raises(DomainException):
            hero.update_hero(
                name="x" * 101,
                description="Valid",
                is_primary=False,
                publisher=mock_publisher,
            )

    def test_update_hero_updates_fields_correctly(
        self,
        hero: Hero,
        mock_publisher: MagicMock,
    ):
        """Test that update_hero() updates fields correctly."""
        new_name = "Updated Hero Name"
        new_description = "Updated description"
        new_is_primary = False

        hero.update_hero(
            name=new_name,
            description=new_description,
            is_primary=new_is_primary,
            publisher=mock_publisher,
        )

        assert hero.name == new_name
        assert hero.description == new_description
        assert hero.is_primary == new_is_primary

    def test_update_hero_emits_hero_updated_event(
        self,
        hero: Hero,
        mock_publisher: MagicMock,
    ):
        """Test that update_hero() emits HeroUpdated event."""
        new_name = "Updated Hero Name"

        mock_publisher.reset_mock()

        hero.update_hero(
            name=new_name,
            description=None,
            is_primary=False,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "HeroUpdated"
        assert event.payload["name"] == new_name

    def test_get_journey_summary(
        self,
        hero: Hero,
    ):
        """Test that get_journey_summary() generates summary."""
        summary = hero.get_journey_summary()

        assert "Sarah, The Solo Builder" in summary
        assert "Description:" in summary
        assert "Active Story Arcs:" in summary
        assert "Open Conflicts:" in summary

    def test_unique_constraint_enforced_for_workspace_name(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that (workspace_id, name) unique constraint is enforced."""
        hero1 = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Description 1",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero1)

        hero2 = Hero(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier="H-0002",
            name="Sarah, The Solo Builder",
            description="Description 2",
            is_primary=False,
        )
        session.add(hero2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_unique_constraint_enforced_for_workspace_identifier(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that (workspace_id, identifier) unique constraint is enforced."""
        hero1 = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Hero 1",
            description="Description 1",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero1)

        hero2 = Hero(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier=hero1.identifier,
            name="Hero 2",
            description="Description 2",
            is_primary=False,
        )
        session.add(hero2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_hero_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that hero is stored correctly in database."""
        name = "Sarah, The Solo Builder"
        description = "Sarah is a solo developer building a SaaS product."
        is_primary = True

        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            is_primary=is_primary,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)

        saved_hero = session.query(Hero).filter(Hero.id == hero.id).first()

        assert saved_hero is not None
        assert saved_hero.name == name
        assert saved_hero.description == description
        assert saved_hero.is_primary == is_primary
        assert saved_hero.workspace_id == workspace.id
