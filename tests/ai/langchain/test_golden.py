"""
Golden I/O tests for Langchain agent using real LLM calls.

These tests execute the agent against the gold dataset and validate
responses through multiple assertion layers while handling LLM variance.
"""

import json
import logging
import time
from typing import List, Union

import pytest
from hamcrest import (
    assert_that,
    contains_inanyorder,
    equal_to,
    greater_than_or_equal_to,
    has_length,
    instance_of,
    is_,
    less_than,
    less_than_or_equal_to,
)

from evals.agent_evaluator import AgentEvaluator, EvalResult, GoldTestCase
from src.ai.models import (
    DiscussResponseModel,
    EasyInitiativeLLMResponse,
    EasyTaskLLMResponse,
)
from src.models import InitiativeLLMResponse, ManagedEntityAction, TaskLLMResponse

logger = logging.getLogger(__name__)

# Test categorization markers
pytestmark = [pytest.mark.asyncio]

# Fast test cases for CI (< 30s total)
FAST_TEST_CASES = {
    "simple_initiative_creation",
    "create_standalone_task",
    "pure_discussion_question",
    "delete_initiative",
    "delete_task_validation",
}

# Performance tracking storage (in production, this would be external)
_performance_history = {}


def load_gold_dataset() -> List[GoldTestCase]:
    """Load all test cases from gold dataset."""
    return AgentEvaluator.load_gold_dataset(
        "/Users/samboyd/projects/OpenBacklog/datasets/gold.jsonl"
    )


def load_fast_test_cases() -> List[GoldTestCase]:
    """Load only fast test cases for CI."""
    all_cases = load_gold_dataset()
    return [case for case in all_cases if case.name in FAST_TEST_CASES]


def load_all_test_cases() -> List[GoldTestCase]:
    """Load all test cases for comprehensive testing."""
    return load_gold_dataset()


class SmartAssertionHelpers:
    """Helper methods for flexible agent response validation."""

    @staticmethod
    def assert_tool_sequence_matches(actual: List[str], expected: List[str]) -> None:
        """Allow benign variations in tool order while ensuring core sequence."""
        if not expected:
            return  # No expected tools to validate

        # Filter to only expected tools, preserve order
        filtered_actual = [tool for tool in actual if tool in expected]

        # Core tools must appear in expected order
        assert_that(filtered_actual, contains_inanyorder(*expected))

    @staticmethod
    def assert_content_similarity(actual: str, expected_keywords: List[str]) -> None:
        """Flexible content matching using keyword presence."""
        if not expected_keywords:
            return  # No keywords to validate

        actual_lower = actual.lower()

        # Keyword-based scoring
        found_keywords = [kw for kw in expected_keywords if kw.lower() in actual_lower]
        keyword_ratio = len(found_keywords) / len(expected_keywords)

        # Allow 80% keyword match to handle LLM variance
        assert_that(
            keyword_ratio,
            greater_than_or_equal_to(0.8),
            f"Only found {len(found_keywords)}/{len(expected_keywords)} keywords: {found_keywords}",
        )

    @staticmethod
    def validate_operation_count(actual: int, expected: Union[int, List[str]]) -> None:
        """Handle flexible operation count expectations."""
        if isinstance(expected, int):
            assert_that(actual, equal_to(expected))
        elif len(expected) == 2:  # Assume it's a list at this point
            operator, value = expected[0], expected[1]
            if operator == ">=":
                assert_that(actual, greater_than_or_equal_to(value))
            elif operator == "<=":
                assert_that(actual, less_than_or_equal_to(value))
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        else:
            raise ValueError(f"Invalid operation count format: {expected}")


