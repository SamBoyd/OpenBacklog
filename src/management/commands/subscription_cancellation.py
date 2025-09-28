import asyncio
import logging
import time
from typing import Optional

from src.db import get_db
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    set_user_context,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)


async def execute(
    interval: int = 1800, component_logger: Optional[logging.Logger] = None
):
    """
    Continuously process overdue subscription cancellations at specified interval.

    Args:
        interval: Time in seconds between runs (default 30 minutes)
        component_logger: Logger instance to use (defaults to module logger)
    """
    from src.accounting.accounting_controller import (
        get_overdue_subscription_cancellations,
        process_overdue_subscription_cancellation,
    )

    worker_logger = component_logger or logger

    # Set operation context for this worker
    set_operation_context(
        "subscription_cancellation_worker",
        details={
            "interval": interval,
            "worker_type": "continuous",
        },
    )

    # Track worker startup
    add_breadcrumb(
        "Starting subscription cancellation worker",
        category="subscription_cancellation.worker",
        data={
            "interval": interval,
        },
    )
    track_ai_metrics(
        "subscription_cancellation.worker.started", 1, tags={"interval": str(interval)}
    )

    worker_logger.info(
        f"Starting subscription cancellations worker (interval: {interval}s)"
    )

    while True:
        loop_start_time = time.time()

        try:
            # Add breadcrumb for processing iteration
            add_breadcrumb(
                "Starting subscription cancellation processing cycle",
                category="subscription_cancellation.worker",
                data={"cycle_start_time": loop_start_time},
            )

            session = next(get_db())
            try:
                # Get users with overdue cancellations
                overdue_users = get_overdue_subscription_cancellations(session)

                # Track users found for processing
                track_ai_metrics(
                    "subscription_cancellation.worker.users_found",
                    len(overdue_users),
                    tags={"batch_size": str(len(overdue_users))},
                )

                if overdue_users:
                    add_breadcrumb(
                        f"Found {len(overdue_users)} users with overdue subscription cancellations",
                        category="subscription_cancellation.processing",
                        data={
                            "user_count": len(overdue_users),
                            "user_emails": [user.email for user in overdue_users],
                        },
                    )

                    worker_logger.info(
                        f"Processing overdue subscription cancellations for {len(overdue_users)} users"
                    )
                    processed_count = 0
                    failed_count = 0

                    for user in overdue_users:
                        user_start_time = time.time()

                        try:
                            # Set user context for this cancellation
                            set_user_context(user)

                            add_breadcrumb(
                                f"Processing cancellation for user {user.email}",
                                category="subscription_cancellation.user",
                                data={
                                    "user_id": str(user.id),
                                    "user_email": user.email,
                                },
                            )

                            result = process_overdue_subscription_cancellation(
                                user, session
                            )

                            user_processing_time = (
                                time.time() - user_start_time
                            ) * 1000

                            if result.success:
                                processed_count += 1

                                add_breadcrumb(
                                    f"Successfully cancelled subscription for {user.email}",
                                    category="subscription_cancellation.success",
                                    data={
                                        "user_id": str(user.id),
                                        "user_email": user.email,
                                        "refunded_cents": result.total_refunded_cents,
                                        "processing_time_ms": user_processing_time,
                                    },
                                )

                                track_ai_metrics(
                                    "subscription_cancellation.user.processed_success",
                                    1,
                                    tags={
                                        "user_id": str(user.id),
                                        "refunded": str(
                                            result.total_refunded_cents > 0
                                        ),
                                    },
                                )

                                worker_logger.info(
                                    f"✓ Cancelled subscription for {user.email}: refunded ${result.total_refunded_cents / 100:.2f}"
                                )
                            else:
                                failed_count += 1

                                add_breadcrumb(
                                    f"Failed to cancel subscription for {user.email}",
                                    category="subscription_cancellation.failure",
                                    level="error",
                                    data={
                                        "user_id": str(user.id),
                                        "user_email": user.email,
                                        "error": result.error,
                                        "processing_time_ms": user_processing_time,
                                    },
                                )

                                track_ai_metrics(
                                    "subscription_cancellation.user.processed_failed",
                                    1,
                                    tags={
                                        "user_id": str(user.id),
                                        "error_type": "business_logic_failure",
                                    },
                                )

                                worker_logger.error(
                                    f"✗ Failed to cancel subscription for {user.email}: {result.error}"
                                )

                        except Exception as e:
                            failed_count += 1
                            user_processing_time = (
                                time.time() - user_start_time
                            ) * 1000

                            add_breadcrumb(
                                f"Unexpected error processing {user.email}",
                                category="subscription_cancellation.error",
                                level="error",
                                data={
                                    "user_id": str(user.id),
                                    "user_email": user.email,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                    "processing_time_ms": user_processing_time,
                                },
                            )

                            track_ai_metrics(
                                "subscription_cancellation.user.unexpected_error",
                                1,
                                tags={
                                    "user_id": str(user.id),
                                    "error_type": type(e).__name__,
                                },
                            )

                            capture_ai_exception(
                                e,
                                user=user,
                                operation_type="subscription_cancellation_processing",
                                extra_context={
                                    "user_email": user.email,
                                    "processing_time_ms": user_processing_time,
                                    "worker_type": "subscription_cancellation",
                                },
                            )

                            worker_logger.error(
                                f"✗ Unexpected error processing {user.email}: {e}"
                            )

                    # Track batch completion metrics
                    batch_processing_time = (time.time() - loop_start_time) * 1000

                    track_ai_metrics(
                        "subscription_cancellation.batch.processed_success",
                        processed_count,
                        tags={"batch_size": str(len(overdue_users))},
                    )

                    track_ai_metrics(
                        "subscription_cancellation.batch.processed_failed",
                        failed_count,
                        tags={"batch_size": str(len(overdue_users))},
                    )

                    add_breadcrumb(
                        "Completed subscription cancellation batch processing",
                        category="subscription_cancellation.batch",
                        data={
                            "total_users": len(overdue_users),
                            "processed_count": processed_count,
                            "failed_count": failed_count,
                            "batch_processing_time_ms": batch_processing_time,
                        },
                    )

                    worker_logger.info(
                        f"Subscription cancellations complete: {processed_count} successful, {failed_count} failed"
                    )
                else:
                    add_breadcrumb(
                        "No overdue subscription cancellations found",
                        category="subscription_cancellation.worker",
                        data={
                            "cycle_processing_time_ms": (time.time() - loop_start_time)
                            * 1000
                        },
                    )

                    worker_logger.debug("No overdue subscription cancellations found")

            finally:
                session.close()

        except Exception as e:
            loop_processing_time = (time.time() - loop_start_time) * 1000

            add_breadcrumb(
                "Error in subscription cancellations worker",
                category="subscription_cancellation.worker",
                level="error",
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "loop_processing_time_ms": loop_processing_time,
                },
            )

            track_ai_metrics(
                "subscription_cancellation.worker.error",
                1,
                tags={"error_type": type(e).__name__},
            )

            capture_ai_exception(
                e,
                operation_type="subscription_cancellation_worker",
                extra_context={
                    "worker_type": "subscription_cancellation",
                    "interval": interval,
                    "loop_processing_time_ms": loop_processing_time,
                },
            )

            worker_logger.error(f"Error in subscription cancellations worker: {e}")

        # Wait for next interval
        add_breadcrumb(
            f"Waiting {interval} seconds before next processing cycle",
            category="subscription_cancellation.worker",
            data={"interval": interval},
        )

        await asyncio.sleep(interval)
