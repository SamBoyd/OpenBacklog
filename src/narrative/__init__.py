"""Narrative domain package.

This package contains all narrative functionality including:
- Aggregates: Hero, Villain, Conflict, TurningPoint
- Exceptions: DomainException (reused from strategic_planning)
"""

from src.narrative.aggregates.conflict import Conflict
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.turning_point import TurningPoint
from src.narrative.aggregates.villain import Villain

__all__ = [
    "Hero",
    "Villain",
    "Conflict",
    "TurningPoint",
]
