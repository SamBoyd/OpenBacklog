"""Unit tests for FrameworkBuilder and natural language mapping."""

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_entries,
    has_key,
    has_length,
    is_not,
)

from src.mcp_server.prompt_driven_tools.utils.framework_builder import FrameworkBuilder


class TestFrameworkBuilderCore:
    """Test suite for core FrameworkBuilder functionality."""

    def test_basic_build(self):
        """Test building a basic framework with required fields."""
        builder = FrameworkBuilder("test_entity")
        builder.set_purpose("Test purpose")
        builder.add_criterion("Criterion 1")

        result = builder.build()

        assert_that(result, has_key("entity_type"))
        assert_that(result["entity_type"], equal_to("test_entity"))
        assert_that(result, has_key("purpose"))
        assert_that(result["purpose"], equal_to("Test purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result["criteria"], has_length(1))

    def test_add_example(self):
        """Test adding examples with why_good and additional fields."""
        builder = FrameworkBuilder("hero")
        builder.add_example(
            text="Sarah, The Solo Builder",
            why_good="Specific person with observable context",
            context="Building SaaS solo",
        )

        result = builder.build()

        assert_that(result, has_key("examples"))
        assert_that(result["examples"], has_length(1))
        assert_that(result["examples"][0]["text"], equal_to("Sarah, The Solo Builder"))
        assert_that(result["examples"][0]["context"], equal_to("Building SaaS solo"))

    def test_add_anti_pattern(self):
        """Test adding anti-patterns with example, why_bad, and better."""
        builder = FrameworkBuilder("vision")
        builder.add_anti_pattern(
            example="Build the best AI tool",
            why_bad="Solution-focused, not outcome-focused",
            better="Enable X users to achieve Y",
        )

        result = builder.build()

        assert_that(result, has_key("anti_patterns"))
        assert_that(result["anti_patterns"], has_length(1))
        assert_that(
            result["anti_patterns"][0],
            has_entries(
                {
                    "example": "Build the best AI tool",
                    "why_bad": "Solution-focused, not outcome-focused",
                    "better": "Enable X users to achieve Y",
                }
            ),
        )

    def test_add_coaching_tips(self):
        """Test adding multiple coaching tips."""
        builder = FrameworkBuilder("pillar")
        builder.add_coaching_tips(
            [
                "Anti-strategy is just as important as strategy",
                "Good anti-strategy feels uncomfortable",
            ]
        )

        result = builder.build()

        assert_that(result, has_key("coaching_tips"))
        assert_that(result["coaching_tips"], has_length(2))

    def test_set_current_state(self):
        """Test setting current state."""
        builder = FrameworkBuilder("outcome")
        builder.set_current_state({"existing_outcomes": [], "outcome_count": 0})

        result = builder.build()

        assert_that(result, has_key("current_state"))
        assert_that(result["current_state"]["outcome_count"], equal_to(0))

    def test_add_context(self):
        """Test adding additional context fields."""
        builder = FrameworkBuilder("villain")
        builder.add_context(
            "villain_types",
            {
                "WORKFLOW": "Difficult processes",
                "TECHNICAL": "Bugs and limitations",
            },
        )

        result = builder.build()

        assert_that(result, has_key("villain_types"))
        assert_that(result["villain_types"], has_key("WORKFLOW"))


class TestNaturalLanguageMapping:
    """Test suite for natural language mapping features."""

    def test_set_conversation_guidelines(self):
        """Test setting conversation guidelines for framework-invisible UX."""
        builder = FrameworkBuilder("hero")
        builder.set_conversation_guidelines(
            say_this="use their actual name (Sarah, Alex)",
            not_this="the Hero, your hero persona",
            example="Who's the one person you're building this for?",
        )

        result = builder.build()

        assert_that(result, has_key("conversation_guidelines"))
        assert_that(
            result["conversation_guidelines"],
            has_entries(
                {
                    "say_this": "use their actual name (Sarah, Alex)",
                    "not_this": "the Hero, your hero persona",
                    "example_question": "Who's the one person you're building this for?",
                }
            ),
        )

    def test_add_natural_question(self):
        """Test adding natural question mappings."""
        builder = FrameworkBuilder("vision")
        builder.add_natural_question(
            "vision_statement",
            "What do you want to make possible for people?",
        )
        builder.add_natural_question(
            "outcome_focus",
            "When this works, what will users be able to do?",
        )

        result = builder.build()

        assert_that(result, has_key("natural_questions"))
        assert_that(result["natural_questions"], has_length(2))
        assert_that(
            result["natural_questions"][0],
            has_entries(
                {
                    "framework_term": "vision_statement",
                    "natural_question": "What do you want to make possible for people?",
                }
            ),
        )

    def test_add_extraction_guidance(self):
        """Test adding extraction guidance for parsing user input."""
        builder = FrameworkBuilder("hero")
        builder.add_extraction_guidance(
            from_input="Solo founders drowning in feedback",
            extractions={
                "name_pattern": "[Role], The [Descriptor]",
                "core_pain": "drowning = overwhelmed",
                "context": "solo = works alone",
            },
        )

        result = builder.build()

        assert_that(result, has_key("extraction_guidance"))
        assert_that(result["extraction_guidance"], has_length(1))
        assert_that(
            result["extraction_guidance"][0]["from_input"],
            equal_to("Solo founders drowning in feedback"),
        )
        assert_that(
            result["extraction_guidance"][0]["extractions"],
            has_key("name_pattern"),
        )

    def test_add_inference_example(self):
        """Test adding inference examples for implicit entity detection."""
        builder = FrameworkBuilder("vision")
        builder.add_inference_example(
            user_says="We help developers ship faster by removing context switching",
            inferences={
                "vision": "Enable developers to ship faster by staying in flow",
                "implied_hero": "Developer who loses time to context switching",
                "implied_villain": "Context switching between tools",
            },
        )

        result = builder.build()

        assert_that(result, has_key("inference_examples"))
        assert_that(result["inference_examples"], has_length(1))
        assert_that(
            result["inference_examples"][0]["user_says"],
            contains_string("context switching"),
        )
        assert_that(
            result["inference_examples"][0]["inferences"],
            has_key("implied_villain"),
        )

    def test_complete_natural_language_framework(self):
        """Test building a complete framework with all natural language mapping."""
        builder = FrameworkBuilder("hero")
        builder.set_purpose("Define who you're building for")

        builder.set_conversation_guidelines(
            say_this="use their actual name",
            not_this="the Hero",
            example="Who's the one person you're building this for?",
        )

        builder.add_natural_question(
            "hero_identity",
            "Who's the one person you're building this for?",
        )
        builder.add_natural_question(
            "pains",
            "What frustrates them most right now?",
        )

        builder.add_extraction_guidance(
            from_input="Solo founders drowning in feedback",
            extractions={"name_pattern": "Alex, The Solo Founder"},
        )

        builder.add_inference_example(
            user_says="Developers who lose hours to context switching",
            inferences={"hero_name": "A developer (give them a name like Sarah)"},
        )

        result = builder.build()

        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("conversation_guidelines"))
        assert_that(result, has_key("natural_questions"))
        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))

        assert_that(result["natural_questions"], has_length(2))

    def test_empty_natural_language_fields_not_included(self):
        """Test that empty natural language fields are not included in output."""
        builder = FrameworkBuilder("test")
        builder.set_purpose("Test purpose")

        result = builder.build()

        assert_that(result, is_not(has_key("conversation_guidelines")))
        assert_that(result, is_not(has_key("natural_questions")))
        assert_that(result, is_not(has_key("extraction_guidance")))
        assert_that(result, is_not(has_key("inference_examples")))

    def test_method_chaining(self):
        """Test that all methods support fluent chaining."""
        result = (
            FrameworkBuilder("test")
            .set_purpose("Test")
            .add_criterion("Criterion")
            .add_example(text="Example", why_good="Good")
            .add_question("Question?")
            .add_anti_pattern(example="Bad", why_bad="Why", better="Better")
            .add_coaching_tip("Tip")
            .set_current_state({"key": "value"})
            .add_context("extra", "data")
            .set_conversation_guidelines(say_this="Say", not_this="Not", example="Ex")
            .add_natural_question("term", "question")
            .add_extraction_guidance(from_input="input", extractions={"k": "v"})
            .add_inference_example(user_says="says", inferences={"k": "v"})
            .build()
        )

        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("conversation_guidelines"))
        assert_that(result, has_key("natural_questions"))
        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))
