import datetime
import json
import logging
import os
import random
import sys
import uuid  # Add uuid import
from time import sleep
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session  # Add Session import
from sqlalchemy.schema import DropTable
from playwright.sync_api import expect

from alembic import command
from alembic.config import Config
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.config import settings
from src.db import Base, SessionLocal, get_db
from src.main import app, auth_module

CHAT__MESSAGE_TEXTBOX = "chat-textbox"
CHAT__MODE_SELECT = "chat-mode"
CHAT__SEND_BUTTON = "chat-send"


def pytest_configure_node(node: pytest.Config) -> None:
    """Configure pytest node with worker-specific settings for parallel execution."""
    worker_id = os.environ.get("WORKER_ID")
    if worker_id:
        logger = logging.getLogger(f"test_worker_{worker_id}")
        logger.info(f"Configuring pytest node for worker {worker_id}")

        # Ensure the database is properly configured for this worker
        database_name = f"taskmanager_test_db_{int(worker_id):02d}"
        os.environ["DATABASE_NAME"] = database_name

        # Re-import settings to get updated database URLs
        from src.config import settings

        logger.info(f"Worker {worker_id} using database: {settings.database_name}")
        logger.info(f"Worker {worker_id} database URL: {settings.database_url}")


# Add necessary model imports
from src.models import (
    APIProvider,
    Initiative,
    Task,
    User,
    UserKey,
    Workspace,
)
from src.views import dependency_to_override

logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.database_url, echo=False)


@pytest.fixture(scope="function")
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user(session: Session):  # Add type hint
    existing_user = (
        session.query(User).filter(User.email == settings.dev_user_email).first()
    )
    if existing_user:
        yield existing_user
    else:
        raise Exception(
            "Cannot get test user, run the reset test user management command: ./manage.py reset-test-user"
        )


@pytest.fixture
def workspace(session: Session, user: User):  # Add type hints
    from src.models import Workspace  # Keep import local if preferred

    existing_workspace = session.query(Workspace).first()
    if existing_workspace:
        # If workspace exists from a previous failed test run cleanup, use it
        yield existing_workspace
        return

    # Otherwise, create a new one
    workspace = Workspace(
        name="Test Workspace",
        description="Test description",
        icon="test_icon.png",
        user_id=user.id,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    yield workspace
    # Cleanup handled by clean_tables
    session.delete(workspace)
    session.commit()


# --- Additions for E2E AI tests ---


@pytest.fixture(scope="function")
def test_initiative(
    session: Session, user: User, workspace: Workspace
) -> Generator[Initiative, None, None]:
    """Creates a test initiative for use in tests."""
    initiative = Initiative(
        title="Original Initiative Title E2E",
        description="This is the initial description for E2E testing.",
        user_id=user.id,
        workspace_id=workspace.id,
        identifier="E2E-INIT-"
        + random.choice(
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        ),  # Unique identifier
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    yield initiative
    session.delete(initiative)
    session.commit()
    # Cleanup handled by clean_tables


@pytest.fixture(scope="function")
def test_task(
    session: Session, user: User, test_initiative: Initiative, workspace: Workspace
) -> Generator[Task, None, None]:
    """Creates a test task for use in tests."""
    task = Task(
        title="Test Task E2E",
        description="This is the initial description for E2E testing.",
        user_id=user.id,
        initiative_id=test_initiative.id,
        identifier="E2E-TASK-"
        + random.choice(
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        ),  # Unique identifier
        workspace_id=workspace.id,
    )

    test_initiative.tasks.append(task)
    session.add(test_initiative)
    session.add(task)
    session.commit()
    session.refresh(task)
    yield task
    session.delete(task)
    session.commit()


@pytest.fixture(scope="session")
def openai_api_key() -> str:
    """Retrieves the OpenAI API key from environment variable for E2E tests."""
    key = os.getenv("TEST_OPENAI_API_KEY")
    if not key:
        pytest.skip(
            "TEST_OPENAI_API_KEY environment variable not set. Skipping E2E test."
        )
    # Basic validation (optional but good)
    if not key.startswith("sk-"):
        pytest.skip(
            "TEST_OPENAI_API_KEY does not look like a valid OpenAI key. Skipping E2E test."
        )
    return key


@pytest.fixture(scope="function")
def test_user_key(
    session: Session, user: User, openai_api_key: str
) -> Generator[UserKey, None, None]:
    """
    Creates a UserKey entry for the test user for OpenAI, marking it as valid.
    Ensures only one valid key exists per user/provider for the test.
    """
    # Check if a key already exists for this user/provider
    existing_key = (
        session.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENAI)
        .first()
    )

    if existing_key:
        # Update existing key to be valid for the test if needed
        existing_key.is_valid = True
        existing_key.last_validated_at = datetime.datetime.now()
        session.commit()
        session.refresh(existing_key)
        yield existing_key
    else:
        # Create a new key
        redacted = (
            f"sk-...{openai_api_key[-4:]}" if len(openai_api_key) > 8 else "sk-..."
        )
        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENAI,
            redacted_key=redacted,
            is_valid=True,
            last_validated_at=datetime.datetime.now(),
        )
        session.add(user_key)
        session.commit()
        session.refresh(user_key)
        yield user_key
    # Cleanup handled by clean_tables


# --- End Additions ---


@pytest.fixture
def test_client(user):
    app.dependency_overrides[dependency_to_override] = lambda: user
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(dependency_to_override, None)


@pytest.fixture
def test_client_no_user():
    client = TestClient(app)
    yield client


@pytest.fixture(autouse=True)
def clean_tables(session: Session):  # Use session fixture for cleanup

    # list all tables in the database
    tables = session.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'dev'"
        )
    )
    for table in tables:

        session.execute(text(f"DELETE FROM dev.{table[0]} CASCADE"))

    tables = session.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'private'"
        )
    )
    for table in tables:
        session.execute(text(f"DELETE FROM private.{table[0]} CASCADE"))

    # Add other tables as needed, ensuring correct cascade or order
    session.commit()


# Add fixture to temporarily modify sys.argv for CLI tests
@pytest.fixture
def cli_args():
    """
    Fixture to temporarily change sys.argv for CLI testing.

    Example:
        def test_something(cli_args):
            with cli_args(["manage.py", "some_command", "--option"]):
                # Test code that reads from sys.argv
                pass
    """
    original_argv = sys.argv.copy()

    def _set_args(new_args):
        sys.argv = new_args
        return sys.argv

    yield _set_args

    # Restore original argv
    sys.argv = original_argv


# Add fixture to simulate running from command line
@pytest.fixture
def run_cli_command():
    """
    Fixture to simulate running a management command.

    Returns a function that takes command arguments and returns the exit code.

    Example:
        def test_command(run_cli_command):
            result = run_cli_command(["process_jobs", "--single-run"])
            assert result == 0
    """
    from src.management.cli import main

    def _run_command(args):
        with patch("sys.argv", ["manage.py"] + args):
            return main()

    return _run_command


@pytest.fixture(autouse=True)
def mock_litellm_model_cost():
    """
    Fixture to mock litellm.model_cost with example pricing data.

    This prevents litellm from making actual API calls during tests and provides
    consistent pricing data for cost estimation tests.
    """
    try:
        # Try to load the bundled example costs file
        import litellm

        example_costs_path = os.path.join(
            os.path.dirname(litellm.__file__),
            "model_prices_and_context_window_backup.json",
        )

        if os.path.exists(example_costs_path):
            with open(example_costs_path, "r") as f:
                example_costs = json.load(f)
        else:
            # Fallback to a minimal set of test costs if the file doesn't exist
            example_costs = {
                "gpt-4": {
                    "input_cost_per_token": 0.03,
                    "output_cost_per_token": 0.06,
                    "max_tokens": 8192,
                    "litellm_provider": "openai",
                },
                "gpt-4.1-nano": {
                    "input_cost_per_token": 0.001,
                    "output_cost_per_token": 0.002,
                    "max_tokens": 4096,
                    "litellm_provider": "openai",
                },
                "gpt-3.5-turbo": {
                    "input_cost_per_token": 0.0015,
                    "output_cost_per_token": 0.002,
                    "max_tokens": 4096,
                    "litellm_provider": "openai",
                },
            }

        with patch("litellm.model_cost", example_costs):
            yield example_costs

    except Exception as e:
        # If anything goes wrong, provide a minimal fallback
        fallback_costs = {
            "gpt-4.1-nano": {
                "input_cost_per_token": 0.001,
                "output_cost_per_token": 0.002,
                "max_tokens": 4096,
                "litellm_provider": "openai",
            }
        }
        with patch("litellm.model_cost", fallback_costs):
            yield fallback_costs


@pytest.fixture
def onboard_test_user(browser_page):
    browser_page.goto("http://localhost/")
    expect(browser_page.get_by_text("OpenBacklog")).to_be_visible()
    browser_page.get_by_text("Sign in").click()
    expect(
        browser_page.get_by_role("heading", name="Plan Your Projects")
    ).to_be_visible(timeout=10_000)
    browser_page.get_by_role("button", name="Next").click()

    expect(
        browser_page.get_by_role("heading", name="AI Coding Assistants")
    ).to_be_visible()
    browser_page.get_by_role("button", name="Next").click()

    expect(
        browser_page.get_by_role("heading", name="Context-Aware Development")
    ).to_be_visible()
    browser_page.get_by_role("button", name="Next").click()

    expect(
        browser_page.get_by_role("heading", name="What's your project name?")
    ).to_be_visible()
    browser_page.get_by_role("textbox", name="Project Name").click()
    browser_page.get_by_role("textbox", name="Project Name").fill("TaskManagement")
    browser_page.get_by_role("button", name="Next").click()

    expect(
        browser_page.get_by_role("heading", name="Simple Usage-Based Pricing")
    ).to_be_visible()
    expect(browser_page.get_by_text('Your "TaskManagement"')).to_be_visible()
    browser_page.get_by_role("button", name="Continue with Free Trial").click()

    expect(browser_page.get_by_test_id(CHAT__MESSAGE_TEXTBOX)).to_be_visible()
