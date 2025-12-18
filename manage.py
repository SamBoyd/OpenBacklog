#!/usr/bin/env python
"""
Management script for TaskManagement application.
Similar to Django's manage.py or Flask's CLI.
"""

import logging
import asyncclick
import sentry_sdk
from sqlalchemy import text
import stripe
import asyncio
import signal
import sys

from src.db import get_async_db, get_db
from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info("Starting TaskManagement CLI...")


def initialize_sentry():
    if settings.sentry_url != "":
        logging.info("Sentry URL is provided, initializing Sentry SDK")
        sentry_sdk.init(
            dsn=settings.sentry_url,
            send_default_pii=True,
        )


@asyncclick.group()
def cli():
    """TaskManagement CLI commands."""
    pass


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


@cli.command()
async def run_unified_background_worker():
    """Run usage tracker, monthly credits reset, and subscription cancellations in a unified background worker."""
    initialize_sentry()

    # Create component-specific loggers for clear identification
    main_logger = logging.getLogger("manage.unified_worker")
    usage_logger = logging.getLogger("manage.usage_tracker")
    credits_logger = logging.getLogger("manage.monthly_credits")
    cancellations_logger = logging.getLogger("manage.subscription_cancellations")

    main_logger.info("Starting unified background worker...")
    main_logger.info(
        "Components: usage tracker (60s), monthly credits reset (3600s), subscription cancellations (1800s)"
    )

    # Signal handler for graceful shutdown
    def handle_sigint(sig, frame):
        main_logger.info("Shutting down unified background worker")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        # Run all three services concurrently with appropriate intervals and component-specific loggers
        await asyncio.gather(
            usage_tracker_execute(dict(interval=60, single_run=False)),
            monthly_credits_reset_execute(
                interval=3600, component_logger=credits_logger
            ),
            subscription_cancellation_execute(
                interval=1800, component_logger=cancellations_logger
            ),
        )
    except KeyboardInterrupt:
        main_logger.info("Unified background worker stopped by user")
    except Exception as e:
        main_logger.error(f"Error running unified background worker: {e}")
        return 1

    return 0


if __name__ == "__main__":
    cli()
