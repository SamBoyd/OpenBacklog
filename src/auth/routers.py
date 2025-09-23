"""
Unified authentication routers that work with any auth provider.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from src.config import settings
from src.main import templates

from .factory import (
    get_auth_provider,
    get_provider_type,
    is_oauth_flow,
    supports_password_auth,
)
from .providers import AuthProvider, AuthResult

logger = logging.getLogger(__name__)


class SignupDisabledException(Exception):
    """Exception raised when new user signup is attempted but signups are disabled."""

    def __init__(self, message: str = "New user signups are currently disabled"):
        self.message = message
        super().__init__(self.message)


def _get_cookie_settings() -> dict[str, bool | str]:
    """Get environment-appropriate cookie settings."""
    is_production = settings.environment == "production"

    # Set domain for cookie sharing between subdomains
    cookie_domain = None
    if settings.app_domain:
        # In development: .dev.openbacklog.ai allows sharing between www.dev.openbacklog.ai and dev.openbacklog.ai
        cookie_domain = f".{settings.app_domain}"

    base_settings = {
        "httponly": is_production,  # True in production, False in development
        "secure": is_production,  # True in production, False in development
        "samesite": "strict" if is_production else "lax",
    }

    if cookie_domain:
        base_settings["domain"] = cookie_domain

    return base_settings


def _set_auth_cookie(
    response: Response, key: str, value: str, max_age: int, path: str = "/"
) -> None:
    """Set authentication cookie with environment-appropriate settings."""
    cookie_settings = _get_cookie_settings()

    response.set_cookie(
        key=key, value=value, max_age=max_age, path=path, **cookie_settings
    )


class LoginRequest(BaseModel):
    """Login request for username/password auth."""

    username: str
    password: str
    redirect_uri: Optional[str] = None


class RegisterRequest(BaseModel):
    """Registration request."""

    email: str
    password: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    """Standard auth response."""

    success: bool
    message: str
    redirect_url: Optional[str] = None


# Create router
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login-url")
async def get_login_url(
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    provider: AuthProvider = Depends(get_auth_provider),
):
    """
    Get login URL for current auth provider.

    For OAuth providers: Returns authorization URL
    For simple auth: Returns login form URL
    For dev auth: Returns dev login URL
    """
    try:
        if not redirect_uri:
            redirect_uri = f"{settings.app_url}/auth/callback"

        login_url = await provider.get_authorization_url(
            redirect_uri=redirect_uri, state=state
        )

        return {
            "authorization_url": login_url,
            "provider_type": get_provider_type(),
            "is_oauth": is_oauth_flow(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get login URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate login URL")


@auth_router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request, redirect_uri: Optional[str] = None, state: Optional[str] = None
):
    """
    Render login form for simple auth providers.
    """
    if not supports_password_auth():
        raise HTTPException(
            status_code=400,
            detail="Password authentication not supported by current provider",
        )

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "redirect_uri": redirect_uri,
            "state": state,
            "provider_type": get_provider_type(),
        },
    )


@auth_router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    provider: AuthProvider = Depends(get_auth_provider),
):
    """
    Login with username/password (for simple and dev auth).
    """
    if not supports_password_auth():
        raise HTTPException(
            status_code=400,
            detail="Password authentication not supported by current provider",
        )

    try:
        # Authenticate user
        user = await provider.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create tokens
        tokens = await provider.create_tokens(user)

        # Set cookies
        _set_auth_cookie(response, "access_token", tokens.access_token, 30 * 24 * 3600)

        if tokens.refresh_token:
            _set_auth_cookie(
                response, "refresh_token", tokens.refresh_token, 30 * 24 * 3600
            )  # 30 days

        return AuthResponse(
            success=True,
            message="Login successful",
            redirect_url=request.redirect_uri or f"{settings.app_url}/workspace",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@auth_router.post("/register")
async def register(
    request: RegisterRequest, provider: AuthProvider = Depends(get_auth_provider)
):
    """
    Register new user (for simple auth).
    """
    provider_type = get_provider_type()

    if provider_type == "auth0":
        raise HTTPException(
            status_code=400,
            detail="Registration handled by Auth0. Please use OAuth flow.",
        )
    elif provider_type == "dev":
        raise HTTPException(
            status_code=400, detail="Registration not needed in development mode"
        )
    elif provider_type == "simple":
        # Use SimpleAuthProvider's register method
        if hasattr(provider, "register_user"):
            user = await provider.register_user(
                email=request.email, password=request.password, name=request.name
            )

            if not user:
                raise HTTPException(status_code=400, detail="Registration failed")

            # Auto-login after registration
            tokens = await provider.create_tokens(user)

            response = JSONResponse(
                content=dict(success=True, redirect_url="/workspace")
            )
            _set_auth_cookie(
                response, "access_token", tokens.access_token, tokens.expires_in
            )
            response.status_code = 201

            return response
        else:
            raise HTTPException(status_code=500, detail="Registration not supported")
    else:
        raise HTTPException(status_code=400, detail="Registration not supported")


@auth_router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request, redirect_uri: Optional[str] = None, state: Optional[str] = None
):
    """
    Render registration form for simple auth providers.
    """
    provider_type = get_provider_type()

    if provider_type == "auth0":
        raise HTTPException(
            status_code=400,
            detail="Registration handled by Auth0. Please use OAuth flow.",
        )
    elif provider_type == "dev":
        raise HTTPException(
            status_code=400, detail="Registration not needed in development mode"
        )
    elif provider_type != "simple":
        raise HTTPException(status_code=400, detail="Registration not supported")

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "redirect_uri": redirect_uri,
            "state": state,
            "provider_type": provider_type,
        },
    )


@auth_router.get("/callback")
async def auth_callback(
    request: Request,
    response: RedirectResponse,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    provider: AuthProvider = Depends(get_auth_provider),
) -> RedirectResponse:
    """
    Handle OAuth callback (for Auth0 and similar providers).
    """
    if not is_oauth_flow():
        raise HTTPException(
            status_code=400, detail="Callback not supported by current provider"
        )

    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        # Handle the callback
        redirect_uri = f"{settings.app_url}/auth/callback"
        auth_result = await provider.handle_callback(code, redirect_uri, state)

        # Get or create user from auth result
        user = await _get_or_create_user_from_auth_result(auth_result)

        # Create our unified tokens
        tokens = await provider.create_tokens(user)

        # Set cookies
        _set_auth_cookie(
            response, "access_token", tokens.access_token, tokens.expires_in
        )

        logger.info(f"Setting access_token: {tokens.access_token}")

        if tokens.refresh_token:
            _set_auth_cookie(
                response, "refresh_token", tokens.refresh_token, 30 * 24 * 3600
            )  # 30 days

            logger.info(f"Setting refresh_token: {tokens.refresh_token}")

        # Redirect to workspace
        response.headers["location"] = "/workspace"
        response.status_code = 302
        return response

    except SignupDisabledException as se:
        # Handle signup disabled error specially
        logger.info(f"New user signup blocked: {se.message}")
        response = RedirectResponse(status_code=302, url="/?error=signups_disabled")
        return response

    except HTTPException as he:
        # Re-raise other HTTP exceptions
        raise he

    except Exception as e:
        logger.exception(f"Callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@auth_router.post("/logout")
async def logout():
    """Logout user by clearing cookies."""
    response = RedirectResponse(status_code=302, url="/")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@auth_router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    provider: AuthProvider = Depends(get_auth_provider),
):
    """Refresh access token using refresh token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        tokens = await provider.refresh_token(refresh_token)

        # Set new access token
        _set_auth_cookie(
            response, "access_token", tokens.access_token, tokens.expires_in
        )

        # Update refresh token if provided
        if tokens.refresh_token and tokens.refresh_token != refresh_token:
            _set_auth_cookie(
                response, "refresh_token", tokens.refresh_token, 30 * 24 * 3600
            )

        return {"success": True, "message": "Token refreshed"}

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Token refresh failed")


