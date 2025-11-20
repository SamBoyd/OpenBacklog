"""Junction table models for TurningPoint many-to-many relationships."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class TurningPointStoryArc(Base):
    """Junction table linking turning points to story arcs.

    This table implements the many-to-many relationship between
    turning points and story arcs (roadmap themes). One turning point
    can affect multiple arcs, and one arc can be affected by multiple turning points.

    Attributes:
        turning_point_id: Foreign key to turning_points table
        story_arc_id: Foreign key to roadmap_themes table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "turning_point_story_arcs"
    __table_args__ = ({"schema": "dev"},)

    turning_point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.turning_points.id", ondelete="CASCADE"),
        primary_key=True,
    )

    story_arc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="CASCADE"),
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


class TurningPointInitiative(Base):
    """Junction table linking turning points to initiatives.

    This table implements the many-to-many relationship between
    turning points and initiatives (beats). One turning point
    can affect multiple initiatives, and one initiative can be affected
    by multiple turning points.

    Attributes:
        turning_point_id: Foreign key to turning_points table
        initiative_id: Foreign key to initiative table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "turning_point_initiatives"
    __table_args__ = ({"schema": "dev"},)

    turning_point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.turning_points.id", ondelete="CASCADE"),
        primary_key=True,
    )

    initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.initiative.id", ondelete="CASCADE"),
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
