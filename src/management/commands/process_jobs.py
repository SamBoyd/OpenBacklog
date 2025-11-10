"""
Command to process pending AI improvement jobs.
"""

import logging
import signal
import sys
import time

from src.background_service import (
    cancel_users_previous_jobs_and_get_last,
    get_next_pending_job,
    process_job,
)
from src.db import get_db
from src.secrets import get_vault

logger = logging.getLogger(__name__)


async def execute(interval: int, single_run: bool) -> int:
    """
    Execute the job processing command.

    Args:
        args: Command arguments (optional)
    """
    logger.info("Starting job processor...")

    # Register signal handler for graceful shutdown
    def handle_sigint(sig, frame):
        logger.info("Shutting down job processor")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    vault = get_vault()

    try:
        while True:
            # Get database session
            db = next(get_db())

            try:
                # Process one job
                job = get_next_pending_job(db)
                if job:
                    most_recent_job_for_user = cancel_users_previous_jobs_and_get_last(db, job.user_id)  # type: ignore
                    await process_job(most_recent_job_for_user, db)
                    logger.info(f"Successfully processed job {job.id}")
                else:
                    logger.debug("No pending jobs found")
            except Exception as e:
                logger.exception(f"Error in job processor: {str(e)}")
            finally:
                db.close()

            # Exit if single run mode
            if single_run:
                break

            # Sleep before next iteration
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Job processor stopped by user")
    except Exception as e:
        logger.exception(f"Unexpected error in job processor: {str(e)}")
        return 1

    return 0


def get_help() -> str:
    """Return help text for this command."""
    return "Process pending AI improvement jobs from the queue"
