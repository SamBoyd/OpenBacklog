# pragma: no mutate

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypedDict, Union

from dateutil.parser import isoparse  # Keep for potential use if needed

# Removed FastAPI Users dependencies - now using direct SQLAlchemy models
from pydantic import BaseModel, Field, ValidationInfo, field_validator

# Define UUID_ID type (previously from fastapi_users_db_sqlalchemy)
UUID_ID = uuid.UUID
from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

# Forward declaration for type hints
if TYPE_CHECKING:
    from src.github_app.models import RepositoryFileIndex
    from src.initiative_management.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
    from src.narrative.aggregates.conflict import Conflict
    from src.narrative.aggregates.hero import Hero
    from src.narrative.aggregates.turning_point import TurningPoint
    from src.narrative.aggregates.villain import Villain
    from src.roadmap_intelligence.aggregates.prioritized_roadmap import (
        PrioritizedRoadmap,
    )

title_max_length: int = 100
description_max_length: int = 500


class InitiativeType(str, enum.Enum):
    FEATURE = "FEATURE"
    BUGFIX = "BUGFIX"
    RESEARCH = "RESEARCH"
    CHORE = "CHORE"


class TaskType(str, enum.Enum):
    CODING = "CODING"
    TESTING = "TESTING"
    DOCUMENTATION = "DOCUMENTATION"
    DESIGN = "DESIGN"


class TaskStatus(str, enum.Enum):
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class InitiativeStatus(str, enum.Enum):
    BACKLOG = "BACKLOG"
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class PriorityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(str, enum.Enum):
    INITIATIVE = "INITIATIVE"
    TASK = "TASK"
    CHECKLIST = "CHECKLIST"


class FieldType(str, enum.Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    SELECT = "SELECT"
    MULTI_SELECT = "MULTI_SELECT"
    STATUS = "STATUS"
    DATE = "DATE"
    CHECKBOX = "CHECKBOX"
    URL = "URL"
    EMAIL = "EMAIL"
    PHONE = "PHONE"


class GroupType(str, enum.Enum):
    EXPLICIT = "EXPLICIT"
    SMART = "SMART"


class PublicBase:
    __abstract__ = True
    __table_args__ = {"schema": "dev"}

    def __init__(self, **kwargs):  # type: ignore
        super().__init__(**kwargs)


class PrivateBase:
    __abstract__ = True
    __table_args__ = {"schema": "private"}

    def __init__(self, **kwargs):  # type: ignore
        super().__init__(**kwargs)


DEFAULT_USER_DISPLAY_PREFERENCES = dict(
    timezone="UTC",
    language="English",
    dateFormat="YYYY-MM-DD",
    theme="Light",
)


class User(PrivateBase, Base):
    __tablename__ = "users"

    # Primary key (previously from SQLAlchemyBaseUserTableUUID)
    id: Mapped[UUID_ID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # Required fields from FastAPI Users base class
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Custom fields
    name: Mapped[str] = mapped_column(String, nullable=True)
    last_logged_in: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )

    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_preferences: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        nullable=True,
        default=DEFAULT_USER_DISPLAY_PREFERENCES,
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    account_details: Mapped["UserAccountDetails"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        innerjoin=True,
    )

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, User):
            return False

        return self.id == value.id and self.name == value.name

    def __hash__(self) -> int:
        return hash((self.id, self.name))

    def __str__(self) -> str:
        return f"<User email={self.email} name={self.name}>"

    def __repr__(self) -> str:
        return f"<User email={self.email} name={self.name}>"


class UserAccountStatus(str, enum.Enum):
    NEW = "NEW"
    ACTIVE_SUBSCRIPTION = "ACTIVE_SUBSCRIPTION"
    NO_SUBSCRIPTION = "NO_SUBSCRIPTION"
    METERED_BILLING = "METERED_BILLING"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class UserAccountDetails(PrivateBase, Base):
    __tablename__ = "user_account_details"
    __table_args__ = ({"schema": "private"},)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"),
        nullable=False,
        primary_key=True,
    )
    user: Mapped["User"] = relationship("User", back_populates="account_details")

    balance_cents: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus), nullable=False, default=UserAccountStatus.NEW
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_usage_query_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Onboarding tracking
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Subscription cancellation tracking
    subscription_cancel_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    subscription_canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    subscription_cancel_at_period_end: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )

    # Monthly credits tracking
    monthly_credits_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    monthly_credits_used: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    next_billing_cycle_starts: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


@event.listens_for(User, "after_insert")
def create_user_account_details(mapper, connection, target):
    """Automatically create UserAccountDetails when a User is created."""
    # Insert UserAccountDetails using the same connection/transaction
    # This ensures atomicity with the User creation
    connection.execute(
        UserAccountDetails.__table__.insert().values(
            user_id=target.id,
            status=UserAccountStatus.NEW.value,
            onboarding_completed=False,
        )
    )


