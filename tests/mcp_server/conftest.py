from unittest.mock import Mock

import pytest


# Override the session fixture from the parent conftest to prevent database connection
@pytest.fixture(scope="function")
def session():
    """Mock session fixture to prevent database operations in unit tests."""
    return Mock()


# Override the clean_tables fixture to prevent database operations
@pytest.fixture(autouse=True)
def clean_tables(session):
    """Mock clean_tables fixture to prevent database operations in unit tests."""
    pass
