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
worker_logger = logger


async def execute(
    interval: int = 3600, component_logger: Optional[logging.Logger] = None
):
    """
    Continuously run monthly credits reset at specified interval.

    Args:
        interval: Time in seconds between runs (default 1 hour)
        component_logger: Logger instance to use (defaults to module logger)
    """
    from src.accounting.accounting_controller import (
        get_users_due_for_credit_reset,
        process_billing_cycle_reset,
    )

    worker_logger = component_logger or logger

    # Set operation context for this worker
    set_operation_context(
        "monthly_credits_reset_worker",
        details={
            "interval": interval,
            "worker_type": "continuous",
        },
    )

    # Track worker startup
    add_breadcrumb(
        "Starting monthly credits reset worker",
        category="credits_reset.worker",
        data={
            "interval": interval,
        },
    )

    track_ai_metrics(
        "credits_reset.worker.started",
        1,
        tags={
            "interval": str(interval),
        },
    )

    worker_logger.info(f"Starting monthly credits reset worker (interval: {interval}s)")

    iteration_count = 0

    while True:
        iteration_start_time = time.time()
        iteration_count += 1

        add_breadcrumb(
            f"Starting credits reset iteration {iteration_count}",
            category="credits_reset.iteration",
            data={
                "iteration": iteration_count,
            },
        )

        try:
            session = next(get_db())
            try:
                # Monitor database query performance
                query_start_time = time.time()
                eligible_users = get_users_due_for_credit_reset(session)
                query_duration_ms = (time.time() - query_start_time) * 1000

                track_ai_metrics(
                    "credits_reset.query.duration_ms",
                    query_duration_ms,
                    tags={
                        "iteration": str(iteration_count),
                    },
                )

                track_ai_metrics(
                    "credits_reset.eligible_users.count",
                    len(eligible_users),
                    tags={
                        "iteration": str(iteration_count),
                    },
                )

                add_breadcrumb(
                    f"Found {len(eligible_users)} users due for credit reset",
                    category="credits_reset.batch",
                    data={
                        "eligible_users_count": len(eligible_users),
                        "query_duration_ms": query_duration_ms,
                    },
                )

                if eligible_users:
                    batch_start_time = time.time()
                    worker_logger.info(
                        f"Processing monthly credit reset for {len(eligible_users)} users"
                    )
                    processed_count = 0
                    failed_count = 0

                    for user in eligible_users:
                        user_start_time = time.time()

                        # Set user context for enhanced debugging
                        set_user_context(user)

                        add_breadcrumb(
                            f"Processing credit reset for user {user.id}",
                            category="credits_reset.user_processing",
                            data={
                                "user_id": str(user.id),
                                "user_email": user.email,
                                "iteration": iteration_count,
                            },
                        )

                        try:
                            result = process_billing_cycle_reset(user, session)
                            user_duration_ms = (time.time() - user_start_time) * 1000

                            if result.success:
                                processed_count += 1
                                worker_logger.info(
                                    f"✓ Reset monthly credits for {user.email}"
                                )

                                add_breadcrumb(
                                    f"Successfully reset credits for user {user.id}",
                                    category="credits_reset.user_processing",
                                    data={
                                        "user_id": str(user.id),
                                        "processing_time_ms": user_duration_ms,
                                        "success": True,
                                    },
                                )

                                track_ai_metrics(
                                    "credits_reset.user.success",
                                    1,
                                    tags={
                                        "user_id": str(user.id)[
                                            :8
                                        ],  # Truncated for privacy
                                    },
                                )

                                track_ai_metrics(
                                    "credits_reset.user.processing_time_ms",
                                    user_duration_ms,
                                    tags={
                                        "result": "success",
                                    },
                                )
                            else:
                                failed_count += 1
                                worker_logger.error(
                                    f"✗ Failed to reset credits for {user.email}: {result.error}"
                                )

                                add_breadcrumb(
                                    f"Failed to reset credits for user {user.id}",
                                    category="credits_reset.user_processing",
                                    level="error",
                                    data={
                                        "user_id": str(user.id),
                                        "error": result.error,
                                        "processing_time_ms": user_duration_ms,
                                        "success": False,
                                    },
                                )

                                track_ai_metrics(
                                    "credits_reset.user.failure",
                                    1,
                                    tags={
                                        "user_id": str(user.id)[
                                            :8
                                        ],  # Truncated for privacy
                                        "error_type": "billing_service_error",
                                    },
                                )

                                track_ai_metrics(
                                    "credits_reset.user.processing_time_ms",
                                    user_duration_ms,
                                    tags={
                                        "result": "failure",
                                    },
                                )
                        except Exception as e:
                            failed_count += 1
                            user_duration_ms = (time.time() - user_start_time) * 1000
                            worker_logger.error(
                                f"✗ Unexpected error processing {user.email}: {e}"
                            )

                            add_breadcrumb(
                                f"Unexpected error processing user {user.id}",
                                category="credits_reset.user_processing",
                                level="error",
                                data={
                                    "user_id": str(user.id),
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                    "processing_time_ms": user_duration_ms,
                                },
                            )

                            # Capture the exception with user context
                            capture_ai_exception(
                                e,
                                user=user,
                                operation_type="monthly_credits_reset_user_processing",
                                extra_context={
                                    "user_id": str(user.id),
                                    "iteration": iteration_count,
                                    "error_type": "unexpected_error",
                                },
                            )

                            track_ai_metrics(
                                "credits_reset.user.unexpected_error",
                                1,
                                tags={
                                    "user_id": str(user.id)[
                                        :8
                                    ],  # Truncated for privacy
                                    "error_type": type(e).__name__,
                                },
                            )

                    batch_duration_ms = (time.time() - batch_start_time) * 1000

                    worker_logger.info(
                        f"Monthly credits reset complete: {processed_count} successful, {failed_count} failed"
                    )

                    add_breadcrumb(
                        f"Completed credit reset batch processing",
                        category="credits_reset.batch",
                        data={
                            "processed_count": processed_count,
                            "failed_count": failed_count,
                            "total_users": len(eligible_users),
                            "batch_duration_ms": batch_duration_ms,
                            "iteration": iteration_count,
                        },
                    )

                    track_ai_metrics(
                        "credits_reset.batch.processed_count",
                        processed_count,
                        tags={
                            "iteration": str(iteration_count),
                        },
                    )

                    track_ai_metrics(
                        "credits_reset.batch.failed_count",
                        failed_count,
                        tags={
                            "iteration": str(iteration_count),
                        },
                    )

                    track_ai_metrics(
                        "credits_reset.batch.duration_ms",
                        batch_duration_ms,
                        tags={
                            "batch_size": str(len(eligible_users)),
                        },
                    )
                else:
                    worker_logger.debug("No users found due for monthly credit reset")

                    add_breadcrumb(
                        "No users found due for credit reset",
                        category="credits_reset.batch",
                        data={
                            "iteration": iteration_count,
                        },
                    )

                    track_ai_metrics(
                        "credits_reset.batch.no_users",
                        1,
                        tags={
                            "iteration": str(iteration_count),
                        },
                    )

            finally:
                session.close()

        except Exception as e:
            worker_logger.error(f"Error in monthly credits reset worker: {e}")

            add_breadcrumb(
                "Monthly credits reset worker iteration failed",
                category="credits_reset.worker",
                level="error",
                data={
                    "iteration": iteration_count,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Capture the exception with operation context
            capture_ai_exception(
                e,
                operation_type="monthly_credits_reset_worker_iteration",
                extra_context={
                    "iteration": iteration_count,
                    "interval": interval,
                    "error_type": "worker_iteration_error",
                },
            )

            track_ai_metrics(
                "credits_reset.worker.iteration_error",
                1,
                tags={
                    "error_type": type(e).__name__,
                    "iteration": str(iteration_count),
                },
            )

        # Track iteration completion
        iteration_duration_ms = (time.time() - iteration_start_time) * 1000

        track_ai_metrics(
            "credits_reset.iteration.duration_ms",
            iteration_duration_ms,
            tags={
                "iteration": str(iteration_count),
            },
        )

        add_breadcrumb(
            f"Completed credits reset iteration {iteration_count}",
            category="credits_reset.iteration",
            data={
                "iteration": iteration_count,
                "duration_ms": iteration_duration_ms,
            },
        )

        # Wait for next interval
        await asyncio.sleep(interval)
