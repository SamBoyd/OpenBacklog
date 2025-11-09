"""SQLAlchemy models for MCP server storage."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import TIMESTAMP, UUID, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base
from src.models import PrivateBase


class MCPOAuthStorage(PrivateBase, Base):
    """
    Storage for FastMCP OAuth tokens and session data.

    Implements persistent storage for the MCP server's Auth0 OAuth flow,
    storing access tokens, refresh tokens, and session state with optional TTL.
    """

    __tablename__ = "mcp_oauth_storage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Optional collection for logical grouping (like Redis databases)
    collection: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Storage key (unique within a collection)
    key: Mapped[str] = mapped_column(String(512), nullable=False)

    # Value stored as JSON (encrypted by FernetEncryptionWrapper)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Optional expiration timestamp for TTL support
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
