#!/usr/bin/env python
"""
Management script for TaskManagement application.
Similar to Django's manage.py or Flask's CLI.
"""

import logging
import asyncclick
from sqlalchemy import text
import stripe
import asyncio
import signal
import sys

from src.accounting.openmeter_service import OpenMeterService
from src.db import get_async_db, get_db
from src.management.commands.process_jobs import execute as background_jobs_execute
from src.management.commands.usage_tracker import execute as usage_tracker_execute
from src.litellm_service import (
    regenerate_litellm_master_key as regenerate_litellm_master_key_command,
    retrieve_litellm_key_for_user,
)
from src.litellm_service import (
    retrieve_litellm_master_key as retrieve_litellm_master_key_command,
)

from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info("Starting TaskManagement CLI...")


@asyncclick.group()
def cli():
    """TaskManagement CLI commands."""
    pass


@cli.command()
@asyncclick.option(
    "--interval", default=10, help="Interval in seconds between job checks."
)
@asyncclick.option(
    "--single-run", is_flag=True, help="Run the job processor once and exit."
)
async def process_jobs(interval, single_run):
    """Run the background service."""
    await background_jobs_execute(interval, single_run)


@cli.command()
@asyncclick.option(
    "--interval", default=10, help="Interval in seconds between job checks."
)
@asyncclick.option(
    "--single-run", is_flag=True, help="Run the job processor once and exit."
)
async def usage_tracker(interval, single_run):
    """Run the usage tracker."""
    await usage_tracker_execute(dict(interval=interval, single_run=single_run))


@cli.command()
async def preprod_run_both_background_jobs_and_usage_tracker():
    """Run both background jobs processor and usage tracker concurrently for preprod environment."""
    import asyncio
    import signal
    import sys

    logger.info("Starting both background jobs processor and usage tracker...")

    # Signal handler for graceful shutdown
    def handle_sigint(sig, frame):
        logger.info("Shutting down both services")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        # Run both services concurrently with default intervals
        await asyncio.gather(
            background_jobs_execute(interval=10, single_run=False),
            usage_tracker_execute(dict(interval=60, single_run=False)),
        )
    except KeyboardInterrupt:
        logger.info("Services stopped by user")
    except Exception as e:
        logger.error(f"Error running concurrent services: {e}")
        return 1

    return 0


@cli.command()
def regenerate_litellm_master_key():
    """Regenerate the LiteLLM master key."""
    logger.info("Regenerating LiteLLM master key...")
    new_key = regenerate_litellm_master_key_command()
    logger.info(f"LiteLLM master key regenerated successfully. New key: {new_key}")


@cli.command()
def get_litellm_master_key():
    """Get the LiteLLM master key."""
    logger.info("Getting LiteLLM master key...")
    key = retrieve_litellm_master_key_command()
    logger.info(f"LiteLLM master key: {key}")


@cli.command()
def get_litellm_key_for_dev_user():
    """Get the LiteLLM key for a user."""
    logger.info(f"Getting LiteLLM key for the dev user...")
    db = next(get_db())
    user = db.query(User).filter(User.email == settings.dev_user_email).first()
    if not user:
        logger.error(f"Dev user not found with email: {settings.dev_user_email}")
        return

    key = retrieve_litellm_key_for_user(user, db)
    logger.info(f"Dev user: {user.id}")
    logger.info(f"LiteLLM key: {key}")


@cli.command()
@asyncclick.option("--user-id", help="User ID to revoke tokens for.")
@asyncclick.option("--email", help="Email of the user to revoke tokens for.")
async def revoke_user_tokens(user_id: str = None, email: str = None):
    """Revoke all tokens for a user."""
    if not user_id and not email:
        logger.error("Either --user-id or --email must be provided")
        return

    if user_id and email:
        logger.error("Provide either --user-id or --email, not both")
        return

    try:
        from src.auth.factory import get_auth_provider
        from sqlalchemy import select
        import uuid

        async for db in get_async_db():
            user = None

            if user_id:
                # Look up by user ID
                try:
                    user_uuid = uuid.UUID(user_id)
                    user = await db.get(User, user_uuid)
                except ValueError:
                    logger.error(f"Invalid user ID format: {user_id}")
                    return
            else:
                # Look up by email
                result = await db.execute(
                    select(User).filter(User.email == email.lower())
                )
                user = result.scalar_one_or_none()

            if not user:
                identifier = user_id if user_id else email
                logger.error(f"User not found: {identifier}")
                return

            # Get auth provider and revoke tokens
            provider = get_auth_provider()
            await provider._revoke_tokens_for_user(str(user.id))

            logger.info(
                f"Successfully revoked all tokens for user: {user.email} (ID: {user.id})"
            )
            break

    except Exception as e:
        logger.error(f"Failed to revoke tokens: {e}")


