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


# Add a custom page fixture that sets ignore_https_errors to True
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


def test_can_create_a_new_initiative_with_tasks(
    browser_page, onboard_test_user, disable_job_processor_service
):
    browser_page.get_by_test_id(CHAT__MESSAGE_TEXTBOX).fill("Create a todo list app")
    browser_page.get_by_test_id(CHAT__SEND_BUTTON).click()

    # Set up database connection to manually control job processing
    engine = create_engine(TEST_DATABASE_CONNECTION_STRING)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    try:
        # Wait for job to be created, then fetch the pending AIImprovementJob
        import time

        time.sleep(2)  # Give time for job creation

        pending_job = (
            db_session.query(AIImprovementJob)
            .filter(AIImprovementJob.status == JobStatus.PENDING)
            .first()
        )

        assert pending_job is not None, "No pending AI improvement job found"

        # Create mock result data structure
        mock_result_data = {
            "message": "I'll help you create a todo list app. Let me break this down into manageable tasks.",
            "managed_initiatives": [
                {
                    "action": "CREATE",
                    "title": "Todo List Application",
                    "description": "Create a simple todo list application with basic CRUD operations",
                    "tasks": [
                        {
                            "action": "CREATE",
                            "title": "Set up project structure",
                            "description": "Initialize the project with necessary files and folders",
                            "checklist": [
                                {"title": "Create HTML file", "is_complete": False},
                                {"title": "Create CSS file", "is_complete": False},
                                {
                                    "title": "Create JavaScript file",
                                    "is_complete": False,
                                },
                            ],
                        },
                        {
                            "action": "CREATE",
                            "title": "Implement todo functionality",
                            "description": "Add ability to create, read, update, and delete todos",
                            "checklist": [
                                {"title": "Add new todo form", "is_complete": False},
                                {"title": "Display todo list", "is_complete": False},
                                {
                                    "title": "Mark todos as complete",
                                    "is_complete": False,
                                },
                                {"title": "Delete todos", "is_complete": False},
                            ],
                        },
                    ],
                }
            ],
        }

        # Update the job with mock results
        pending_job.result_data = mock_result_data
        pending_job.status = JobStatus.COMPLETED
        db_session.commit()

        # Wait for frontend to receive and display results
        time.sleep(3)

        expect(browser_page.get_by_text("I'll help you create a todo")).to_be_visible()
        expect(browser_page.get_by_role("button", name="Reject All")).to_be_visible()
        expect(browser_page.get_by_role("button", name="Accept All")).to_be_visible()

        browser_page.get_by_role("button", name="Accept All").click()

        expect(browser_page.get_by_text("Create Accepted")).to_be_visible()
        expect(
            browser_page.get_by_test_id("suggestion-card-create-0-CREATE").get_by_role(
                "button"
            )
        ).to_be_visible()
        expect(browser_page.get_by_role("button", name="Rollback All")).to_be_visible()
        expect(browser_page.get_by_role("button", name="Save Changes")).to_be_visible()

        browser_page.get_by_role("button", name="Save Changes").click()

        expect(
            browser_page.get_by_role("button", name="Todo List Application I-")
        ).to_be_visible()
        browser_page.get_by_role("button", name="Todo List Application I-").click()

        expect(
            browser_page.get_by_role("button", name="TM-001 Set up project")
        ).to_be_visible()
        expect(
            browser_page.get_by_role("button", name="TM-002 Implement todo")
        ).to_be_visible()
    finally:
        db_session.close()

    browser_page.pause()
