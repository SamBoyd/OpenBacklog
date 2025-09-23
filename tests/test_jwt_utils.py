import uuid
from unittest.mock import patch

import pytest
from hamcrest import assert_that, equal_to, has_key, is_

from src.auth.jwt_utils import (
    create_unified_jwt,
    extract_user_id_from_jwt,
    validate_jwt,
)
from src.models import User


class TestCreateUnifiedJWTWithKeyId:
    """Test suite for JWT creation with key_id functionality."""

    def test_creates_jwt_without_key_id(self, user):
        """Test that JWT creation works without key_id (backward compatibility)."""
        # Execute
        token = create_unified_jwt(user, lifetime_seconds=3600)

        # Verify
        claims = validate_jwt(token)
        assert_that(claims, has_key("sub"))
        assert_that(claims["sub"], equal_to(str(user.id)))
        assert_that("key_id" not in claims, equal_to(True))

    def test_creates_jwt_with_key_id(self, user):
        """Test that JWT creation includes key_id when provided."""
        # Setup
        key_id = str(uuid.uuid4())

        # Execute
        token = create_unified_jwt(user, lifetime_seconds=3600, key_id=key_id)

        # Verify
        claims = validate_jwt(token)
        assert_that(claims, has_key("sub"))
        assert_that(claims["sub"], equal_to(str(user.id)))
        assert_that(claims, has_key("key_id"))
        assert_that(claims["key_id"], equal_to(key_id))

    def test_creates_jwt_with_none_key_id(self, user):
        """Test that JWT creation handles None key_id correctly."""
        # Execute
        token = create_unified_jwt(user, lifetime_seconds=3600, key_id=None)

        # Verify
        claims = validate_jwt(token)
        assert_that(claims, has_key("sub"))
        assert_that(claims["sub"], equal_to(str(user.id)))
        assert_that("key_id" not in claims, equal_to(True))

    def test_jwt_contains_all_required_claims_with_key_id(self, user):
        """Test that JWT contains all standard claims plus key_id."""
        # Setup
        key_id = "test-key-123"

        # Execute
        token = create_unified_jwt(user, lifetime_seconds=3600, key_id=key_id)

        # Verify all expected claims are present
        claims = validate_jwt(token)

        # Standard JWT claims
        assert_that(claims, has_key("sub"))
        assert_that(claims, has_key("iat"))
        assert_that(claims, has_key("exp"))

        # FastAPI Users claims
        assert_that(claims, has_key("email"))
        assert_that(claims, has_key("email_verified"))

        # PostgREST claims
        assert_that(claims, has_key("role"))

        # Auth0 compatibility claims
        assert_that(claims, has_key("https://samboyd.dev/role"))
        assert_that(claims, has_key("https://samboyd.dev/type"))
        assert_that(claims, has_key("type"))
        assert_that(claims, has_key("scope"))

        # Our custom key_id claim
        assert_that(claims, has_key("key_id"))
        assert_that(claims["key_id"], equal_to(key_id))


class TestJWTKeyIdExtraction:
    """Test suite for extracting key_id from JWT tokens."""

    def test_extract_user_id_from_jwt_with_key_id(self, user):
        """Test that user ID extraction still works with key_id present."""
        # Setup
        key_id = str(uuid.uuid4())
        token = create_unified_jwt(user, lifetime_seconds=3600, key_id=key_id)

        # Execute
        extracted_user_id = extract_user_id_from_jwt(token)

        # Verify
        assert_that(extracted_user_id, equal_to(str(user.id)))
