"""User management endpoints."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.auth import auth_module
from src.db import get_db
from src.main import app
from src.models import User
from src.schemas import UserRead, UserUpdate


@app.get("/users/me", response_model=UserRead, tags=["users"])
async def get_current_user_endpoint(user: User = Depends(auth_module.require_auth)):
    """Get current user information."""
    return user


@app.patch("/users/me", response_model=UserRead, tags=["users"])
async def update_current_user(
    user_update: UserUpdate,
    user: User = Depends(auth_module.require_auth),
    db: Session = Depends(get_db),
):
    """Update current user information."""
    # Update fields if provided
    if user_update.email and user_update.email != user.email:
        user.email = user_update.email

    if user_update.name is not None:
        user.name = user_update.name

    if user_update.password:
        # Hash the password using the simple auth provider
        from src.auth.providers.simple import SimpleAuthProvider

        provider = SimpleAuthProvider()
        user.hashed_password = provider.hash_password(user_update.password)

    # Save changes
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
