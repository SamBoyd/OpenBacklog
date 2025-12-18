import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import lifespan


class TestAppLifespan:
    """Test suite for the application lifespan function."""

    @pytest.mark.asyncio
    @patch("src.main.logging")
    async def test_lifespan_logs_successful_initialization(self, mock_logging):
        """Test that the lifespan function logs successful vault client initialization."""
        # Setup
        mock_app = FastAPI()

        # Execute - use a context manager to call lifespan
        async with lifespan(mock_app):
            pass

        # Verify
        mock_logging.info.assert_called_with(
            "Application lifespan function successfully initialized"
        )
