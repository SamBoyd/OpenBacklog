"""
Sentry context helpers for enhanced AI usage monitoring.

This module provides utilities to set structured context in Sentry for better
error tracking, debugging, and monitoring of the AI job processing system.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union

import sentry_sdk
from sentry_sdk import set_context, set_tag, set_user

from src.models import User

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

        if hasattr(user, "account_details") and user.account_details:
            account_status = (
                user.account_details.status.value
                if user.account_details.status
                else None
            )

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

    except Exception as e:
        logger.warning(f"Failed to set user context in Sentry: {e}")


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
        if operation_type:
            set_operation_context(operation_type, success=False)
        if extra_context:
            set_context("extra", extra_context)

        # Set error fingerprint for better grouping
        fingerprint = ["{{ default }}"]
        if operation_type:
            fingerprint.append(operation_type)

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
