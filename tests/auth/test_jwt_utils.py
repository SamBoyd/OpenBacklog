"""
Unit tests for JWT utilities.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import jwt
import pytest
from hamcrest import assert_that, contains_string, equal_to, is_, none, not_none
from jose.exceptions import JWTError

from src.auth.jwt_utils import (
    create_refresh_token,
    create_unified_jwt,
    extract_user_id_from_jwt,
    validate_jwt,
    validate_refresh_token,
)


class TestCreateUnifiedJWT:
    """Test cases for create_unified_jwt function."""

    def test_creates_jwt_with_default_settings(self):
        """Test JWT creation with default settings."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        with patch("src.auth.jwt_utils.settings") as mock_settings:
            mock_settings.dev_jwt_lifetime_seconds = 3600
            mock_settings.dev_jwt_secret = "test-secret"
            mock_settings.postgrest_authenticated_role = "authenticated"

            token = create_unified_jwt(user)

            assert_that(token, not_none())
            assert_that(isinstance(token, str), is_(True))

    def test_creates_jwt_with_custom_lifetime(self):
        """Test JWT creation with custom lifetime."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        token = create_unified_jwt(user, lifetime_seconds=7200, secret="dev_jwt_secret")

        # Decode to verify expiration
        payload = jwt.decode(token, "dev_jwt_secret", algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])

        assert_that((exp_time - iat_time).seconds, equal_to(7200))

    def test_creates_jwt_with_oauth_user_id(self):
        """Test JWT creation with sub being user id."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True
        token = create_unified_jwt(user, secret="dev_jwt_secret")

        payload = jwt.decode(token, "dev_jwt_secret", algorithms=["HS256"])
        assert_that(payload["sub"], equal_to(str(user.id)))

    def test_creates_jwt_with_custom_secret(self):
        """Test JWT creation with custom secret."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True
        custom_secret = "custom-secret-key"

        token = create_unified_jwt(user, secret=custom_secret)

        # Should be able to decode with custom secret
        payload = jwt.decode(token, custom_secret, algorithms=["HS256"])
        assert_that(payload["email"], equal_to(user.email))

    def test_jwt_contains_required_claims(self):
        """Test that JWT contains all required claims."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        # with patch('src.auth.jwt_utils.settings') as mock_settings:
        #     mock_settings.postgrest_authenticated_role = "authenticated"
        #     mock_settings.dev_jwt_lifetime_seconds = 3600
        #     mock_settings.dev_jwt_secret = "dev_jwt_secret"

        token = create_unified_jwt(user, secret="dev_jwt_secret")
        payload = jwt.decode(token, "dev_jwt_secret", algorithms=["HS256"])

        # Standard JWT claims
        assert_that(payload["sub"], equal_to(str(user.id)))
        assert_that("iat" in payload, is_(True))
        assert_that("exp" in payload, is_(True))

        # FastAPI Users claims
        assert_that(payload["email"], equal_to(user.email))
        assert_that(payload["email_verified"], equal_to(user.is_verified))

        # PostgREST claims
        assert_that(payload["role"], equal_to("test_authenticated"))

        # Auth0 compatibility claims
        assert_that(payload["https://samboyd.dev/role"], equal_to("test_authenticated"))
        assert_that(payload["https://samboyd.dev/type"], equal_to("accessToken"))
        assert_that(payload["type"], equal_to("accessToken"))
        assert_that(payload["scope"], contains_string("openid"))


class TestValidateJWT:
    """Test cases for validate_jwt function."""

    def test_validates_valid_token(self):
        """Test validation of a valid token."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        token = create_unified_jwt(user, secret="dev_jwt_secret")
        claims = validate_jwt(token, secret="dev_jwt_secret")

        assert_that(claims["email"], equal_to(user.email))
        assert_that(claims["sub"], equal_to(str(user.id)))

    def test_validates_token_with_custom_secret(self):
        """Test validation with custom secret."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True
        custom_secret = "custom-secret"

        token = create_unified_jwt(user, secret=custom_secret)
        claims = validate_jwt(token, secret=custom_secret)

        assert_that(claims["email"], equal_to(user.email))

    def test_raises_error_for_invalid_token(self):
        """Test that invalid token raises JWTError."""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError) as exc_info:
            validate_jwt(invalid_token)

        assert_that(str(exc_info.value), contains_string("Invalid token"))

    def test_raises_error_for_expired_token(self):
        """Test that expired token raises JWTError."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        # Create token that expires immediately
        token = create_unified_jwt(user, lifetime_seconds=-1, secret="dev_jwt_secret")

        with pytest.raises(JWTError):
            validate_jwt(token, secret="dev_jwt_secret")

    def test_validates_with_audience_and_issuer(self):
        """Test validation with audience and issuer."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        # Create token with audience and issuer
        now = datetime.now(UTC)
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "aud": "test-audience",
            "iss": "test-issuer",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(claims, "dev_jwt_secret", algorithm="HS256")

        validated_claims = validate_jwt(
            token,
            secret="dev_jwt_secret",
            audience="test-audience",
            issuer="test-issuer",
        )

        assert_that(validated_claims["sub"], equal_to(str(user.id)))


