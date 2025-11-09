"""Tests for PostgreSQL MCP storage backend.

NOTE: These tests do not use the standard clean_tables fixture to avoid connection
pool conflicts between sync and async sessions. Tests are isolated via unique keys
and collections. If test pollution becomes an issue, clean the table manually:
    ENVIRONMENT=test python -c "from src.db import SessionLocal; from sqlalchemy import text; \
    s = SessionLocal(); s.execute(text('TRUNCATE TABLE private.mcp_oauth_storage')); s.commit()"
"""

import asyncio

import pytest

from src.mcp_server.storage import PostgreSQLMCPStorage


@pytest.fixture
async def storage():
    """Fixture for PostgreSQL storage backend.

    Creates a new engine and session_maker per test to avoid event loop conflicts.
    Each test gets its own event loop from pytest-asyncio, so we need to ensure
    both the engine and session maker are bound to the correct loop.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.config import settings

    # Create a new async engine bound to the current event loop
    test_engine = create_async_engine(
        settings.async_database_url,
        echo=False,
        pool_size=5,  # Smaller pool for tests
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # Create a session maker bound to the test engine
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    # Yield the storage backend
    yield PostgreSQLMCPStorage(session_maker)

    # Cleanup: dispose the engine to close all connections
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_put_and_get(storage: PostgreSQLMCPStorage):
    """Test basic put and get operations."""
    test_data = {"access_token": "test_token_123", "user_id": "user_456"}

    await storage.put("session:123", test_data)
    result = await storage.get("session:123")

    assert result == test_data


@pytest.mark.asyncio
async def test_get_nonexistent_key(storage: PostgreSQLMCPStorage):
    """Test getting a non-existent key returns None."""
    result = await storage.get("nonexistent:key")
    assert result is None


@pytest.mark.asyncio
async def test_put_with_collection(storage: PostgreSQLMCPStorage):
    """Test put and get with collections."""
    test_data = {"value": "test"}

    await storage.put("key1", test_data, collection="oauth")
    await storage.put("key1", {"value": "different"}, collection="sessions")

    result1 = await storage.get("key1", collection="oauth")
    result2 = await storage.get("key1", collection="sessions")

    assert result1 == test_data
    assert result2 == {"value": "different"}


@pytest.mark.asyncio
async def test_put_updates_existing(storage: PostgreSQLMCPStorage):
    """Test that put updates existing values (upsert behavior)."""
    await storage.put("key1", {"version": 1})
    await storage.put("key1", {"version": 2})

    result = await storage.get("key1")
    assert result == {"version": 2}


@pytest.mark.asyncio
async def test_put_updates_existing_with_collection(storage: PostgreSQLMCPStorage):
    """Test that put updates existing values (upsert behavior)."""
    await storage.put("key1", {"version": 1}, collection="oauth")
    await storage.put("key1", {"version": 2}, collection="oauth")

    result = await storage.get("key1", collection="oauth")
    assert result == {"version": 2}


@pytest.mark.asyncio
async def test_delete(storage: PostgreSQLMCPStorage):
    """Test delete operation."""
    await storage.put("key1", {"data": "value"})

    deleted = await storage.delete("key1")
    assert deleted is True

    result = await storage.get("key1")
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent(storage: PostgreSQLMCPStorage):
    """Test deleting a non-existent key returns False."""
    deleted = await storage.delete("nonexistent:key")
    assert deleted is False


@pytest.mark.asyncio
async def test_delete_with_collection(storage: PostgreSQLMCPStorage):
    """Test delete respects collections."""
    await storage.put("key1", {"data": "oauth"}, collection="oauth")
    await storage.put("key1", {"data": "sessions"}, collection="sessions")

    deleted = await storage.delete("key1", collection="oauth")
    assert deleted is True

    # Should only delete from oauth collection
    result_oauth = await storage.get("key1", collection="oauth")
    result_sessions = await storage.get("key1", collection="sessions")

    assert result_oauth is None
    assert result_sessions == {"data": "sessions"}


@pytest.mark.asyncio
async def test_ttl_with_expiration(storage: PostgreSQLMCPStorage):
    """Test TTL with expiration."""
    test_data = {"data": "value"}

    # Set TTL to 1 second
    await storage.put("temp:key", test_data, ttl=1.0)

    # Immediately check - should exist
    value, remaining_ttl = await storage.ttl("temp:key")
    assert value == test_data
    assert remaining_ttl is not None
    assert 0 < remaining_ttl <= 1.0

    # Wait for expiration
    await asyncio.sleep(1.1)

    # Should be expired now
    value, remaining_ttl = await storage.ttl("temp:key")
    assert value is None
    assert remaining_ttl is None


@pytest.mark.asyncio
async def test_ttl_without_expiration(storage: PostgreSQLMCPStorage):
    """Test TTL for key without expiration."""
    test_data = {"data": "value"}

    await storage.put("persistent:key", test_data)

    value, remaining_ttl = await storage.ttl("persistent:key")
    assert value == test_data
    assert remaining_ttl is None  # No expiration


@pytest.mark.asyncio
async def test_ttl_nonexistent_key(storage: PostgreSQLMCPStorage):
    """Test TTL for non-existent key."""
    value, remaining_ttl = await storage.ttl("nonexistent:key")
    assert value is None
    assert remaining_ttl is None


@pytest.mark.asyncio
async def test_get_filters_expired(storage: PostgreSQLMCPStorage):
    """Test that get() filters out expired entries."""
    test_data = {"data": "value"}

    # Set very short TTL
    await storage.put("temp:key", test_data, ttl=0.1)

    # Wait for expiration
    await asyncio.sleep(0.2)

    # get() should return None for expired key
    result = await storage.get("temp:key")
    assert result is None


@pytest.mark.asyncio
async def test_get_many(storage: PostgreSQLMCPStorage):
    """Test bulk get operation."""
    await storage.put("key1", {"value": 1})
    await storage.put("key2", {"value": 2})
    await storage.put("key3", {"value": 3})

    results = await storage.get_many(["key1", "key2", "nonexistent", "key3"])

    assert results == [
        {"value": 1},
        {"value": 2},
        None,
        {"value": 3},
    ]


@pytest.mark.asyncio
async def test_get_many_with_collection(storage: PostgreSQLMCPStorage):
    """Test bulk get with collections."""
    await storage.put("key1", {"value": "oauth1"}, collection="oauth")
    await storage.put("key2", {"value": "oauth2"}, collection="oauth")

    results = await storage.get_many(["key1", "key2"], collection="oauth")

    assert results == [
        {"value": "oauth1"},
        {"value": "oauth2"},
    ]


@pytest.mark.asyncio
async def test_get_many_filters_expired(storage: PostgreSQLMCPStorage):
    """Test that get_many filters expired entries."""
    await storage.put("key1", {"value": 1}, ttl=10)
    await storage.put("key2", {"value": 2}, ttl=0.1)

    await asyncio.sleep(0.2)

    results = await storage.get_many(["key1", "key2"])
    assert results == [{"value": 1}, None]


@pytest.mark.asyncio
async def test_put_many(storage: PostgreSQLMCPStorage):
    """Test bulk put operation."""
    keys = ["key1", "key2", "key3"]
    values = [{"value": 1}, {"value": 2}, {"value": 3}]

    await storage.put_many(keys, values)

    result1 = await storage.get("key1")
    result2 = await storage.get("key2")
    result3 = await storage.get("key3")

    assert result1 == {"value": 1}
    assert result2 == {"value": 2}
    assert result3 == {"value": 3}


@pytest.mark.asyncio
async def test_put_many_with_ttl(storage: PostgreSQLMCPStorage):
    """Test bulk put with individual TTLs."""
    keys = ["key1", "key2"]
    values = [{"value": 1}, {"value": 2}]
    ttls = [10.0, 0.1]

    await storage.put_many(keys, values, ttl=ttls)

    await asyncio.sleep(0.2)

    result1 = await storage.get("key1")
    result2 = await storage.get("key2")

    assert result1 == {"value": 1}  # Still exists
    assert result2 is None  # Expired


@pytest.mark.asyncio
async def test_put_many_validation_errors(storage: PostgreSQLMCPStorage):
    """Test put_many validation errors."""
    # Mismatched keys and values length
    with pytest.raises(ValueError, match="keys and values must have the same length"):
        await storage.put_many(["key1"], [{"value": 1}, {"value": 2}])

    # Mismatched keys and ttl length
    with pytest.raises(ValueError, match="keys and ttl must have the same length"):
        await storage.put_many(
            ["key1", "key2"], [{"value": 1}, {"value": 2}], ttl=[1.0]
        )


@pytest.mark.asyncio
async def test_delete_many(storage: PostgreSQLMCPStorage):
    """Test bulk delete operation."""
    await storage.put("key1", {"value": 1})
    await storage.put("key2", {"value": 2})
    await storage.put("key3", {"value": 3})

    deleted_count = await storage.delete_many(["key1", "key2", "nonexistent"])

    assert deleted_count == 2

    result1 = await storage.get("key1")
    result2 = await storage.get("key2")
    result3 = await storage.get("key3")

    assert result1 is None
    assert result2 is None
    assert result3 == {"value": 3}


@pytest.mark.asyncio
async def test_delete_many_with_collection(storage: PostgreSQLMCPStorage):
    """Test bulk delete with collections."""
    await storage.put("key1", {"value": "oauth1"}, collection="oauth")
    await storage.put("key2", {"value": "oauth2"}, collection="oauth")
    await storage.put("key1", {"value": "session1"}, collection="sessions")

    deleted_count = await storage.delete_many(["key1", "key2"], collection="oauth")

    assert deleted_count == 2

    # Should not delete from sessions collection
    result_session = await storage.get("key1", collection="sessions")
    assert result_session == {"value": "session1"}


@pytest.mark.asyncio
async def test_ttl_many(storage: PostgreSQLMCPStorage):
    """Test bulk TTL operation."""
    await storage.put("key1", {"value": 1}, ttl=10.0)
    await storage.put("key2", {"value": 2})  # No TTL
    await storage.put("key3", {"value": 3}, ttl=0.1)

    await asyncio.sleep(0.2)

    results = await storage.ttl_many(["key1", "key2", "key3", "nonexistent"])

    # key1: should have value and TTL
    assert results[0][0] == {"value": 1}
    assert results[0][1] is not None
    assert 0 < results[0][1] <= 10.0

    # key2: should have value but no TTL
    assert results[1][0] == {"value": 2}
    assert results[1][1] is None

    # key3: should be expired
    assert results[2][0] is None
    assert results[2][1] is None

    # nonexistent: should be None
    assert results[3][0] is None
    assert results[3][1] is None


@pytest.mark.asyncio
async def test_empty_bulk_operations(storage: PostgreSQLMCPStorage):
    """Test bulk operations with empty lists."""
    # Empty get_many
    results = await storage.get_many([])
    assert results == []

    # Empty put_many
    await storage.put_many([], [])
    # Should not raise an error

    # Empty delete_many
    deleted = await storage.delete_many([])
    assert deleted == 0

    # Empty ttl_many
    results = await storage.ttl_many([])
    assert results == []


@pytest.mark.asyncio
async def test_cleanup_expired(storage: PostgreSQLMCPStorage):
    """Test cleanup_expired removes only expired tokens."""
    # Create some tokens with different TTLs
    await storage.put("permanent:key", {"data": "permanent"})  # No expiration
    await storage.put("short:key", {"data": "short"}, ttl=0.1)  # Expires soon
    await storage.put("long:key", {"data": "long"}, ttl=10.0)  # Expires later
    await storage.put(
        "expired:key", {"data": "expired"}, collection="oauth", ttl=0.1
    )  # Expires soon with collection

    # Wait for short TTL tokens to expire
    await asyncio.sleep(0.2)

    # Run cleanup
    deleted_count = await storage.cleanup_expired()

    # Should have deleted 2 tokens (short:key and expired:key)
    assert deleted_count == 2

    # Verify expired tokens are gone
    assert await storage.get("short:key") is None
    assert await storage.get("expired:key", collection="oauth") is None

    # Verify non-expired tokens still exist
    assert await storage.get("permanent:key") == {"data": "permanent"}
    assert await storage.get("long:key") == {"data": "long"}


@pytest.mark.asyncio
async def test_cleanup_expired_no_tokens(storage: PostgreSQLMCPStorage):
    """Test cleanup_expired when there are no expired tokens."""
    # Create only non-expired tokens
    await storage.put("key1", {"data": "value"}, ttl=10.0)
    await storage.put("key2", {"data": "value"}, ttl=10.0)

    # Run cleanup
    deleted_count = await storage.cleanup_expired()

    # Should have deleted nothing
    assert deleted_count == 0

    # Verify tokens still exist
    assert await storage.get("key1") == {"data": "value"}
    assert await storage.get("key2") == {"data": "value"}


@pytest.mark.asyncio
async def test_cleanup_expired_all_tokens(storage: PostgreSQLMCPStorage):
    """Test cleanup_expired when all tokens are expired."""
    # Create only expired tokens
    await storage.put("key1", {"data": "value"}, ttl=0.1)
    await storage.put("key2", {"data": "value"}, ttl=0.1)
    await storage.put("key3", {"data": "value"}, ttl=0.1)

    # Wait for expiration
    await asyncio.sleep(0.2)

    # Run cleanup
    deleted_count = await storage.cleanup_expired()

    # Should have deleted all 3
    assert deleted_count == 3

    # Verify all tokens are gone
    assert await storage.get("key1") is None
    assert await storage.get("key2") is None
    assert await storage.get("key3") is None