@cli.command()
@asyncclick.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="List overdue cancellations without processing (default).",
)
@asyncclick.option(
    "--limit", type=int, help="Maximum number of subscriptions to process."
)
@asyncclick.option("--user-id", help="Process specific user ID only.")
async def list_overdue_subscription_cancellations(dry_run, limit, user_id):
    """List and optionally process overdue subscription cancellations."""
    from src.accounting.accounting_controller import (
        get_overdue_subscription_cancellations,
        process_overdue_subscription_cancellation,
    )
    from src.models import User
    import uuid

    if dry_run:
        logger.info("Running in dry run mode")

    session = next(get_db())

    try:
        # Get overdue cancellations
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                user = session.get(User, user_uuid)
                if not user:
                    logger.error(f"User not found: {user_id}")
                    return

                # Check if this user is overdue
                overdue_users = get_overdue_subscription_cancellations(session)
                if user not in overdue_users:
                    logger.info(
                        f"User {user_id} does not have overdue subscription cancellation"
                    )
                    return
                overdue_users = [user]
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                return
        else:
            overdue_users = get_overdue_subscription_cancellations(session, limit=limit)

        if not overdue_users:
            logger.info("No overdue subscription cancellations found")
            return

        logger.info(
            f"Found {len(overdue_users)} overdue subscription cancellation{'s' if len(overdue_users) != 1 else ''}"
        )
        logger.info("")
        logger.info(
            "┌─────────────────────┬──────────────────────────────┬─────────────────────┬─────────────────────┐"
        )
        logger.info(
            "│ User ID             │ Email                        │ Cancel At           │ Status              │"
        )
        logger.info(
            "├─────────────────────┼──────────────────────────────┼─────────────────────┼─────────────────────┤"
        )

        for user in overdue_users:
            cancel_at = user.account_details.subscription_cancel_at
            cancel_at_str = cancel_at.strftime("%Y-%m-%d %H:%M") if cancel_at else "N/A"

            logger.info(
                f"│ {str(user.id)[:19]:<19} │ {user.email[:28]:<28} │ {cancel_at_str:<19} │ {user.account_details.status.value:<19} │"
            )

        logger.info(
            "└─────────────────────┴──────────────────────────────┴─────────────────────┴─────────────────────┘"
        )
        logger.info("")

        if dry_run:
            logger.info(
                "DRY RUN: stopping here... remove --dry-run to process these cancellations"
            )
            return

        # Process cancellations
        logger.info("Processing overdue subscription cancellations...")
        processed_count = 0
        failed_count = 0

        for user in overdue_users:
            logger.info(f"Processing user {user.id} ({user.email})...")

            try:
                result = process_overdue_subscription_cancellation(user, session)

                if result.success:
                    processed_count += 1
                    logger.info(
                        f"✓ Successfully cancelled subscription for {user.email}: "
                        f"refunded ${result.total_refunded_cents / 100:.2f}"
                    )
                else:
                    failed_count += 1
                    logger.error(
                        f"✗ Failed to cancel subscription for {user.email}: {result.error}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Unexpected error processing {user.email}: {e}")

        logger.info("")
        logger.info(
            f"Processing complete: {processed_count} successful, {failed_count} failed"
        )

    except Exception as e:
        logger.error(f"Error processing overdue subscription cancellations: {e}")
    finally:
        session.close()


@cli.command()
async def create_test_user():
    """Create a test user."""
    from src.main import app
    from src.auth.auth_module import initialize_auth
    from src.auth.factory import get_provider_type

    email = settings.dev_user_email

    auth_module = initialize_auth(app)
    provider_type = get_provider_type()

    if provider_type != "dev":
        logger.error("Can only create test user for the dev auth provider")

    session = next(get_db())
    existing = session.query(User).filter(User.email == email.lower()).first()
    if existing:
        logger.info(
            "Test user already exists. To reset test user, run manage.py reset-test-user"
        )
        return

    user = await auth_module.provider._get_or_create_dev_user(email)  # type: ignore
    logger.info(f"Test user successfully reset. Email: {user.email}")


