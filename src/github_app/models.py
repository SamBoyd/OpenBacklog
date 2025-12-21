import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.db import Base

if TYPE_CHECKING:
    from src.models import GitHubInstallation


class PrivateBase:
    __abstract__ = True
    __table_args__ = {"schema": "private"}

    def __init__(self, **kwargs):  # type: ignore
        super().__init__(**kwargs)


class RepositoryFileIndex(PrivateBase, Base):
    """
    Cached file index for GitHub repositories to enable fast autocomplete.

    Stores a searchable string of all file paths in a repository,
    updated via GitHub webhooks when repository contents change.
    """

    __tablename__ = "repository_file_index"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Foreign key to GitHub installation
    github_installation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.github_installation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository identifier in "owner/repo" format
    repository_full_name: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )

    # Newline-separated sorted list of file paths for client-side search
    file_search_string: Mapped[str] = mapped_column(Text, nullable=False)

    # Commit SHA for webhook synchronization
    last_indexed_commit_sha: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )

    # Automatic timestamp for cache invalidation
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()"), default=datetime.now
    )

    # Relationships
    github_installation: Mapped["GitHubInstallation"] = relationship(
        "GitHubInstallation", back_populates="repository_file_indexes"
    )

    def __repr__(self) -> str:
        return f"<RepositoryFileIndex(repository='{self.repository_full_name}', files={len(self.file_search_string.split())})>"
