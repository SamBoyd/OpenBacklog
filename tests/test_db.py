import json
import uuid

import pytest
from hamcrest import assert_that, contains, equal_to, has_item, is_
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import Base, SessionLocal, engine


def test_engine():
    assert_that(engine.echo, is_(False))


def test_base():
    assert_that(Base.metadata.tables, has_item("private.users"))


def test_session_local():
    session = SessionLocal()
    assert_that(session, is_(Session))
    session.close()

    assert_that(session.autoflush, is_(False))
    assert_that(session.autobegin, is_(True))


def test_tables_in_public_schema(session: Session):
    SCHEMA_NAME = "dev"

    # Check that the public schema exists
    result = session.execute(
        text(f"SELECT has_schema_privilege('{SCHEMA_NAME}', 'usage')")
    )
    assert_that(result.fetchone()[0], is_(True))

    # Check that the tables in the public schema are present
    result = session.execute(
        text(
            f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{SCHEMA_NAME}'"
        )
    )
    table_names = [row[0] for row in result.fetchall()]
    assert_that(len(table_names), equal_to(20))

    for table in table_names:
        # Check that the table exists
        result = session.execute(
            text(f"SELECT has_table_privilege('{SCHEMA_NAME}.{table}', 'select')")
        )
        assert_that(result.fetchone()[0], is_(True))

        # Check that the table has ROW_LEVEL_SECURITY enabled
        query = text(
            f"select relname, relrowsecurity from pg_class where oid = '{SCHEMA_NAME}.{table}'::regclass;"
        )
        result = session.execute(query)
        row = result.fetchone()
        assert_that(
            row[1], is_(True), f"Table {table} does not have ROW_LEVEL_SECURITY enabled"
        )

        # Check that the table has security policies
        expected_check = "(user_id = get_user_id_from_jwt())"
        query = text(f"select with_check from pg_policies where tablename = '{table}';")
        result = session.execute(query)
        assert_that(
            result.fetchone()[0],
            is_(expected_check),
            f"Table {table} does not have security policies",
        )


