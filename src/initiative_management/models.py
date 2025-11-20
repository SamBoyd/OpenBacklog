"""Junction table models for StrategicInitiative many-to-many relationships."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class StrategicInitiativeHero(Base):
    """Junction table linking strategic initiatives to heroes.

    This table implements the many-to-many relationship between
    strategic initiatives and heroes. One initiative can serve
    multiple heroes, and one hero can be served by multiple initiatives.

    Attributes:
        strategic_initiative_id: Foreign key to strategic_initiatives table
        hero_id: Foreign key to heroes table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "strategic_initiative_heroes"
    __table_args__ = ({"schema": "dev"},)

    strategic_initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.strategic_initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    )

    hero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.heroes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class StrategicInitiativeVillain(Base):
    """Junction table linking strategic initiatives to villains.

    This table implements the many-to-many relationship between
    strategic initiatives and villains. One initiative can confront
    multiple villains, and one villain can be confronted by multiple initiatives.

    Attributes:
        strategic_initiative_id: Foreign key to strategic_initiatives table
        villain_id: Foreign key to villains table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "strategic_initiative_villains"
    __table_args__ = ({"schema": "dev"},)

    strategic_initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.strategic_initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    )

    villain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.villains.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class StrategicInitiativeConflict(Base):
    """Junction table linking strategic initiatives to conflicts.

    This table implements the many-to-many relationship between
    strategic initiatives and conflicts. One initiative can address
    multiple conflicts, and one conflict can be addressed by multiple initiatives.

    Attributes:
        strategic_initiative_id: Foreign key to strategic_initiatives table
        conflict_id: Foreign key to conflicts table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "strategic_initiative_conflicts"
    __table_args__ = ({"schema": "dev"},)

    strategic_initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.strategic_initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    )

    conflict_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.conflicts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
