from time import sleep
from hamcrest import assert_that, has_length
import pytest
from playwright.sync_api import expect, Page, Position, Locator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from src.controllers.initiative_controller import InitiativeController
from src.config import settings
from src.models import AIImprovementJob, Initiative, InitiativeStatus, JobStatus, User, Workspace

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

def test_can_reorder_initiative_list(
    browser_page: Page, onboard_test_user: None
):
    # Create a new initiative
    browser_page.get_by_test_id("open-button").click()
    browser_page.get_by_test_id("title-input").click()
    browser_page.get_by_test_id("title-input").fill("This is a new Initiative")
    browser_page.get_by_role("button", name="To do").click()
    browser_page.get_by_role("option", name="In progress").click()
    browser_page.get_by_test_id("expanded-form").click()
    browser_page.get_by_role("button", name="Select type").click()
    browser_page.get_by_role("option", name="Research").click()
    browser_page.get_by_test_id("create-button").click()

    # See the initiative created
    expect(browser_page.get_by_role("button", name="This is a new Initiative I-")).to_be_visible()

    # Inspect the initiative
    browser_page.get_by_role("button", name="This is a new Initiative I-").click()

    # Update the intiative
    browser_page.get_by_test_id("initiative-description-section").get_by_test_id("title-input").click()
    browser_page.get_by_test_id("initiative-description-section").get_by_test_id("title-input").fill("Let's update the description text\n\nWith some multiline text")
    browser_page.get_by_test_id("bottom-content").get_by_text("This is a new Initiative").click()
    browser_page.get_by_role("textbox", name="Title of your initiative").fill("This is a new Initiative - updated title")
    
    # Go back to kanban and check titles changed
    browser_page.get_by_test_id("navigation-button").click()
    expect(browser_page.get_by_role("button", name="This is a new Initiative - updated title")).to_be_visible()
    
    browser_page.get_by_role("button", name="This is a new Initiative - updated title").click()
    expect(browser_page.get_by_test_id("initiative-description-section").get_by_test_id("title-input")).to_have_text("Let's update the description text\n\nWith some multiline text")
    expect(browser_page.get_by_test_id("bottom-content").get_by_text("This is a new Initiative - updated title")).to_be_visible()

    # Create a task
    browser_page.get_by_test_id("open-button").click()
    browser_page.get_by_test_id("expanded-form").get_by_test_id("title-input").click()
    browser_page.get_by_test_id("expanded-form").get_by_test_id("title-input").fill("This is a test task")
    browser_page.get_by_role("button", name="To do").click()
    browser_page.get_by_role("option", name="In progress").click()
    browser_page.get_by_role("button", name="Select type").click()
    browser_page.get_by_test_id("type-select").get_by_role("option", name="Bugfix").click()
    browser_page.get_by_test_id("create-button").click()
    expect(browser_page.get_by_role("button", name="TM-001 This is a test task")).to_be_visible()

    # Navigate to task
    browser_page.get_by_role("button", name="TM-001 This is a test task").click()
    expect(browser_page.get_by_test_id("content").get_by_text("This is a test task")).to_be_visible()
    expect(browser_page.get_by_role("button", name="IN_PROGRESS")).to_be_visible()
    expect(browser_page.get_by_role("button", name="BUGFIX")).to_be_visible()

    # Update task
    browser_page.get_by_test_id("title-input").click()
    browser_page.get_by_test_id("title-input").fill("Let's update the task description")
    browser_page.get_by_test_id("content").get_by_text("This is a test task").click()
    browser_page.get_by_role("textbox", name="Title of your task").fill("This is a test task - updated title")

    # Go back and check the list in the initiative view
    browser_page.get_by_test_id("navigation-button").click()
    expect(browser_page.get_by_role("button", name="This is a test task - updated title")).to_be_visible()

    # Navigate to task and check the values there
    browser_page.get_by_role("button", name="This is a test task - updated title").click()
    expect(browser_page.get_by_test_id("content").get_by_text("This is a test task - updated title")).to_be_visible()
    expect(browser_page.get_by_test_id("title-input")).to_have_text("Let's update the task description")

    # Delete task
    browser_page.get_by_test_id("more-menu-button").click()
    browser_page.get_by_test_id("confirm-delete").click()
    expect(browser_page.get_by_text("You currently don't have any")).to_be_visible()

    # Delete initiative
    browser_page.get_by_test_id("more-menu-button").click()
    browser_page.get_by_test_id("confirm-delete").click()
    expect(browser_page.get_by_role("button", name="This is a new Initiative - updated title")).not_to_be_visible()
