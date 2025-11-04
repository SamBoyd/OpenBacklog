import pytest


# Override the clean_tables fixture to prevent database operations for tests that don't need it
@pytest.fixture(autouse=True)
def clean_tables():
    """Mock clean_tables fixture to prevent database operations in unit tests."""
    pass
