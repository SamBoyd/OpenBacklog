import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src import controller
from src.accounting.billing_service import BillingService, BillingServiceException
from src.accounting.models import UserAccountDetails
from src.accounting.openmeter_service import OpenMeterService
from src.accounting.stripe_service import RefundBreakdownItem
from src.accounting.stripe_service import RefundResult as StripeRefundResult
from src.accounting.stripe_service import StripeService
from src.accounting.usage_tracker import UsageTracker
from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.accounting.accounting_views import RefundResult


@dataclass
class SubscriptionCancellationResult:
    """Response model for subscription cancellation operations."""

    billing_cancelled: bool
    stripe_cancelled: bool
    refunds_processed: int
    total_refunded_cents: int
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BillingCycleResetResult:
    """Response model for billing cycle reset operations."""

    success: bool
    credits_reset: bool
    billing_cycle_updated: bool
    error: Optional[str] = None
    details: Optional[str] = None


def get_usage_tracker(db: Session) -> UsageTracker:
    openmeter_service = OpenMeterService(
        base_url=settings.openmeter_base_url,
        api_token=settings.openmeter_api_token,
    )

    def db_session():
        return db

    return UsageTracker(openmeter_service=openmeter_service, db_session=db_session)


def process_refund(
    user: User,
    refund_amount_cents: int,
    db: Session,
) -> "RefundResult":
    """
    Process a refund for the current user.

    This endpoint:
    1. Updates user usage to get current accurate balance
    2. Validates eligibility and processes refund through billing service FSM
    3. Retrieves paid invoices from Stripe
    4. Calculates refund breakdown across invoices
    5. Processes refunds through Stripe and creates credit notes
    6. Records ledger entries and state transitions

    Args:
        user: Current authenticated user
        refund_amount_cents: Amount to refund in cents
        db: Database session

    Returns:
        RefundResult containing refund details and updated account state

    Raises:
        HTTPException: If refund cannot be processed
    """

    from src.accounting.accounting_views import RefundResult

    try:
        # Initialize services
        billing_service = BillingService(db)
        stripe_service = StripeService(db)
        usage_tracker = get_usage_tracker(db)
        user_account_details = user.account_details

        # 1. Update the usage of the user to get accurate current balance
        usage_tracker.process_user_usage(user_account_details)

        # 2. Validate refund eligibility through billing service FSM
        refund_id = f"refund_{user.id}_{int(datetime.now().timestamp())}"
        try:
            updated_account = billing_service.process_balance_refund(
                user=user,
                external_id=refund_id,
            )
        except BillingServiceException as e:
            logger.error(
                f"Billing service error processing refund for user {user.id}: {e}"
            )
            return RefundResult(success=False, details=str(e))

        # 3. Fetch paid invoices from Stripe
        try:
            paid_invoices = stripe_service.get_paid_invoices(
                user_account_details.stripe_customer_id  # type: ignore
            )
        except Exception as e:
            logger.error(
                "Error retrieving invoices for user %s (customer %s): %s",
                user.id,
                user_account_details.stripe_customer_id,  # type: ignore
                e,
            )
            return RefundResult(success=False, details="Failed to retrieve invoices.")

        if not paid_invoices:
            logger.error(
                "No paid invoices found for user %s (customer %s)",
                user.id,
                user_account_details.stripe_customer_id,  # type: ignore
            )
            return RefundResult(
                success=False, details="No paid invoices available for refund."
            )

        # 4. Calculate how the refund should be split across invoices
        try:
            refund_breakdown: List[RefundBreakdownItem] = (
                stripe_service.calculate_refund_breakdown(
                    paid_invoices, refund_amount_cents
                )
            )
        except ValueError as e:
            logger.error("Refund calculation failed for user %s: %s", user.id, e)
            return RefundResult(success=False, details=str(e))

        # 5. Create the actual Stripe refunds (and credit notes)
        stripe_refunds: List[StripeRefundResult] = stripe_service.process_refunds(
            refund_breakdown
        )

        successful_refund_amount_cents = sum(
            r.amount_cents for r in stripe_refunds if r.success
        )

        logger.info(
            f"Successfully processed refund for user {user.id}: "
            f"amount {successful_refund_amount_cents} cents, "
            f"new balance {updated_account.balance_cents} cents, "
            f"new status {updated_account.status}"
        )

        return RefundResult(
            success=True, details=f"Refunded {successful_refund_amount_cents} cents"
        )

    except HTTPException:
        raise
    except BillingServiceException as e:
        logger.error(f"Billing service error for user {user.id}: {e}")
        return RefundResult(success=False, details=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing refund for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")


def complete_onboarding(user: User, db: Session) -> UserAccountDetails:
    """
    Mark onboarding as completed and transition user from NEW to NO_SUBSCRIPTION state.

    This allows users to complete onboarding and access task management features
    without signing up for a paid subscription (free tier).

    Args:
        user: The user completing onboarding
        db: Database session

    Returns:
        Updated UserAccountDetails with onboarding_completed=True and status=NO_SUBSCRIPTION
    """
    from src.accounting.models import UserAccountStatus

    billing_service = BillingService(db)
    account_details = user.account_details

    # Only transition state if user is in NEW state
    # If already in NO_SUBSCRIPTION or another state, this is idempotent
    if account_details.status == UserAccountStatus.NEW:
        # Transition NEW → NO_SUBSCRIPTION through billing service FSM
        onboarding_id = f"onboarding_{user.id}"
        billing_service.skip_subscription(user, onboarding_id)

    # Mark onboarding as completed
    account_details.onboarding_completed = True
    db.add(account_details)
    db.commit()
    db.refresh(account_details)
    return account_details


def cancel_subscription_with_refund(
    user: User, db: Session, refund_last_n_days: int = 30
) -> SubscriptionCancellationResult:
    """
    Cancel a user's subscription and refund recent payments with proper transaction rollback.

    This function coordinates:
    1. Canceling the subscription in the billing service (event-sourced)
    2. Canceling the Stripe subscription and processing refunds
    3. Rolling back billing changes if Stripe operations fail

    Args:
        user: The user whose subscription should be canceled
        db: Database session
        refund_last_n_days: Number of days to look back for refundable payments

    Returns:
        SubscriptionCancellationResult with operation details

    Raises:
        HTTPException: For critical system errors only
    """
    try:
        # Initialize services
        billing_service = BillingService(db)
        stripe_service = StripeService(db)
        user_account_details = user.account_details

        if not user_account_details.stripe_customer_id:
            return SubscriptionCancellationResult(
                billing_cancelled=False,
                stripe_cancelled=False,
                refunds_processed=0,
                total_refunded_cents=0,
                success=False,
                error="User has no Stripe customer ID",
            )

        # Create a database savepoint for rollback capability
        savepoint = db.begin_nested()

        try:
            # Step 1: Cancel subscription in billing service
            cancellation_id = f"cancel_{user.id}_{int(datetime.now().timestamp())}"

            try:
                billing_service.cancel_subscription(
                    user=user, external_id=cancellation_id
                )
                logger.info(f"Billing service canceled subscription for user {user.id}")
            except BillingServiceException as e:
                savepoint.rollback()
                logger.error(
                    f"Billing service error canceling subscription for user {user.id}: {e}"
                )
                return SubscriptionCancellationResult(
                    billing_cancelled=False,
                    stripe_cancelled=False,
                    refunds_processed=0,
                    total_refunded_cents=0,
                    success=False,
                    error=f"Billing service error: {str(e)}",
                )

            # Step 2: Cancel Stripe subscription and process refunds
            try:
                stripe_result = stripe_service.cancel_and_refund_subscription(
                    stripe_customer_id=user_account_details.stripe_customer_id,
                    refund_last_n_days=refund_last_n_days,
                )

                if not stripe_result.success:
                    # Stripe operation failed, rollback billing changes
                    savepoint.rollback()

                    # Attempt to reactivate subscription as compensating action
                    try:
                        billing_service.reactivate_subscription(
                            user=user, external_id=cancellation_id
                        )
                        logger.info(
                            f"Reactivated subscription for user {user.id} after Stripe failure"
                        )
                    except Exception as reactivate_error:
                        logger.error(
                            f"Failed to reactivate subscription for user {user.id} after rollback: {reactivate_error}"
                        )

                    return SubscriptionCancellationResult(
                        billing_cancelled=False,
                        stripe_cancelled=stripe_result.subscription_cancelled,
                        refunds_processed=len(stripe_result.refunds_processed),
                        total_refunded_cents=stripe_result.total_refunded_cents,
                        success=False,
                        error=f"Stripe operation failed: {stripe_result.error}",
                    )

                # Both operations succeeded, commit the transaction
                savepoint.commit()

                logger.info(
                    f"Successfully canceled subscription for user {user.id}: "
                    f"refunded {stripe_result.total_refunded_cents} cents from "
                    f"{len(stripe_result.refunds_processed)} invoices"
                )

                return SubscriptionCancellationResult(
                    billing_cancelled=True,
                    stripe_cancelled=stripe_result.subscription_cancelled,
                    refunds_processed=len(stripe_result.refunds_processed),
                    total_refunded_cents=stripe_result.total_refunded_cents,
                    success=True,
                    details=f"Canceled subscription and refunded {stripe_result.total_refunded_cents} cents",
                    error=None,
                )

            except Exception as stripe_error:
                # Unexpected Stripe error, rollback and attempt compensating action
                savepoint.rollback()

                try:
                    billing_service.reactivate_subscription(
                        user=user, external_id=cancellation_id
                    )
                    logger.info(
                        f"Reactivated subscription for user {user.id} after Stripe error"
                    )
                except Exception as reactivate_error:
                    logger.error(
                        f"Failed to reactivate subscription for user {user.id} after rollback: {reactivate_error}"
                    )

                logger.error(
                    f"Unexpected Stripe error for user {user.id}: {stripe_error}"
                )
                return SubscriptionCancellationResult(
                    billing_cancelled=False,
                    stripe_cancelled=False,
                    refunds_processed=0,
                    total_refunded_cents=0,
                    success=False,
                    error=f"Unexpected Stripe error: {str(stripe_error)}",
                )

        except Exception as transaction_error:
            # Database transaction error
            savepoint.rollback()
            logger.error(
                f"Database transaction error for user {user.id}: {transaction_error}"
            )
            return SubscriptionCancellationResult(
                billing_cancelled=False,
                stripe_cancelled=False,
                refunds_processed=0,
                total_refunded_cents=0,
                success=False,
                error=f"Database transaction error: {str(transaction_error)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in cancel_subscription_with_refund for user {user.id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to cancel subscription with refund"
        )


def handle_subscription_created_with_setup(event: Dict[str, Any], db: Session) -> None:
    """
    Handle customer.subscription.created webhook with complete subscription setup.

    This function orchestrates both the Stripe subscription processing and the
    administrative setup tasks that were previously done via frontend trigger.

    Steps performed:
    1. Process the Stripe subscription created event (save customer ID)
    2. Find the user by customer email
    3. Setup LiteLLM user and key for AI usage tracking
    4. Initialize billing service FSM state
    5. Complete onboarding on User & UserAccountDetails models
    6. Create OpenMeter customer

    Args:
        event: The Stripe webhook event data
        db: Database session

    Raises:
        ValueError: If the event data is invalid or missing required fields
        Exception: If any setup step fails (with proper rollback)
    """
    import stripe

    subscription_data = event["data"]["object"]
    subscription_id = subscription_data["id"]
    customer_id = subscription_data.get("customer")

    logger.info(
        f"Processing customer.subscription.created with setup for subscription: {subscription_id}"
    )

    if not customer_id:
        error_msg = f"No customer ID found in subscription {subscription_id}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Step 1: Process the Stripe subscription created event (original StripeService logic)
        stripe_service = StripeService(db)
        stripe_service.handle_subscription_created(event)

        # Step 2: Find the user by customer email (reusing logic from StripeService)
        try:
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email

            if not customer_email:
                logger.error(f"No email found for Stripe customer {customer_id}")
                raise ValueError(f"No email found for Stripe customer {customer_id}")

            # Find user by email
            user = db.query(User).filter(User.email == customer_email).first()

            if not user:
                logger.error(
                    f"No user found with email {customer_email} for customer {customer_id}. "
                    f"Cannot complete subscription setup."
                )
                raise ValueError(f"No user found with email {customer_email}")

            logger.info(f"Found user {user.id} for subscription setup")

        except stripe.StripeError as e:
            logger.error(f"Stripe API error retrieving customer {customer_id}: {e}")
            raise ValueError(f"Failed to retrieve customer details: {str(e)}")

        # Step 3: Get user account details (should have stripe_customer_id set by Step 1)
        merged_user = db.merge(user)
        user_account_details = merged_user.account_details

        if not user_account_details.stripe_customer_id:
            logger.error(
                f"User {user.id} has no Stripe customer ID after subscription processing"
            )
            raise ValueError(
                "Stripe customer ID not set during subscription processing"
            )

        # Step 4: Setup LiteLLM keys for AI usage tracking
        try:
            controller.create_litellm_user_and_key(merged_user, db)
            logger.info(f"Created LiteLLM user and key for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to create LiteLLM user for user {user.id}: {e}")
            raise ValueError(f"LiteLLM setup failed: {str(e)}")

        # Step 5: Initialize billing service FSM state
        try:
            billing_service = BillingService(db)
            billing_service.signup_subscription(
                merged_user, user_account_details.stripe_customer_id
            )
            logger.info(f"Initialized billing service FSM for user {user.id}")
        except Exception as e:
            logger.error(
                f"Failed to initialize billing service for user {user.id}: {e}"
            )
            raise ValueError(f"Billing service initialization failed: {str(e)}")

        # Step 6: Initialize monthly billing cycle tracking
        try:
            from datetime import datetime

            from dateutil.relativedelta import relativedelta

            # Set up billing cycle - starts 1 month from now
            next_billing_cycle = datetime.now() + relativedelta(months=1)
            user_account_details.next_billing_cycle_starts = next_billing_cycle
            user_account_details.monthly_credits_total = (
                settings.monthly_subscription_cost_cents
            )
            user_account_details.monthly_credits_used = 0

            db.add(user_account_details)
            db.commit()
            logger.info(
                f"Initialized billing cycle for user {user.id}, next cycle: {next_billing_cycle}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize billing cycle for user {user.id}: {e}")
            raise ValueError(f"Billing cycle initialization failed: {str(e)}")

        # Step 7: Complete onboarding on User & UserAccountDetails models
        try:
            complete_onboarding(merged_user, db)
            logger.info(f"Completed onboarding for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to complete onboarding for user {user.id}: {e}")
            raise ValueError(f"Onboarding completion failed: {str(e)}")

        # Step 8: Create OpenMeter customer
        try:
            openmeter_service = OpenMeterService(
                base_url=settings.openmeter_base_url,
                api_token=settings.openmeter_api_token,
            )
            openmeter_service.create_customer(
                user, user_account_details.stripe_customer_id
            )
            logger.info(f"Created OpenMeter customer for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to create OpenMeter customer for user {user.id}: {e}")
            raise ValueError(f"OpenMeter customer creation failed: {str(e)}")

        logger.info(
            f"Successfully completed subscription setup for user {user.id} "
            f"(customer {customer_id}, subscription {subscription_id})"
        )

    except Exception as e:
        logger.error(
            f"Failed to complete subscription setup for subscription {subscription_id}: {e}"
        )
        # Re-raise to let webhook handler decide how to respond
        raise


def get_overdue_subscription_cancellations(
    db: Session, limit: Optional[int] = None
) -> List[User]:
    """
    Get users whose subscriptions are due for cancellation.

    Returns users where:
    - subscription_cancel_at is set and has passed
    - subscription_canceled_at is NULL (not yet processed)

    Args:
        db: Database session
        limit: Optional limit on number of results

    Returns:
        List of User objects with overdue subscription cancellations
    """
    from sqlalchemy import and_

    query = (
        db.query(User)
        .join(UserAccountDetails)
        .filter(
            and_(
                UserAccountDetails.subscription_cancel_at_period_end.is_(True),
                UserAccountDetails.subscription_cancel_at <= datetime.now(),
            )
        )
    )

    if limit:
        query = query.limit(limit)

    return query.all()


def process_overdue_subscription_cancellation(
    user: User, db: Session
) -> SubscriptionCancellationResult:
    """
    Process an overdue subscription cancellation for a single user.

    This is a simplified version of cancel_subscription_with_refund() specifically
    for automated processing of overdue cancellations.

    Args:
        user: User whose subscription should be cancelled
        db: Database session

    Returns:
        SubscriptionCancellationResult with operation details
    """
    try:
        billing_service = BillingService(db)
        # Use existing cancellation logic with standard refund window
        billing_service.cancel_subscription(
            user=user, external_id=f"cancel_{user.id}_{int(datetime.now().timestamp())}"
        )

        user_account_details = db.merge(user.account_details)
        user_account_details.subscription_cancel_at = None
        user_account_details.subscription_canceled_at = None
        user_account_details.subscription_cancel_at_period_end = None
        db.add(user_account_details)
        db.commit()

        return SubscriptionCancellationResult(
            billing_cancelled=True,
            stripe_cancelled=True,
            refunds_processed=0,
            total_refunded_cents=0,
            success=True,
        )

    except Exception as e:
        logger.error(f"Failed to process overdue cancellation for user {user.id}: {e}")
        return SubscriptionCancellationResult(
            billing_cancelled=False,
            stripe_cancelled=False,
            refunds_processed=0,
            total_refunded_cents=0,
            success=False,
            error=f"Processing failed: {str(e)}",
        )


def get_users_due_for_credit_reset(
    db: Session, limit: Optional[int] = None, user_id: Optional[uuid.UUID] = None
) -> List[User]:
    """
    Get users whose billing cycles are due for monthly credit reset.

    Returns users where:
    - Status is ACTIVE_SUBSCRIPTION, SUSPENDED, or METERED_BILLING
    - next_billing_cycle_starts is set and has passed

    Args:
        db: Database session
        limit: Optional limit on number of results
        user_id: Optional specific user ID to check

    Returns:
        List of User objects due for billing cycle reset
    """
    from src.accounting.models import UserAccountStatus

    # Define statuses that are eligible for billing cycle reset
    eligible_statuses = [
        UserAccountStatus.ACTIVE_SUBSCRIPTION,
        UserAccountStatus.SUSPENDED,
        UserAccountStatus.METERED_BILLING,
    ]

    if user_id:
        # Handle specific user case
        user = db.get(User, user_id)
        if not user:
            return []

        account_details = user.account_details
        if (
            account_details.status not in eligible_statuses
            or not account_details.next_billing_cycle_starts
            or account_details.next_billing_cycle_starts > datetime.now()
        ):
            return []

        return [user]
    else:
        # Query all eligible users whose billing cycle has expired
        query = (
            db.query(User)
            .join(UserAccountDetails)
            .filter(
                UserAccountDetails.status.in_(eligible_statuses),
                UserAccountDetails.next_billing_cycle_starts <= datetime.now(),
                UserAccountDetails.next_billing_cycle_starts.isnot(None),
            )
        )

        if limit:
            query = query.limit(limit)

        return query.all()


def process_billing_cycle_reset(user: User, db: Session) -> BillingCycleResetResult:
    """
    Process billing cycle reset for a single user.

    This function:
    1. Resets monthly credits using BillingService.start_new_billing_cycle()
    2. Updates next_billing_cycle_starts to 30 days from now
    3. Commits the changes to the database

    Args:
        user: User to process billing cycle reset for
        db: Database session

    Returns:
        BillingCycleResetResult with operation details
    """
    from datetime import timedelta

    try:
        # Initialize billing service
        billing_service = BillingService(db)

        # Reset monthly credits using existing billing service method
        billing_service.start_new_billing_cycle(user)

        # Update next billing cycle date (30 days from now)
        account_details = user.account_details
        account_details.next_billing_cycle_starts = datetime.now() + timedelta(days=30)
        db.add(account_details)
        db.commit()

        logger.info(
            f"Successfully reset monthly credits for user {user.id} ({user.email})"
        )

        return BillingCycleResetResult(
            success=True,
            credits_reset=True,
            billing_cycle_updated=True,
            details=f"Reset monthly credits and updated billing cycle for {user.email}",
        )

    except BillingServiceException as e:
        logger.error(f"Billing service error resetting credits for user {user.id}: {e}")
        db.rollback()
        return BillingCycleResetResult(
            success=False,
            credits_reset=False,
            billing_cycle_updated=False,
            error=f"Billing service error: {str(e)}",
        )

    except Exception as e:
        logger.error(f"Failed to reset billing cycle for user {user.id}: {e}")
        db.rollback()
        return BillingCycleResetResult(
            success=False,
            credits_reset=False,
            billing_cycle_updated=False,
            error=f"Processing failed: {str(e)}",
        )
