"""PostgreSQL storage backend for FastMCP OAuth tokens."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence, SupportsFloat

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.mcp_server.models import MCPOAuthStorage

logger = logging.getLogger(__name__)


class PostgreSQLMCPStorage:
    """
    PostgreSQL implementation of AsyncKeyValueProtocol for FastMCP storage.

    Provides persistent, TTL-aware key-value storage for OAuth tokens and
    session data using PostgreSQL as the backend.
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        """
        Initialize the PostgreSQL storage backend.

        Args:
            session_maker: SQLAlchemy async session factory
        """
        self.session_maker = session_maker

    def _build_upsert_statement(
        self,
        key: str,
        value: dict[str, Any],
        collection: str | None,
        expires_at: datetime | None,
    ):
        """
        Build an INSERT...ON CONFLICT DO UPDATE statement for upsert operations.

        Uses partial unique indexes to handle NULL collection values correctly:
        - NULL collection: UNIQUE (key) WHERE collection IS NULL
        - Non-NULL collection: UNIQUE (collection, key) WHERE collection IS NOT NULL

        Args:
            key: The storage key
            value: The value to store
            collection: Optional collection/namespace for the key
            expires_at: Optional expiration timestamp

        Returns:
            SQLAlchemy insert statement with ON CONFLICT clause
        """
        stmt = insert(MCPOAuthStorage).values(
            key=key,
            collection=collection,
            value=value,
            expires_at=expires_at,
            updated_at=datetime.now(timezone.utc),
        )

        # Use the appropriate partial index depending on whether collection is NULL
        if collection is None:
            # Use partial index for NULL collection: UNIQUE (key) WHERE collection IS NULL
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"],
                index_where=MCPOAuthStorage.collection.is_(None),
                set_={
                    "value": value,
                    "expires_at": expires_at,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        else:
            # Use partial index for non-NULL collection: UNIQUE (collection, key) WHERE collection IS NOT NULL
            stmt = stmt.on_conflict_do_update(
                index_elements=["collection", "key"],
                index_where=MCPOAuthStorage.collection.isnot(None),
                set_={
                    "value": value,
                    "expires_at": expires_at,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

        return stmt

    async def get(
        self, key: str, *, collection: str | None = None
    ) -> dict[str, Any] | None:
        """
        Retrieve a value by key from the specified collection.

        Args:
            key: The storage key
            collection: Optional collection/namespace for the key

        Returns:
            The value associated with the key, or None if not found or expired
        """
        async with self.session_maker() as session:
            stmt = select(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key == key,
                    MCPOAuthStorage.collection == collection,
                    # Filter out expired entries
                    (
                        (MCPOAuthStorage.expires_at.is_(None))
                        | (MCPOAuthStorage.expires_at > datetime.now(timezone.utc))
                    ),
                )
            )

            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                return None

            return row.value

    async def put(
        self,
        key: str,
        value: dict[str, Any],
        *,
        collection: str | None = None,
        ttl: SupportsFloat | None = None,
    ) -> None:
        """
        Store a key-value pair with optional TTL.

        Args:
            key: The storage key
            value: The value to store (must be JSON-serializable dict)
            collection: Optional collection/namespace for the key
            ttl: Time-to-live in seconds (None = no expiration)
        """
        async with self.session_maker() as session:
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=float(ttl))

            stmt = self._build_upsert_statement(key, value, collection, expires_at)
            await session.execute(stmt)
            await session.commit()

    async def delete(self, key: str, *, collection: str | None = None) -> bool:
        """
        Delete a key-value pair.

        Args:
            key: The storage key
            collection: Optional collection/namespace for the key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        async with self.session_maker() as session:
            stmt = delete(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key == key,
                    MCPOAuthStorage.collection == collection,
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

    async def ttl(
        self, key: str, *, collection: str | None = None
    ) -> tuple[dict[str, Any] | None, float | None]:
        """
        Retrieve the value and TTL information for a key.

        Args:
            key: The storage key
            collection: Optional collection/namespace for the key

        Returns:
            Tuple of (value, remaining_ttl_seconds) or (None, None) if not found
        """
        async with self.session_maker() as session:
            stmt = select(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key == key,
                    MCPOAuthStorage.collection == collection,
                )
            )

            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                return (None, None)

            # Check if expired
            if row.expires_at is not None and row.expires_at <= datetime.now(
                timezone.utc
            ):
                return (None, None)

            # Calculate remaining TTL
            remaining_ttl = None
            if row.expires_at is not None:
                remaining_ttl = (
                    row.expires_at - datetime.now(timezone.utc)
                ).total_seconds()
                # Ensure non-negative
                remaining_ttl = max(0.0, remaining_ttl)

            return (row.value, remaining_ttl)

    # Bulk operations for efficiency

    async def get_many(
        self, keys: list[str], *, collection: str | None = None
    ) -> list[dict[str, Any] | None]:
        """
        Retrieve multiple values by key.

        Args:
            keys: List of storage keys
            collection: Optional collection/namespace for the keys

        Returns:
            List of values in the same order as keys (None for missing/expired)
        """
        if not keys:
            return []

        async with self.session_maker() as session:
            stmt = select(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key.in_(keys),
                    MCPOAuthStorage.collection == collection,
                    # Filter out expired entries
                    (
                        (MCPOAuthStorage.expires_at.is_(None))
                        | (MCPOAuthStorage.expires_at > datetime.now(timezone.utc))
                    ),
                )
            )

            result = await session.execute(stmt)
            rows = result.scalars().all()

            # Build a lookup map
            value_map = {row.key: row.value for row in rows}

            # Return values in the same order as input keys
            return [value_map.get(key) for key in keys]

    async def put_many(
        self,
        keys: list[str],
        values: Sequence[dict[str, Any]],
        *,
        collection: str | None = None,
        ttl: Sequence[SupportsFloat | None] | None = None,
    ) -> None:
        """
        Store multiple key-value pairs.

        Args:
            keys: List of storage keys
            values: List of values to store
            collection: Optional collection/namespace for the keys
            ttl: Optional list of TTLs in seconds (None for no expiration)
        """
        if not keys:
            return

        if len(keys) != len(values):
            raise ValueError("keys and values must have the same length")

        if ttl is not None and len(keys) != len(ttl):
            raise ValueError("keys and ttl must have the same length")

        async with self.session_maker() as session:
            for i, key in enumerate(keys):
                value = values[i]
                item_ttl = ttl[i] if ttl is not None else None

                expires_at = None
                if item_ttl is not None:
                    expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=float(item_ttl)
                    )

                stmt = self._build_upsert_statement(key, value, collection, expires_at)
                await session.execute(stmt)

            await session.commit()

    async def delete_many(
        self, keys: list[str], *, collection: str | None = None
    ) -> int:
        """
        Delete multiple keys.

        Args:
            keys: List of storage keys
            collection: Optional collection/namespace for the keys

        Returns:
            Count of deleted keys
        """
        if not keys:
            return 0

        async with self.session_maker() as session:
            stmt = delete(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key.in_(keys),
                    MCPOAuthStorage.collection == collection,
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount

    async def ttl_many(
        self, keys: list[str], *, collection: str | None = None
    ) -> list[tuple[dict[str, Any] | None, float | None]]:
        """
        Retrieve multiple values and TTL information.

        Args:
            keys: List of storage keys
            collection: Optional collection/namespace for the keys

        Returns:
            List of (value, remaining_ttl_seconds) tuples in same order as keys
        """
        if not keys:
            return []

        async with self.session_maker() as session:
            stmt = select(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.key.in_(keys),
                    MCPOAuthStorage.collection == collection,
                )
            )

            result = await session.execute(stmt)
            rows = result.scalars().all()

            # Build a lookup map
            now = datetime.now(timezone.utc)
            row_map = {}
            for row in rows:
                # Check if expired
                if row.expires_at is not None and row.expires_at <= now:
                    row_map[row.key] = (None, None)
                else:
                    remaining_ttl = None
                    if row.expires_at is not None:
                        remaining_ttl = (row.expires_at - now).total_seconds()
                        remaining_ttl = max(0.0, remaining_ttl)
                    row_map[row.key] = (row.value, remaining_ttl)

            # Return in the same order as input keys
            return [row_map.get(key, (None, None)) for key in keys]

    async def cleanup_expired(self) -> int:
        """
        Delete all expired tokens from storage.

        Returns:
            Count of deleted tokens
        """
        async with self.session_maker() as session:
            stmt = delete(MCPOAuthStorage).where(
                and_(
                    MCPOAuthStorage.expires_at.isnot(None),
                    MCPOAuthStorage.expires_at <= datetime.now(timezone.utc),
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount
