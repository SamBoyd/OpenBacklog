import pytest
from playwright.sync_api import expect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings
from src.models import AIImprovementJob, JobStatus

TEST_DATABASE_CONNECTION_STRING = (
    "postgresql://taskmanager_user:securepassword123@localhost:5433/taskmanager_db"
)

BASE_URL = "http://localhost"

CHAT__MESSAGE_TEXTBOX = "chat-textbox"
CHAT__MODE_SELECT = "chat-mode"
CHAT__SEND_BUTTON = "chat-send"


@pytest.fixture
def reset_test_user():
    import subprocess

    cmd = "docker exec -it fastapi ./manage.py reset-test-user"
    subprocess.run(cmd, shell=True, check=True)


@pytest.fixture(scope="function")
def browser_page(reset_test_user, browser):  # type: ignore
    context = browser.new_context(
        ignore_https_errors=True,
        # Use incognito mode to isolate sessions
        storage_state=None,
        viewport={"width": 1280, "height": 1020},
    )
    page = context.new_page()
    # Clear any existing cookies
    context.clear_cookies()
    yield page
    context.close()


@pytest.fixture
def disable_job_processor_service():
    import subprocess

    subprocess.run(
        "docker compose -f docker/docker-compose.yml --env-file .env down job_processor",
        shell=True,
        check=True,
    )

    yield

    subprocess.run(
        "docker compose -f docker/docker-compose.yml --env-file .env up -d job_processor",
        shell=True,
        check=True,
    )

