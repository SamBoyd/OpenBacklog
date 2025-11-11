import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import lifespan


class TestAppLifespan:
    """Test suite for the application lifespan function."""

    @pytest.mark.asyncio
    @patch("src.secrets.vault_factory.get_vault")
    async def test_lifespan_initializes_vault_client(self, mock_get_vault):
        """Test that the lifespan function initializes the Vault client."""
        # Setup
        mock_vault = MagicMock()
        mock_get_vault.return_value = mock_vault
        mock_app = FastAPI()

        # Execute - use a context manager to call lifespan
        async with lifespan(mock_app):
            pass

        # Verify
        mock_get_vault.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.secrets.vault_factory.get_vault")
    @patch("src.main.logging")
    async def test_lifespan_logs_successful_initialization(
        self, mock_logging, mock_get_vault
    ):
        """Test that the lifespan function logs successful vault client initialization."""
        # Setup
        mock_vault = MagicMock()
        mock_get_vault.return_value = mock_vault
        mock_app = FastAPI()

        # Execute - use a context manager to call lifespan
        async with lifespan(mock_app):
            pass

        # Verify
        mock_logging.info.assert_called_with(
            "Vault successfully initialized at startup"
        )

    @pytest.mark.asyncio
    @patch("src.secrets.vault_factory.get_vault", side_effect=Exception("Test error"))
    @patch("src.main.logging")
    async def test_lifespan_handles_initialization_error(
        self, mock_logging, mock_get_vault
    ):
        """Test that the lifespan function handles errors during vault client initialization."""
        # Setup
        mock_app = FastAPI()

        # Execute - use a context manager to call lifespan
        async with lifespan(mock_app):
            pass

        # Verify
        mock_logging.error.assert_called_once()
        # Application should continue running even if Vault initialization fails
