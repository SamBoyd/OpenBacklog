import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import freezegun
import pytest
from fastapi import HTTPException
from hamcrest import assert_that, contains_string, equal_to, has_length, is_, none

from src.controller import (
    create_openbacklog_token,
    delete_openbacklog_token,
    get_openbacklog_tokens_for_user,
)
from src.models import APIProvider, UserKey


class TestCreateOpenBacklogToken:
    """Test suite for create_openbacklog_token function."""

    @patch("src.controller.get_vault")
    @patch("src.auth.jwt_utils.create_unified_jwt")
    def test_creates_new_openbacklog_token(
        self, mock_create_jwt, mock_get_vault, session, user
    ):
        """Test successful creation of a new OpenBacklog token."""
        # Setup
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        mock_create_jwt.return_value = mock_token
        mock_vault = MagicMock()
        mock_vault.store_api_key_in_vault.return_value = "vault/path"
        mock_get_vault.return_value = mock_vault

        # Execute
        result = create_openbacklog_token(user, session)

        # Verify JWT creation was called with correct parameters (including key_id)
        mock_create_jwt.assert_called_once()
        call_args = mock_create_jwt.call_args
        assert_that(call_args[0][0], equal_to(user))  # First positional arg is user
        assert_that(call_args[1]["lifetime_seconds"], equal_to(31536000))
        assert_that(
            "key_id" in call_args[1], equal_to(True)
        )  # key_id should be present

        # Verify UserKey was created
        user_key = (
            session.query(UserKey)
            .filter(
                UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENBACKLOG
            )
            .first()
        )

        assert_that(user_key, is_(UserKey))
        assert_that(user_key.provider, equal_to(APIProvider.OPENBACKLOG))
        assert_that(user_key.redacted_key, equal_to("eyJ***7HgQ"))
        assert_that(user_key.is_valid, equal_to(True))
        assert_that(user_key.last_used_at, is_(none()))
        assert_that(
            user_key.access_token, equal_to(mock_token)
        )  # Verify full token is stored

        # Verify token was stored in Vault
        mock_vault.store_api_key_in_vault.assert_called_once_with(
            user_key.vault_path, mock_token
        )

        # Verify return value
        assert_that(
            result["message"], equal_to("OpenBacklog token created successfully")
        )
        assert_that(result["token"], equal_to(mock_token))
        assert_that(result["token_id"], equal_to(str(user_key.id)))
        assert_that(result["redacted_key"], equal_to("eyJ***7HgQ"))
        assert_that("created_at" in result, equal_to(True))

    @patch("src.controller.get_vault")
    @patch("src.auth.jwt_utils.create_unified_jwt")
    def test_handles_multiple_tokens_for_same_user(
        self, mock_create_jwt, mock_get_vault, session, user
    ):
        """Test that multiple tokens can be created for the same user."""
        # Setup
        mock_token1 = "token1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        mock_token2 = "token2_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"

        mock_create_jwt.side_effect = [mock_token1, mock_token2]
        mock_vault = MagicMock()
        mock_vault.store_api_key_in_vault.return_value = "vault/path"
        mock_get_vault.return_value = mock_vault

        # Execute - create first token
        result1 = create_openbacklog_token(user, session)

        # Execute - create second token
        result2 = create_openbacklog_token(user, session)

        # Verify both tokens were created
        user_keys = (
            session.query(UserKey)
            .filter(
                UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENBACKLOG
            )
            .all()
        )

        assert_that(user_keys, has_length(2))
        assert_that(result1["token"], equal_to(mock_token1))
        assert_that(result2["token"], equal_to(mock_token2))

    @patch("src.auth.jwt_utils.create_unified_jwt")
    def test_handles_jwt_creation_failure(self, mock_create_jwt, session, user):
        """Test handling of JWT creation failure."""
        # Setup
        mock_create_jwt.side_effect = Exception("JWT creation failed")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            create_openbacklog_token(user, session)

        assert_that(exc_info.value.status_code, equal_to(500))
        assert_that(
            str(exc_info.value.detail), contains_string("Failed to create token")
        )

    @patch("src.controller.get_vault")
    @patch("src.auth.jwt_utils.create_unified_jwt")
    def test_jwt_includes_key_id_for_tracking(
        self, mock_create_jwt, mock_get_vault, session, user
    ):
        """Test that the JWT token includes the key_id for proper tracking."""
        # Setup
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwia2V5X2lkIjoiYWJjZC0xMjM0In0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        mock_create_jwt.return_value = mock_token
        mock_vault = MagicMock()
        mock_vault.store_api_key_in_vault.return_value = "vault/path"
        mock_get_vault.return_value = mock_vault

        # Execute
        create_openbacklog_token(user, session)

        # Verify JWT creation was called with key_id matching the UserKey ID
        mock_create_jwt.assert_called_once()
        call_args = mock_create_jwt.call_args

        # Get the created UserKey to verify the key_id matches
        user_key = (
            session.query(UserKey)
            .filter(
                UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENBACKLOG
            )
            .first()
        )

        assert_that(call_args[1]["key_id"], equal_to(str(user_key.id)))


