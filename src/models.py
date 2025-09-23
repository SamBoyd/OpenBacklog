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
    from src.accounting.models import UserAccountDetails
    from src.github_app.models import RepositoryFileIndex

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


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


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


class APIProvider(str, enum.Enum):
    OPENAI = "OPENAI"
    LITELLM = "LITELLM"
    OPENBACKLOG = "OPENBACKLOG"


class Lens(str, enum.Enum):
    TASK = "TASK"
    TASKS = "TASKS"
    INITIATIVE = "INITIATIVE"
    INITIATIVES = "INITIATIVES"


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


@event.listens_for(User, "after_insert")
def create_user_account_details(mapper, connection, target):
    """Automatically create UserAccountDetails when a User is created."""
    # Import here to avoid circular imports
    from src.accounting.models import UserAccountDetails, UserAccountStatus

    # Insert UserAccountDetails using the same connection/transaction
    # This ensures atomicity with the User creation
    connection.execute(
        UserAccountDetails.__table__.insert().values(
            user_id=target.id,
            balance_cents=0.0,
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

    def dict(self) -> Dict[str, Union[str, datetime]]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


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


class ChatMessage(TypedDict):
    role: Literal["assistant", "system", "user"]
    content: str


class ChatMode(str, enum.Enum):
    DISCUSS = "DISCUSS"
    EDIT = "EDIT"


class AIImprovementJob(PublicBase, Base):
    __tablename__ = "ai_improvement_job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    lens: Mapped[Lens] = mapped_column(Enum(Lens, schema="dev"), nullable=False)
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")
    thread_id: Mapped[str] = mapped_column(String, nullable=True)
    mode: Mapped[ChatMode] = mapped_column(Enum(ChatMode, schema="dev"), nullable=True)
    messages: Mapped[Optional[List[ChatMessage]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, schema="dev"),
        nullable=False,
        default=JobStatus.PENDING,
        server_default=text("'PENDING'"),
    )
    input_data: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    result_data: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB()), nullable=True
    )
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=text("now()")
    )

    def dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "initiative_id": str(self.initiative_id) if self.initiative_id else None,
            "status": self.status,
            "messages": self.messages,
            "input_data": self.input_data,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserKey(PublicBase, Base):
    __tablename__ = "user_key"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User")
    provider: Mapped[APIProvider] = mapped_column(
        Enum(APIProvider, schema="private"),
        nullable=False,
    )

    # redacted key is for display purposes only
    # it is in the form 'sk-***2322'
    redacted_key: Mapped[str] = mapped_column(String, nullable=False)

    # Fields for tracking validation status
    is_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Field for tracking when the token was last used (for PATs)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Field for storing the full access token (used for OpenBacklog token identification)
    access_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Field for tracking soft deletion of tokens
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def vault_path(self):
        return f"secret/data/{self.user_id}/api_keys/{self.provider.value}"


# --- Define Pydantic Models for AI Service Input ---


class PydanticChecklistItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    is_complete: bool = False
    order: int = 0
    # We might not need user_id/task_id from the input dict here
    # unless they are strictly required for the prompt itself.

    model_config = {"from_attributes": True}


