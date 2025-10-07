"""
Sentry context helpers for enhanced AI usage monitoring.

This module provides utilities to set structured context in Sentry for better
error tracking, debugging, and monitoring of the AI job processing system.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union
from uuid import UUID

import sentry_sdk
from sentry_sdk import set_context, set_tag, set_user

from src.accounting.models import UserAccountStatus
from src.models import AIImprovementJob, JobStatus, Lens, User

logger = logging.getLogger(__name__)


def set_user_context(user: User) -> None:
    """
    Set user context in Sentry for better error tracking.

    Args:
        user: The User model instance
    """
    try:
        # Get account details safely
        account_status = None
        api_key_status = "unknown"

        if hasattr(user, "account_details") and user.account_details:
            account_status = (
                user.account_details.status.value
                if user.account_details.status
                else None
            )

        # Check for API key validity
        if hasattr(user, "user_keys") and user.user_keys:
            valid_keys = [k for k in user.user_keys if k.is_valid]
            api_key_status = "valid" if valid_keys else "invalid"

        # Set Sentry user context
        set_user(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.name,
            }
        )

        # Set additional user context
        set_context(
            "user_details",
            {
                "user_id": str(user.id),
                "account_status": account_status,
                "api_key_status": api_key_status,
                "is_verified": getattr(user, "is_verified", None),
                "is_active": getattr(user, "is_active", None),
                "last_logged_in": (
                    str(user.last_logged_in)
                    if hasattr(user, "last_logged_in") and user.last_logged_in
                    else None
                ),
            },
        )

        # Set tags for filtering
        if account_status:
            set_tag("account_status", account_status)
        set_tag("api_key_status", api_key_status)

    except Exception as e:
        logger.warning(f"Failed to set user context in Sentry: {e}")


def set_job_context(job: AIImprovementJob) -> None:
    """
    Set AI job context in Sentry for better error tracking.

    Args:
        job: The AIImprovementJob instance
    """
    try:
        set_context(
            "ai_job",
            {
                "job_id": str(job.id),
                "status": job.status.value if job.status else None,
                "lens": job.lens.value if job.lens else None,
                "mode": job.mode.value if job.mode else None,
                "thread_id": job.thread_id,
                "user_id": str(job.user_id),
                "created_at": str(job.created_at) if job.created_at else None,
                "updated_at": str(job.updated_at) if job.updated_at else None,
                "input_data_count": len(job.input_data) if job.input_data else 0,
                "has_messages": bool(job.messages),
                "error_message": (
                    job.error_message[:200] if job.error_message else None
                ),  # Truncate for readability
            },
        )

        # Set tags for filtering
        if job.status:
            set_tag("job_status", job.status.value)
        if job.lens:
            set_tag("job_lens", job.lens.value)
        if job.mode:
            set_tag("job_mode", job.mode.value)

    except Exception as e:
        logger.warning(f"Failed to set job context in Sentry: {e}")


def set_operation_context(
    operation_type: str,
    details: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    success: Optional[bool] = None,
) -> None:
    """
    Set operation context in Sentry for tracking specific operations.

    Args:
        operation_type: Type of operation (e.g., "ai_processing", "vault_lookup", "llm_call")
        details: Additional operation-specific details
        duration_ms: Operation duration in milliseconds
        success: Whether the operation was successful
    """
    try:
        context = {
            "operation_type": operation_type,
            "duration_ms": duration_ms,
            "success": success,
        }

        if details:
            context.update(details)

        set_context("operation", context)

        # Set tags
        set_tag("operation_type", operation_type)
        if success is not None:
            set_tag("operation_success", "true" if success else "false")

    except Exception as e:
        logger.warning(f"Failed to set operation context in Sentry: {e}")


def add_breadcrumb(
    message: str,
    category: str = "ai.processing",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add a breadcrumb to Sentry for tracking execution flow.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category for grouping
        level: Log level (info, warning, error, debug)
        data: Additional data to include
    """
    try:
        logger.info(
            f"Adding breadcrumb: {message} with category: {category} and level: {level} and data: {data}"
        )

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )
    except Exception as e:
        logger.warning(f"Failed to add breadcrumb to Sentry: {e}")


@contextmanager
def sentry_operation_tracking(
    operation_type: str,
    user: Optional[User] = None,
    job: Optional[AIImprovementJob] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for tracking operations with automatic timing and error capture.

    Args:
        operation_type: Type of operation being tracked
        user: Optional user context
        job: Optional job context
        details: Additional operation details

    Example:
        with sentry_operation_tracking("ai_processing", user=user, job=job):
            # Your operation code here
            result = process_ai_job(job)
    """
    start_time = time.time()

    try:
        # Set contexts
        if user:
            set_user_context(user)
        if job:
            set_job_context(job)

        add_breadcrumb(f"Starting {operation_type}", category="ai.operation")

        yield

        # Operation succeeded
        duration_ms = (time.time() - start_time) * 1000
        set_operation_context(operation_type, details, duration_ms, success=True)
        add_breadcrumb(
            f"Completed {operation_type}",
            category="ai.operation",
            data={"duration_ms": duration_ms},
        )

    except Exception as e:
        # Operation failed
        duration_ms = (time.time() - start_time) * 1000
        set_operation_context(operation_type, details, duration_ms, success=False)
        add_breadcrumb(
            f"Failed {operation_type}: {str(e)}",
            category="ai.operation",
            level="error",
            data={"duration_ms": duration_ms, "error": str(e)},
        )
        raise


def capture_ai_exception(
    exception: Exception,
    user: Optional[User] = None,
    job: Optional[AIImprovementJob] = None,
    operation_type: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Capture an exception with rich AI-specific context.

    Args:
        exception: The exception to capture
        user: Optional user context
        job: Optional job context
        operation_type: Type of operation that failed
        extra_context: Additional context to include
    """
    try:
        # Set contexts
        if user:
            set_user_context(user)
        if job:
            set_job_context(job)
        if operation_type:
            set_operation_context(operation_type, success=False)
        if extra_context:
            set_context("extra", extra_context)

        # Set error fingerprint for better grouping
        fingerprint = ["{{ default }}"]
        if operation_type:
            fingerprint.append(operation_type)
        if job and job.lens:
            fingerprint.append(job.lens.value)

        sentry_sdk.capture_exception(exception, fingerprint=fingerprint)

    except Exception as e:
        logger.warning(f"Failed to capture exception in Sentry: {e}")
        # Fallback to basic capture
        sentry_sdk.capture_exception(exception)


def track_ai_metrics(
    metric_name: str,
    value: Union[int, float],
    tags: Optional[Dict[str, str]] = None,
    unit: Optional[str] = None,
) -> None:
    """
    Track custom metrics for AI operations.

    Args:
        metric_name: Name of the metric
        value: Metric value
        tags: Additional tags for the metric
        unit: Unit of measurement
    """
    try:
        # Sentry metrics (if available in your plan)
        # This would be used with Sentry's custom metrics feature
        # For now, we'll log it and add as breadcrumb

        add_breadcrumb(
            f"Metric: {metric_name} = {value}",
            category="ai.metrics",
            data={
                "metric_name": metric_name,
                "value": value,
                "tags": tags,
                "unit": unit,
            },
        )

        logger.info(
            f"AI Metric - {metric_name}: {value} {unit or ''}",
            extra={
                "metric_name": metric_name,
                "metric_value": value,
                "metric_tags": tags,
                "metric_unit": unit,
            },
        )

    except Exception as e:
        logger.warning(f"Failed to track metric {metric_name}: {e}")