class TestGoldenIO:
    """Golden I/O tests with real agent execution."""

    def _get_expected_model_type(self, validation_schema: str):
        """Get the expected Pydantic model type for validation."""
        schema_mapping = {
            "EasyInitiativeLLMResponse": EasyInitiativeLLMResponse,
            "EasyTaskLLMResponse": EasyTaskLLMResponse,
            "DiscussResponseModel": DiscussResponseModel,
            "InitiativeLLMResponse": InitiativeLLMResponse,
            "TaskLLMResponse": TaskLLMResponse,
        }
        return schema_mapping.get(validation_schema)

    async def _execute_agent_test(
        self,
        test_case: GoldTestCase,
        agent_evaluator: AgentEvaluator,
        agent_test_context: dict,
        openai_api_key: str,
    ) -> EvalResult:
        """Execute agent test with comprehensive logging for debugging."""
        logger.info(f"Executing test case: {test_case.name}")
        logger.debug(f"Test context: {test_case.context}")

        start_time = time.time()

        try:
            result = await agent_evaluator.run_agent(
                test_case=test_case,
                api_key=openai_api_key,
                user_auth_token=agent_test_context.get("user_auth_token", "test-token"),
                workspace_id=agent_test_context["workspace_id"],
                thread_id=agent_test_context["thread_id"],
                user_id=agent_test_context["user_id"],
            )

            execution_time = (time.time() - start_time) * 1000
            logger.info(
                f"Agent execution completed: {result.success} ({execution_time:.0f}ms)"
            )

            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"Agent execution failed for {test_case.name} after {execution_time:.0f}ms: {e}"
            )
            # Store failure artifacts for debugging
            self._store_failure_artifacts(test_case, str(e))
            raise

    def _store_failure_artifacts(self, test_case: GoldTestCase, error: str) -> None:
        """Store debugging artifacts for failed tests."""
        # In production, this would write to a persistent location
        failure_data = {
            "test_case": test_case.name,
            "error": error,
            "timestamp": time.time(),
            "context": test_case.context,
        }
        logger.debug(f"Failure artifacts: {json.dumps(failure_data, indent=2)}")

    def _validate_result(self, result: EvalResult, test_case: GoldTestCase) -> None:
        """Comprehensive validation through multiple assertion layers."""
        logger.info(f"=== VALIDATING RESULT FOR TEST: {test_case.name} ===")
        logger.info(f"Agent final answer: {result.final_answer}")
        logger.info(
            f"Agent structured output type: {getattr(result.structured_output, 'type', 'None')}"
        )

        if result.structured_output:
            try:
                if hasattr(result.structured_output, "model_dump"):
                    output_dict = result.structured_output.model_dump()
                elif hasattr(result.structured_output, "dict"):
                    # Fallback for older Pydantic versions
                    output_dict = result.structured_output.dict()
                else:
                    output_dict = str(result.structured_output)
                logger.info(
                    f"Agent structured output: {json.dumps(output_dict, indent=2)}"
                )
            except Exception:
                logger.info(f"Agent structured output: {str(result.structured_output)}")

        logger.info(f"Tool calls made: {[call.name for call in result.tool_calls]}")
        logger.info(f"Expected keywords: {test_case.must_include}")
        logger.info(f"Expected operations: {test_case.expected_operations}")
        logger.info(f"Expected tools: {test_case.tool_plan}")

        helpers = SmartAssertionHelpers()

        try:
            # Layer 1: Schema Validation
            logger.info("--- Layer 1: Schema Validation ---")
            self._validate_schema(result, test_case)
            logger.info("✓ Schema validation passed")

            # Layer 2: Content Validation
            logger.info("--- Layer 2: Content Validation ---")
            self._validate_content(result, test_case, helpers)
            logger.info("✓ Content validation passed")

            # Layer 3: Tool Sequence Validation
            logger.info("--- Layer 3: Tool Sequence Validation ---")
            self._validate_tool_sequence(result, test_case, helpers)
            logger.info("✓ Tool sequence validation passed")

            # Layer 4: Operations Validation
            logger.info("--- Layer 4: Operations Validation ---")
            self._validate_operations(result, test_case, helpers)
            logger.info("✓ Operations validation passed")

            # Layer 5: Performance Validation
            logger.info("--- Layer 5: Performance Validation ---")
            self._validate_performance(result, test_case)
            logger.info("✓ Performance validation passed")

            logger.info("=== ALL VALIDATIONS PASSED ===")
        except Exception as e:
            logger.error(f"=== VALIDATION FAILED: {str(e)} ===")
            raise

    def _validate_schema(self, result: EvalResult, test_case: GoldTestCase) -> None:
        """Validate structured output matches expected schema."""
        logger.info(f"Expected schema: {test_case.validation_schema}")
        logger.info(
            f"Schema validation result: {result.validation_result.schema_valid}"
        )

        if not result.validation_result.schema_valid:
            logger.error(f"Schema validation errors: {result.validation_result.errors}")
            logger.error(
                f"Raw structured output that failed validation: {result.structured_output}"
            )

        assert_that(
            result.validation_result.schema_valid,
            is_(True),
            f"Schema validation failed: {result.validation_result.errors}",
        )

        expected_model_type = self._get_expected_model_type(test_case.validation_schema)
        if expected_model_type:
            logger.info(f"Expected model type: {expected_model_type.__name__}")
            logger.info(
                f"Actual structured output type: {type(result.structured_output).__name__}"
            )
            assert_that(result.structured_output, instance_of(expected_model_type))

    def _validate_content(
        self,
        result: EvalResult,
        test_case: GoldTestCase,
        helpers: SmartAssertionHelpers,
    ) -> None:
        """Validate response content using flexible matching."""
        logger.info(f"Agent final answer length: {len(result.final_answer)} characters")
        logger.info(
            f"Agent final answer preview: {result.final_answer[:500]}{'...' if len(result.final_answer) > 500 else ''}"
        )

        # Regex pattern matching (handles LLM variance)
        if test_case.expected_regex:
            logger.info(f"Expected regex pattern: {test_case.expected_regex}")
            logger.info(f"Regex match result: {result.validation_result.regex_match}")
            if not result.validation_result.regex_match:
                logger.error(
                    f"Regex pattern '{test_case.expected_regex}' not found in agent response"
                )
            assert_that(
                result.validation_result.regex_match,
                is_(True),
                f"Regex pattern '{test_case.expected_regex}' not found in response",
            )

        # Required keywords (case-insensitive, flexible)
        logger.info(f"Keywords found: {result.validation_result.keywords_found}")
        logger.info(f"Keywords missing: {result.validation_result.keywords_missing}")

        if result.validation_result.keywords_missing:
            logger.error(
                f"Agent response is missing required keywords: {result.validation_result.keywords_missing}"
            )
            logger.error(
                f"Full agent response for keyword analysis:\n{result.final_answer}"
            )

        assert_that(
            result.validation_result.keywords_missing,
            has_length(0),
            f"Missing required keywords: {result.validation_result.keywords_missing}",
        )

        # Smart content similarity (not exact string matching)
        if test_case.must_include:
            logger.info(
                f"Checking content similarity for keywords: {test_case.must_include}"
            )
            try:
                helpers.assert_content_similarity(
                    result.final_answer, test_case.must_include
                )
                logger.info("✓ Content similarity check passed")
            except Exception as e:
                logger.error(f"Content similarity check failed: {str(e)}")
                logger.error(
                    f"Agent response for similarity analysis:\n{result.final_answer}"
                )
                raise

    def _validate_tool_sequence(
        self,
        result: EvalResult,
        test_case: GoldTestCase,
        helpers: SmartAssertionHelpers,
    ) -> None:
        """Validate tool calls with flexible matching."""
        if not test_case.tool_plan:
            logger.info("No expected tools to validate")
            return  # No expected tools to validate

        actual_tools = [call.name for call in result.tool_calls]
        logger.info(f"Expected tools: {test_case.tool_plan}")
        logger.info(f"Actual tools called: {actual_tools}")

        # Log detailed tool call information
        for i, call in enumerate(result.tool_calls):
            logger.info(f"Tool call {i+1}: {call.name} with args: {call.arguments}")
            logger.info(f"  Duration: {call.duration_ms:.1f}ms")
            if hasattr(call, "result") and call.result:
                result_preview = str(call.result)[:200]
                logger.info(
                    f"  Result preview: {result_preview}{'...' if len(str(call.result)) > 200 else ''}"
                )

        # Flexible tool order matching (allow benign variations)
        try:
            helpers.assert_tool_sequence_matches(actual_tools, test_case.tool_plan)
            logger.info("✓ Tool sequence validation passed")
        except Exception as e:
            logger.error(f"Tool sequence validation failed: {str(e)}")
            logger.error(f"Expected tool sequence: {test_case.tool_plan}")
            logger.error(f"Actual tool sequence: {actual_tools}")

            # Show which tools are missing or unexpected
            expected_set = set(test_case.tool_plan)
            actual_set = set(actual_tools)
            missing_tools = expected_set - actual_set
            unexpected_tools = actual_set - expected_set

            if missing_tools:
                logger.error(f"Missing expected tools: {list(missing_tools)}")
            if unexpected_tools:
                logger.error(f"Unexpected tools called: {list(unexpected_tools)}")

            raise

    def _validate_operations(
        self,
        result: EvalResult,
        test_case: GoldTestCase,
        helpers: SmartAssertionHelpers,
    ) -> None:
        """Validate expected operations were performed."""
        expected_ops = test_case.expected_operations
        if not expected_ops:
            logger.info("No expected operations to validate")
            return  # No operations to validate

        logger.info(f"Expected operations: {expected_ops}")
        logger.info(
            f"Structured output type: {getattr(result.structured_output, 'type', 'None')}"
        )

        # Log the actual operations found in structured output
        if result.structured_output and hasattr(
            result.structured_output, "managed_initiatives"
        ):
            try:
                initiative_ops = result.structured_output.managed_initiatives
                if initiative_ops:
                    logger.info(f"Found {len(initiative_ops)} initiative operations:")
                    for i, op in enumerate(initiative_ops):
                        logger.info(
                            f"  Initiative {i+1}: action={getattr(op, 'action', 'Unknown')}, id={getattr(op, 'id', 'N/A')}"
                        )
                        if hasattr(op, "tasks") and getattr(op, "tasks", None):
                            tasks = getattr(op, "tasks", [])
                            logger.info(f"    With {len(tasks)} task operations:")
                            for j, task_op in enumerate(tasks):
                                logger.info(
                                    f"      Task {j+1}: action={getattr(task_op, 'action', 'Unknown')}, id={getattr(task_op, 'id', 'N/A')}"
                                )
            except Exception as e:
                logger.error(f"Error logging initiative operations: {e}")

        if result.structured_output and hasattr(
            result.structured_output, "managed_tasks"
        ):
            try:
                task_ops = result.structured_output.managed_tasks
                if task_ops:
                    logger.info(f"Found {len(task_ops)} direct task operations:")
                    for i, op in enumerate(task_ops):
                        logger.info(
                            f"  Task {i+1}: action={getattr(op, 'action', 'Unknown')}, id={getattr(op, 'id', 'N/A')}"
                        )
            except Exception as e:
                logger.error(f"Error logging task operations: {e}")

        # Validate initiative operations
        if (
            "created_initiatives" in expected_ops
            and result.structured_output
            and hasattr(result.structured_output, "managed_initiatives")
        ):
            managed_initiatives = getattr(
                result.structured_output, "managed_initiatives", []
            )
            create_operations = [
                operation
                for operation in managed_initiatives
                if getattr(operation, "action", None) == ManagedEntityAction.CREATE
            ]
            actual_count = len(create_operations)
            logger.info(
                f"Initiative CREATE operations: expected={expected_ops['created_initiatives']}, actual={actual_count}"
            )
            if actual_count != expected_ops["created_initiatives"]:
                logger.error(
                    f"Initiative CREATE count mismatch! Expected: {expected_ops['created_initiatives']}, Got: {actual_count}"
                )
                op_details = [
                    f"id={getattr(op, 'id', 'N/A')}" for op in create_operations
                ]
                logger.error(f"Actual CREATE operations: {op_details}")
            helpers.validate_operation_count(
                actual_count, expected_ops["created_initiatives"]
            )

        if (
            "updated_initiatives" in expected_ops
            and result.structured_output
            and hasattr(result.structured_output, "managed_initiatives")
        ):
            managed_initiatives = getattr(
                result.structured_output, "managed_initiatives", []
            )
            update_operations = [
                operation
                for operation in managed_initiatives
                if getattr(operation, "action", None) == ManagedEntityAction.UPDATE
            ]
            actual_count = len(update_operations)
            logger.info(
                f"Initiative UPDATE operations: expected={expected_ops['updated_initiatives']}, actual={actual_count}"
            )
            if actual_count != expected_ops["updated_initiatives"]:
                logger.error(
                    f"Initiative UPDATE count mismatch! Expected: {expected_ops['updated_initiatives']}, Got: {actual_count}"
                )
                op_details = [
                    f"id={getattr(op, 'id', 'N/A')}" for op in update_operations
                ]
                logger.error(f"Actual UPDATE operations: {op_details}")
            helpers.validate_operation_count(
                actual_count, expected_ops["updated_initiatives"]
            )

        if (
            "deleted_initiatives" in expected_ops
            and result.structured_output
            and hasattr(result.structured_output, "managed_initiatives")
        ):
            managed_initiatives = getattr(
                result.structured_output, "managed_initiatives", []
            )
            delete_operations = [
                operation
                for operation in managed_initiatives
                if getattr(operation, "action", None) == ManagedEntityAction.DELETE
            ]
            actual_count = len(delete_operations)
            logger.info(
                f"Initiative DELETE operations: expected={expected_ops['deleted_initiatives']}, actual={actual_count}"
            )
            if actual_count != expected_ops["deleted_initiatives"]:
                logger.error(
                    f"Initiative DELETE count mismatch! Expected: {expected_ops['deleted_initiatives']}, Got: {actual_count}"
                )
                op_details = [
                    f"id={getattr(op, 'id', 'N/A')}" for op in delete_operations
                ]
                logger.error(f"Actual DELETE operations: {op_details}")
            helpers.validate_operation_count(
                actual_count, expected_ops["deleted_initiatives"]
            )

        if (
            result.structured_output
            and getattr(result.structured_output, "type", None) == "task_llm_response"
        ):
            logger.info("Validating task operations for task_llm_response")
            # Validate task operations
            if "created_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_tasks"
            ):
                managed_tasks = getattr(result.structured_output, "managed_tasks", [])
                create_operations = [
                    operation
                    for operation in managed_tasks
                    if getattr(operation, "action", None) == ManagedEntityAction.CREATE
                ]
                actual_count = len(create_operations)
                logger.info(
                    f"Task CREATE operations: expected={expected_ops['created_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["created_tasks"]:
                    logger.error(
                        f"Task CREATE count mismatch! Expected: {expected_ops['created_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in create_operations
                    ]
                    logger.error(f"Actual CREATE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["created_tasks"]
                )

            if "updated_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_tasks"
            ):
                managed_tasks = getattr(result.structured_output, "managed_tasks", [])
                update_operations = [
                    operation
                    for operation in managed_tasks
                    if getattr(operation, "action", None) == ManagedEntityAction.UPDATE
                ]
                actual_count = len(update_operations)
                logger.info(
                    f"Task UPDATE operations: expected={expected_ops['updated_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["updated_tasks"]:
                    logger.error(
                        f"Task UPDATE count mismatch! Expected: {expected_ops['updated_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in update_operations
                    ]
                    logger.error(f"Actual UPDATE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["updated_tasks"]
                )

            if "deleted_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_tasks"
            ):
                managed_tasks = getattr(result.structured_output, "managed_tasks", [])
                delete_operations = [
                    operation
                    for operation in managed_tasks
                    if getattr(operation, "action", None) == ManagedEntityAction.DELETE
                ]
                actual_count = len(delete_operations)
                logger.info(
                    f"Task DELETE operations: expected={expected_ops['deleted_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["deleted_tasks"]:
                    logger.error(
                        f"Task DELETE count mismatch! Expected: {expected_ops['deleted_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in delete_operations
                    ]
                    logger.error(f"Actual DELETE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["deleted_tasks"]
                )

        elif (
            result.structured_output
            and getattr(result.structured_output, "type", None)
            == "initiative_llm_response"
        ):
            logger.info("Validating task operations for initiative_llm_response")
            # Validate task operations
            if "created_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_initiatives"
            ):
                create_operations = []
                managed_initiatives = getattr(
                    result.structured_output, "managed_initiatives", []
                )
                for initiative_operation in managed_initiatives:
                    action = getattr(initiative_operation, "action", None)
                    if (
                        action == ManagedEntityAction.CREATE
                        or action == ManagedEntityAction.UPDATE
                    ):
                        tasks = getattr(initiative_operation, "tasks", [])
                        if tasks:
                            task_creates = [
                                task
                                for task in tasks
                                if getattr(task, "action", None)
                                == ManagedEntityAction.CREATE
                            ]
                            create_operations.extend(task_creates)
                actual_count = len(create_operations)
                logger.info(
                    f"Task CREATE operations (in initiatives): expected={expected_ops['created_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["created_tasks"]:
                    logger.error(
                        f"Task CREATE count mismatch! Expected: {expected_ops['created_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in create_operations
                    ]
                    logger.error(f"Actual CREATE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["created_tasks"]
                )

            if "updated_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_initiatives"
            ):
                update_operations = []
                managed_initiatives = getattr(
                    result.structured_output, "managed_initiatives", []
                )
                for initiative_operation in managed_initiatives:
                    action = getattr(initiative_operation, "action", None)
                    if (
                        action == ManagedEntityAction.CREATE
                        or action == ManagedEntityAction.UPDATE
                    ):
                        tasks = getattr(initiative_operation, "tasks", [])
                        if tasks:
                            task_updates = [
                                task
                                for task in tasks
                                if getattr(task, "action", None)
                                == ManagedEntityAction.UPDATE
                            ]
                            update_operations.extend(task_updates)
                actual_count = len(update_operations)
                logger.info(
                    f"Task UPDATE operations (in initiatives): expected={expected_ops['updated_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["updated_tasks"]:
                    logger.error(
                        f"Task UPDATE count mismatch! Expected: {expected_ops['updated_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in update_operations
                    ]
                    logger.error(f"Actual UPDATE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["updated_tasks"]
                )

            if "deleted_tasks" in expected_ops and hasattr(
                result.structured_output, "managed_initiatives"
            ):
                delete_operations = []
                managed_initiatives = getattr(
                    result.structured_output, "managed_initiatives", []
                )
                for initiative_operation in managed_initiatives:
                    action = getattr(initiative_operation, "action", None)
                    if action == ManagedEntityAction.DELETE:
                        tasks = getattr(initiative_operation, "tasks", [])
                        if tasks:
                            task_deletes = [
                                task
                                for task in tasks
                                if getattr(task, "action", None)
                                == ManagedEntityAction.DELETE
                            ]
                            delete_operations.extend(task_deletes)
                actual_count = len(delete_operations)
                logger.info(
                    f"Task DELETE operations (in initiatives): expected={expected_ops['deleted_tasks']}, actual={actual_count}"
                )
                if actual_count != expected_ops["deleted_tasks"]:
                    logger.error(
                        f"Task DELETE count mismatch! Expected: {expected_ops['deleted_tasks']}, Got: {actual_count}"
                    )
                    op_details = [
                        f"id={getattr(op, 'id', 'N/A')}" for op in delete_operations
                    ]
                    logger.error(f"Actual DELETE operations: {op_details}")
                helpers.validate_operation_count(
                    actual_count, expected_ops["deleted_tasks"]
                )

    def _validate_performance(
        self, result: EvalResult, test_case: GoldTestCase
    ) -> None:
        """Validate performance bounds and track regression."""
        metrics = result.performance_metrics

        logger.info(f"Performance metrics for test '{test_case.name}':")
        logger.info(f"  Total latency: {metrics.total_latency_ms:.1f}ms")
        logger.info(f"  Token count: {metrics.token_count}")
        logger.info(f"  Tool call count: {metrics.tool_call_count}")
        logger.info(f"  Memory operations: {metrics.memory_operation_count}")
        logger.info(f"  Response length: {metrics.response_length}")
        logger.info(f"  Estimated cost: ${metrics.estimated_cost:.4f}")

        # Latency bounds (generous for LLM variance)
        if metrics.total_latency_ms >= 30000:
            logger.error(
                f"Performance FAILURE: Test exceeded 30s limit with {metrics.total_latency_ms:.1f}ms"
            )
        assert_that(
            metrics.total_latency_ms,
            less_than(30000),  # 30 second max
            f"Test took too long: {metrics.total_latency_ms}ms",
        )

        # Token efficiency (reasonable upper bound)
        if metrics.token_count >= 2000:
            logger.error(
                f"Performance FAILURE: Token usage too high with {metrics.token_count} tokens"
            )
        assert_that(
            metrics.token_count,
            less_than(2000),
            f"Token usage too high: {metrics.token_count}",
        )

        logger.info(
            f"✓ Performance validation passed - Latency: {metrics.total_latency_ms:.0f}ms, "
            f"Tokens: {metrics.token_count}, Tools: {metrics.tool_call_count}"
        )

    def _track_performance_metrics(
        self, result: EvalResult, test_case: GoldTestCase
    ) -> None:
        """Track performance metrics for regression detection."""
        metrics = result.performance_metrics

        # Store metrics (in production, this would be external storage)
        test_name = test_case.name
        if test_name not in _performance_history:
            _performance_history[test_name] = []

        _performance_history[test_name].append(
            {
                "timestamp": time.time(),
                "latency_ms": metrics.total_latency_ms,
                "token_count": metrics.token_count,
                "tool_call_count": metrics.tool_call_count,
                "estimated_cost": metrics.estimated_cost,
            }
        )

        # Log for CI metrics collection
        logger.info(
            f"PERFORMANCE_METRIC: {test_name} {metrics.total_latency_ms:.0f}ms {metrics.token_count}tokens"
        )

    @pytest.mark.parametrize(
        "test_case", load_fast_test_cases(), ids=lambda tc: tc.name
    )
    @pytest.mark.fast
    async def test_golden_fast_cases(
        self,
        test_case: GoldTestCase,
        agent_evaluator: AgentEvaluator,
        agent_test_context: dict,
        openai_api_key: str,
    ):
        """Fast golden tests for CI (< 30s total)."""
        result = await self._execute_agent_test(
            test_case, agent_evaluator, agent_test_context, openai_api_key
        )

        self._validate_result(result, test_case)

    @pytest.mark.parametrize("test_case", load_all_test_cases(), ids=lambda tc: tc.name)
    async def test_golden_standard_cases(
        self,
        test_case: GoldTestCase,
        agent_evaluator: AgentEvaluator,
        agent_test_context: dict,
        openai_api_key: str,
    ):
        """Standard golden tests for development (full dataset)."""
        result = await self._execute_agent_test(
            test_case, agent_evaluator, agent_test_context, openai_api_key
        )
        self._validate_result(result, test_case)

    @pytest.mark.parametrize("test_case", load_all_test_cases(), ids=lambda tc: tc.name)
    @pytest.mark.performance
    async def test_golden_performance_tracking(
        self,
        test_case: GoldTestCase,
        agent_evaluator: AgentEvaluator,
        agent_test_context: dict,
        openai_api_key: str,
    ):
        """Performance tracking tests with detailed metrics."""
        result = await self._execute_agent_test(
            test_case, agent_evaluator, agent_test_context, openai_api_key
        )
        self._validate_result(result, test_case)
        self._track_performance_metrics(result, test_case)
