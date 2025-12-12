"""Unit tests for Villain aggregate.

Tests verify that Villain aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestVillain:
    """Unit tests for Villain aggregate."""

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
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Create a Villain instance for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow state.",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    def test_define_villain_success(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() creates villain successfully."""
        name = "Context Switching"
        villain_type = VillainType.WORKFLOW
        description = "Jumping between tools breaks flow state."
        severity = 5

        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            villain_type=villain_type,
            description=description,
            severity=severity,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(villain)

        assert villain.id is not None
        assert villain.identifier is not None
        assert villain.identifier.startswith("V-")
        assert villain.name == name
        assert villain.villain_type == villain_type.value
        assert villain.description == description
        assert villain.severity == severity
        assert villain.is_defeated is False
        assert villain.workspace_id == workspace.id

    def test_define_villain_name_validation_empty(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                villain_type=VillainType.WORKFLOW,
                description="Some description",
                severity=3,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_villain_name_validation_too_long(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for name > 100 chars."""
        long_name = "x" * 101

        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name=long_name,
                villain_type=VillainType.WORKFLOW,
                description="Some description",
                severity=3,
                session=session,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_define_villain_description_validation_empty(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for empty description."""
        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                villain_type=VillainType.WORKFLOW,
                description="",
                severity=3,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_villain_description_validation_too_long(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for description > 2000 chars."""
        long_description = "x" * 2001

        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                villain_type=VillainType.WORKFLOW,
                description=long_description,
                severity=3,
                session=session,
                publisher=mock_publisher,
            )

        assert "2000 characters or less" in str(exc_info.value)
        assert "2001" in str(exc_info.value)

    def test_define_villain_severity_validation_low(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for severity < 1."""
        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                villain_type=VillainType.WORKFLOW,
                description="Valid description",
                severity=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 1-5" in str(exc_info.value)

    def test_define_villain_severity_validation_high(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() raises exception for severity > 5."""
        with pytest.raises(DomainException) as exc_info:
            Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                villain_type=VillainType.WORKFLOW,
                description="Valid description",
                severity=6,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 1-5" in str(exc_info.value)

    def test_define_villain_emits_villain_identified_event(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_villain() emits VillainIdentified event."""
        name = "Context Switching"
        villain_type = VillainType.WORKFLOW
        description = "Jumping between tools breaks flow state."
        severity = 5

        mock_publisher.reset_mock()

        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            villain_type=villain_type,
            description=description,
            severity=severity,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(villain)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "VillainIdentified"
        assert event.aggregate_id == villain.id
        assert event.payload["name"] == name
        assert event.payload["villain_type"] == villain_type.value
        assert event.payload["description"] == description
        assert event.payload["severity"] == severity
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_mark_defeated_sets_flag(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that mark_defeated() sets is_defeated flag."""
        assert villain.is_defeated is False

        villain.mark_defeated(mock_publisher)

        assert villain.is_defeated is True

    def test_mark_defeated_emits_villain_defeated_event(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that mark_defeated() emits VillainDefeated event."""
        mock_publisher.reset_mock()

        villain.mark_defeated(mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "VillainDefeated"
        assert event.aggregate_id == villain.id
        assert event.payload["workspace_id"] == str(villain.workspace_id)
        assert event.payload["villain_id"] == str(villain.id)
        assert workspace_id_arg == str(villain.workspace_id)

    def test_unique_constraint_enforced_for_workspace_name(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that (workspace_id, name) unique constraint is enforced."""
        villain1 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Description 1",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain1)

        villain2 = Villain(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier="V-0002",
            name="Context Switching",
            villain_type=VillainType.WORKFLOW.value,
            description="Description 2",
            severity=3,
        )
        session.add(villain2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_unique_constraint_enforced_for_workspace_identifier(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that (workspace_id, identifier) unique constraint is enforced."""
        villain1 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Villain 1",
            villain_type=VillainType.WORKFLOW,
            description="Description 1",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain1)

        villain2 = Villain(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier=villain1.identifier,
            name="Villain 2",
            villain_type=VillainType.WORKFLOW.value,
            description="Description 2",
            severity=3,
        )
        session.add(villain2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_villain_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that villain is stored correctly in database."""
        name = "Context Switching"
        villain_type = VillainType.WORKFLOW
        description = "Jumping between tools breaks flow state."
        severity = 5

        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            villain_type=villain_type,
            description=description,
            severity=severity,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)

        saved_villain = session.query(Villain).filter(Villain.id == villain.id).first()

        assert saved_villain is not None
        assert saved_villain.name == name
        assert saved_villain.villain_type == villain_type.value
        assert saved_villain.description == description
        assert saved_villain.severity == severity
        assert saved_villain.workspace_id == workspace.id

    def test_update_villain_name_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating villain's name successfully."""
        new_name = "Context Switching (Critical)"

        villain.update_villain(
            name=new_name,
            villain_type=VillainType.WORKFLOW,
            description=villain.description,
            severity=villain.severity,
            is_defeated=villain.is_defeated,
            publisher=mock_publisher,
        )

        assert villain.name == new_name

    def test_update_villain_type_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating villain's type successfully."""
        new_type = VillainType.TECHNICAL

        villain.update_villain(
            name=villain.name,
            villain_type=new_type,
            description=villain.description,
            severity=villain.severity,
            is_defeated=villain.is_defeated,
            publisher=mock_publisher,
        )

        assert villain.villain_type == new_type.value

    def test_update_villain_description_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating villain's description successfully."""
        new_description = "Updated description of the problem"

        villain.update_villain(
            name=villain.name,
            villain_type=VillainType.WORKFLOW,
            description=new_description,
            severity=villain.severity,
            is_defeated=villain.is_defeated,
            publisher=mock_publisher,
        )

        assert villain.description == new_description

    def test_update_villain_severity_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating villain's severity successfully."""
        new_severity = 3

        villain.update_villain(
            name=villain.name,
            villain_type=VillainType.WORKFLOW,
            description=villain.description,
            severity=new_severity,
            is_defeated=villain.is_defeated,
            publisher=mock_publisher,
        )

        assert villain.severity == new_severity

    def test_update_villain_defeated_status_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating villain's defeated status."""
        assert villain.is_defeated is False

        villain.update_villain(
            name=villain.name,
            villain_type=VillainType.WORKFLOW,
            description=villain.description,
            severity=villain.severity,
            is_defeated=True,
            publisher=mock_publisher,
        )

        assert villain.is_defeated is True

    def test_update_villain_all_fields_success(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test updating all villain fields at once."""
        new_name = "Technical Debt"
        new_type = VillainType.TECHNICAL
        new_description = "Legacy code slows development"
        new_severity = 4

        villain.update_villain(
            name=new_name,
            villain_type=new_type,
            description=new_description,
            severity=new_severity,
            is_defeated=True,
            publisher=mock_publisher,
        )

        assert villain.name == new_name
        assert villain.villain_type == new_type.value
        assert villain.description == new_description
        assert villain.severity == new_severity
        assert villain.is_defeated is True

    def test_update_villain_updates_timestamp(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain updates the updated_at timestamp."""
        original_updated_at = villain.updated_at

        villain.update_villain(
            name="New Name",
            villain_type=VillainType.WORKFLOW,
            description=villain.description,
            severity=villain.severity,
            is_defeated=villain.is_defeated,
            publisher=mock_publisher,
        )

        assert villain.updated_at > original_updated_at

    def test_update_villain_name_validation_empty(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name="",
                villain_type=VillainType.WORKFLOW,
                description=villain.description,
                severity=villain.severity,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_update_villain_name_validation_too_long(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for name > 100 chars."""
        long_name = "x" * 101

        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name=long_name,
                villain_type=VillainType.WORKFLOW,
                description=villain.description,
                severity=villain.severity,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_update_villain_description_validation_empty(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for empty description."""
        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name=villain.name,
                villain_type=VillainType.WORKFLOW,
                description="",
                severity=villain.severity,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_update_villain_description_validation_too_long(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for description > 2000 chars."""
        long_description = "x" * 2001

        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name=villain.name,
                villain_type=VillainType.WORKFLOW,
                description=long_description,
                severity=villain.severity,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "2000 characters or less" in str(exc_info.value)
        assert "2001" in str(exc_info.value)

    def test_update_villain_severity_validation_low(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for severity < 1."""
        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name=villain.name,
                villain_type=VillainType.WORKFLOW,
                description=villain.description,
                severity=0,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "between 1-5" in str(exc_info.value)

    def test_update_villain_severity_validation_high(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain raises exception for severity > 5."""
        with pytest.raises(DomainException) as exc_info:
            villain.update_villain(
                name=villain.name,
                villain_type=VillainType.WORKFLOW,
                description=villain.description,
                severity=6,
                is_defeated=villain.is_defeated,
                publisher=mock_publisher,
            )

        assert "between 1-5" in str(exc_info.value)

    def test_update_villain_emits_villain_updated_event(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
    ):
        """Test that update_villain emits VillainUpdated event."""
        new_name = "Updated Name"
        new_type = VillainType.EXTERNAL
        new_description = "Updated description"
        new_severity = 2

        mock_publisher.reset_mock()

        villain.update_villain(
            name=new_name,
            villain_type=new_type,
            description=new_description,
            severity=new_severity,
            is_defeated=True,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "VillainUpdated"
        assert event.aggregate_id == villain.id
        assert event.payload["name"] == new_name
        assert event.payload["villain_type"] == new_type.value
        assert event.payload["description"] == new_description
        assert event.payload["severity"] == new_severity
        assert event.payload["is_defeated"] is True
        assert event.payload["workspace_id"] == str(villain.workspace_id)
        assert workspace_id_arg == str(villain.workspace_id)

    def test_update_villain_persists_changes_to_database(
        self,
        villain: Villain,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that update_villain persists changes to database."""
        new_name = "Persisted Name"
        new_description = "Persisted description"
        new_severity = 2
        new_type = VillainType.EXTERNAL

        villain.update_villain(
            name=new_name,
            villain_type=new_type,
            description=new_description,
            severity=new_severity,
            is_defeated=False,
            publisher=mock_publisher,
        )
        session.commit()

        refreshed_villain: Villain = (
            session.query(Villain).filter(Villain.id == villain.id).first()
        )

        assert refreshed_villain is not None
        assert refreshed_villain.name == new_name
        assert refreshed_villain.villain_type == new_type.value
        assert refreshed_villain.description == new_description
        assert refreshed_villain.severity == new_severity
        assert refreshed_villain.is_defeated is False

    def test_identifier_increments_sequentially(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that identifiers increment sequentially for same user."""
        villain1 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Villain One",
            villain_type=VillainType.WORKFLOW,
            description="First villain",
            severity=3,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain1)

        villain2 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Villain Two",
            villain_type=VillainType.TECHNICAL,
            description="Second villain",
            severity=4,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain2)

        assert_that(villain1.identifier, equal_to("V-001"))
        assert_that(villain2.identifier, equal_to("V-002"))