class TestDeleteOpenBacklogToken:
    """Test suite for delete_openbacklog_token function."""

    def test_deletes_existing_token(self, session, user):
        """Test successful soft deletion of an existing token."""
        # Setup - create a token
        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="eyJ***7HgQ",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )
        session.add(user_key)
        session.commit()
        session.refresh(user_key)

        token_id = str(user_key.id)

        # Execute
        result = delete_openbacklog_token(user, token_id, session)

        # Verify token was soft deleted (marked as invalid with deleted_at timestamp)
        deleted_key = session.query(UserKey).filter(UserKey.id == token_id).first()

        assert_that(deleted_key, is_(UserKey))  # Token still exists in database
        assert_that(deleted_key.is_valid, equal_to(False))  # But marked as invalid
        assert_that(deleted_key.deleted_at, is_(datetime))  # And has deletion timestamp
        assert_that(result["message"], equal_to("Token deleted successfully"))

    def test_fails_for_nonexistent_token(self, session, user):
        """Test deletion of a non-existent token."""
        # Setup
        fake_token_id = str(uuid.uuid4())

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            delete_openbacklog_token(user, fake_token_id, session)

        assert_that(exc_info.value.status_code, equal_to(404))
        assert_that(str(exc_info.value.detail), equal_to("Token not found"))

    def test_fails_for_token_belonging_to_different_user(
        self, session, user, other_user
    ):
        """Test that a user cannot delete another user's token."""
        # Setup - create a token for other_user
        user_key = UserKey(
            user_id=other_user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="eyJ***7HgQ",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )
        session.add(user_key)
        session.commit()
        session.refresh(user_key)

        token_id = str(user_key.id)

        # Execute & Verify - user tries to delete other_user's token
        with pytest.raises(HTTPException) as exc_info:
            delete_openbacklog_token(user, token_id, session)

        assert_that(exc_info.value.status_code, equal_to(404))
        assert_that(str(exc_info.value.detail), equal_to("Token not found"))

        # Verify token still exists
        existing_key = session.query(UserKey).filter(UserKey.id == token_id).first()
        assert_that(existing_key, is_(UserKey))

    def test_fails_for_non_openbacklog_token(self, session, user):
        """Test that only OpenBacklog tokens can be deleted via this function."""
        # Setup - create an OpenAI token
        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENAI,
            redacted_key="sk-***1234",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )
        session.add(user_key)
        session.commit()
        session.refresh(user_key)

        token_id = str(user_key.id)

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            delete_openbacklog_token(user, token_id, session)

        assert_that(exc_info.value.status_code, equal_to(404))
        assert_that(str(exc_info.value.detail), equal_to("Token not found"))


