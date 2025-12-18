from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

from src import controller
from src.db import get_db
from src.main import app
from src.views import dependency_to_override


class TaskCreate(BaseModel):
    title: str
    description: str


#  === Routes that don't require being logged in ===

#  === Routes that require being logged in ===


# New user update model and endpoint
class UserUpdate(BaseModel):
    name: str | None = None


@app.post("/api/user", response_class=JSONResponse)
async def update_user(
    userUpdate: UserUpdate,
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> JSONResponse:
    if userUpdate.name is None:
        return JSONResponse(
            status_code=422, content={"message": "At least one field must be provided"}
        )

    if userUpdate.name == "":
        return JSONResponse(
            status_code=422, content={"message": "Fields cannot be empty"}
        )

    controller.update_user(user=user, name=userUpdate.name, db=session)
    return JSONResponse(content={})


class UserAccountDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    onboardingCompleted: bool


@app.get("/api/user-account-details", response_class=JSONResponse)
async def get_user_account_details(
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> UserAccountDetailsResponse:
    user_account_details = user.account_details

    return UserAccountDetailsResponse(
        status=user_account_details.status.value,
        onboardingCompleted=user_account_details.onboarding_completed,
    )


# New enums for display preferences
class DisplayPreferenceField(str, Enum):
    dateFormat = "dateFormat"
    timezone = "timezone"
    language = "language"
    theme = "theme"


class DateFormatEnum(str, Enum):
    mmddyyyy = "MM/DD/YYYY"
    ddmmyyyy = "DD/MM/YYYY"
    yyyymmdd = "YYYY-MM-DD"


class TimezoneEnum(str, Enum):
    utc = "UTC"
    gmt = "GMT"
    est = "EST"
    pst = "PST"


class LanguageEnum(str, Enum):
    english = "English"
    spanish = "Spanish"
    french = "French"
    german = "German"


class ThemeEnum(str, Enum):
    light = "Light"
    dark = "Dark"


class DisplayPrefUpdate(BaseModel):
    field: DisplayPreferenceField
    value: str

    @field_validator("value")
    def validate_value(cls, v, info):
        mapping = {
            DisplayPreferenceField.dateFormat: {e.value for e in DateFormatEnum},
            DisplayPreferenceField.timezone: {e.value for e in TimezoneEnum},
            DisplayPreferenceField.language: {e.value for e in LanguageEnum},
            DisplayPreferenceField.theme: {e.value for e in ThemeEnum},
        }
        field_obj = info.data.get("field")
        if field_obj and v not in mapping[field_obj]:
            raise ValueError(f"Invalid value '{v}' for field '{field_obj.value}'.")
        return v


@app.get("/api/user/display-pref", response_class=JSONResponse)
async def get_display_pref(
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> JSONResponse:
    return JSONResponse(content=controller.get_display_pref(user=user, db=session))


@app.post("/api/user/display-pref", response_class=JSONResponse)
async def update_display_pref(
    displayPrefUpdate: DisplayPrefUpdate,
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> JSONResponse:
    # Validate input (you can add more validations as needed)
    if not displayPrefUpdate.value:
        raise HTTPException(status_code=422, detail="Preference value cannot be empty")

    allowed_fields = {"dateFormat", "timezone", "language", "theme"}
    if displayPrefUpdate.field not in allowed_fields:
        raise HTTPException(status_code=422, detail="Invalid preference field")

    # Update the user's display preferences via the controller (assumed to be implemented)
    controller.update_display_pref(
        user=user,
        field=displayPrefUpdate.field,
        value=displayPrefUpdate.value,
        db=session,
    )
    return JSONResponse(content={"message": "Display preference updated successfully"})


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


@app.post("/api/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> WorkspaceResponse:
    """Create a new workspace with required dependencies.

    This endpoint creates a workspace and automatically creates the required
    1:1 relationship entities (PrioritizedRoadmap and ProductVision) via
    the SQLAlchemy event listener.
    """
    # Create workspace using controller
    new_workspace = controller.create_workspace(
        user=user,
        name=workspace.name,
        description=workspace.description,
        icon=workspace.icon,
        db=session,
    )

    # Return workspace data
    return WorkspaceResponse(
        id=str(new_workspace.id),
        name=new_workspace.name,
        description=new_workspace.description,
        icon=new_workspace.icon,
    )


@app.post("/api/workspace", response_class=JSONResponse)
async def update_workspace(
    workspace: WorkspaceUpdate,
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> JSONResponse:
    updated_workspace = controller.update_workspace(
        user=user, workspace_update=workspace, db=session
    )
    return JSONResponse(content=updated_workspace.dict())


@app.delete("/api/workspace/{workspace_id}", response_class=JSONResponse)
async def delete_workspace(
    workspace_id: str,
    user=Depends(dependency_to_override),
    session=Depends(get_db),
) -> JSONResponse:
    controller.delete_workspace(user=user, workspace_id=workspace_id, db=session)
    return JSONResponse(content={})