@cli.command()
@asyncclick.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="List users due for credit reset without processing (default).",
)
@asyncclick.option(
    "--limit", type=int, help="Maximum number of users to process."
)
@asyncclick.option("--user-id", help="Process specific user ID only.")
async def reset_monthly_credits(dry_run, limit, user_id):
    """Reset monthly credits for users whose billing cycle has expired."""
    from src.accounting.accounting_controller import (
        get_users_due_for_credit_reset,
        process_billing_cycle_reset,
    )
    import uuid

    if dry_run:
        logger.info("Running in dry run mode (use --no-dry-run to execute)")

    session = next(get_db())
    
    try:
        # Get users due for credit reset using controller function
        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                return

        eligible_users = get_users_due_for_credit_reset(session, limit=limit, user_id=user_uuid)

        if not eligible_users:
            if user_id:
                logger.info(f"User {user_id} is not due for monthly credit reset or not found")
            else:
                logger.info("No users found due for monthly credit reset")
            return

        logger.info(
            f"Found {len(eligible_users)} user{'s' if len(eligible_users) != 1 else ''} due for monthly credit reset"
        )
        logger.info("")
        logger.info(
            "┌─────────────────────┬──────────────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐"
        )
        logger.info(
            "│ User ID             │ Email                        │ Status              │ Next Cycle Due      │ Credits Used        │"
        )
        logger.info(
            "├─────────────────────┼──────────────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤"
        )

        for user in eligible_users:
            account_details = user.account_details
            next_cycle_str = account_details.next_billing_cycle_starts.strftime("%Y-%m-%d %H:%M") if account_details.next_billing_cycle_starts else "N/A"
            credits_used_str = f"{account_details.monthly_credits_used}/{account_details.monthly_credits_total}"

            logger.info(
                f"│ {str(user.id)[:19]:<19} │ {user.email[:28]:<28} │ {account_details.status.value[:19]:<19} │ {next_cycle_str:<19} │ {credits_used_str:<19} │"
            )

        logger.info(
            "└─────────────────────┴──────────────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘"
        )
        logger.info("")

        if dry_run:
            logger.info(
                "DRY RUN: Use --no-dry-run to reset monthly credits for these users"
            )
            return

        # Process monthly credit resets using controller function
        logger.info("Processing monthly credit resets...")
        processed_count = 0
        failed_count = 0

        for user in eligible_users:
            logger.info(f"Processing user {user.id} ({user.email})...")

            result = process_billing_cycle_reset(user, session)
            
            if result.success:
                processed_count += 1
                logger.info(f"✓ Successfully reset monthly credits for {user.email}")
            else:
                failed_count += 1
                logger.error(f"✗ Failed to reset credits for {user.email}: {result.error}")

        logger.info("")
        logger.info(
            f"Processing complete: {processed_count} successful, {failed_count} failed"
        )

    except Exception as e:
        logger.error(f"Error processing monthly credit resets: {e}")
    finally:
        session.close()


@cli.command()
async def reset_test_user():
    """Reset the test user."""
    email = settings.dev_user_email
    from src.auth.auth_module import initialize_auth
    from src.auth.factory import get_provider_type
    from src.main import app

    auth_module = initialize_auth(app)
    provider_type = get_provider_type()

    if provider_type != "dev":
        logger.error("Can only create test user for the dev auth provider")

    session = next(get_db())
    existing = session.query(User).filter(User.email == email.lower()).first()
    if existing:
        logger.info("Deleting existing user")
        session.execute(
            text("DELETE FROM dev.checklist WHERE user_id = :user_id"),
            {"user_id": existing.id},
        )
        session.execute(
            text("DELETE FROM dev.task WHERE user_id = :user_id"),
            {"user_id": existing.id},
        )
        session.execute(
            text("DELETE FROM dev.initiative WHERE user_id = :user_id"),
            {"user_id": existing.id},
        )
        session.delete(existing)
        session.commit()

    customer_query = stripe.Customer.search(query=f"email:'{email}'")
    existing_customers = customer_query.data
    if len(existing_customers) == 1:
        customer = existing_customers[0]
        logger.info(f"found existing stripe customer {customer['id']}")
        try:
            stripe.Customer.delete(customer["id"])
        except Exception as e:
            logger.error(f"Failed to delete stripe customer {customer['id']}: {e}")
    elif len(existing_customers) > 1:
        raise Exception("Too many stripe customers returned")
    else:
        logger.info(f"no found existing stripe customer")

    logger.info("Deleting existing OpenMeter customer")
    openmeter_service = OpenMeterService(
        base_url=settings.openmeter_base_url,
        api_token=settings.openmeter_api_token,
    )

    try:
        customers = openmeter_service.find_customers_by_name("Dev User")
        if customers["totalCount"] > 0:
            for customer in customers["items"]:
                subject_id = customer["usageAttribution"]["subjectKeys"][0]
                logger.info(
                    f"found existing OpenMeter customer {customer['id']} and subject {subject_id}"
                )
                openmeter_service.delete_customer(customer["id"])
                try:
                    openmeter_service.delete_subject(subject_id)
                except Exception as e:
                    logger.error(f"Failed to delete OpenMeter subject: {e}")
    except Exception as e:
        logger.error(f"Failed to delete OpenMeter customer: {e}")

    user = await auth_module.provider._get_or_create_dev_user(email)  # type: ignore
    logger.info(f"Test user successfully reset. Email: {user.email}")


