import datetime
from typing import Dict
import logging

import pytest
import requests
from fastapi.testclient import TestClient
from hamcrest import (
    anything,
    assert_that,
    empty,
    equal_to,
    has_entries,
    has_length,
    is_,
)
from sqlalchemy import text

from src.db import SessionLocal
from src.main import app
from src.models import OAuthAccount, User

logger = logging.getLogger(__name__)


POSTGREST_SERVER_URL = "http://localhost:3003"
POSTGREST_ADMIN_SERVER_URL = "http://localhost:3004"


# @pytest.fixture(scope="session", autouse=True)
# def test_client():
#     return TestClient(app)


# @pytest.fixture(autouse=True)
# def clean_tables():
#     yield
#     with SessionLocal() as s:
#         s.execute(text("TRUNCATE TABLE dev.task CASCADE"))
#         s.execute(text("TRUNCATE TABLE dev.workspace CASCADE"))
#         s.execute(text("TRUNCATE TABLE private.users CASCADE"))
#         # add more if needed
#         s.commit()


# @pytest.fixture
# def user():
#     with SessionLocal() as session:
#         user = User(
#             name="Steven Stevenson",
#             email="steve@gmail.com",
#             hashed_password="hashed_password",
#             is_active=True,
#             is_superuser=False,
#             is_verified=True,
#             last_logged_in=datetime.datetime.now(),
#         )
#         session.add(user)
#         session.commit()
#         session.refresh(user)

#         oauth_account = OAuthAccount(
#             user_id=user.id,
#             oauth_name="oauth_name",
#             access_token="access_token",
#             expires_at=datetime.datetime.now().timestamp(),
#             refresh_token="refresh_token",
#             account_id="oauth_account_id",
#             account_email="samboyd10@gmail.com",
#         )
#         session.add(oauth_account)
#         session.commit()
#         session.refresh(oauth_account)

#         yield user

#         session.delete(user)


@pytest.fixture()
def workspace(user, jwt):
    # First create a workspace
    workspace_response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/workspace",
        jwt,
        {"name": "Test Workspace"},
        headers={"Prefer": "return=representation"},
    )
    print(f"Workspace response: {workspace_response.status_code} - {workspace_response.content}")
    
    if workspace_response.status_code == 201:
        workspace_id = workspace_response.json()[0]["id"]
    else:
        # Try to get existing workspace
        workspace_get_response = authenticated_get_request(f"{POSTGREST_SERVER_URL}/workspace", jwt)
        print(f"Get workspace response: {workspace_get_response.status_code} - {workspace_get_response.content}")
        if workspace_get_response.status_code == 200 and workspace_get_response.json():
            workspace_id = workspace_get_response.json()[0]["id"]
        else:
            workspace_id = None

    return workspace_id
    

@pytest.fixture
def jwt(user):
    import jwt

    SECRET_KEY = "this-is-my-super-secret-development-key"

    payload = {
        "https://samboyd.dev/role": "test_authenticated",
        "role": "test_authenticated",
        "sub": str(user.id),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=1),
    }

    yield jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def authenticated_get_request(url, jwt):
    return requests.get(
        url,
        headers={"Authorization": f"Bearer {jwt}"},
    )


def authenticated_post_request(url, jwt, data, headers=None):
    return requests.post(
        url,
        headers={"Authorization": f"Bearer {jwt}", **(headers or {})},
        json=data,
    )


@pytest.fixture(autouse=True)
def check_postgrest_is_up():
    try:
        response = requests.get(f"{POSTGREST_ADMIN_SERVER_URL}/ready")
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        pytest.fail("Postgrest server is not running")
    except requests.exceptions.HTTPError as e:
        pytest.fail(f"HTTP error occurred: {e}")

    try:
        response = requests.get(f"{POSTGREST_ADMIN_SERVER_URL}/config")
        response.raise_for_status()
        assert (
            "taskmanager_test_db" in response.text
        ), "Postgrest is not connected to the test database"
    except requests.exceptions.ConnectionError:
        pytest.fail("Postgrest server is not running")
    except requests.exceptions.HTTPError as e:
        pytest.fail(f"HTTP error occurred: {e}")


