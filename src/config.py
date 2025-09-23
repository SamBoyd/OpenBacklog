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

    log_prompts: bool = Field(default=False)

    openai_model: str
    openai_api_test_key: str = Field(default="")

    static_site_url: str
    static_site_domain: str

    app_domain: str
    app_url: str

    postgrest_domain: str
    mcp_server_domain: str

    current_workspace_cookie_name: str = Field(default="current_workspace")

    database_name: str
    database_app_user_username: str
    database_app_user_password: str
    database_url: str = Field(default="")
    async_database_url: str = Field(default="")
    memory_database_url: str

    # Auth0 settings (optional - only required if using Auth0 provider)
    auth0_application_id: str = Field(default="")
    auth0_audience: str = Field(default="")
    auth0_client_id: str = Field(default="")
    auth0_client_secret: str = Field(default="")
    auth0_domain: str = Field(default="")
    cookie_lifetime_seconds: int = Field(default=3600)
    auth0_jwks_endpoint: str = Field(default="")
    auth0_jwt_cookie_name: str = Field(default="auth0_jwt")

    postgrest_authenticator__role: str
    postgrest_authenticator__password: str
    postgrest_anonymous__role: str
    postgrest_authenticated_role: str

    cloudflare_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_profile_picture_bucket_name: str

    default_profile_picture: str

    github_app_id: str
    github_app_name: str = Field(default="samboyd-taskmanagement-dev")
    github_app_private_key: str
    github_webhook_secret: str

    tavily_api_key: str
    vault_url: str
    vault_cert_path: str
    vault_cert_key_path: str
    vault_role_id_path: str
    vault_secret_id_path: str
    vault_verify_cert: bool

    sentry_url: str

    internal_request_timeout: int = Field(default=15)

    csrf_token_name: str = Field(default="fastapi-csrf-token")
    csrf_token_secret_key: str

    langsmith_tracing: str
    langsmith_api_key: str
    langsmith_openai_api_key: str

    # Development auth settings
    dev_jwt_secret: str
    dev_jwt_algorithm: str = Field(default="HS256")
    dev_jwt_lifetime_seconds: int = Field(default=3600)
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

    llm_model: str
    litellm_url: str
    litellm_master_key: str
    litellm_master_key_vault_path: str = Field(default="secret/data/litellm/master_key")

    # OpenMeter settings
    openmeter_base_url: str = Field(default="https://openmeter.cloud")
    openmeter_api_token: str

    # Stripe settings
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id: str

    # Support page settings
    support_email_address: str = Field(default="support@openbacklog.ai")
    github_repo_url: str = Field(default="https://github.com/samboyd/openbacklog")
    discord_invite_link: str = Field(default="https://discord.gg/ZaK5e8wp")
    reddit_launch_thread_url: str = Field(default="")

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