class TestExtractUserIdFromJWT:
    """Test cases for extract_user_id_from_jwt function."""

    def test_extracts_user_id_from_valid_token(self):
        """Test extracting user ID from valid token."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        token = create_unified_jwt(user, secret="dev_jwt_secret")
        user_id = extract_user_id_from_jwt(token)

        assert_that(user_id, equal_to(str(user.id)))

    def test_extracts_user_id_without_validation(self):
        """Test that function extracts ID without validating signature."""
        # Create token with wrong secret but valid structure
        claims = {"sub": "test-user-id", "exp": 9999999999}
        token = jwt.encode(claims, "wrong-secret", algorithm="HS256")

        user_id = extract_user_id_from_jwt(token)

        assert_that(user_id, equal_to("test-user-id"))

    def test_returns_none_for_invalid_token(self):
        """Test that invalid token returns None."""
        invalid_token = "completely.invalid.token"

        user_id = extract_user_id_from_jwt(invalid_token)

        assert_that(user_id, none())

    def test_returns_none_for_token_without_sub(self):
        """Test that token without sub claim returns None."""
        claims = {"email": "test@example.com", "exp": 9999999999}
        token = jwt.encode(claims, "any-secret", algorithm="HS256")

        user_id = extract_user_id_from_jwt(token)

        assert_that(user_id, none())


class TestCreateRefreshToken:
    """Test cases for create_refresh_token function."""

    def test_creates_refresh_token(self):
        """Test creation of refresh token."""
        user = Mock()
        user.id = uuid.uuid4()

        with patch("src.auth.jwt_utils.settings") as mock_settings:
            mock_settings.dev_jwt_secret = "dev_jwt_secret"
            token = create_refresh_token(user)

            assert_that(token, not_none())
            assert_that(isinstance(token, str), is_(True))

    def test_refresh_token_contains_correct_claims(self):
        """Test that refresh token contains correct claims."""
        user = Mock()
        user.id = uuid.uuid4()

        token = create_refresh_token(user, secret="dev_jwt_secret")
        payload = jwt.decode(token, "dev_jwt_secret", algorithms=["HS256"])

        assert_that(payload["sub"], equal_to(str(user.id)))
        assert_that(payload["type"], equal_to("refresh_token"))
        assert_that("iat" in payload, is_(True))
        assert_that("exp" in payload, is_(True))

    def test_refresh_token_has_long_expiration(self):
        """Test that refresh token has 30-day expiration."""
        user = Mock()
        user.id = uuid.uuid4()

        token = create_refresh_token(user, secret="dev_jwt_secret")
        payload = jwt.decode(token, "dev_jwt_secret", algorithms=["HS256"])

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        duration = exp_time - iat_time

        # Should be approximately 30 days
        assert_that(duration.days, equal_to(30))

    def test_creates_refresh_token_with_custom_secret(self):
        """Test refresh token creation with custom secret."""
        user = Mock()
        user.id = uuid.uuid4()
        custom_secret = "custom-refresh-secret"

        token = create_refresh_token(user, secret=custom_secret)
        payload = jwt.decode(token, custom_secret, algorithms=["HS256"])

        assert_that(payload["sub"], equal_to(str(user.id)))


class TestValidateRefreshToken:
    """Test cases for validate_refresh_token function."""

    def test_validates_valid_refresh_token(self):
        """Test validation of valid refresh token."""
        user = Mock()
        user.id = uuid.uuid4()

        token = create_refresh_token(user, secret="dev_jwt_secret")
        user_id = validate_refresh_token(token, secret="dev_jwt_secret")

        assert_that(user_id, equal_to(str(user.id)))

    def test_validates_refresh_token_with_custom_secret(self):
        """Test validation with custom secret."""
        user = Mock()
        user.id = uuid.uuid4()
        custom_secret = "custom-secret"

        token = create_refresh_token(user, secret=custom_secret)
        user_id = validate_refresh_token(token, secret=custom_secret)

        assert_that(user_id, equal_to(str(user.id)))

    def test_returns_none_for_invalid_token(self):
        """Test that invalid token returns None."""
        invalid_token = "invalid.token.here"

        user_id = validate_refresh_token(invalid_token)

        assert_that(user_id, none())

    def test_returns_none_for_wrong_token_type(self):
        """Test that access token returns None."""
        user = Mock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.is_verified = True

        # Create access token instead of refresh token
        access_token = create_unified_jwt(user, secret="dev_jwt_secret")
        user_id = validate_refresh_token(access_token, secret="dev_jwt_secret")

        assert_that(user_id, none())

    def test_returns_none_for_expired_refresh_token(self):
        """Test that expired refresh token returns None."""
        user = Mock()
        user.id = uuid.uuid4()

        # Create expired refresh token
        now = datetime.now(UTC)
        claims = {
            "sub": str(user.id),
            "type": "refresh_token",
            "iat": int(now.timestamp()),
            "exp": int((now - timedelta(days=1)).timestamp()),  # Expired
        }
        token = jwt.encode(claims, "dev_jwt_secret", algorithm="HS256")

        user_id = validate_refresh_token(token, secret="dev_jwt_secret")

        assert_that(user_id, none())

    def test_returns_none_for_token_without_sub(self):
        """Test that refresh token without sub returns None."""
        now = datetime.now(UTC)
        claims = {
            "type": "refresh_token",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),
        }
        token = jwt.encode(claims, "dev_jwt_secret", algorithm="HS256")

        user_id = validate_refresh_token(token, secret="dev_jwt_secret")

        assert_that(user_id, none())
