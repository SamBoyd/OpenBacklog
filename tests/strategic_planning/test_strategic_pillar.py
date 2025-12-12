"""Unit tests for StrategicPillar aggregate.

Tests verify that StrategicPillar aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestStrategicPillar:
    """Unit tests for StrategicPillar aggregate."""

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
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def strategic_pillar(self, workspace: Workspace):
        """Create a StrategicPillar instance for testing."""
        return StrategicPillar(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            name="Developer Experience",
            description="Make developers love our product",
            display_order=0,
        )

    def test_validate_pillar_limit_raises_exception_when_5_pillars_exist(
        self,
        workspace: Workspace,
        session: Session,
    ):
        """Test that validate_pillar_limit() raises exception when 5 pillars exist."""
        for i in range(5):
            pillar = StrategicPillar(
                identifier=f"P-00{i+1}",
                user_id=uuid.uuid4(),
                workspace_id=workspace.id,
                name=f"Pillar {i}",
                display_order=i,
            )
            session.add(pillar)
        session.commit()

        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.validate_pillar_limit(workspace.id, session)

        assert "maximum of 5 strategic pillars" in str(exc_info.value)

    def test_validate_pillar_limit_passes_when_less_than_5_pillars(
        self,
        workspace: Workspace,
        session: Session,
    ):
        """Test that validate_pillar_limit() passes when < 5 pillars exist."""
        for i in range(4):
            pillar = StrategicPillar(
                identifier=f"P-00{i+1}",
                user_id=uuid.uuid4(),
                workspace_id=workspace.id,
                name=f"Pillar {i}",
                display_order=i,
            )
            session.add(pillar)
        session.commit()

        StrategicPillar.validate_pillar_limit(workspace.id, session)

    def test_define_pillar_validates_name_minimum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.define_pillar(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                description="Some description",
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_pillar_validates_name_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() raises exception for name > 100 chars."""
        long_name = "x" * 101

        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.define_pillar(
                workspace_id=workspace.id,
                user_id=user.id,
                name=long_name,
                description="Some description",
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_define_pillar_validates_description_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() raises exception for description > 3000 chars."""
        long_description = "x" * 3001

        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.define_pillar(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description=long_description,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "3000 characters or less" in str(exc_info.value)
        assert "Description" in str(exc_info.value)

    def test_define_pillar_validates_display_order_range(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() raises exception for display_order outside 0-4."""
        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.define_pillar(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="Valid description",
                display_order=5,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 0-4" in str(exc_info.value)

        with pytest.raises(DomainException) as exc_info:
            StrategicPillar.define_pillar(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="Valid description",
                display_order=-1,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 0-4" in str(exc_info.value)

    def test_define_pillar_accepts_valid_input(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() accepts valid input."""
        name = "Developer Experience"
        description = "Make developers love our product"
        display_order = 2

        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        assert pillar.name == name
        assert pillar.description == description
        assert pillar.display_order == display_order

    def test_define_pillar_accepts_none_for_optional_fields(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() accepts None for optional fields."""
        name = "Developer Experience"

        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=None,
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )

        assert pillar.name == name
        assert pillar.description is None

    def test_define_pillar_emits_strategic_pillar_defined_event(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_pillar() emits StrategicPillarDefined event."""
        name = "Developer Experience"
        description = "Make developers love our product"
        display_order = 1

        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "StrategicPillarDefined"
        assert event.aggregate_id == pillar.id
        assert event.payload["name"] == name
        assert event.payload["description"] == description
        assert event.payload["display_order"] == display_order
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_update_pillar_validates_fields(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that update_pillar() validates field lengths."""
        with pytest.raises(DomainException):
            strategic_pillar.update_pillar(
                name="x" * 101,
                description="Valid",
                publisher=mock_publisher,
            )

    def test_update_pillar_updates_fields_correctly(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that update_pillar() updates fields correctly."""
        new_name = "Updated Name"
        new_description = "Updated description"

        strategic_pillar.update_pillar(
            name=new_name,
            description=new_description,
            publisher=mock_publisher,
        )

        assert strategic_pillar.name == new_name
        assert strategic_pillar.description == new_description

    def test_update_pillar_emits_strategic_pillar_updated_event(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that update_pillar() emits StrategicPillarUpdated event."""
        new_name = "Updated Name"

        strategic_pillar.update_pillar(
            name=new_name,
            description=None,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "StrategicPillarUpdated"
        assert event.payload["name"] == new_name

    def test_reorder_pillar_validates_display_order(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_pillar() validates display order."""
        with pytest.raises(DomainException) as exc_info:
            strategic_pillar.reorder_pillar(5, mock_publisher)

        assert "between 0-4" in str(exc_info.value)

    def test_reorder_pillar_updates_display_order(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_pillar() updates display_order correctly."""
        old_order = strategic_pillar.display_order
        new_order = 3

        strategic_pillar.reorder_pillar(new_order, mock_publisher)

        assert strategic_pillar.display_order == new_order
        assert strategic_pillar.display_order != old_order

    def test_reorder_pillar_emits_strategic_pillars_reordered_event(
        self,
        strategic_pillar: StrategicPillar,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_pillar() emits StrategicPillarsReordered event."""
        old_order = strategic_pillar.display_order
        new_order = 2

        strategic_pillar.reorder_pillar(new_order, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "StrategicPillarsReordered"
        assert event.payload["old_order"] == old_order
        assert event.payload["new_order"] == new_order
        assert event.payload["pillar_id"] == str(strategic_pillar.id)

    def test_unique_constraint_enforced_for_workspace_name(
        self,
        workspace: Workspace,
        session: Session,
    ):
        """Test that (workspace_id, name) unique constraint is enforced."""
        pillar1 = StrategicPillar(
            identifier=f"P-001",
            user_id=uuid.uuid4(),
            workspace_id=workspace.id,
            name="Developer Experience",
            display_order=0,
        )
        session.add(pillar1)
        session.commit()

        pillar2 = StrategicPillar(
            identifier="P-002",
            user_id=uuid.uuid4(),
            workspace_id=workspace.id,
            name="Developer Experience",
            display_order=1,
        )
        session.add(pillar2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_pillar_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that pillar is stored correctly in database."""
        name = "Developer Experience"
        description = "Make developers love our product"
        display_order = 1

        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        saved_pillar = (
            session.query(StrategicPillar)
            .filter(StrategicPillar.id == pillar.id)
            .first()
        )

        assert saved_pillar is not None
        assert saved_pillar.name == name
        assert saved_pillar.description == description
        assert saved_pillar.display_order == display_order
        assert saved_pillar.workspace_id == workspace.id

    def test_identifier_auto_generated_on_create(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that identifier is auto-generated in P-001 format on create."""
        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Pillar",
            description="Test description",
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(pillar)

        assert_that(pillar.identifier, equal_to("P-001"))

    def test_identifier_increments_sequentially(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that identifiers increment sequentially for same user."""
        pillar1 = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Pillar One",
            description=None,
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(pillar1)

        pillar2 = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Pillar Two",
            description=None,
            display_order=1,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(pillar2)

        assert_that(pillar1.identifier, equal_to("P-001"))
        assert_that(pillar2.identifier, equal_to("P-002"))