def test_update_user_key_last_used_trigger_with_no_jwt_claims(session: Session):
    """Test that the update_user_key_last_used trigger handles missing JWT claims gracefully."""
    # Create a test user and user_key first
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    test_key_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO dev.user_key (id, user_id, provider, redacted_key, is_valid, last_validated_at)
            VALUES (:key_id, :user_id, 'OPENAI', 'sk-...test', true, NOW())
        """
        ),
        {"key_id": test_key_id, "user_id": test_user_id},
    )

    # Ensure JWT claims are not set (or set to empty)
    session.execute(text("SET request.jwt.claims = ''"))

    # Insert a task which should trigger update_user_key_last_used
    # This should NOT fail even without JWT claims
    task_id = str(uuid.uuid4())
    initiative_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    # Create required dependencies first
    session.execute(
        text(
            """
            INSERT INTO dev.workspace (id, name, user_id)
            VALUES (:workspace_id, 'Test Workspace', :user_id)
        """
        ),
        {"workspace_id": workspace_id, "user_id": test_user_id},
    )

    session.execute(
        text(
            """
            INSERT INTO dev.initiative (id, title, description, user_id, workspace_id)
            VALUES (:initiative_id, 'Test Initiative', 'Description', :user_id, :workspace_id)
        """
        ),
        {
            "initiative_id": initiative_id,
            "user_id": test_user_id,
            "workspace_id": workspace_id,
        },
    )

    # This should succeed without throwing an error
    session.execute(
        text(
            """
            INSERT INTO dev.task (id, identifier, title, description, user_id, workspace_id, initiative_id)
            VALUES (:task_id, 'TEST-001', 'Test Task', 'Test Description', :user_id, :workspace_id, :initiative_id)
        """
        ),
        {
            "task_id": task_id,
            "user_id": test_user_id,
            "workspace_id": workspace_id,
            "initiative_id": initiative_id,
        },
    )

    session.commit()

    # Verify the task was created successfully
    result = session.execute(
        text("SELECT id FROM dev.task WHERE id = :task_id"), {"task_id": task_id}
    )
    assert_that(result.fetchone()[0], equal_to(uuid.UUID(task_id)))


def test_update_user_key_last_used_trigger_with_valid_jwt_claims(session: Session):
    """Test that the update_user_key_last_used trigger works correctly with valid JWT claims."""
    # Create a test user and user_key first
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'test2@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Create oauth account for JWT lookup
    session.execute(
        text(
            """
            INSERT INTO private.oauth_account 
                (id, user_id, account_id, oauth_name, access_token, account_email)
            VALUES (:id, :user_id, :account_id, 'test_oauth', 'dummy_token', 'test2@example.com')
        """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "account_id": "test_account_456",
        },
    )

    test_key_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO dev.user_key (id, user_id, provider, redacted_key, is_valid, last_validated_at, last_used_at)
            VALUES (:key_id, :user_id, 'OPENAI', 'sk-...test', true, NOW(), :old_timestamp)
        """
        ),
        {
            "key_id": test_key_id,
            "user_id": test_user_id,
            "old_timestamp": "2024-01-01 10:00:00",
        },
    )

    # Set valid JWT claims
    jwt_claims = json.dumps({"sub": test_user_id, "key_id": test_key_id})
    session.execute(text(f"SET request.jwt.claims = '{jwt_claims}'"))

    # Insert a task which should trigger update_user_key_last_used
    task_id = str(uuid.uuid4())
    initiative_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    # Create required dependencies first
    session.execute(
        text(
            """
            INSERT INTO dev.workspace (id, name, user_id)
            VALUES (:workspace_id, 'Test Workspace 2', :user_id)
        """
        ),
        {"workspace_id": workspace_id, "user_id": test_user_id},
    )

    session.execute(
        text(
            """
            INSERT INTO dev.initiative (id, title, description, user_id, workspace_id)
            VALUES (:initiative_id, 'Test Initiative 2', 'Test Description', :user_id, :workspace_id)
        """
        ),
        {
            "initiative_id": initiative_id,
            "user_id": test_user_id,
            "workspace_id": workspace_id,
        },
    )
    # Reset the timestamp to an old value for testing the task trigger
    # (The initiative insert above would have already updated it)
    session.execute(
        text(
            "UPDATE dev.user_key SET last_used_at = :old_timestamp WHERE id = :key_id"
        ),
        {"old_timestamp": "2024-01-01 10:00:00", "key_id": test_key_id},
    )

    # Get the current last_used_at value
    before_result = session.execute(
        text("SELECT last_used_at FROM dev.user_key WHERE id = :key_id"),
        {"key_id": test_key_id},
    )
    before_last_used = before_result.fetchone()[0]

    # This should succeed and update the last_used_at timestamp
    session.execute(
        text(
            """
            INSERT INTO dev.task (id, identifier, title, description, user_id, workspace_id, initiative_id)
            VALUES (:task_id, 'TEST-002', 'Test Task 2', 'Test Description', :user_id, :workspace_id, :initiative_id)
        """
        ),
        {
            "task_id": task_id,
            "user_id": test_user_id,
            "workspace_id": workspace_id,
            "initiative_id": initiative_id,
        },
    )

    session.commit()

    # Verify the task was created successfully
    result = session.execute(
        text("SELECT id FROM dev.task WHERE id = :task_id"), {"task_id": task_id}
    )
    assert_that(result.fetchone()[0], equal_to(uuid.UUID(task_id)))

    # Verify that last_used_at was updated
    session.execute(text(f"SET request.jwt.claims = '{jwt_claims}'"))
    after_result = session.execute(
        text("SELECT last_used_at FROM dev.user_key WHERE id = :key_id"),
        {"key_id": test_key_id},
    )
    after_last_used = after_result.fetchone()[0]

    # The timestamp should have been updated (or at least not be None if it was None before)
    if before_last_used is None:
        assert_that(after_last_used is not None, is_(True))
    else:
        # If there was a previous timestamp, the new one should be different
        assert_that(after_last_used != before_last_used, is_(True))


