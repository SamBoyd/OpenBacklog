"""Domain exceptions for narrative domain.

This module re-exports DomainException from strategic_planning
for consistency across domains.
"""

from src.strategic_planning.exceptions import DomainException

__all__ = ["DomainException"]
