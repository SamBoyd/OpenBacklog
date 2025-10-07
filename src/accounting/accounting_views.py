import logging
import math
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.accounting import accounting_controller
from src.accounting.accounting_controller import SubscriptionCancellationResult
from src.accounting.billing_events import deserialize_event
from src.accounting.models import (
    BillingEventRecord,
    PendingTopup,
    PendingTopupStatus,
    UserAccountDetails,
    UserAccountStatus,
)
from src.accounting.openmeter_service import OpenMeterService, OpenMeterTokenResponse
from src.accounting.stripe_service import StripeService
from src.config import settings
from src.db import get_db
from src.main import app
from src.models import User
from src.views import dependency_to_override

logger = logging.getLogger(__name__)


class OnboardResponse(BaseModel):
    """Response model for billing onboarding."""

    customer_id: str = Field(alias="customerId", description="OpenMeter customer ID")
    stripe_customer_id: str = Field(
        alias="stripeCustomerId", description="Stripe customer ID"
    )
    session_id: str = Field(alias="sessionId", description="Stripe session ID")
    setup_intent_id: str = Field(
        alias="setupIntentId", description="Stripe setup intent ID"
    )
    url: str = Field(description="Stripe checkout URL")
    mode: str = Field(description="Checkout session mode")
    cancel_url: Optional[str] = Field(
        alias="cancelURL", default=None, description="Cancel URL"
    )
    success_url: Optional[str] = Field(
        alias="successURL", default=None, description="Success URL"
    )
    return_url: Optional[str] = Field(
        alias="returnURL", default=None, description="Return URL"
    )


def get_openmeter_service() -> OpenMeterService:
    """
    Dependency to get OpenMeter service instance.

    Returns:
        OpenMeterService: Configured OpenMeter service instance
    """
    return OpenMeterService(
        base_url=settings.openmeter_base_url, api_token=settings.openmeter_api_token
    )


class TransactionResponse(BaseModel):
    """Response model for user transactions."""

    id: str = Field(description="Transaction ID")
    user_id: str = Field(alias="userId", description="User ID")
    amount_cents: float = Field(alias="amountCents", description="Amount in cents")
    source: str = Field(description="Transaction source")
    external_id: Optional[str] = Field(
        alias="externalId", default=None, description="External reference ID"
    )
    created_at: str = Field(
        alias="createdAt", description="Transaction creation timestamp"
    )
    download_url: Optional[str] = Field(
        alias="downloadUrl", default=None, description="Download URL"
    )


class TransactionsListResponse(BaseModel):
    """Response model for list of user transactions."""

    transactions: List[TransactionResponse] = Field(
        description="List of user transactions"
    )
    total_count: int = Field(
        description="Total number of transactions available",
    )
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Number of transactions per page")
    has_next: bool = Field(description="Whether there are more pages available")


def convert_event_record_to_transaction(
    record: BillingEventRecord,
) -> Optional[TransactionResponse]:
    """
    Convert a BillingEventRecord to a TransactionResponse.

    Args:
        record: The billing event record to convert

    Returns:
        TransactionResponse if conversion successful, None if event should be skipped
    """
    try:
        # Deserialize the event to get typed access to event data
        event = deserialize_event(record.event_type, record.event_data)

        # Extract amount_cents from event data (not all events have this)
        amount_cents = 0.0
        if hasattr(event, "amount_cents"):
            amount_cents = event.amount_cents  # type: ignore
        elif hasattr(event, "monthly_credits_cents"):  # For subscription events
            amount_cents = event.monthly_credits_cents  # type: ignore

        # Extract external_id from event data (if present)
        external_id = None
        if hasattr(event, "external_id"):
            external_id = event.external_id  # type: ignore

        # Extract download URL (for topup events with invoices)
        download_url = None
        if hasattr(event, "invoice_url") and event.invoice_url:  # type: ignore
            download_url = event.invoice_url  # type: ignore

        return TransactionResponse(
            id=str(record.id),
            userId=str(record.user_id),
            amountCents=amount_cents,
            source=record.event_type,
            externalId=external_id,
            createdAt=record.created_at.isoformat(),
            downloadUrl=download_url,
        )

    except Exception as e:
        logger.error(f"Failed to convert event record {record.id} to transaction: {e}")
        return None