class PydanticTask(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    identifier: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    type: Optional[str] = None
    has_pending_job: Optional[bool] = None
    initiative_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    checklist: List[PydanticChecklistItem] = Field(default_factory=list)

    @field_validator("created_at", "updated_at", mode="before")
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                # Attempt parsing, return None if invalid format and field is Optional
                dt = isoparse(value)
                return dt
            except (ValueError, TypeError):
                # Let Pydantic handle the error if field is required
                # or return None/raise specific error if needed
                return None  # Return None for Optional fields if parsing fails
        return value

    model_config = {"from_attributes": True, "use_enum_values": True}


class PydanticInitiative(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    identifier: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: Optional[InitiativeStatus] = None
    type: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tasks: List[PydanticTask] = Field(default_factory=list)  # Embed tasks

    @field_validator("created_at", "updated_at", mode="before")
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                dt = isoparse(value)
                return dt
            except (ValueError, TypeError):
                return None
        return value

    model_config = {"from_attributes": True, "use_enum_values": True}


# --- Add Task Management Models ---


class ManagedEntityAction(str, enum.Enum):
    """Specifies the action proposed by the LLM for an entity."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class TitleAndDescriptionValidation:
    @field_validator("title", "description")
    def validate_title_and_description(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError(f"{v} must be non-empty strings.")
        return v


class ChecklistItemModel(BaseModel):
    """Model representing a checklist item."""

    title: str = Field(..., description="The title of the checklist item.")

    @field_validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError(f"{v} must be non-empty strings.")
        return v


class CreateTaskModel(BaseModel, TitleAndDescriptionValidation):
    """Model representing a CREATE action on a task."""

    action: Literal[ManagedEntityAction.CREATE] = ManagedEntityAction.CREATE
    title: str
    description: str
    checklist: Optional[List[ChecklistItemModel]] = Field(
        ..., description="Proposed checklist for the new task."
    )


class UpdateTaskModel(BaseModel, TitleAndDescriptionValidation):
    """Model representing an UPDATE action on a task."""

    action: Literal[ManagedEntityAction.UPDATE] = ManagedEntityAction.UPDATE
    identifier: str = Field(
        ..., description="The identifier of the task to update eg (T-001)."
    )
    title: Optional[str] = Field(..., description="The title of the task to update.")
    description: Optional[str] = Field(
        ..., description="The description of the task to update."
    )
    checklist: Optional[List[ChecklistItemModel]]


class DeleteTaskModel(BaseModel):
    """Model representing a DELETE action on a task."""

    action: Literal[ManagedEntityAction.DELETE] = ManagedEntityAction.DELETE
    identifier: str = Field(
        ..., description="The identifier of the task to delete eg (T-001)."
    )


ManagedTaskModel = Union[CreateTaskModel, UpdateTaskModel, DeleteTaskModel]


class BalanceWarning(BaseModel):
    """Model for account balance warnings."""

    has_warning: bool = Field(
        default=False, description="Whether there is a balance warning"
    )
    warning_type: Optional[str] = Field(
        default=None, description="Type of warning (low_balance, suspended, etc.)"
    )
    message: Optional[str] = Field(
        default=None, description="Warning message for the user"
    )
    current_balance_cents: Optional[float] = Field(
        default=None, description="Current balance in cents"
    )
    current_balance_dollars: Optional[float] = Field(
        default=None, description="Current balance in dollars"
    )
    estimated_cost_cents: Optional[float] = Field(
        default=None, description="Estimated cost of this request in cents"
    )
    estimated_cost_dollars: Optional[float] = Field(
        default=None, description="Estimated cost of this request in dollars"
    )
    top_up_needed_cents: Optional[float] = Field(
        default=None, description="Amount needed to top up in cents"
    )
    top_up_needed_dollars: Optional[float] = Field(
        default=None, description="Amount needed to top up in dollars"
    )


class TaskLLMResponse(BaseModel):
    """
    Pydantic model defining the *standard* structure of the LLM response
    for any task-related operation.

    Includes validation to ensure UPDATE actions reference known task identifiers
    provided in the validation context.
    """

    type: Literal["task_llm_response"] = "task_llm_response"

    message: str = Field(
        ...,
        description="Your reply to the user. If no changes are needed, or you're asked a question then this is where you should put your reply.",
    )
    managed_tasks: List[ManagedTaskModel] = Field(
        ...,
        description="List of proposed actions (CREATE, UPDATE, DELETE) for tasks. Leave this empty if no changes are needed.",
    )
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )

    @field_validator("managed_tasks")
    @classmethod
    def check_update_identifiers(cls, v, info: ValidationInfo):
        """Validate UPDATE actions reference identifiers from context."""
        context = info.context
        if not context or "valid_task_identifiers" not in context:
            # If no context/ids provided, skip this validation.
            # Consider raising an error if context is mandatory for this model.
            # print("Warning: Validation context with 'valid_task_identifiers' not provided for TaskLLMResponse.")
            return v

        valid_task_identifiers = context.get("valid_task_identifiers", set())

        if not isinstance(valid_task_identifiers, set):
            print(
                "Warning: 'valid_task_identifiers' in context is not a set."
            )  # Or raise
            valid_task_identifiers = set()  # Avoid erroring out if type is wrong

        for managed_task in v:
            if isinstance(managed_task, UpdateTaskModel):
                if managed_task.identifier not in valid_task_identifiers:
                    raise ValueError(
                        f"Validation Error (in response): Proposed update for task with identifier "
                        f"'{managed_task.identifier}' but no such task identifier was found in the provided tasks."
                    )

        return v

    @field_validator("managed_tasks")
    @classmethod
    def validate_create_fields(cls, v):
        """Ensure CREATE actions have non-null title and description."""
        for managed_task in v:
            if managed_task.action == ManagedEntityAction.CREATE:
                if not managed_task.title or not managed_task.title.strip():
                    raise ValueError(
                        "Validation Error: Tasks being created must have a non-empty title."
                    )
                if not managed_task.description or not managed_task.description.strip():
                    raise ValueError(
                        "Validation Error: Tasks being created must have a non-empty description."
                    )
        return v

    @field_validator("managed_tasks")
    @classmethod
    def validate_update_fields(cls, v):
        """Ensure UPDATE actions with title/description fields have non-null values."""
        for managed_task in v:
            if managed_task.action == ManagedEntityAction.UPDATE:
                # Only validate fields that are being updated (not None)
                if managed_task.title is not None and (
                    not managed_task.title or not managed_task.title.strip()
                ):
                    raise ValueError(
                        f"Validation Error: Task '{managed_task.identifier}' update contains an empty title."
                    )
                if managed_task.description is not None and (
                    not managed_task.description or not managed_task.description.strip()
                ):
                    raise ValueError(
                        f"Validation Error: Task '{managed_task.identifier}' update contains an empty description."
                    )
        return v


class CreateInitiativeModel(BaseModel, TitleAndDescriptionValidation):
    """Model representing a CREATE action on an initiative."""

    action: Literal[ManagedEntityAction.CREATE] = ManagedEntityAction.CREATE
    title: str = Field(..., description="The title of the initiative to create.")
    description: str = Field(
        ..., description="The description of the initiative to create."
    )
    tasks: Optional[List[CreateTaskModel]] = Field(
        ..., description="The tasks to create with the initiative."
    )


class UpdateInitiativeModel(BaseModel, TitleAndDescriptionValidation):
    """Model representing an UPDATE action on an initiative."""

    action: Literal[ManagedEntityAction.UPDATE] = ManagedEntityAction.UPDATE
    identifier: str = Field(
        ..., description="The identifier of the initiative to update eg (I-001)."
    )
    title: Optional[str] = Field(
        ...,
        description="The title of the initiative to update.",
    )
    description: Optional[str] = Field(
        ..., description="The description of the initiative to update."
    )
    tasks: Optional[List[ManagedTaskModel]] = Field(
        ..., description="The tasks to update with the initiative."
    )


class DeleteInitiativeModel(BaseModel):
    """Model representing a DELETE action on an initiative."""

    action: Literal[ManagedEntityAction.DELETE] = ManagedEntityAction.DELETE
    identifier: str = Field(
        ..., description="The identifier of the initiative to delete eg (I-001)."
    )


ManagedInitiativeModel = Union[
    CreateInitiativeModel, UpdateInitiativeModel, DeleteInitiativeModel
]


class InitiativeLLMResponse(BaseModel):
    """
    Pydantic model defining the standardized structure of the LLM response
    for initiative batch operations.
    """

    type: Literal["initiative_llm_response"] = "initiative_llm_response"

    message: str = Field(
        ...,
        description="Your reply to the user. If no changes are needed, or you're asked a question then this is where you should put your reply.",
    )
    managed_initiatives: List[ManagedInitiativeModel] = Field(
        ...,
        description="List of proposed actions for initiatives. If no changes are needed, then this should be an empty list.",
    )
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )

    @field_validator("managed_initiatives")
    @classmethod
    def validate_create_fields(cls, v):
        """Ensure CREATE actions have non-null title and description."""
        for initiative in v:
            if isinstance(initiative, CreateInitiativeModel):
                if not initiative.title or not initiative.title.strip():
                    raise ValueError(
                        "Validation Error: Initiatives being created must have a non-empty title."
                    )
                if not initiative.description or not initiative.description.strip():
                    raise ValueError(
                        "Validation Error: Initiatives being created must have a non-empty description."
                    )
                # Also validate any tasks being created with the initiative
                if initiative.tasks:
                    for task in initiative.tasks:
                        if not task.title or not task.title.strip():
                            raise ValueError(
                                "Validation Error: Tasks within new initiative must have a non-empty title."
                            )
                        if not task.description or not task.description.strip():
                            raise ValueError(
                                "Validation Error: Tasks within new initiative must have a non-empty description."
                            )
        return v

    @field_validator("managed_initiatives")
    @classmethod
    def check_update_identifiers(cls, v, info: ValidationInfo):
        """Validate UPDATE actions reference identifiers from context."""
        context = info.context
        if not context or "valid_initiative_identifiers" not in context:
            # If no context/ids provided, skip this validation.
            # Consider raising an error if context is mandatory for this model.
            # print("Warning: Validation context with 'valid_initiative_identifiers' not provided for InitiativeLLMResponse.")
            return v

        valid_initiative_identifiers = context.get(
            "valid_initiative_identifiers", set()
        )

        if not isinstance(valid_initiative_identifiers, set):
            print(
                "Warning: 'valid_initiative_identifiers' in context is not a set."
            )  # Or raise

        for managed_initiative in v:
            if isinstance(managed_initiative, UpdateInitiativeModel):
                if managed_initiative.identifier not in valid_initiative_identifiers:
                    raise ValueError(
                        f"Validation Error (in response): Proposed update for initiative with identifier "
                        f"'{managed_initiative.identifier}' but no such initiative identifier was found in the provided initiatives."
                    )

        return v

    @field_validator("managed_initiatives")
    @classmethod
    def validate_update_fields(cls, v):
        """Ensure UPDATE actions with title/description fields have non-null values."""
        for initiative in v:
            if isinstance(initiative, UpdateInitiativeModel):
                # Only validate fields that are being updated (not None)
                if initiative.title is not None and (
                    not initiative.title or not initiative.title.strip()
                ):
                    raise ValueError(
                        f"Validation Error: Initiative '{initiative.identifier}' update contains an empty title."
                    )
                if initiative.description is not None and (
                    not initiative.description or not initiative.description.strip()
                ):
                    raise ValueError(
                        f"Validation Error: Initiative '{initiative.identifier}' update contains an empty description."
                    )

                # Also validate any tasks being updated with the initiative
                if initiative.tasks:
                    for task in initiative.tasks:
                        if isinstance(task, CreateTaskModel):
                            if not task.title or not task.title.strip():
                                raise ValueError(
                                    "Validation Error: New tasks within updated initiative must have a non-empty title."
                                )
                            if not task.description or not task.description.strip():
                                raise ValueError(
                                    "Validation Error: New tasks within updated initiative must have a non-empty description."
                                )
                        elif isinstance(task, UpdateTaskModel):
                            if task.title is not None and (
                                not task.title or not task.title.strip()
                            ):
                                raise ValueError(
                                    f"Validation Error: Task '{task.identifier}' update within initiative contains an empty title."
                                )
                            if task.description is not None and (
                                not task.description or not task.description.strip()
                            ):
                                raise ValueError(
                                    f"Validation Error: Task '{task.identifier}' update within initiative contains an empty description."
                                )
        return v


class DiscussLLMResponse:
    """
    Pydantic model defining the *standard* structure of the LLM response
    for .

    Includes validation to ensure UPDATE actions reference known task identifiers
    provided in the validation context.
    """

    type: Literal["discuss_llm_response"] = "discuss_llm_response"

    message: str = Field(..., description="Your reply to the user. In markdown format")


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
