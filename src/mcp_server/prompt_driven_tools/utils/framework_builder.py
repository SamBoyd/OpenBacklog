"""Framework building utilities for prompt-driven tools.

Provides the FrameworkBuilder class for constructing rich, conversational
frameworks that guide Claude Code in collaborative refinement sessions.
"""

from typing import Any, Dict, List, Optional


class FrameworkBuilder:
    """Builder for constructing rich framework responses.

    Frameworks provide guidance, examples, and context to enable Claude Code
    to coach users through strategic planning conversations.

    Example:
        >>> builder = FrameworkBuilder("vision")
        >>> builder.set_purpose("Define the change you want to make in the world")
        >>> builder.add_criterion("Outcome-focused, not solution-focused")
        >>> builder.add_example(
        ...     text="Enable developers to manage tasks without leaving their IDE",
        ...     why_good="Focuses on user outcome, not features"
        ... )
        >>> framework = builder.build()
    """

    def __init__(self, entity_type: str):
        """Initialize framework builder.

        Args:
            entity_type: Type of entity (vision, pillar, outcome, foundation)
        """
        self.entity_type = entity_type
        self._purpose: Optional[str] = None
        self._criteria: List[str] = []
        self._examples: List[Dict[str, str]] = []
        self._questions: List[str] = []
        self._anti_patterns: List[Dict[str, str]] = []
        self._coaching_tips: List[str] = []
        self._current_state: Optional[Dict[str, Any]] = None
        self._additional_context: Dict[str, Any] = {}

    def set_purpose(self, purpose: str) -> "FrameworkBuilder":
        """Set the purpose/why for this entity.

        Args:
            purpose: Description of why this entity matters

        Returns:
            Self for method chaining
        """
        self._purpose = purpose
        return self

    def add_criterion(self, criterion: str) -> "FrameworkBuilder":
        """Add a quality criterion.

        Args:
            criterion: What makes this entity good

        Returns:
            Self for method chaining
        """
        self._criteria.append(criterion)
        return self

    def add_criteria(self, criteria: List[str]) -> "FrameworkBuilder":
        """Add multiple quality criteria.

        Args:
            criteria: List of quality criteria

        Returns:
            Self for method chaining
        """
        self._criteria.extend(criteria)
        return self

    def add_example(
        self, text: str, why_good: str, **kwargs: Any
    ) -> "FrameworkBuilder":
        """Add a positive example.

        Args:
            text: Example text
            why_good: Explanation of why this is good
            **kwargs: Additional example properties

        Returns:
            Self for method chaining
        """
        example = {"text": text, "why_good": why_good, **kwargs}
        self._examples.append(example)
        return self

    def add_question(self, question: str) -> "FrameworkBuilder":
        """Add a guiding question to explore.

        Args:
            question: Question to help user think through this entity

        Returns:
            Self for method chaining
        """
        self._questions.append(question)
        return self

    def add_questions(self, questions: List[str]) -> "FrameworkBuilder":
        """Add multiple guiding questions.

        Args:
            questions: List of questions to explore

        Returns:
            Self for method chaining
        """
        self._questions.extend(questions)
        return self

    def add_anti_pattern(
        self, example: str, why_bad: str, better: str
    ) -> "FrameworkBuilder":
        """Add an anti-pattern (what NOT to do).

        Args:
            example: Anti-pattern example
            why_bad: Explanation of why this is bad
            better: Suggestion for better approach

        Returns:
            Self for method chaining
        """
        self._anti_patterns.append(
            {"example": example, "why_bad": why_bad, "better": better}
        )
        return self

    def add_coaching_tip(self, tip: str) -> "FrameworkBuilder":
        """Add a coaching tip.

        Args:
            tip: Actionable guidance for user

        Returns:
            Self for method chaining
        """
        self._coaching_tips.append(tip)
        return self

    def add_coaching_tips(self, tips: List[str]) -> "FrameworkBuilder":
        """Add multiple coaching tips.

        Args:
            tips: List of coaching tips

        Returns:
            Self for method chaining
        """
        self._coaching_tips.extend(tips)
        return self

    def set_current_state(self, state: Dict[str, Any]) -> "FrameworkBuilder":
        """Set the current state/context.

        Args:
            state: Current workspace state for this entity

        Returns:
            Self for method chaining
        """
        self._current_state = state
        return self

    def add_context(self, key: str, value: Any) -> "FrameworkBuilder":
        """Add additional context field.

        Args:
            key: Context field name
            value: Context field value

        Returns:
            Self for method chaining
        """
        self._additional_context[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build the complete framework dictionary.

        Returns:
            Framework dictionary ready for return to Claude Code
        """
        framework: Dict[str, Any] = {
            "entity_type": self.entity_type,
        }

        if self._purpose:
            framework["purpose"] = self._purpose

        if self._criteria:
            framework["criteria"] = self._criteria

        if self._examples:
            framework["examples"] = self._examples

        if self._questions:
            framework["questions_to_explore"] = self._questions

        if self._anti_patterns:
            framework["anti_patterns"] = self._anti_patterns

        if self._coaching_tips:
            framework["coaching_tips"] = self._coaching_tips

        if self._current_state is not None:
            framework["current_state"] = self._current_state

        # Add any additional context
        framework.update(self._additional_context)

        return framework