@app.get("/api/accounting/transactions", response_model=TransactionsListResponse)
async def get_user_transactions(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Number of transactions per page"
    ),
) -> TransactionsListResponse:
    """
    Get the current user's transaction history from the billing events with pagination.

    Args:
        user: Current authenticated user
        db: Database session
        page: Page number (1-based)
        page_size: Number of transactions per page

    Returns:
        TransactionsListResponse containing the user's transaction history with pagination

    Raises:
        HTTPException: If the database query fails
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * page_size

        # Get total count of billing events for this user
        total_count = (
            db.query(BillingEventRecord)
            .filter(BillingEventRecord.user_id == user.id)
            .filter(BillingEventRecord.event_type != "STATE_TRANSITION")
            .count()
        )

        # Query billing event records for the current user, ordered by creation date (newest first)
        # with pagination
        event_records = (
            db.query(BillingEventRecord)
            .filter(BillingEventRecord.user_id == user.id)
            .filter(BillingEventRecord.event_type != "MONTHLY_CREDITS_RESET")
            .filter(BillingEventRecord.event_type != "STATE_TRANSITION")
            .order_by(desc(BillingEventRecord.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Convert event records to transaction responses
        transactions = []
        for record in event_records:
            transaction = convert_event_record_to_transaction(record)
            if transaction:  # Skip corrupted events
                transactions.append(transaction)

        # Calculate if there are more pages
        has_next = offset + len(transactions) < total_count

        logger.info(
            f"Retrieved {len(transactions)} transactions for user {user.id}, "
            f"page {page}, total_count {total_count}"
        )

        return TransactionsListResponse(
            transactions=transactions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    except Exception as e:
        logger.error(f"Failed to fetch transactions for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user transactions: {str(e)}"
        )


class UserAccountDetailsResponse(BaseModel):
    """Response model for user account details."""

    balance_cents: int = Field(alias="balanceCents", description="Balance in cents")
    status: UserAccountStatus = Field(description="Account status")
    onboarding_completed: bool = Field(
        alias="onboardingCompleted", description="Whether onboarding is completed"
    )
    monthly_credits_total: int = Field(
        alias="monthlyCreditsTotal",
        description="Total monthly AI credits included with subscription (in cents)",
    )
    monthly_credits_used: int = Field(
        alias="monthlyCreditsUsed",
        description="Monthly AI credits used this billing cycle (in cents)",
    )
    subscription_cancel_at: Optional[str] = Field(
        alias="subscriptionCancelAt",
        default=None,
        description="ISO timestamp when subscription will be cancelled",
    )
    subscription_canceled_at: Optional[str] = Field(
        alias="subscriptionCanceledAt",
        default=None,
        description="ISO timestamp when subscription cancellation was requested",
    )
    subscription_cancel_at_period_end: Optional[bool] = Field(
        alias="subscriptionCancelAtPeriodEnd",
        default=None,
        description="Whether subscription cancels at end of billing period",
    )


@app.get(
    "/api/accounting/user-account-details", response_model=UserAccountDetailsResponse
)
async def get_user_account_details(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> UserAccountDetailsResponse:
    """
    Get the current user's account details from the user_account_details table.
    """
    try:
        user_account_details: UserAccountDetails = user.account_details

        return UserAccountDetailsResponse(
            balanceCents=math.floor(user_account_details.balance_cents),
            status=user_account_details.status,
            onboardingCompleted=user_account_details.onboarding_completed,
            monthlyCreditsTotal=user_account_details.monthly_credits_total,
            monthlyCreditsUsed=user_account_details.monthly_credits_used,
            subscriptionCancelAt=(
                user_account_details.subscription_cancel_at.isoformat()
                if user_account_details.subscription_cancel_at
                else None
            ),
            subscriptionCanceledAt=(
                user_account_details.subscription_canceled_at.isoformat()
                if user_account_details.subscription_canceled_at
                else None
            ),
            subscriptionCancelAtPeriodEnd=user_account_details.subscription_cancel_at_period_end,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user account details: {str(e)}"
        )


@app.post("/api/accounting/openmeter-token", response_model=OpenMeterTokenResponse)
async def get_openmeter_token(
    user: User = Depends(dependency_to_override),
) -> OpenMeterTokenResponse:
    openmeter_service = OpenMeterService(
        base_url=settings.openmeter_base_url, api_token=settings.openmeter_api_token
    )
    return openmeter_service.get_portal_token(str(user.id))


class RefundRequest(BaseModel):
    """Request model for refund operations."""

    amount_cents: int = Field(description="Amount to refund in cents", gt=0)


class RefundResult(BaseModel):
    """Response model for refund operations."""

    success: bool = Field(description="Whether the refund was successful")
    details: Optional[str] = Field(description="Details of the refund", default=None)


@app.post("/api/accounting/refund", response_model=RefundResult)
async def process_refund(
    request: RefundRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> RefundResult:

    logger.info(
        f"Processing refund for user {user.id} with amount {request.amount_cents}"
    )

    return accounting_controller.process_refund(user, request.amount_cents, db)


class PendingTopupResponse(BaseModel):
    """Response model for a pending topup."""

    id: str = Field(description="Pending topup ID")
    user_id: str = Field(alias="userId", description="User ID")
    session_id: str = Field(alias="sessionId", description="Stripe session ID")
    amount_cents: int = Field(alias="amountCents", description="Amount in cents")
    status: PendingTopupStatus = Field(description="Topup status")
    created_at: str = Field(alias="createdAt", description="Creation timestamp")
    completed_at: Optional[str] = Field(
        alias="completedAt", default=None, description="Completion timestamp"
    )


@app.get("/api/accounting/pending-topup", response_model=PendingTopupResponse)
async def get_pending_topup(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> PendingTopupResponse:
    """
    Get the latest user's latest pending topup if it exists.
    Returns 404 if no pending topup is found.
    """
    pending_topup = (
        db.query(PendingTopup)
        .filter(PendingTopup.user_id == user.id)
        .order_by(PendingTopup.created_at.desc())
        .first()
    )
    if not pending_topup:
        raise HTTPException(status_code=404, detail="No pending topup found")
    return PendingTopupResponse(
        id=str(pending_topup.id),
        userId=str(pending_topup.user_id),
        sessionId=pending_topup.session_id,
        amountCents=pending_topup.amount_cents,
        status=pending_topup.status,
        createdAt=pending_topup.created_at.isoformat(),
        completedAt=(
            pending_topup.completed_at.isoformat()
            if pending_topup.completed_at
            else None
        ),
    )
