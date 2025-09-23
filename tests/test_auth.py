import responses
from fastapi.testclient import TestClient
from hamcrest import assert_that, is_
from responses import matchers

from src.config import settings
from src.main import app


def test_invalid_auth_cookie():
    # Ensure no dependency override for valid user
    # app.dependency_overrides.pop(fastapi_users.current_user, None)

    client = TestClient(app)
    # Simulate an expired cookie by setting an invalid token
    client.cookies.set("access_token", "invalid")

    response = client.get("/workspace", follow_redirects=False)

    # Expecting redirection due to 401 caught by exception handler
    assert response.status_code == 302
    assert response.headers.get("location") == "/"  # redirected to home


def test_renew_jwt_returns_if_no_refresh_token_present(test_client):
    response = test_client.post("/auth/renew-jwt")

    # Expecting 401 due to missing refresh token
    assert response.status_code == 401
    assert response.json() == {"error": "No refresh token available"}


@responses.activate
def test_renew_jwt_returns_new_jwt(test_client):
    # Set a dummy refresh token in the client
    test_client.cookies.set("refresh_token", "dummy_refresh_token")

    # Mock the Auth0 token endpoint
    responses.add(
        responses.POST,
        f"https://{settings.auth0_domain}/oauth/token",
        match=[
            matchers.json_params_matcher(
                {
                    "grant_type": "refresh_token",
                    "client_id": settings.auth0_client_id,
                    "client_secret": settings.auth0_client_secret,
                    "refresh_token": "dummy_refresh_token",
                }
            )
        ],
        status=200,
        json={
            "access_token": "new_access",
            "id_token": "new_id",
            "refresh_token": "new_refresh",
        },
    )

    response = test_client.post("/auth/renew-jwt")
    assert_that(response.status_code, is_(200))
    assert_that(response.json(), is_({}))
    assert_that(response.cookies.get("auth0_jwt"), is_("new_access"))
    assert_that(response.cookies.get("refresh_token"), is_("new_refresh"))
