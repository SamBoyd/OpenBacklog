import re
from time import sleep
import pytest
from playwright.sync_api import expect, Page


from src.controllers.task_controller import TaskController
from src.controllers.initiative_controller import InitiativeController
from src.models import Group, GroupType, InitiativeStatus, Task, TaskStatus, User, Workspace

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
    browser_page: Page, onboard_test_user, user: User, workspace: Workspace, session
):
    controller = InitiativeController(session)
    test_initiative_1 = controller.create_initiative(
        title="Test Initiative 1",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )
    test_initiative_2 = controller.create_initiative(
        title="Test Initiative 2",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )
    test_initiative_3 = controller.create_initiative(
        title="Test Initiative 3",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )

    sleep(0.5)
    browser_page.reload()

    expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_count(3)
    expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_text([
        'Test Initiative 1I-001',
        'Test Initiative 2I-002',
        'Test Initiative 3I-003'
    ])

    # Playwright notes
    # If your page relies on the dragover event being dispatched, you need at least two mouse moves 
    # to trigger it in all browsers. To reliably issue the second mouse move, repeat your mouse.move() 
    # or locator.hover() twice. The sequence of operations would be: hover the drag element, mouse 
    # down, hover the drop element, hover the drop element second time, mouse up.
    
    # card_height: float = browser_page.get_by_role("button", name="Test Initiative 1").bounding_box()["height"] # type: ignore

    # browser_page.get_by_role("button", name="Test Initiative 1").hover();
    # sleep(1)
    # browser_page.mouse.down(click_count=2);
    # sleep(1)
    # browser_page.mouse.move(x=0, y=2*card_height, steps=5)
    # sleep(1)
    # browser_page.mouse.up();
    # sleep(1)

    # # browser_page.pause()

    # expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_count(3)
    # expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_text([
    #     'Test Initiative 2I-002',
    #     'Test Initiative 3I-003',
    #     'Test Initiative 1I-001'
    # ])

    # Couldnt get the drag n drop working so for the moment we'll change the order via the api
    controller.move_initiative(
        initiative_id=test_initiative_1.id,
        user_id=user.id,
        after_id=test_initiative_3.id,
        before_id=None
    )

    sleep(0.5)
    browser_page.reload()

    expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_count(3)
    expect(browser_page.get_by_role("button", name="Test Initiative")).to_have_text([
        'Test Initiative 2I-002',
        'Test Initiative 3I-003',
        'Test Initiative 1I-001'
    ])

def test_can_reorder_task_list(
    browser_page: Page, onboard_test_user, user: User, workspace: Workspace, session
):
    
    initiative_controller = InitiativeController(session)
    test_initiative = initiative_controller.create_initiative(
        title="Test Initiative",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )

    task_controller = TaskController(session)
    test_task_1: Task = task_controller.create_task(
        initiative_id=test_initiative.id,
        title="Test task 1",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=TaskStatus.TO_DO
    )
    test_task_2: Task = task_controller.create_task(
        initiative_id=test_initiative.id,
        title="Test task 2",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=TaskStatus.TO_DO
    )
    test_task_3: Task = task_controller.create_task(
        initiative_id=test_initiative.id,
        title="Test task 3",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=TaskStatus.TO_DO
    )

    sleep(0.5)
    browser_page.reload()

    expect(browser_page.get_by_role("button", name="Test Initiative")).to_be_visible()
    browser_page.get_by_role("button", name="Test Initiative").click()

    expect(browser_page.get_by_role("button", name="Test task")).to_have_count(3)
    expect(browser_page.get_by_role("button", name="Test task")).to_have_text([
        'TM-001Test task 1',
        'TM-002Test task 2',
        'TM-003Test task 3',
    ])

    task_controller.move_task(
        task_id=test_task_1.id,
        user_id=user.id,
        after_id=test_task_3.id,
        before_id=None
    )

    sleep(0.5)
    browser_page.reload()

    expect(browser_page.get_by_role("button", name="Test task")).to_have_count(3)
    expect(browser_page.get_by_role("button", name="Test task")).to_have_text([
        'TM-002Test task 2',
        'TM-003Test task 3',
        'TM-001Test task 1',
    ])


def test_can_reorder_initiative_group(
    browser_page: Page, onboard_test_user, user: User, workspace: Workspace, session
):
    controller = InitiativeController(session)
    test_initiative_1 = controller.create_initiative(
        title="Test Initiative 1",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )
    test_initiative_2 = controller.create_initiative(
        title="Test Initiative 2",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )
    test_initiative_3 = controller.create_initiative(
        title="Test Initiative 3",
        description="",
        user_id=user.id,
        workspace_id=workspace.id,
        status=InitiativeStatus.TO_DO,
    )

    group = Group(
        user_id=user.id,
        workspace_id=workspace.id,
        name="Test group",
        group_type=GroupType.EXPLICIT,
    )
    session.add(group)
    session.flush()


    controller.add_initiative_to_group(
        initiative_id=test_initiative_1.id,
        user_id=user.id,
        group_id=group.id
    )

    controller.add_initiative_to_group(
        initiative_id=test_initiative_2.id,
        user_id=user.id,
        group_id=group.id
    )

    controller.add_initiative_to_group(
        initiative_id=test_initiative_3.id,
        user_id=user.id,
        group_id=group.id
    )

    sleep(0.5)
    browser_page.reload()

    browser_page.get_by_role("button", name="Backlog").click()
    browser_page.locator("#selected-groups-list").get_by_role("button").filter(has_text=re.compile(r"^$")).click()
    expect(browser_page.get_by_text("Test group")).to_be_visible()
    browser_page.locator(f"#group-checkbox-header-group-select-{group.id}").check()
    browser_page.locator(".flex-grow").first.click()
    expect(browser_page.get_by_role("heading", name="Test group")).to_be_visible()
    expect(browser_page.get_by_role("button", name="I-001Test Initiative")).to_be_visible()
    expect(browser_page.get_by_role("button", name="I-002Test Initiative")).to_be_visible()
    expect(browser_page.get_by_role("button", name="I-003Test Initiative")).to_be_visible()

    expect(browser_page.get_by_role("button", name="I-00")).to_have_text([
        "I-001Test Initiative 1",
        "I-002Test Initiative 2",
        "I-003Test Initiative 3",
    ])

    controller.move_initiative_in_group(
        initiative_id=test_initiative_1.id,
        user_id=user.id,
        group_id=group.id,
        after_id=test_initiative_3.id,
        before_id=None
    )

    sleep(0.5)
    browser_page.reload()

    expect(browser_page.get_by_role("button", name="I-00")).to_have_text([
        "I-002Test Initiative 2",
        "I-003Test Initiative 3",
        "I-001Test Initiative 1",
    ])
