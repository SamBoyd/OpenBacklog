"""Unit tests for ProductOutcome aggregate.

Tests verify that ProductOutcome aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestProductOutcome:
    """Unit tests for ProductOutcome aggregate."""

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
    def product_outcome(self, workspace: Workspace, user: User):
        """Create a ProductOutcome instance for testing."""
        return ProductOutcome(
            id=uuid.uuid4(),
            user_id=user.id,
            workspace_id=workspace.id,
            name="80% weekly AI usage",
            description="Measure AI adoption as a leading indicator",
            metrics="% of weekly active users who use AI features",
            time_horizon_months=12,
            display_order=0,
        )

    def test_validate_outcome_limit_raises_exception_when_10_outcomes_exist(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ):
        """Test that validate_outcome_limit() raises exception when 10 outcomes exist."""
        for i in range(10):
            outcome = ProductOutcome(
                user_id=user.id,
                workspace_id=workspace.id,
                name=f"Outcome {i}",
                display_order=i,
            )
            session.add(outcome)
        session.commit()

        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.validate_outcome_limit(workspace.id, session)

        assert "maximum of 10 product outcomes" in str(exc_info.value)

    def test_validate_outcome_limit_passes_when_less_than_10_outcomes(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ):
        """Test that validate_outcome_limit() passes when < 10 outcomes exist."""
        for i in range(9):
            outcome = ProductOutcome(
                user_id=user.id,
                workspace_id=workspace.id,
                name=f"Outcome {i}",
                display_order=i,
            )
            session.add(outcome)
        session.commit()

        ProductOutcome.validate_outcome_limit(workspace.id, session)

    def test_map_outcome_validates_name_minimum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                description="Some description",
                metrics=None,
                time_horizon_months=12,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_map_outcome_validates_name_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for name > 150 chars."""
        long_name = "x" * 151

        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name=long_name,
                description="Some description",
                metrics=None,
                time_horizon_months=12,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "150 characters or less" in str(exc_info.value)
        assert "151" in str(exc_info.value)

    def test_map_outcome_validates_description_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for description > 1500 chars."""
        long_description = "x" * 1501

        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description=long_description,
                metrics=None,
                time_horizon_months=12,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "1500 characters or less" in str(exc_info.value)
        assert "Description" in str(exc_info.value)

    def test_map_outcome_validates_metrics_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for metrics > 1000 chars."""
        long_metrics = "x" * 1001

        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="Valid description",
                metrics=long_metrics,
                time_horizon_months=12,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "1000 characters or less" in str(exc_info.value)
        assert "Metrics" in str(exc_info.value)

    def test_map_outcome_validates_time_horizon_minimum(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for time_horizon < 6."""
        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="Valid description",
                metrics=None,
                time_horizon_months=5,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 6-36 months" in str(exc_info.value)
        assert "5" in str(exc_info.value)

    def test_map_outcome_validates_time_horizon_maximum(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() raises exception for time_horizon > 36."""
        with pytest.raises(DomainException) as exc_info:
            ProductOutcome.map_outcome(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="Valid description",
                metrics=None,
                time_horizon_months=37,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 6-36 months" in str(exc_info.value)
        assert "37" in str(exc_info.value)

    def test_map_outcome_accepts_valid_input(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() accepts valid input."""
        name = "80% weekly AI usage"
        description = "Measure AI adoption as a leading indicator"
        metrics = "% of weekly active users who use AI features"
        time_horizon_months = 12
        display_order = 2

        outcome = ProductOutcome.map_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        assert outcome.name == name
        assert outcome.description == description
        assert outcome.metrics == metrics
        assert outcome.time_horizon_months == time_horizon_months
        assert outcome.display_order == display_order

    def test_map_outcome_accepts_none_for_optional_fields(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() accepts None for optional fields."""
        name = "80% weekly AI usage"

        outcome = ProductOutcome.map_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=None,
            metrics=None,
            time_horizon_months=None,
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )

        assert outcome.name == name
        assert outcome.description is None
        assert outcome.metrics is None
        assert outcome.time_horizon_months is None

    def test_map_outcome_emits_outcome_mapped_event(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that map_outcome() emits OutcomeMapped event."""
        name = "80% weekly AI usage"
        description = "Measure AI adoption as a leading indicator"
        metrics = "% of weekly active users who use AI features"
        time_horizon_months = 12
        display_order = 1

        outcome = ProductOutcome.map_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "OutcomeMapped"
        assert event.aggregate_id == outcome.id
        assert event.payload["name"] == name
        assert event.payload["description"] == description
        assert event.payload["metrics"] == metrics
        assert event.payload["time_horizon_months"] == time_horizon_months
        assert event.payload["display_order"] == display_order
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_update_outcome_validates_fields(
        self,
        product_outcome: ProductOutcome,
        mock_publisher: MagicMock,
    ):
        """Test that update_outcome() validates field lengths."""
        with pytest.raises(DomainException):
            product_outcome.update_outcome(
                name="x" * 151,
                description="Valid",
                metrics=None,
                time_horizon_months=12,
                publisher=mock_publisher,
            )

    def test_update_outcome_updates_fields_correctly(
        self,
        product_outcome: ProductOutcome,
        mock_publisher: MagicMock,
    ):
        """Test that update_outcome() updates fields correctly."""
        new_name = "Updated Name"
        new_description = "Updated description"
        new_metrics = "Updated metrics"
        new_time_horizon = 24

        product_outcome.update_outcome(
            name=new_name,
            description=new_description,
            metrics=new_metrics,
            time_horizon_months=new_time_horizon,
            publisher=mock_publisher,
        )

        assert product_outcome.name == new_name
        assert product_outcome.description == new_description
        assert product_outcome.metrics == new_metrics
        assert product_outcome.time_horizon_months == new_time_horizon

    def test_update_outcome_emits_outcome_updated_event(
        self,
        product_outcome: ProductOutcome,
        mock_publisher: MagicMock,
    ):
        """Test that update_outcome() emits OutcomeUpdated event."""
        new_name = "Updated Name"

        product_outcome.update_outcome(
            name=new_name,
            description=None,
            metrics=None,
            time_horizon_months=None,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "OutcomeUpdated"
        assert event.payload["name"] == new_name

    def test_reorder_outcome_updates_display_order(
        self,
        product_outcome: ProductOutcome,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_outcome() updates display_order correctly."""
        old_order = product_outcome.display_order
        new_order = 5

        product_outcome.reorder_outcome(new_order, mock_publisher)

        assert product_outcome.display_order == new_order
        assert product_outcome.display_order != old_order

    def test_reorder_outcome_emits_outcome_reordered_event(
        self,
        product_outcome: ProductOutcome,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_outcome() emits OutcomeReordered event."""
        new_order = 3

        product_outcome.reorder_outcome(new_order, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "OutcomeReordered"
        assert event.payload["display_order"] == new_order
        assert event.payload["outcome_id"] == str(product_outcome.id)
        assert event.payload["workspace_id"] == str(product_outcome.workspace_id)
        assert workspace_id_arg == str(product_outcome.workspace_id)

    def test_link_to_pillars_creates_pillar_links(
        self,
        product_outcome: ProductOutcome,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_pillars() creates pillar linkages."""
        # Create some pillars
        pillar1 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 1",
            display_order=0,
        )
        pillar2 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 2",
            display_order=1,
        )
        session.add(pillar1)
        session.add(pillar2)
        session.add(product_outcome)
        session.commit()

        product_outcome.link_to_pillars(
            [pillar1.id, pillar2.id],
            user.id,
            session,
            mock_publisher,
        )
        session.commit()

        # Refresh to get updated relationships
        session.refresh(product_outcome)

        assert len(product_outcome.pillars) == 2
        pillar_ids = {p.id for p in product_outcome.pillars}
        assert pillar1.id in pillar_ids
        assert pillar2.id in pillar_ids

    def test_link_to_pillars_replaces_existing_links(
        self,
        product_outcome: ProductOutcome,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_pillars() replaces existing pillar linkages."""
        # Create pillars
        pillar1 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 1",
            display_order=0,
        )
        pillar2 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 2",
            display_order=1,
        )
        session.add(pillar1)
        session.add(pillar2)
        session.add(product_outcome)
        session.commit()

        # Link to pillar1
        product_outcome.link_to_pillars([pillar1.id], user.id, session, mock_publisher)
        session.commit()
        session.refresh(product_outcome)
        assert len(product_outcome.pillars) == 1

        # Replace with pillar2
        product_outcome.link_to_pillars([pillar2.id], user.id, session, mock_publisher)
        session.commit()
        session.refresh(product_outcome)

        assert len(product_outcome.pillars) == 1
        assert product_outcome.pillars[0].id == pillar2.id

    def test_link_to_pillars_emits_outcome_pillars_linked_event(
        self,
        product_outcome: ProductOutcome,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_pillars() emits OutcomePillarsLinked event."""
        pillar1 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 1",
            display_order=0,
        )
        session.add(pillar1)
        session.add(product_outcome)
        session.commit()

        product_outcome.link_to_pillars([pillar1.id], user.id, session, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "OutcomePillarsLinked"
        assert event.payload["outcome_id"] == str(product_outcome.id)
        assert str(pillar1.id) in event.payload["pillar_ids"]

    def test_unique_constraint_enforced_for_workspace_name(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ):
        """Test that (workspace_id, name) unique constraint is enforced."""
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="80% weekly AI usage",
            display_order=0,
        )
        session.add(outcome1)
        session.commit()

        outcome2 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="80% weekly AI usage",
            display_order=1,
        )
        session.add(outcome2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_outcome_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that outcome is stored correctly in database."""
        name = "80% weekly AI usage"
        description = "Measure AI adoption as a leading indicator"
        metrics = "% of weekly active users who use AI features"
        time_horizon_months = 12
        display_order = 1

        outcome = ProductOutcome.map_outcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        saved_outcome = (
            session.query(ProductOutcome)
            .filter(ProductOutcome.id == outcome.id)
            .first()
        )

        assert saved_outcome is not None
        assert saved_outcome.name == name
        assert saved_outcome.description == description
        assert saved_outcome.metrics == metrics
        assert saved_outcome.time_horizon_months == time_horizon_months
        assert saved_outcome.display_order == display_order
        assert saved_outcome.workspace_id == workspace.id
