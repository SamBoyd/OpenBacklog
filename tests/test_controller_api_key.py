import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, contains_string, equal_to, is_

from src.controller import get_openai_key_from_vault, update_openai_key
from src.models import APIProvider, UserKey


@patch("src.controller._validate_openai_key", MagicMock())
@patch("src.controller.store_api_key_in_vault")
def test_update_openai_key_creates_new_user_key(mock_store_in_vault, session, user):
    api_key = "sk-abcdefghijklmnopqrstuvwxyz1234"

    # Execute
    result = update_openai_key(api_key, user, session)

    # Verify
    # Check that a new UserKey was created
    user_key = (
        session.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENAI)
        .first()
    )

    assert_that(user_key, is_(UserKey))
    assert_that(user_key.provider, equal_to(APIProvider.OPENAI))
    assert_that(user_key.redacted_key, equal_to("sk-***1234"))

    # Check that the key was stored in Vault
    mock_store_in_vault.assert_called_once_with(user_key.vault_path, api_key)

    # Check the return message
    assert_that(
        result["message"], equal_to("OpenAI key updated and validated successfully")
    )


@patch("src.controller._validate_openai_key", MagicMock())
@patch("src.controller.store_api_key_in_vault")
def test_update_openai_key_updates_existing_user_key(
    mock_store_in_vault, session, user
):
    # Create existing UserKey
    user_key = UserKey(
        user_id=user.id,
        provider=APIProvider.OPENAI,
        redacted_key="sk-***7890",
        is_valid=True,
        last_validated_at=datetime.now() + timedelta(hours=1),
    )
    session.add(user_key)
    session.commit()
    session.refresh(user_key)

    api_key = "sk-abcdefghijklmnopqrstuvwxyz1234"

    # Execute
    result = update_openai_key(api_key, user, session)

    # Verify
    # Check that a new UserKey was created
    user_key = (
        session.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENAI)
        .first()
    )

    assert_that(user_key, is_(UserKey))
    assert_that(user_key.provider, equal_to(APIProvider.OPENAI))
    assert_that(user_key.redacted_key, equal_to("sk-***1234"))

    # Check that the key was stored in Vault
    mock_store_in_vault.assert_called_once_with(user_key.vault_path, api_key)

    # Check the return message
    assert_that(
        result["message"], equal_to("OpenAI key updated and validated successfully")
    )


@patch("src.controller._validate_openai_key", MagicMock())
@patch("src.controller.store_api_key_in_vault")
def test_update_openai_key_handles_vault_error(mock_store_in_vault, session, user):
    # Create existing UserKey
    user_key = UserKey(
        user_id=user.id,
        provider=APIProvider.OPENAI,
        redacted_key="sk-***7890",
        is_valid=True,
        last_validated_at=datetime.now() + timedelta(hours=1),
    )
    session.add(user_key)
    session.commit()
    session.refresh(user_key)

    api_key = "sk-abcdefghijklmnopqrstuvwxyz1234"
    mock_store_in_vault.side_effect = RuntimeError("Vault connection failed")

    # Execute and verify
    with pytest.raises(RuntimeError) as excinfo:
        update_openai_key(api_key, user, session)

    # Check that the error message is propagated
    assert_that(str(excinfo.value), contains_string("Failed to store API key"))

    session.refresh(user_key)
    assert_that(user_key.redacted_key, equal_to("sk-***7890"))


@patch("src.controller._validate_openai_key", MagicMock())
@patch("src.controller.retrieve_api_key_from_vault")
def test_can_get_users_openai_key(mock_retrieve_api_key_from_vault, user, session):
    user_key = UserKey(
        user=user,
        provider=APIProvider.OPENAI,
        redacted_key="sk-***1234",
        is_valid=True,
        last_validated_at=datetime.now() + timedelta(hours=1),
    )
    session.add(user_key)
    session.commit()

    mock_retrieve_api_key_from_vault.return_value = "sk-abcdefghijklmnopqrstuvwxyz1234"

    response = get_openai_key_from_vault(user, session)
    assert response == "sk-abcdefghijklmnopqrstuvwxyz1234"


def test_can_get_users_openai_key_when_no_key(user, session):
    with pytest.raises(RuntimeError):
        get_openai_key_from_vault(user, session)

    pass


@patch("src.controller.store_api_key_in_vault", MagicMock())
@patch("src.controller._validate_openai_key")
def test_validates_the_key(mock_validate_openai_key, session, user):
    api_key = "sk-abcdefghijklmnopqrstuvwxyz1234"

    # Execute
    update_openai_key(api_key, user, session)

    mock_validate_openai_key.assert_called_once_with(api_key)
