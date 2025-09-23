import json
import uuid

import pytest
from sqlalchemy import create_engine, text

from src.db import engine


@pytest.fixture(scope="function")
def connection():
    conn = engine.connect()
    trans = conn.begin()
    yield conn
    trans.rollback()
    conn.close()


def test_get_user_id_from_jwt(connection):
    test_account_id = "test_account_123"
    test_user_id = str(uuid.uuid4())

    # Insert a test user.
    connection.execute(
        text(
            f"""
            INSERT INTO private.users (id, email, hashed_password, is_active, is_superuser, is_verified)
            VALUES ('{test_user_id}', 'test@example.com', 'dummy_hash', true, false, true)
        """
        )
    )

    # Insert a test oauth_account.
    connection.execute(
        text(
            """
            INSERT INTO private.oauth_account 
                (id, user_id, account_id, oauth_name, access_token, account_email)
            VALUES (:id, :user_id, :account_id, 'test_oauth', 'dummy_token', 'test@example.com')
        """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "account_id": test_account_id,
        },
    )

    # Set the JWT claims session variable.
    jwt_claims = json.dumps({"sub": test_user_id})
    connection.execute(text(f"SET request.jwt.claims = '{jwt_claims}'"))

    # Execute the function and validate the result.
    result = connection.execute(
        text("SELECT private.get_user_id_from_jwt()")
    ).fetchone()[0]
    assert str(result) == test_user_id
