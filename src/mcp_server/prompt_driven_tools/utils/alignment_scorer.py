"""Strategic alignment scoring for roadmap themes.

This module provides utilities for calculating how well themes align with
strategic outcomes and identifying alignment issues.
"""

from typing import List

from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar


def calculate_alignment_score(theme: RoadmapTheme, total_outcomes: int) -> float:
    """Calculate alignment score (0.0 - 1.0) based on outcome links.

    Score is calculated as: (# of linked outcomes) / (total # of outcomes in workspace)

    Args:
        theme: RoadmapTheme to score
        total_outcomes: Total number of outcomes in the workspace

    Returns:
        Alignment score between 0.0 (no links) and 1.0 (linked to all outcomes)

    Example:
        >>> score = calculate_alignment_score(theme, total_outcomes=5)
        >>> if score < 0.3:
        ...     print("Weak strategic alignment")
    """
    if total_outcomes == 0:
        return 0.0

    linked_count = len(theme.outcomes)
    return linked_count / total_outcomes


def identify_alignment_issues(
    theme: RoadmapTheme, all_pillars: List[StrategicPillar]
) -> List[str]:
    """Identify specific alignment problems with a theme.

    Args:
        theme: RoadmapTheme to analyze
        all_pillars: All strategic pillars in the workspace

    Returns:
        List of human-readable issue descriptions

    Example:
        >>> issues = identify_alignment_issues(theme, pillars)
        >>> for issue in issues:
        ...     print(f"⚠️  {issue}")
    """
    issues = []

    # Check for no outcome links
    if len(theme.outcomes) == 0:
        issues.append("Not linked to any outcomes")

    # Check if problem statement is too vague (< 50 chars suggests low detail)
    if theme.problem_statement and len(theme.problem_statement) < 50:
        issues.append("Problem statement may be too vague (< 50 characters)")

    # Check if hypothesis is missing
    if not theme.hypothesis:
        issues.append("No hypothesis defined - how will you test this theme?")

    # Check if metrics are missing
    if not theme.indicative_metrics:
        issues.append("No metrics defined - how will you measure success?")

    # Check if time horizon is missing
    if theme.time_horizon_months is None:
        issues.append("No time horizon defined - when should this show results?")

    return issues


def get_alignment_recommendation(score: float) -> str:
    """Get human-readable recommendation based on alignment score.

    Args:
        score: Alignment score (0.0 - 1.0)

    Returns:
        Recommendation string

    Example:
        >>> rec = get_alignment_recommendation(0.2)
        >>> print(rec)
        "⚠️  Weak alignment - Consider linking to more strategic outcomes"
    """
    if score >= 0.6:
        return "✅ Strong alignment - Well-connected to strategic outcomes"
    elif score >= 0.3:
        return "⚙️  Moderate alignment - Consider strengthening outcome links"
    else:
        return "⚠️  Weak alignment - Consider linking to more strategic outcomes"