@auth_router.get("/me")
async def get_current_user(
    request: Request, provider: AuthProvider = Depends(get_auth_provider)
):
    """Get current user info from token."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_info = await provider.get_user_info(access_token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "email": user_info.email,
            "name": user_info.name,
            "picture": user_info.picture,
            "email_verified": user_info.email_verified,
        }

    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=401, detail="Failed to get user info")


@auth_router.get("/provider-info")
async def get_provider_info():
    """Get information about current auth provider."""
    return {
        "provider_type": get_provider_type(),
        "is_oauth": is_oauth_flow(),
        "supports_registration": supports_password_auth(),
        "supports_password_auth": supports_password_auth(),
    }


@auth_router.get("/dev-login")
async def dev_login(
    response: Response,
    redirect_uri: Optional[str] = None,
    provider: AuthProvider = Depends(get_auth_provider),
):
    """Auto-login for development mode."""
    if get_provider_type() != "dev":
        raise HTTPException(
            status_code=400, detail="Dev login only available in development mode"
        )

    try:
        # Auto-login the dev user
        if hasattr(provider, "auto_login_dev_user"):
            user = await provider.auto_login_dev_user()
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create dev user")

            # Create tokens
            tokens = await provider.create_tokens(user)

            # Set cookies
            _set_auth_cookie(
                response, "access_token", tokens.access_token, tokens.expires_in
            )

            response.headers["Location"] = redirect_uri or "/workspace"
            response.status_code = 302

            return response
        else:
            raise HTTPException(
                status_code=500, detail="Dev provider doesn't support auto-login"
            )

    except Exception as e:
        logger.exception(f"Dev login error: {e}")
        raise HTTPException(status_code=500, detail="Dev login failed")


async def _get_or_create_user_from_auth_result(auth_result: AuthResult):
    """Get or create user from auth result and handle OAuth account linking."""
    from sqlalchemy import select

    from src.db import get_async_db
    from src.models import OAuthAccount, User

    async for db in get_async_db():
        user = None
        oauth_account = None

        # Extract OAuth account ID from user info (Auth0 sub field)
        oauth_account_id = auth_result.user_info.sub

        # First, try to find user by OAuth account ID (for social login linking)
        if oauth_account_id:
            result = await db.execute(
                select(OAuthAccount).filter(OAuthAccount.account_id == oauth_account_id)
            )
            oauth_account = result.scalar_one_or_none()

            if oauth_account:
                # Load the associated user
                result = await db.execute(
                    select(User).filter(User.id == oauth_account.user_id)
                )
                user = result.scalar_one_or_none()

        # If no user found via OAuth account, try by email
        if not user:
            result = await db.execute(
                select(User).filter(User.email == auth_result.user_info.email)
            )
            user = result.scalar_one_or_none()

        # Create new user if doesn't exist
        if not user:
            # Check if new signups are allowed
            if not settings.allow_new_signups:
                raise SignupDisabledException(
                    "We're not currently accepting new signups. Please check back later."
                )

            user = User(
                email=auth_result.user_info.email,
                name=auth_result.user_info.name,
                is_active=True,
                is_verified=auth_result.user_info.email_verified,
                is_superuser=False,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create or update OAuth account record
        if oauth_account_id:
            if not oauth_account:
                # Create new OAuth account linking
                oauth_account = OAuthAccount(
                    oauth_name="auth0",
                    access_token=auth_result.tokens.access_token,
                    expires_at=None,  # Auth0 tokens handled separately
                    refresh_token=auth_result.tokens.refresh_token,
                    account_id=oauth_account_id,
                    account_email=auth_result.user_info.email,
                    user_id=user.id,
                )
                db.add(oauth_account)
            else:
                # Update existing OAuth account with fresh tokens
                oauth_account.access_token = auth_result.tokens.access_token
                oauth_account.refresh_token = auth_result.tokens.refresh_token
                oauth_account.account_email = auth_result.user_info.email

            await db.commit()

        return user


# Export the router
__all__ = ["auth_router"]
