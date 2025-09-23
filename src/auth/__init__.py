# New unified auth module exports
from src.auth.auth_module import (
    AuthModule,
    get_auth_module,
    get_current_active_user,
    get_current_verified_user,
    initialize_auth,
    require_auth,
)
from src.auth.factory import get_auth_provider, get_provider_type
from src.models import User

# Explicitly define what is exported from this package
__all__ = [
    "AuthModule",
    "get_auth_module",
    "require_auth",
    "get_current_active_user",
    "get_current_verified_user",
    "initialize_auth",
    "get_auth_provider",
    "get_provider_type",
    "User",
]
