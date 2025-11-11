import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import jinja2
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic_settings import BaseSettings

from src import litellm_service
from src.config import settings
from src.db import get_async_db

# from alembic import command
# from alembic.config import Config
from src.mcp_server.main import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ABSOLUTE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent


templates: Jinja2Templates = Jinja2Templates(
    directory=PROJECT_ABSOLUTE_PATH / "templates",
)
templates.env.autoescape = jinja2.select_autoescape(
    ["html", "xml"],
    default_for_string=True,
    default=True,
)
templates.env.globals["app_domain"] = settings.app_domain

from src.utils.assets import get_hashed_css_path

templates.env.globals["hashed_css_path"] = get_hashed_css_path()

mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        from src.secrets.vault_factory import get_vault

        vault = get_vault()
        logging.info("Vault successfully initialized at startup")
    except Exception as e:
        logging.error(f"Failed to initialize Vault at startup: {e}")
        # Continue application startup even if Vault initialization fails
        # The application will attempt to initialize the vault again when needed

    if settings.sentry_url != "":
        logging.info("Sentry URL is provided, initializing Sentry SDK")
        sentry_sdk.init(
            dsn=settings.sentry_url,
            send_default_pii=True,
        )

    if settings.environment == "development":
        litellm_service.regenerate_litellm_master_key()

    yield
    # Clean up the ML models and release the resources
    pass


# Combine both lifespans
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # Run both lifespans
    async with lifespan(app):
        async with mcp_app.lifespan(app):
            yield


def app_init() -> FastAPI:
    from src.mcp_server.main import well_known_routes

    app = FastAPI(
        lifespan=combined_lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        routes=[*well_known_routes],
        redirect_slashes=False,
    )

    app.mount(
        "/mcp",
        mcp_app,
    )

    static_files_dir = PROJECT_ABSOLUTE_PATH / "static"
    if os.path.exists(static_files_dir):
        app.mount(
            "/static",
            StaticFiles(directory=static_files_dir),
            name="static",
        )

    react_app_static_files_dir = PROJECT_ABSOLUTE_PATH / "static/react-components/build"
    if os.path.exists(react_app_static_files_dir):
        app.mount(
            "/js",
            StaticFiles(directory=react_app_static_files_dir),
            name="static",
        )

    origins = [settings.static_site_url, settings.app_url, settings.mcp_server_domain]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"✅ CORS middleware added with origins: {origins}")

    return app


app: FastAPI = app_init()


class CsrfSettings(BaseSettings):
    secret_key: str = settings.csrf_token_secret_key
    cookie_samesite: str = "strict"
    cookie_secure: bool = True
    token_location: str = "body"
    token_key: str = "csrftoken"


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    logger.error("handle csrf exception {exc.stat>us_code}, {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# Initialize Unified Authentication System
from src.auth.auth_module import initialize_auth
from src.auth.factory import get_provider_type

# Initialize the auth module (includes all auth routes)
auth_module = initialize_auth(app)
provider_type = get_provider_type()

logger.info(f"✅ Auth system initialized with provider: {provider_type}")

from src.accounting.accounting_views import *
from src.accounting.models import *
from src.accounting.stripe_views import *
from src.ai.ai_views import *
from src.api import *

# Auth views removed - now handled by the new auth module
from src.api_key_views import *
from src.error_views import *
from src.github_app.views import *
from src.initiative_management.views import *

# --- Other Application Imports ---
from src.models import User
from src.roadmap_intelligence.views import *
from src.strategic_planning.views import *
from src.users_views import *
from src.views import *
from src.views.task_views import *
