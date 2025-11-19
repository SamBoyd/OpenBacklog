"""Narrative aggregates package."""

from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.turning_point import Significance, TurningPoint
from src.narrative.aggregates.villain import Villain, VillainType

__all__ = [
    "Hero",
    "Villain",
    "VillainType",
    "Conflict",
    "ConflictStatus",
    "TurningPoint",
    "Significance",
]
