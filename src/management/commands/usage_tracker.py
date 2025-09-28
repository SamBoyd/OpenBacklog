"""
Management command to synchronize user usage data using the accounting.UsageTracker service.

This command can be executed via the `manage.py` CLI the same way as other
commands (e.g. `python manage.py usage_tracker --interval 60 --single-run`).
It supports running either a single sync cycle or continuously at a given
interval, mirroring the behaviour of `process_jobs.py`.
"""

import asyncio
import logging
import signal
import sys
from typing import Any, Dict

from src.accounting.openmeter_service import OpenMeterService
from src.accounting.usage_tracker import UsageTracker
from src.config import settings
from src.db import SessionLocal
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)


def _build_usage_tracker() -> UsageTracker:
    """Construct and return a configured ``UsageTracker`` instance."""
    openmeter_service = OpenMeterService(
        base_url=settings.openmeter_base_url,
        api_token=settings.openmeter_api_token,
    )

    # ``SessionLocal`` is a SQLAlchemy ``sessionmaker`` exposed from ``src.db``
    return UsageTracker(openmeter_service=openmeter_service, db_session=SessionLocal)


def _handle_sigint(sig, frame):  # type: ignore[override]
    """Signal handler to ensure graceful shutdown."""
    logger.info("Shutting down usage tracker")
    sys.exit(0)


async def execute(
    args: Dict[str, Any]
) -> int:  # noqa: D401 – simple function description suffices
    """Entry-point invoked by the management CLI.

    Parameters
    ----------
    args: Dict[str, Any]
        Parsed CLI arguments forwarded by ``src.management.cli``. Supported keys:
        - ``interval`` (int, optional): Interval in seconds between sync cycles when
          running continuously. Defaults to 60.
        - ``single_run`` (bool, optional): If ``True`` only a single sync cycle is
          executed.

    Returns
    -------
    int
        Process exit code (0 for success, non-zero for error).
    """
    interval: int = int(args.get("interval", 60))
    single_run: bool = bool(args.get("single_run", False))

    # Start monitoring this usage tracker command execution
    add_breadcrumb(
        "Starting usage tracker command",
        category="usage_tracker.command",
        data={
            "interval": interval,
            "single_run": single_run,
        },
    )

    # Set operation context for this command execution
    set_operation_context(
        "usage_tracker_command",
        details={
            "interval": interval,
            "single_run": single_run,
            "command_type": "single_run" if single_run else "continuous",
        },
    )

    # Track command startup metrics
    track_ai_metrics(
        "usage_tracker.command.started",
        1,
        tags={
            "mode": "single_run" if single_run else "continuous",
            "interval": str(interval),
        },
    )

    logger.info(
        "Starting usage tracker – interval=%s, single_run=%s", interval, single_run
    )

    # Register signal handler for graceful shutdown (Ctrl-C)
    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        tracker = _build_usage_tracker()
        add_breadcrumb(
            "Usage tracker constructed successfully", category="usage_tracker.command"
        )

        if single_run:
            add_breadcrumb(
                "Executing single usage sync", category="usage_tracker.command"
            )
            tracker.sync_usage_once()
            track_ai_metrics("usage_tracker.command.single_run.completed", 1)
        else:
            add_breadcrumb(
                "Starting continuous usage tracking", category="usage_tracker.command"
            )
            # ``run_continuous`` is an *async* coroutine so we need an event loop.
            await tracker.run_continuous(interval_seconds=interval)

    except KeyboardInterrupt:
        logger.info("Usage tracker stopped by user")
        add_breadcrumb(
            "Usage tracker stopped by user interrupt",
            category="usage_tracker.command",
            level="info",
        )
        track_ai_metrics("usage_tracker.command.stopped_by_user", 1)
        set_operation_context(
            "usage_tracker_command", success=True
        )  # Graceful shutdown is success
    except Exception as exc:
        logger.exception("Unexpected error in usage tracker: %s", exc)
        add_breadcrumb(
            "Usage tracker command failed with unexpected error",
            category="usage_tracker.command",
            level="error",
            data={"error": str(exc), "error_type": type(exc).__name__},
        )

        # Capture the exception with operation context
        capture_ai_exception(
            exc,
            operation_type="usage_tracker_command",
            extra_context={
                "interval": interval,
                "single_run": single_run,
                "command_type": "single_run" if single_run else "continuous",
            },
        )

        track_ai_metrics(
            "usage_tracker.command.failed",
            1,
            tags={
                "error_type": type(exc).__name__,
                "mode": "single_run" if single_run else "continuous",
            },
        )

        set_operation_context("usage_tracker_command", success=False)
        return 1

    # Command completed successfully
    add_breadcrumb(
        "Usage tracker command completed successfully",
        category="usage_tracker.command",
    )
    track_ai_metrics("usage_tracker.command.completed", 1)
    set_operation_context("usage_tracker_command", success=True)
    return 0


def get_help() -> str:
    """Return the help text advertised by ``manage.py --list``."""
    return "Synchronize OpenMeter usage data and update user balances"
