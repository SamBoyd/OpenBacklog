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

    logger.info(
        "Starting usage tracker – interval=%s, single_run=%s", interval, single_run
    )

    # Register signal handler for graceful shutdown (Ctrl-C)
    signal.signal(signal.SIGINT, _handle_sigint)

    tracker = _build_usage_tracker()

    try:
        if single_run:
            tracker.sync_usage_once()
        else:
            # ``run_continuous`` is an *async* coroutine so we need an event loop.
            await tracker.run_continuous(interval_seconds=interval)

    except KeyboardInterrupt:
        logger.info("Usage tracker stopped by user")
    except Exception as exc:
        logger.exception("Unexpected error in usage tracker: %s", exc)
        return 1

    return 0


def get_help() -> str:
    """Return the help text advertised by ``manage.py --list``."""
    return "Synchronize OpenMeter usage data and update user balances"
