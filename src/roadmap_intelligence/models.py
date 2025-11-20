"""Junction table models for RoadmapTheme many-to-many relationships."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class RoadmapThemeHero(Base):
    """Junction table linking roadmap themes to heroes.

    This table implements the many-to-many relationship between
    roadmap themes (story arcs) and heroes. One theme can concern
    multiple heroes, and one hero can be featured in multiple themes.

    Attributes:
        roadmap_theme_id: Foreign key to roadmap_themes table
        hero_id: Foreign key to heroes table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "roadmap_theme_heroes"
    __table_args__ = ({"schema": "dev"},)

    roadmap_theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="CASCADE"),
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


class RoadmapThemeVillain(Base):
    """Junction table linking roadmap themes to villains.

    This table implements the many-to-many relationship between
    roadmap themes (story arcs) and villains. One theme can oppose
    multiple villains, and one villain can be opposed by multiple themes.

    Attributes:
        roadmap_theme_id: Foreign key to roadmap_themes table
        villain_id: Foreign key to villains table
        user_id: Foreign key to user (for RLS)
        created_at: Timestamp when the link was created
    """

    __tablename__ = "roadmap_theme_villains"
    __table_args__ = ({"schema": "dev"},)

    roadmap_theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="CASCADE"),
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