def test_verify_token_with_valid_token(session: Session):
    """Test that dev.verify_token() completes without exception for valid tokens in the database."""
    # Create a test user
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'token_test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Insert a valid access token
    test_token = "test_jwt_token_valid_12345"
    session.execute(
        text(
            """
            INSERT INTO private.access_token (token, user_id, created_at)
            VALUES (:token, :user_id, NOW())
        """
        ),
        {"token": test_token, "user_id": test_user_id},
    )

    # Mock the Authorization header
    headers_json = json.dumps({"authorization": f"Bearer {test_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should complete without exception
    session.execute(text("SELECT dev.verify_token()"))
    # If we reach here without exception, the test passes


def test_verify_token_with_invalid_token(session: Session):
    """Test that dev.verify_token() raises exception for tokens not in the database."""
    # Use a token that doesn't exist in the database
    invalid_token = "invalid_jwt_token_not_in_db"

    # Mock the Authorization header with invalid token
    headers_json = json.dumps({"authorization": f"Bearer {invalid_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should raise exception
    with pytest.raises(Exception, match="Invalid or expired token"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_no_authorization_header(session: Session):
    """Test that dev.verify_token() raises exception when no Authorization header is present."""
    # Set empty headers
    headers_json = json.dumps({})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should raise exception
    with pytest.raises(Exception, match="Missing authorization header"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_malformed_authorization_header_missing_bearer(
    session: Session,
):
    """Test that dev.verify_token() raises exception for missing Bearer prefix."""
    # Test case 1: Missing "Bearer " prefix
    headers_json = json.dumps({"authorization": "just_a_token_without_bearer"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    with pytest.raises(Exception, match="Invalid authorization header format"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_malformed_authorization_header_empty_token(session: Session):
    """Test that dev.verify_token() raises exception for empty token after Bearer."""
    # Test case 2: Empty token part after Bearer
    headers_json = json.dumps({"authorization": "Bearer "})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    with pytest.raises(Exception, match="Invalid or expired token"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_malformed_authorization_header_bearer_only(session: Session):
    """Test that dev.verify_token() raises exception for Bearer without space or token."""
    # Test case 3: Only "Bearer" without space or token
    headers_json = json.dumps({"authorization": "Bearer"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    with pytest.raises(Exception, match="Invalid authorization header format"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_revocation_scenario(session: Session):
    """Test that dev.verify_token() demonstrates real-world token revocation flow."""
    # Create a test user
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'revocation_test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Insert a valid access token
    test_token = "test_jwt_token_revocation_67890"
    session.execute(
        text(
            """
            INSERT INTO private.access_token (token, user_id, created_at)
            VALUES (:token, :user_id, NOW())
        """
        ),
        {"token": test_token, "user_id": test_user_id},
    )

    # Mock the Authorization header
    headers_json = json.dumps({"authorization": f"Bearer {test_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Verify the token works initially - should complete without exception
    session.execute(text("SELECT dev.verify_token()"))

    # Now delete the token (simulate token revocation)
    session.execute(
        text("DELETE FROM private.access_token WHERE token = :token"),
        {"token": test_token},
    )

    # Keep the same headers but verify the token is now invalid - should raise exception
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    with pytest.raises(Exception, match="Invalid or expired token"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_handles_malformed_json_headers(session: Session):
    """Test that dev.verify_token() handles malformed JSON in headers gracefully."""
    # Set malformed JSON as headers (this should trigger the exception handling)
    session.execute(text("SET request.headers = 'invalid_json{'"))

    # Call the verify_token function - should raise exception due to malformed JSON
    with pytest.raises(Exception, match="Invalid or missing authorization header"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_handles_missing_headers_setting(session: Session):
    """Test that dev.verify_token() handles missing request.headers setting gracefully."""
    # Don't set request.headers at all (or reset it)
    try:
        session.execute(text("RESET request.headers"))
    except:
        # If RESET fails, try to set it to empty
        pass

    # Call the verify_token function - should raise exception due to missing headers
    with pytest.raises(Exception, match="Invalid or missing authorization header"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_valid_openbacklog_token(session: Session):
    """Test that dev.verify_token() completes without exception for valid OpenBacklog tokens in user_key table."""
    # Create a test user
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'openbacklog_test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Insert a valid OpenBacklog token in user_key table
    test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
    session.execute(
        text(
            """
            INSERT INTO dev.user_key (user_id, provider, redacted_key, is_valid, access_token, last_validated_at)
            VALUES (:user_id, 'OPENBACKLOG', 'eyJ***7HgQ', true, :token, NOW())
        """
        ),
        {"user_id": test_user_id, "token": test_token},
    )

    # Mock the Authorization header
    headers_json = json.dumps({"authorization": f"Bearer {test_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should complete without exception
    session.execute(text("SELECT dev.verify_token()"))
    # If we reach here without exception, the test passes


def test_verify_token_with_soft_deleted_openbacklog_token(session: Session):
    """Test that dev.verify_token() raises exception for soft deleted OpenBacklog tokens."""
    # Create a test user
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'soft_deleted_test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Insert a soft deleted OpenBacklog token (is_valid=false, deleted_at set)
    test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
    session.execute(
        text(
            """
            INSERT INTO dev.user_key (user_id, provider, redacted_key, is_valid, access_token, last_validated_at, deleted_at)
            VALUES (:user_id, 'OPENBACKLOG', 'eyJ***7HgQ', false, :token, NOW(), NOW())
        """
        ),
        {"user_id": test_user_id, "token": test_token},
    )

    # Mock the Authorization header
    headers_json = json.dumps({"authorization": f"Bearer {test_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should raise exception
    with pytest.raises(Exception, match="Invalid or expired token"):
        session.execute(text("SELECT dev.verify_token()"))


def test_verify_token_with_non_openbacklog_provider_in_user_key(session: Session):
    """Test that dev.verify_token() raises exception for non-OpenBacklog tokens in user_key table."""
    # Create a test user
    test_user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES (:user_id, 'openai_test@example.com', 'dummy_hash', true, false, true)
        """
        ),
        {"user_id": test_user_id},
    )

    # Insert an OpenAI token in user_key table (should not validate for PostgREST access)
    test_token = "sk-1234567890abcdef1234567890abcdef"
    session.execute(
        text(
            """
            INSERT INTO dev.user_key (user_id, provider, redacted_key, is_valid, access_token, last_validated_at)
            VALUES (:user_id, 'OPENAI', 'sk-***cdef', true, :token, NOW())
        """
        ),
        {"user_id": test_user_id, "token": test_token},
    )

    # Mock the Authorization header
    headers_json = json.dumps({"authorization": f"Bearer {test_token}"})
    session.execute(text(f"SET request.headers = '{headers_json}'"))

    # Call the verify_token function - should raise exception
    with pytest.raises(Exception, match="Invalid or expired token"):
        session.execute(text("SELECT dev.verify_token()"))
