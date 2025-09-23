import importlib
import os
from unittest.mock import patch

import pytest
from hamcrest import assert_that, ends_with, is_
from pydantic import ValidationError

from src import config


@pytest.fixture
def clear_env():
    """
    A test fixture to clear environment variables that might be set
    so we start from a clean slate for each test.
    """
    original_env = os.environ.copy()
    for var in (
        "ENVIRONMENT",
        "DATABASE_NAME",
        "DATABASE_APP_USER_USERNAME",
        "DATABASE_APP_USER_PASSWORD",
        "DATABASE_URL",
        "DATABASE_SYNC_URL",
        "AUTH0_AUDIENCE",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
    ):
        if var in os.environ:
            del os.environ[var]
    yield
    # Restore the original environment variables
    os.environ.clear()
    os.environ.update(original_env)


def test_settings_load_test_env_file(clear_env):
    """
    Test that Settings loads from the `.env.test` file
    when ENVIRONMENT == 'test'.
    """
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        importlib.reload(config)

        # Check that environment is 'test'
        assert_that(config.settings.environment, is_("test"))
        # Ensure ENV_FILE ends with .env.test
        assert_that(config.ENV_FILE, ends_with("/.env.test"))


def test_settings_mocked_values(clear_env):
    """
    Test that we can inject environment variables through patch.dict
    and have them appear in Settings as expected.
    """
    env_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_NAME": "my_database",
        "DATABASE_APP_USER_USERNAME": "db_user",
        "DATABASE_APP_USER_PASSWORD": "db_pass",
        "DATABASE_URL": "postgresql://mydburl",
        "DATABASE_SYNC_URL": "postgresql+asyncpg://mydburl",
        "AUTH0_AUDIENCE": "my_audience",
        "AUTH0_CLIENT_ID": "my_client_id",
        "AUTH0_CLIENT_SECRET": "my_client_secret",
        "AUTH0_DOMAIN": "my_domain",
    }

    with patch.dict(os.environ, env_vars):
        importlib.reload(config)

        assert_that(config.settings.environment, is_("test"))
        assert_that(config.settings.database_name, is_("my_database"))
        assert_that(config.settings.database_app_user_username, is_("db_user"))
        assert_that(config.settings.database_app_user_password, is_("db_pass"))
        assert_that(config.settings.database_url, is_("postgresql://mydburl"))
        assert_that(config.settings.auth0_audience, is_("my_audience"))
        assert_that(config.settings.auth0_client_id, is_("my_client_id"))
        assert_that(config.settings.auth0_client_secret, is_("my_client_secret"))
        assert_that(config.settings.auth0_domain, is_("my_domain"))


# def test_settings_missing_required(clear_env):
#     """
#     Test that missing required environment variables will cause
#     Pydantic to raise a ValidationError.
#     """

#     with patch('src.config.load_dotenv') as mock_load_dotenv:
#         importlib.reload(config)
#         breakpoint()
#         with pytest.raises(ValidationError):
#             _ = config.Settings()
