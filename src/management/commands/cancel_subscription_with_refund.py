import logging
import uuid
from typing import Optional

from src.accounting.accounting_controller import cancel_subscription_with_refund
from src.db import get_db
from src.models import User
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    set_user_context,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)


async def execute(email: Optional[str] = None, user_id: Optional[str] = None):
    """
    Cancel a user's subscription and refund their last invoice.

    This command is used by support staff to manually process subscription
    cancellations with refunds for the last invoice (30-day window).

    Args:
        email: User email address
        user_id: User UUID

    Raises:
        ValueError: If neither or both email and user_id are provided
    """
    # Validate input
    if not email and not user_id:
        logger.error("Either --email or --user-id must be provided")
        raise ValueError("Either --email or --user-id must be provided")

    if email and user_id:
        logger.error("Provide either --email or --user-id, not both")
        raise ValueError("Provide either --email or --user-id, not both")

    # Set operation context
    set_operation_context(
        "cancel_subscription_with_refund_command",
        details={
            "email": email if email else None,
            "user_id": user_id if user_id else None,
        },
    )

    add_breadcrumb(
        "Starting subscription cancellation with refund",
        category="subscription.cancel_with_refund",
        data={
            "email": email if email else None,
            "user_id": user_id if user_id else None,
        },
    )

    track_ai_metrics(
        "subscription.cancel_with_refund.command_started",
        1,
        tags={
            "lookup_type": "email" if email else "user_id",
        },
    )

    session = next(get_db())

    try:
        # Look up user
        user = None
        if email:
            logger.info(f"Looking up user by email: {email}")
            user = session.query(User).filter(User.email == email.lower()).first()
            if not user:
                logger.error(f"User not found with email: {email}")
                track_ai_metrics(
                    "subscription.cancel_with_refund.user_not_found",
                    1,
                    tags={"lookup_type": "email"},
                )
                return
        else:
            logger.info(f"Looking up user by ID: {user_id}")
            try:
                user_uuid = uuid.UUID(user_id)
                user = session.get(User, user_uuid)
                if not user:
                    logger.error(f"User not found with ID: {user_id}")
                    track_ai_metrics(
                        "subscription.cancel_with_refund.user_not_found",
                        1,
                        tags={"lookup_type": "user_id"},
                    )
                    return
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                track_ai_metrics(
                    "subscription.cancel_with_refund.invalid_user_id",
                    1,
                )
                return

        # Set user context for enhanced debugging
        set_user_context(user)

        add_breadcrumb(
            f"Found user {user.id}",
            category="subscription.cancel_with_refund",
            data={
                "user_id": str(user.id),
                "user_email": user.email,
            },
        )

        # Check if user has a subscription
        user_account_details = user.account_details
        if not user_account_details.stripe_customer_id:
            logger.error(
                f"User {user.email} has no Stripe customer ID - cannot cancel subscription"
            )
            track_ai_metrics(
                "subscription.cancel_with_refund.no_stripe_customer",
                1,
            )
            return

        logger.info(
            f"Processing subscription cancellation with refund for {user.email}..."
        )
        logger.info(
            f"User ID: {user.id}, Stripe Customer: {user_account_details.stripe_customer_id}"
        )

        add_breadcrumb(
            "Calling cancel_subscription_with_refund",
            category="subscription.cancel_with_refund",
            data={
                "user_id": str(user.id),
                "stripe_customer_id": user_account_details.stripe_customer_id,
            },
        )

        # Call the controller function (30-day refund window for last monthly invoice)
        result = cancel_subscription_with_refund(
            user=user, db=session, refund_last_n_days=30
        )

        # Log results
        logger.info("")
        logger.info("=" * 80)
        logger.info("SUBSCRIPTION CANCELLATION RESULT")
        logger.info("=" * 80)
        logger.info(f"User: {user.email} (ID: {user.id})")
        logger.info(f"Success: {result.success}")
        logger.info(f"Billing Cancelled: {result.billing_cancelled}")
        logger.info(f"Stripe Cancelled: {result.stripe_cancelled}")
        logger.info(f"Refunds Processed: {result.refunds_processed}")
        logger.info(
            f"Total Refunded: ${result.total_refunded_cents / 100:.2f} ({result.total_refunded_cents} cents)"
        )

        if result.details:
            logger.info(f"Details: {result.details}")
        if result.error:
            logger.error(f"Error: {result.error}")

        logger.info("=" * 80)
        logger.info("")

        add_breadcrumb(
            "Subscription cancellation complete",
            category="subscription.cancel_with_refund",
            data={
                "user_id": str(user.id),
                "success": result.success,
                "refunds_processed": result.refunds_processed,
                "total_refunded_cents": result.total_refunded_cents,
            },
        )

        # Track metrics
        if result.success:
            logger.info(
                f"✓ Successfully cancelled subscription and refunded ${result.total_refunded_cents / 100:.2f} for {user.email}"
            )
            track_ai_metrics(
                "subscription.cancel_with_refund.success",
                1,
                tags={
                    "refunds_processed": str(result.refunds_processed),
                },
            )
            track_ai_metrics(
                "subscription.cancel_with_refund.refund_amount_cents",
                result.total_refunded_cents,
            )
        else:
            logger.error(
                f"✗ Failed to cancel subscription for {user.email}: {result.error}"
            )
            track_ai_metrics(
                "subscription.cancel_with_refund.failure",
                1,
                tags={
                    "error_type": "cancellation_failed",
                },
            )

    except Exception as e:
        logger.error(f"Unexpected error cancelling subscription: {e}")

        add_breadcrumb(
            "Unexpected error in cancel_subscription_with_refund",
            category="subscription.cancel_with_refund",
            level="error",
            data={
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )

        # Capture the exception
        capture_ai_exception(
            e,
            operation_type="cancel_subscription_with_refund_command",
            extra_context={
                "email": email if email else None,
                "user_id": user_id if user_id else None,
            },
        )

        track_ai_metrics(
            "subscription.cancel_with_refund.unexpected_error",
            1,
            tags={
                "error_type": type(e).__name__,
            },
        )

    finally:
        session.close()
