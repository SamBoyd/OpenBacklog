from unittest.mock import ANY, mock_open, patch

from hamcrest import assert_that, equal_to


@patch("src.api.controller.update_user")
def test_update_user(mock_update_user, test_client, user):
    response = test_client.post(
        "/api/user",
        json={"name": "John Doe"},
    )

    assert_that(response.status_code, equal_to(200))
    assert_that(response.json(), equal_to({}))
    mock_update_user.assert_called_with(
        user=user,
        name="John Doe",
        db=ANY,
    )

    response = test_client.post(
        "/api/user",
        json={"name": ""},
    )
    assert_that(response.status_code, equal_to(422))

    response = test_client.post(
        "/api/user",
        json={},
    )
    assert_that(response.status_code, equal_to(422))


@patch("src.api.controller.get_display_pref")
def test_get_display_pref(mock_get_display_pref, test_client, user):
    mock_get_display_pref.return_value = {
        "message": "Display preference updated successfully"
    }
    response = test_client.get("/api/user/display-pref")
    assert response.status_code == 200
    assert response.json() == {"message": "Display preference updated successfully"}


@patch("src.api.controller.update_display_pref")
def test_can_update_user_display_preference_allowed_fields(
    mock_update_display_pref, test_client, user
):
    # Test with an allowed field ("timezone") and valid value ("UTC").
    payload = {"field": "timezone", "value": "UTC"}
    response = test_client.post("/api/user/display-pref", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Display preference updated successfully"}
    mock_update_display_pref.assert_called_with(
        user=user, field="timezone", value="UTC", db=ANY
    )


def test_rejects_non_allowed_fields(test_client, user):
    # Test with a field that is not allowed.
    payload = {"field": "invalidField", "value": "some_value"}
    response = test_client.post("/api/user/display-pref", json=payload)
    assert response.status_code == 422


def test_update_user_display_preferences_payload_validation(test_client, user):
    # Test with an empty preference value.
    payload = {"field": "theme", "value": ""}
    response = test_client.post("/api/user/display-pref", json=payload)
    assert response.status_code == 422
