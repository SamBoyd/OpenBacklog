"""Domain exceptions for strategic planning.

This module defines custom exceptions for enforcing business rules
and domain invariants in the strategic planning domain.
"""


class DomainException(Exception):
    """Base exception for domain rule violations.

    This exception is raised when business rules or domain invariants
    are violated, such as field length limits, max entity counts, or
    invalid state transitions.

    Attributes:
        message: Human-readable error message
    """

    def __init__(self, message: str):
        """Initialize the domain exception.

        Args:
            message: Human-readable error message describing the violation
        """
        self.message = message
        super().__init__(self.message)