async def _run_monthly_credits_reset_continuously(interval: int = 3600, component_logger = None):
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
    worker_logger.info(f"Starting monthly credits reset worker (interval: {interval}s)")
    
    while True:
        try:
            session = next(get_db())
            try:
                # Get users due for credit reset
                eligible_users = get_users_due_for_credit_reset(session)
                
                if eligible_users:
                    worker_logger.info(f"Processing monthly credit reset for {len(eligible_users)} users")
                    processed_count = 0
                    failed_count = 0
                    
                    for user in eligible_users:
                        try:
                            result = process_billing_cycle_reset(user, session)
                            if result.success:
                                processed_count += 1
                                worker_logger.info(f"✓ Reset monthly credits for {user.email}")
                            else:
                                failed_count += 1
                                worker_logger.error(f"✗ Failed to reset credits for {user.email}: {result.error}")
                        except Exception as e:
                            failed_count += 1
                            worker_logger.error(f"✗ Unexpected error processing {user.email}: {e}")
                    
                    worker_logger.info(f"Monthly credits reset complete: {processed_count} successful, {failed_count} failed")
                else:
                    worker_logger.debug("No users found due for monthly credit reset")
                    
            finally:
                session.close()
                
        except Exception as e:
            worker_logger.error(f"Error in monthly credits reset worker: {e}")
        
        # Wait for next interval
        await asyncio.sleep(interval)


async def _run_subscription_cancellations_continuously(interval: int = 1800, component_logger = None):
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
    worker_logger.info(f"Starting subscription cancellations worker (interval: {interval}s)")
    
    while True:
        try:
            session = next(get_db())
            try:
                # Get users with overdue cancellations
                overdue_users = get_overdue_subscription_cancellations(session)
                
                if overdue_users:
                    worker_logger.info(f"Processing overdue subscription cancellations for {len(overdue_users)} users")
                    processed_count = 0
                    failed_count = 0
                    
                    for user in overdue_users:
                        try:
                            result = process_overdue_subscription_cancellation(user, session)
                            if result.success:
                                processed_count += 1
                                worker_logger.info(f"✓ Cancelled subscription for {user.email}: refunded ${result.total_refunded_cents / 100:.2f}")
                            else:
                                failed_count += 1
                                worker_logger.error(f"✗ Failed to cancel subscription for {user.email}: {result.error}")
                        except Exception as e:
                            failed_count += 1
                            worker_logger.error(f"✗ Unexpected error processing {user.email}: {e}")
                    
                    worker_logger.info(f"Subscription cancellations complete: {processed_count} successful, {failed_count} failed")
                else:
                    worker_logger.debug("No overdue subscription cancellations found")
                    
            finally:
                session.close()
                
        except Exception as e:
            worker_logger.error(f"Error in subscription cancellations worker: {e}")
        
        # Wait for next interval
        await asyncio.sleep(interval)


@cli.command()
async def run_unified_background_worker():
    """Run usage tracker, monthly credits reset, and subscription cancellations in a unified background worker."""
    
    # Create component-specific loggers for clear identification
    main_logger = logging.getLogger("manage.unified_worker")
    usage_logger = logging.getLogger("manage.usage_tracker")
    credits_logger = logging.getLogger("manage.monthly_credits")
    cancellations_logger = logging.getLogger("manage.subscription_cancellations")
    
    main_logger.info("Starting unified background worker...")
    main_logger.info("Components: usage tracker (60s), monthly credits reset (3600s), subscription cancellations (1800s)")

    # Signal handler for graceful shutdown
    def handle_sigint(sig, frame):
        main_logger.info("Shutting down unified background worker")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        # Run all three services concurrently with appropriate intervals and component-specific loggers
        await asyncio.gather(
            usage_tracker_execute(dict(interval=60, single_run=False)),
            _run_monthly_credits_reset_continuously(interval=3600, component_logger=credits_logger),
            _run_subscription_cancellations_continuously(interval=1800, component_logger=cancellations_logger),
        )
    except KeyboardInterrupt:
        main_logger.info("Unified background worker stopped by user")
    except Exception as e:
        main_logger.error(f"Error running unified background worker: {e}")
        return 1

    return 0


if __name__ == "__main__":
    cli()
