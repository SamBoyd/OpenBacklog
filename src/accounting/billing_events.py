"""
Billing Event Domain Models for Event-Sourced Architecture.

This module defines immutable domain events that represent all billing state changes.
Events are the single source of truth for billing operations, replacing the dual
audit trail of BillingStateTransition and Ledger tables.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Type

from src.accounting.models import UserAccountStatus
from src.config import settings


@dataclass(frozen=True)
class BillingEvent(ABC):
    """
    Base class for all billing domain events.

    All events are immutable and contain complete information needed
    to apply the state change they represent.

    Attributes:
        event_id: Unique identifier for this event
        user_id: User this event applies to
        created_at: When this event occurred
    """

    event_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    @abstractmethod
    def event_type(self) -> str:
        """Return the string identifier for this event type."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize event to dictionary for database storage.

        Returns:
            Dictionary representation suitable for JSONB storage
        """
        result = {
            "event_id": str(self.event_id),
            "user_id": str(self.user_id),
            "created_at": self.created_at.isoformat(),
            "event_type": self.event_type(),
        }

        # Add subclass-specific fields
        for field_name, field_value in self.__dict__.items():
            if field_name not in ["event_id", "user_id", "created_at"]:
                if isinstance(field_value, uuid.UUID):
                    result[field_name] = str(field_value)
                elif isinstance(field_value, datetime):
                    result[field_name] = field_value.isoformat()
                elif hasattr(field_value, "value"):  # Handle enums
                    result[field_name] = field_value.value
                else:
                    result[field_name] = field_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BillingEvent":
        """
        Deserialize event from dictionary.

        Args:
            data: Dictionary representation from database

        Returns:
            Reconstructed event instance
        """
        # Convert string UUIDs back to UUID objects
        if "event_id" in data:
            data["event_id"] = uuid.UUID(data["event_id"])
        if "user_id" in data:
            data["user_id"] = uuid.UUID(data["user_id"])

        # Convert ISO datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        # Handle enum conversions for specific event types
        event_type = data.get("event_type")

        # Remove event_type from data as it's not a constructor parameter
        data_copy = data.copy()
        data_copy.pop("event_type", None)

        # Convert enum strings back to enums where needed
        if "from_state" in data_copy:
            data_copy["from_state"] = UserAccountStatus(data_copy["from_state"])
        if "to_state" in data_copy:
            data_copy["to_state"] = UserAccountStatus(data_copy["to_state"])

        return cls(**data_copy)


@dataclass(frozen=True)
class CreditUsageEvent(BillingEvent):
    """
    Event representing usage covered by monthly subscription credits.

    This event tracks usage that is deducted from the user's monthly
    included credits rather than their usage balance.

    Attributes:
        amount_cents: Amount of credits used (positive float)
        external_id: External reference for this usage (e.g., AI request ID)
    """

    amount_cents: float
    external_id: str

    def event_type(self) -> str:
        return "CREDIT_USAGE"


@dataclass(frozen=True)
class BalanceUsageEvent(BillingEvent):
    """
    Event representing usage deducted from the user's usage balance.

    This event tracks usage that exceeds monthly credits and is
    deducted from the user's top-up balance.

    Attributes:
        amount_cents: Amount deducted from balance (positive float)
        external_id: External reference for this usage (e.g., AI request ID)
    """

    amount_cents: float
    external_id: str

    def event_type(self) -> str:
        return "BALANCE_USAGE"


@dataclass(frozen=True)
class StateTransitionEvent(BillingEvent):
    """
    Event representing a billing state transition.

    This event captures when the user's billing state changes
    (e.g., NEW -> ACTIVE_SUBSCRIPTION, ACTIVE_SUBSCRIPTION -> SUSPENDED).

    Attributes:
        from_state: Previous billing state
        to_state: New billing state
        reason: Reason for the transition (e.g., "USAGE_RECORDED", "TOPUP_BALANCE")
    """

    from_state: UserAccountStatus
    to_state: UserAccountStatus
    reason: str

    def event_type(self) -> str:
        return "STATE_TRANSITION"


@dataclass(frozen=True)
class BalanceTopUpEvent(BillingEvent):
    """
    Event representing a top-up of the user's usage balance.

    This event tracks when funds are added to the user's usage balance,
    typically from Stripe payments.

    Attributes:
        amount_cents: Amount added to balance (positive float)
        external_id: External reference (e.g., Stripe session ID)
        invoice_url: Optional URL to download invoice/receipt
    """

    amount_cents: float
    external_id: str
    invoice_url: str | None = None

    def event_type(self) -> str:
        return "BALANCE_TOPUP"


@dataclass(frozen=True)
class MonthlyCreditsResetEvent(BillingEvent):
    """
    Event representing the monthly reset of included credits.

    This event occurs at the start of each billing cycle to reset
    the user's monthly credits usage back to zero.
    """

    def event_type(self) -> str:
        return "MONTHLY_CREDITS_RESET"


@dataclass(frozen=True)
class BalanceRefundEvent(BillingEvent):
    """
    Event representing a refund from the user's usage balance.

    This event tracks when funds are removed from the user's usage balance
    due to refunds or chargebacks.

    Attributes:
        ``amount_cents: Amount refunded (positive float, represents amount removed)
        external_id: External reference for the refund
        reason: Reason for the refund (e.g., "CUSTOMER_REQUEST", "CHARGEBACK")
    """

    amount_cents: float
    external_id: str
    reason: str

    def event_type(self) -> str:
        return "BALANCE_REFUND"


@dataclass(frozen=True)
class SubscriptionSignupEvent(BillingEvent):
    """
    Event representing a subscription signup.

    This event tracks when a user signs up for a monthly subscription,
    typically transitioning from NEW or NO_SUBSCRIPTION to ACTIVE_SUBSCRIPTION.

    Attributes:
        external_id: External reference (e.g., Stripe subscription ID)
        monthly_credits_cents: Monthly credits included with this subscription
    """

    external_id: str
    monthly_credits_cents: float = settings.monthly_subscription_cost_cents

    def event_type(self) -> str:
        return "SUBSCRIPTION_SIGNUP"


@dataclass(frozen=True)
class SubscriptionCancelEvent(BillingEvent):
    """
    Event representing a subscription cancellation.

    This event tracks when a user cancels their monthly subscription.

    Attributes:
        external_id: External reference (e.g., cancellation reason or Stripe ID)
        reason: Reason for cancellation
    """

    external_id: str
    reason: str = "USER_REQUESTED"

    def event_type(self) -> str:
        return "SUBSCRIPTION_CANCEL"


@dataclass(frozen=True)
class ChargebackDetectedEvent(BillingEvent):
    """
    Event representing chargeback/fraud detection.

    This event occurs when a chargeback is detected, typically resulting
    in account closure.

    Attributes:
        external_id: External reference (e.g., Stripe chargeback ID)
        amount_cents: Amount of the chargeback (positive float)
    """

    external_id: str
    amount_cents: float

    def event_type(self) -> str:
        return "CHARGEBACK_DETECTED"


# Registry for event type -> class mapping
EVENT_TYPE_REGISTRY: Dict[str, Type[BillingEvent]] = {
    "CREDIT_USAGE": CreditUsageEvent,
    "BALANCE_USAGE": BalanceUsageEvent,
    "STATE_TRANSITION": StateTransitionEvent,
    "BALANCE_TOPUP": BalanceTopUpEvent,
    "MONTHLY_CREDITS_RESET": MonthlyCreditsResetEvent,
    "BALANCE_REFUND": BalanceRefundEvent,
    "SUBSCRIPTION_SIGNUP": SubscriptionSignupEvent,
    "SUBSCRIPTION_CANCEL": SubscriptionCancelEvent,
    "CHARGEBACK_DETECTED": ChargebackDetectedEvent,
}


def deserialize_event(event_type: str, event_data: Dict[str, Any]) -> BillingEvent:
    """
    Deserialize a billing event from its type and data.

    Args:
        event_type: String identifier of the event type
        event_data: Dictionary containing event data

    Returns:
        Reconstructed event instance

    Raises:
        ValueError: If event_type is not recognized
    """
    if event_type not in EVENT_TYPE_REGISTRY:
        raise ValueError(f"Unknown event type: {event_type}")

    event_class = EVENT_TYPE_REGISTRY[event_type]
    return event_class.from_dict(event_data)


def serialize_event(event: BillingEvent) -> tuple[str, Dict[str, Any]]:
    """
    Serialize a billing event to its type and data components.

    Args:
        event: Event instance to serialize

    Returns:
        Tuple of (event_type, event_data)
    """
    return event.event_type(), event.to_dict()
