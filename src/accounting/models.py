import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.models import Base, PrivateBase, User


class UserAccountStatus(str, enum.Enum):
    NEW = "NEW"
    ACTIVE_SUBSCRIPTION = "ACTIVE_SUBSCRIPTION"
    NO_SUBSCRIPTION = "NO_SUBSCRIPTION"
    METERED_BILLING = "METERED_BILLING"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class PendingTopupStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class UserAccountDetails(PrivateBase, Base):
    __tablename__ = "user_account_details"
    __table_args__ = ({"schema": "private"},)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"),
        nullable=False,
        primary_key=True,
    )
    user: Mapped["User"] = relationship("User", back_populates="account_details")

    balance_cents: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus), nullable=False, default=UserAccountStatus.NEW
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_usage_query_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Onboarding tracking
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Subscription cancellation tracking
    subscription_cancel_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    subscription_canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    subscription_cancel_at_period_end: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )

    # Monthly credits tracking
    monthly_credits_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    monthly_credits_used: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    next_billing_cycle_starts: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


class PendingTopup(PrivateBase, Base):
    __tablename__ = "pending_topups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped["User"] = relationship("User")

    session_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[PendingTopupStatus] = mapped_column(
        Enum(PendingTopupStatus), nullable=False, default=PendingTopupStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=text("now()")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BillingStateTransitionEvent(str, enum.Enum):
    SIGNUP_SUBSCRIPTION = "SIGNUP_SUBSCRIPTION"
    CANCEL_SUBSCRIPTION = "CANCEL_SUBSCRIPTION"
    REACTIVATE_SUBSCRIPTION = "REACTIVATE_SUBSCRIPTION"
    START_BILLING_CYCLE = "START_BILLING_CYCLE"
    TOPUP_BALANCE = "TOPUP_BALANCE"
    USAGE_RECORDED = "USAGE_RECORDED"
    REFUND_BALANCE = "REFUND_BALANCE"
    CHARGEBACK_DETECTED = "CHARGEBACK_DETECTED"


class BillingStateTransition(PrivateBase, Base):
    __tablename__ = "billing_state_transitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")

    from_state: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus), nullable=True
    )
    to_state: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus), nullable=False
    )
    event: Mapped[BillingStateTransitionEvent] = mapped_column(
        Enum(BillingStateTransitionEvent), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=text("now()")
    )


class BillingEventRecord(PrivateBase, Base):
    """
    Event store record for billing events in event-sourced architecture.

    This table provides append-only storage for billing events with
    optimistic concurrency control via version numbers.
    """

    __tablename__ = "billing_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("now()"),
        index=True,
    )

    __table_args__ = (
        # Ensure unique versions per user (optimistic concurrency control)
        UniqueConstraint("user_id", "version", name="uq_billing_events_user_version"),
        {"schema": "private"},
    )
