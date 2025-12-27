from os import environ as env

from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

ENV_FILE = find_dotenv(
    filename=(
        ".env"
        if not env.get("ENVIRONMENT") or env.get("ENVIRONMENT") == "development"
        else f".env.{env.get('ENVIRONMENT')}"
    ),
)
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    environment: str

    static_site_url: str
    static_site_domain: str

    app_domain: str = Field(default="")
    app_url: str

    postgrest_domain: str
    mcp_server_domain: str

    current_workspace_cookie_name: str = Field(default="current_workspace")

    database_name: str
    database_app_user_username: str
    database_app_user_password: str
    database_url: str = Field(default="")
    async_database_url: str = Field(default="")

    # Auth0 settings (optional - only required if using Auth0 provider)
    auth0_application_id: str = Field(default="")
    auth0_audience: str = Field(default="")
    auth0_client_id: str = Field(default="")
    auth0_client_secret: str = Field(default="")
    auth0_domain: str = Field(default="")
    cookie_lifetime_seconds: int = Field(default=3600)
    auth0_jwks_endpoint: str = Field(default="")
    auth0_jwt_cookie_name: str = Field(default="auth0_jwt")

    # Auth0 settings for MCP server
    mcp_server_auth0_application_id: str = Field(default="")
    mcp_server_auth0_audience: str = Field(default="")
    mcp_server_auth0_client_id: str = Field(default="")
    mcp_server_auth0_client_secret: str = Field(default="")
    mcp_server_auth0_domain: str = Field(default="")
    mcp_server_cookie_lifetime_seconds: int = Field(default=3600)
    mcp_server_auth0_jwks_endpoint: str = Field(default="")
    mcp_server_auth0_jwt_cookie_name: str = Field(default="auth0_jwt")
    mcp_server_auth0_refresh_token_cookie_name: str = Field(
        default="auth0_refresh_token"
    )

    # MCP OAuth storage encryption settings
    mcp_oauth_storage_encryption_key: str = Field(
        default="test-encryption-key-for-development-only-not-secure-12345678901234567890123456789012"
    )
    mcp_oauth_jwt_signing_key: str = Field(
        default="test-jwt-signing-key-for-development-only-not-secure"
    )

    # MCP server authentication mode
    mcp_auth_mode: str = Field(
        default="dev",
        description="Authentication mode for MCP server: 'dev', 'auth0', or 'test'",
    )

    postgrest_authenticator__role: str
    postgrest_authenticator__password: str
    postgrest_anonymous__role: str
    postgrest_authenticated_role: str

    # Storage (empty = local filesystem mode)
    cloudflare_account_id: str = Field(default="")
    r2_access_key_id: str = Field(default="")
    r2_secret_access_key: str = Field(default="")
    r2_profile_picture_bucket_name: str = Field(default="")
    default_profile_picture: str = Field(default="")

    # GitHub (empty = feature disabled)
    github_app_id: str = Field(default="")
    github_app_name: str = Field(default="")
    github_app_private_key: str = Field(default="")
    github_webhook_secret: str = Field(default="")

    sentry_url: str = Field(default="")

    internal_request_timeout: int = Field(default=15)

    csrf_token_name: str = Field(default="fastapi-csrf-token")
    csrf_token_secret_key: str = Field(default="dev-csrf-secret-change-in-production")

    # Development auth settings
    dev_jwt_secret: str = Field(default="dev-jwt-secret-change-in-production")
    dev_jwt_algorithm: str = Field(default="HS256")
    dev_jwt_lifetime_seconds: int = Field(default=2592000)  # 30 days
    dev_jwt_oauth_account_name: str = Field(default="dev-oauth-account")

    # Development user settings
    dev_user_email: str = Field(default="dev@localhost.com")
    dev_user_password: str = Field(default="devpassword")

    # Auth provider selection
    auth_provider: str = Field(default="auth0")  # auto, auth0, simple, dev

    # Simple auth settings (for open source deployments)
    simple_auth_allow_registration: bool = Field(default=True)
    simple_auth_require_email_verification: bool = Field(default=False)
    simple_auth_password_min_length: int = Field(default=8)

    # User signup control
    allow_new_signups: bool = Field(default=True)

    docs_site_url: str = Field(default="https://docs.openbacklog.ai")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Check if database name is overridden via environment variable
        if env.get("DATABASE_NAME"):
            self.database_name = env.get("DATABASE_NAME", "")

        # Construct database URLs if not provided
        if not self.database_url:
            self.database_url = f"postgresql://{self.database_app_user_username}:{self.database_app_user_password}@localhost/{self.database_name}"

        if not self.async_database_url:
            self.async_database_url = f"postgresql+asyncpg://{self.database_app_user_username}:{self.database_app_user_password}@localhost/{self.database_name}"


settings = Settings()  # type: ignore # pragma: no mutate