class OAuthAccount(PrivateBase, Base):
    __tablename__ = "oauth_account"

    # Primary key
    id: Mapped[UUID_ID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # Required fields from FastAPI Users base class
    oauth_name: Mapped[str] = mapped_column(String(100), nullable=False)
    access_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    account_id: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    account_email: Mapped[str] = mapped_column(String(320), nullable=False)

    # Foreign key to user
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")


class AccessToken(PrivateBase, Base):
    __tablename__ = "access_token"

    # Token field (primary key-like but not UUID)
    token: Mapped[str] = mapped_column(String(1024), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    # Foreign key to user
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False
    )


class Workspace(PublicBase, Base):
    __tablename__ = "workspace"

    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    icon: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="workspaces")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    initiatives: Mapped[List["Initiative"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    field_definitions: Mapped[List["FieldDefinition"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    vision: Mapped["ProductVision"] = relationship(
        "ProductVision",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )
    strategic_pillars: Mapped[List["StrategicPillar"]] = relationship(
        "StrategicPillar",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    product_outcomes: Mapped[List["ProductOutcome"]] = relationship(
        "ProductOutcome",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    roadmap_themes: Mapped[List["RoadmapTheme"]] = relationship(
        "RoadmapTheme",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    prioritized_roadmap: Mapped["PrioritizedRoadmap"] = relationship(
        "PrioritizedRoadmap",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )
    strategic_initiatives: Mapped[List["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    heroes: Mapped[List["Hero"]] = relationship(
        "Hero",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    villains: Mapped[List["Villain"]] = relationship(
        "Villain",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    conflicts: Mapped[List["Conflict"]] = relationship(
        "Conflict",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    turning_points: Mapped[List["TurningPoint"]] = relationship(
        "TurningPoint",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    def dict(self) -> Dict[str, Union[str, datetime]]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@event.listens_for(Workspace, "after_insert")
def create_workspace_dependencies(mapper, connection, target):
    """Automatically create required 1:1 entities when a Workspace is created.

    Creates:
    - PrioritizedRoadmap (empty prioritized_theme_ids list)
    - ProductVision (empty vision_text)

    This ensures that workspaces always have these required entities,
    preventing race conditions in GET endpoints that expect them to exist.
    """
    from sqlalchemy import Table

    # Import models to get table definitions
    from src.roadmap_intelligence.aggregates.prioritized_roadmap import (
        PrioritizedRoadmap,
    )
    from src.strategic_planning.aggregates.product_vision import ProductVision

    # Create PrioritizedRoadmap
    prioritized_roadmap_table = PrioritizedRoadmap.__table__
    connection.execute(
        prioritized_roadmap_table.insert().values(
            id=uuid.uuid4(),
            user_id=target.user_id,
            workspace_id=target.id,
            prioritized_theme_ids=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )

    # Create ProductVision with empty vision
    product_vision_table = ProductVision.__table__
    connection.execute(
        product_vision_table.insert().values(
            id=uuid.uuid4(),
            user_id=target.user_id,
            workspace_id=target.id,
            vision_text="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )


class DoableBase:
    __abstract__ = True

    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    workspace_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("dev.workspace.id", ondelete="cascade"), nullable=False, index=True
    )

    identifier: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(
        String, nullable=False, default=str, server_default=""
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    has_pending_job: Mapped[bool] = mapped_column(Boolean, default=False)


class Task(DoableBase, PublicBase, Base):
    __tablename__ = "task"

    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),  # Generates a UUID in PostgreSQL
    )

    identifier: Mapped[str] = mapped_column(String, nullable=False, index=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, schema="dev"),
        nullable=False,
        default=TaskStatus.TO_DO,
        server_default=text("'TO_DO'"),
    )

    type: Mapped[str] = mapped_column(String, nullable=True)
    initiative_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.initiative.id"), nullable=False
    )
    initiative: Mapped[Optional["Initiative"]] = relationship(back_populates="tasks")
    workspace: Mapped["Workspace"] = relationship(back_populates="tasks")

    checklist: Mapped[List["ChecklistItem"]] = relationship()

    field_definitions: Mapped[List["FieldDefinition"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    orderings: Mapped[List["Ordering"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    properties: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        nullable=False,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    def __init__(self, **kwargs):  # type: ignore
        if "checklist" not in kwargs or kwargs["checklist"] is None:
            kwargs["checklist"] = []
        super().__init__(**kwargs)

    def truncate_fields(self) -> None:
        if self.title is not None:
            self.title = self.title[:title_max_length]
        if self.description is not None:
            self.description = self.description[:description_max_length]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Task):
            return False

        return (
            self.id == value.id
            and self.identifier == value.identifier
            and self.user_id == value.user_id
            and self.workspace_id == value.workspace_id
            and self.title == value.title
            and self.description == value.description
            and self.created_at == value.created_at
            and self.updated_at == value.updated_at
            and self.status == value.status
            and self.has_pending_job == value.has_pending_job
            and self.type == value.type
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "identifier": self.identifier,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "has_pending_job": self.has_pending_job,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": str(self.user_id),
            "workspace_id": str(self.workspace_id),
            "initiative_id": str(self.initiative_id) if self.initiative_id else None,
            "checklist": [
                checklist_item.to_dict() for checklist_item in self.checklist
            ],
        }


class Initiative(DoableBase, PublicBase, Base):
    __tablename__ = "initiative"

    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),  # Generates a UUID in PostgreSQL
    )

    __table_args__ = (  # type: ignore
        UniqueConstraint(
            "user_id",
            "workspace_id",
            "identifier",
            name="uq_initiative_user_workspace_identifier",
        ),
        {"schema": "dev"},
    )

    status: Mapped[InitiativeStatus] = mapped_column(
        Enum(InitiativeStatus, schema="dev"),
        nullable=False,
        default=InitiativeStatus.BACKLOG,
        server_default=text("'BACKLOG'"),
    )

    type: Mapped[str] = mapped_column(String, nullable=True)

    tasks: Mapped[List[Task]] = relationship(
        back_populates="initiative", cascade="all, delete-orphan"
    )
    workspace: Mapped["Workspace"] = relationship(back_populates="initiatives")

    field_definitions: Mapped[List["FieldDefinition"]] = relationship(
        back_populates="initiative", cascade="all, delete-orphan"
    )

    strategic_context: Mapped[Optional["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        back_populates="initiative",
        uselist=False,
        cascade="all, delete-orphan",
    )

    turning_points: Mapped[List["TurningPoint"]] = relationship(
        "TurningPoint",
        secondary="dev.turning_point_initiatives",
        back_populates="initiatives",
    )

    properties: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        nullable=False,
        default={},
        server_default=text("'{}'::jsonb"),
    )

    blocked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.initiative.id"), nullable=True, index=True
    )
    blocked_by: Mapped[Optional["Initiative"]] = relationship(
        "Initiative",
        back_populates="blocking",
        foreign_keys=[blocked_by_id],
    )
    blocking: Mapped[List["Initiative"]] = relationship(
        "Initiative",
        back_populates="blocked_by",
        remote_side=[id],
    )

    groups: Mapped[List["Group"]] = relationship(
        secondary="dev.initiative_group", back_populates="initiatives"
    )

    orderings: Mapped[List["Ordering"]] = relationship(
        back_populates="initiative", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):  # type: ignore
        super().__init__(**kwargs)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Initiative):
            return False

        return (
            self.id == value.id
            and self.identifier == value.identifier
            and self.user_id == value.user_id
            and self.workspace_id == value.workspace_id
            and self.type == value.type
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "identifier": self.identifier,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "tasks": [task.to_dict() for task in self.tasks],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": str(self.user_id),
            "workspace_id": str(self.workspace_id),
            "status": self.status,
            "has_pending_job": self.has_pending_job,
        }


class ChecklistItem(PublicBase, Base):
    __tablename__ = "checklist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")
    title: Mapped[str] = mapped_column(String)
    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)
    order: Mapped[Integer] = mapped_column(Integer, default=0, server_default=text("0"))

    task_id: Mapped[Optional[UUID_ID]] = mapped_column(
        ForeignKey("dev.task.id"), nullable=False
    )

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ChecklistItem):
            return False

        return (
            self.id == value.id
            and self.title == value.title
            and self.is_complete == value.is_complete
            and self.order == value.order
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "task_id": str(self.task_id),
            "user_id": str(self.user_id),
            "is_complete": self.is_complete,
            "order": self.order,
        }


class GitHubInstallation(PrivateBase, Base):
    __tablename__ = "github_installation"

    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    installation_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.workspace.id"), nullable=True, index=True
    )
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace")

    # Relationship to repository file indexes
    repository_file_indexes: Mapped[List["RepositoryFileIndex"]] = relationship(
        "RepositoryFileIndex",
        back_populates="github_installation",
        cascade="all, delete-orphan",
        lazy="select",
    )


class ContextDocument(PublicBase, Base):
    """Model representing a context document."""

    __tablename__ = "context_document"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")
    workspace_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("dev.workspace.id", ondelete="cascade"), nullable=False, index=True
    )
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace")

    model_config = {"from_attributes": True}


class FieldDefinition(PublicBase, Base):
    """Model representing a user-defined field for a initiative or task."""

    __tablename__ = "field_definition"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "entity_type",
            "key",
            name="uq_field_definition_workspace_entity_key",
        ),
        {"schema": "dev"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dev.workspace.id", ondelete="cascade"), nullable=False, index=True
    )
    workspace: Mapped["Workspace"] = relationship(back_populates="field_definitions")
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")

    initiative_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.initiative.id"), nullable=True
    )
    initiative: Mapped[Optional["Initiative"]] = relationship(
        back_populates="field_definitions"
    )

    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.task.id"), nullable=True
    )
    task: Mapped[Optional["Task"]] = relationship(back_populates="field_definitions")

    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, schema="dev"), nullable=False
    )
    key: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    field_type: Mapped[FieldType] = mapped_column(
        Enum(FieldType, schema="dev"), nullable=False
    )
    is_core: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    column_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    config: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB()),
        nullable=False,
        default={},
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        server_default=text("now()"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "entity_type": self.entity_type.value,
            "key": self.key,
            "name": self.name,
            "field_type": self.field_type.value,
            "is_core": self.is_core,
            "column_name": self.column_name,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Group(PublicBase, Base):
    __tablename__ = "group"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dev.workspace.id", ondelete="cascade"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    group_type: Mapped[GroupType] = mapped_column(
        Enum(GroupType, schema="dev"), nullable=False
    )
    group_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSONB()), nullable=True
    )
    query_criteria: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSONB()), nullable=True
    )
    parent_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.group.id", ondelete="cascade"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship()
    workspace: Mapped["Workspace"] = relationship()

    # Self-referential relationship for hierarchy
    parent: Mapped[Optional["Group"]] = relationship(
        "Group", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Group"]] = relationship("Group", back_populates="parent")

    # Relationship to initiatives via association table
    initiatives: Mapped[List["Initiative"]] = relationship(
        secondary="dev.initiative_group", back_populates="groups"
    )


class InitiativeGroup(PublicBase, Base):
    __tablename__ = "initiative_group"
    __table_args__ = (
        PrimaryKeyConstraint("initiative_id", "group_id"),
        {"schema": "dev"},
    )

    initiative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dev.initiative.id", ondelete="cascade"), nullable=False
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dev.group.id", ondelete="cascade"), nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")