class TestGetOpenBacklogTokensForUser:
    """Test suite for get_openbacklog_tokens_for_user function."""

    def test_returns_empty_list_for_user_with_no_tokens(self, session, user):
        """Test that empty list is returned when user has no tokens."""
        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify
        assert_that(tokens, equal_to([]))

    def test_returns_openbacklog_tokens_only(self, session, user):
        """Test that only OpenBacklog tokens are returned, not other API provider tokens."""
        # Setup - create different types of tokens
        openai_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENAI,
            redacted_key="sk-***1234",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )

        openbacklog_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="eyJ***7HgQ",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )

        session.add_all([openai_key, openbacklog_key])
        session.commit()

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify
        assert_that(tokens, has_length(1))
        assert_that(tokens[0]["redacted_key"], equal_to("eyJ***7HgQ"))
        assert_that(tokens[0]["id"], equal_to(str(openbacklog_key.id)))

    def test_returns_tokens_with_correct_metadata(self, session, user):
        """Test that tokens are returned with all required metadata."""
        # Setup
        created_at = datetime.now(timezone.utc)
        last_used_at = datetime.now(timezone.utc)

        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="eyJ***7HgQ",
            is_valid=True,
            last_validated_at=created_at,
            last_used_at=last_used_at,
        )

        session.add(user_key)
        session.commit()
        session.refresh(user_key)

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify
        assert_that(tokens, has_length(1))
        token = tokens[0]

        assert_that(token["id"], equal_to(str(user_key.id)))
        assert_that(token["redacted_key"], equal_to("eyJ***7HgQ"))
        # The database may return datetime without timezone info, so compare with user_key value
        assert_that(
            token["created_at"],
            equal_to(user_key.last_validated_at.strftime("%Y-%m-%d %H:%M")),
        )
        assert_that(
            token["last_used_at"],
            equal_to(user_key.last_used_at.strftime("%Y-%m-%d %H:%M")),
        )
        assert_that(token["is_valid"], equal_to(True))

    def test_returns_multiple_tokens_ordered_by_creation_date(self, session, user):
        """Test that multiple tokens are returned in correct order."""
        # Setup - create tokens with different creation times
        old_token = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="old***key",
            is_valid=True,
            last_validated_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

        new_token = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="new***key",
            is_valid=True,
            last_validated_at=datetime(2023, 12, 31, tzinfo=timezone.utc),
        )

        session.add_all([old_token, new_token])
        session.commit()

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify - newest first
        assert_that(tokens, has_length(2))
        assert_that(tokens[0]["redacted_key"], equal_to("new***key"))
        assert_that(tokens[1]["redacted_key"], equal_to("old***key"))

    def test_handles_tokens_with_null_timestamps(self, session, user):
        """Test handling of tokens with null last_used_at timestamps."""
        # Setup
        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="eyJ***7HgQ",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
            last_used_at=None,  # Explicitly set to None
        )

        session.add(user_key)
        session.commit()

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify
        assert_that(tokens, has_length(1))
        assert_that(tokens[0]["last_used_at"], is_(none()))

    def test_does_not_return_other_users_tokens(self, session, user, other_user):
        """Test that only the specified user's tokens are returned."""
        # Setup - create tokens for both users
        user_token = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="usr***key",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )

        other_user_token = UserKey(
            user_id=other_user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="oth***key",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )

        session.add_all([user_token, other_user_token])
        session.commit()

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify
        assert_that(tokens, has_length(1))
        assert_that(tokens[0]["redacted_key"], equal_to("usr***key"))

    def test_does_not_return_soft_deleted_tokens(self, session, user):
        """Test that soft deleted tokens are not returned."""
        # Setup - create valid and soft deleted tokens
        valid_token = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="val***key",
            is_valid=True,
            last_validated_at=datetime.now(timezone.utc),
        )

        soft_deleted_token = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="del***key",
            is_valid=False,
            deleted_at=datetime.now(timezone.utc),
            last_validated_at=datetime.now(timezone.utc),
        )

        session.add_all([valid_token, soft_deleted_token])
        session.commit()

        # Execute
        tokens = get_openbacklog_tokens_for_user(user, session)

        # Verify - only valid token is returned
        assert_that(tokens, has_length(1))
        assert_that(tokens[0]["redacted_key"], equal_to("val***key"))
