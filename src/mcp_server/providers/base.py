"""
Base MCP authentication provider interface.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MCPContextError(RuntimeError):
    """
    Raised when MCP tool context (user/workspace) resolution fails.

    Attributes:
        error_type: String identifier describing the error category.
    """

    def __init__(self, message: str, *, error_type: str = "context_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class MCPAuthProvider(ABC):
    """
    Abstract base class for MCP authentication providers.

    Provides context extraction for MCP tools. Each provider implements
    a different authentication strategy (dev, auth0, etc).
    """

    @abstractmethod
    def get_user_context(
        self, session: Session
    ) -> Tuple[uuid.UUID, Optional[uuid.UUID]]:
        """
        Extract authenticated user and workspace context from request.

        Args:
            session: SQLAlchemy database session

        Returns:
            Tuple of (user_id, workspace_id)
            - user_id: UUID of authenticated user
            - workspace_id: UUID of user's workspace (or None if not required)

        Raises:
            MCPContextError: If context cannot be resolved
        """
        pass

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return self.__class__.__name__.replace("MCPAuthProvider", "").replace(
            "AuthProvider", ""
        )