#  Ordering ------------------------------------------------------------


class ContextType(enum.Enum):
    GROUP = "GROUP"
    STATUS_LIST = "STATUS_LIST"

    # Leaving the commented out type value here
    # because the TASK_CHECKLIST is still a thing in the database
    # but isnt used by the code
    # TASK_CHECKLIST = "TASK_CHECKLIST"


class Ordering(Base):
    __tablename__ = "orderings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")

    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.workspace.id"), nullable=True, index=True
    )
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace")

    # context_type defines the List that the ordering is for
    context_type = Column(Enum(ContextType), nullable=False)
    context_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # id of the owning group if ContextType.GROUP

    entity_type = Column(Enum(EntityType), nullable=False)

    # Direct foreign key relationships
    initiative_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.initiative.id", ondelete="cascade"), nullable=True, index=True
    )
    initiative: Mapped[Optional["Initiative"]] = relationship(
        "Initiative", back_populates="orderings"
    )

    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("dev.task.id", ondelete="cascade"), nullable=True, index=True
    )
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="orderings")

    position = Column(String, nullable=False)  # e.g., 'LexaRank position'

    __table_args__ = (
        UniqueConstraint(
            "context_type",
            "context_id",
            "entity_type",
            "task_id",
            "initiative_id",
            name="uq_context_entity_once",
        ),
        Index(
            "ix_context_position",
            "context_type",
            "context_id",
            "entity_type",
            "position",
        ),
        Index("ix_entity_lookup", "entity_type", "initiative_id", "task_id"),
    )


# Import related models to ensure they're in the SQLAlchemy registry
# This must be done after the main models are defined to avoid circular imports
from src.github_app.models import RepositoryFileIndex  # noqa: E402

# Import junction table models to ensure they're registered with SQLAlchemy
from src.initiative_management.models import (
    StrategicInitiativeConflict,
    StrategicInitiativeHero,
    StrategicInitiativeVillain,
)
from src.narrative.models import TurningPointInitiative, TurningPointStoryArc
from src.roadmap_intelligence.aggregates.prioritized_roadmap import (  # noqa: E402
    PrioritizedRoadmap,
)
from src.roadmap_intelligence.models import RoadmapThemeHero, RoadmapThemeVillain