def test_can_create_intiatives_with_just_titles(user, workspace, jwt):
    response = authenticated_get_request(f"{POSTGREST_SERVER_URL}/initiative", jwt)
    assert_that(response.status_code, equal_to(200))
    assert_that(response.json(), is_(empty()))

    # Include workspace_id in the initiative creation
    initiative_data: Dict[str, str] = {"title": "My first initiative", "workspace_id": workspace}
    
    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/initiative",
        jwt,
        initiative_data,
    )
    
    assert_that(response.status_code, equal_to(201))
    
    response = authenticated_get_request(f"{POSTGREST_SERVER_URL}/initiative?select=*", jwt)
    assert_that(response.status_code, equal_to(200))

    assert_that(response.json(), has_length(1))
    assert_that(
        response.json()[0],
        has_entries(
            {
                "type": None,
                "progress": None,
                "id": anything(),
                "identifier": "I-001",
                "user_id": str(user.id),
                "title": "My first initiative",
                "description": None,
                "created_at": anything(),
                "updated_at": anything(),
                "status": "TO_DO",
                "workspace_id": workspace,
                "has_pending_job": False,
                "properties": {},
                "blocked_by_id": None,
            }
        ),
    )


def test_can_create_models_with_just_titles(user, workspace, jwt):
    response = authenticated_get_request(f"{POSTGREST_SERVER_URL}/initiative", jwt)
    assert_that(response.status_code, equal_to(200))
    assert_that(response.json(), is_(empty()))

    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/initiative?select=id",
        jwt,
        {"title": "My first initiative", "workspace_id": workspace},
        headers={"Prefer": "return=representation"},
    )
    assert_that(response.status_code, equal_to(201))

    initiative_id = response.json()[0]["id"]

    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/task?select=id",
        jwt,
        {"title": "My first task", "initiative_id": initiative_id, "workspace_id": workspace},
        headers={"Prefer": "return=representation"},
    )
    assert_that(response.status_code, equal_to(201))
    task_id = response.json()[0]["id"]

    checklist_payload = {
            "title": "My first checklist item",
            "task_id": task_id, 
        }

    logger.info(f"checklist payload: {checklist_payload}")

    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/checklist?select=title",
        jwt,
        checklist_payload,
    )
    assert_that(response.status_code, equal_to(201))

    response = authenticated_get_request(
        f"{POSTGREST_SERVER_URL}/initiative?select=*,task(*, checklist(*))", jwt
    )
    assert_that(response.status_code, equal_to(200))
    assert_that(response.json(), has_length(1))
    assert_that(
        response.json()[0],
        has_entries(
            {
                "type": None,
                "progress": None,
                "id": initiative_id,
                "identifier": "I-001",
                "user_id": str(user.id),
                "title": "My first initiative",
                "description": None,
                "created_at": anything(),
                "updated_at": anything(),
                "status": "TO_DO",
                "workspace_id": workspace,
                "has_pending_job": False,
                "properties": {},
                "blocked_by_id": None,
                "task": has_length(1),
            }
        ),
    )
    assert_that(
        response.json()[0]["task"][0],
        has_entries(
            {
                "id": task_id,
                "type": None,
                "title": "My first task",
                "status": "TO_DO",
                "user_id": str(user.id),
                "created_at": anything(),
                "identifier": "TM-001",
                "updated_at": anything(),
                "description": None,
                "initiative_id": initiative_id,
                "checklist": has_length(1),
            }
        ),
    )
    assert_that(
        response.json()[0]["task"][0]["checklist"][0],
        has_entries(
            {
                "id": anything(),
                "title": "My first checklist item",
                "task_id": task_id,
                "order": 0,
                "is_complete": False,
            }
        ),
    )


def test_user_cannot_create_more_than_one_workspace(user, jwt):
    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/workspace",
        jwt,
        {"name": "My first workspace"},
        headers={"Prefer": "return=representation"},
    )
    assert_that(response.status_code, equal_to(201))
    
    response = authenticated_post_request(
        f"{POSTGREST_SERVER_URL}/workspace",
        jwt,
        {"name": "My second workspace"},
    )
    assert_that(response.status_code, equal_to(409))
