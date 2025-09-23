"""
Agent evaluation library for testing the Langchain agent.

This module provides comprehensive evaluation capabilities for testing the agent's
performance, tool usage, response quality, and adherence to expected patterns.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ValidationError

from src.models import InitiativeLLMResponse, TaskLLMResponse
from src.ai.langchain.langchain_service import call_llm_api
from src.ai.langchain.tool_callback_handler import ToolCallbackHandler
from src.ai.models import (
    ChatMessageInput,
    DiscussResponseModel,
    EasyInitiativeLLMResponse,
    EasyTaskLLMResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class GoldTestCase:
    """Represents a single test case from the gold dataset."""

    name: str
    category: str
    input: str
    context: Dict[str, Any]
    expected_regex: str
    references: List[str]
    tool_plan: List[str]
    must_include: List[str]
    validation_schema: str
    expected_operations: Dict[str, Any]


@dataclass
class ToolCall:
    """Represents a tool call made during agent execution."""

    name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: float
    duration_ms: float


@dataclass
class MemoryOp:
    """Represents a memory operation during agent execution."""

    operation: str  # 'store', 'retrieve', 'search'
    namespace: str
    key: Optional[str]
    value: Any
    timestamp: float


@dataclass
class PerformanceMetrics:
    """Performance metrics for agent execution."""

    total_latency_ms: float
    token_count: int
    estimated_cost: float
    tool_call_count: int
    memory_operation_count: int
    response_length: int


@dataclass
class ValidationResult:
    """Result of validating agent output against expected patterns."""

    schema_valid: bool
    regex_match: bool
    keywords_found: List[str]
    keywords_missing: List[str]
    tool_plan_match: bool
    operations_match: bool
    errors: List[str]


@dataclass
class EvalResult:
    """Complete result of agent evaluation."""

    test_case: GoldTestCase
    final_answer: str
    tool_calls: List[ToolCall]
    structured_output: Union[InitiativeLLMResponse, TaskLLMResponse, DiscussResponseModel, None]
    memory_operations: List[MemoryOp]
    performance_metrics: PerformanceMetrics
    validation_result: ValidationResult
    trace_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


@dataclass
class EvalConfig:
    """Configuration for agent evaluation."""

    temperature: float = 0.1
    timeout_seconds: int = 120
    use_real_api: bool = True
    mock_responses: Dict[str, Any] = field(default_factory=dict)
    include_memory: bool = True
    include_search: bool = True
    log_traces: bool = True


class TracingCallback(ToolCallbackHandler):
    """Enhanced callback handler for comprehensive tracing."""

    def __init__(self):
        super().__init__()
        self.trace_events = []
        self.tool_calls = []
        self.memory_operations = []
        self.start_time = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Track LLM execution start."""
        self.start_time = time.time()
        self.trace_events.append({
            "event": "llm_start",
            "timestamp": self.start_time,
            "prompts": prompts
        })

    def on_llm_end(self, response, **kwargs):
        """Track LLM execution end."""
        end_time = time.time()
        self.trace_events.append({
            "event": "llm_end",
            "timestamp": end_time,
            "response": str(response),
            "duration_ms": (end_time - self.start_time) * 1000 if self.start_time else 0
        })

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, **kwargs):
        """Track tool execution start."""
        tool_start_time = time.time()
        tool_name = serialized.get("name", "unknown")


        self.trace_events.append({
            "event": "tool_start",
            "tool_name": tool_name,
            "input": input_str,
            "timestamp": tool_start_time
        })

        # Store start time and tool name for duration calculation and name retrieval
        self._tool_start_times = getattr(self, "_tool_start_times", {})
        self._tool_run_names = getattr(self, "_tool_run_names", {})
        self._tool_start_times[run_id] = tool_start_time
        self._tool_run_names[run_id] = tool_name

    def on_tool_end(self, output, *, run_id: UUID, **kwargs):
        """Track tool execution end."""
        end_time = time.time()

        # Get tool name and start time using run_id
        self._tool_start_times = getattr(self, "_tool_start_times", {})
        self._tool_run_names = getattr(self, "_tool_run_names", {})

        tool_name = self._tool_run_names.get(run_id, "unknown")
        start_time = self._tool_start_times.get(run_id, end_time)

        duration_ms = (end_time - start_time) * 1000

        tool_call = ToolCall(
            name=tool_name,
            arguments=kwargs.get("input", {}),
            result=output,
            timestamp=end_time,
            duration_ms=duration_ms
        )

        self.tool_calls.append(tool_call)

        # Clean up tracking data for this run
        self._tool_start_times.pop(run_id, None)
        self._tool_run_names.pop(run_id, None)

        self.trace_events.append({
            "event": "tool_end",
            "tool_name": tool_name,
            "output": str(output),
            "timestamp": end_time,
            "duration_ms": duration_ms
        })

        # Track memory operations
        if "memory" in tool_name.lower():
            memory_op = MemoryOp(
                operation="store" if "store" in tool_name else "retrieve",
                namespace=kwargs.get("namespace", "unknown"),
                key=kwargs.get("key"),
                value=output,
                timestamp=end_time
            )
            self.memory_operations.append(memory_op)

    def get_performance_metrics(self, response_text: str) -> PerformanceMetrics:
        """Calculate performance metrics from trace data."""
        total_duration = 0
        if self.trace_events:
            start_events = [e for e in self.trace_events if e["event"].endswith("_start")]
            end_events = [e for e in self.trace_events if e["event"].endswith("_end")]

            if start_events and end_events:
                total_duration = (end_events[-1]["timestamp"] - start_events[0]["timestamp"]) * 1000

        return PerformanceMetrics(
            total_latency_ms=total_duration,
            token_count=len(response_text.split()),  # Rough approximation
            estimated_cost=0.0,  # TODO: Implement cost calculation
            tool_call_count=len(self.tool_calls),
            memory_operation_count=len(self.memory_operations),
            response_length=len(response_text)
        )


class AgentEvaluator:
    """Main evaluation class for testing the Langchain agent."""

    def __init__(self, config: EvalConfig):
        self.config = config

    async def run_agent(
        self,
        test_case: GoldTestCase,
        api_key: str,
        user_auth_token: str,
        workspace_id: str,
        thread_id: str,
        user_id: str
    ) -> EvalResult:
        """Execute the agent with a test case and return comprehensive results."""

        callback = TracingCallback()

        try:
            # Prepare messages for the agent
            messages: List[ChatMessageInput] = [
                ChatMessageInput(role="user", content=test_case.input)
            ]

            # Execute the agent
            start_time = time.time()

            # Determine expected response model
            if test_case.validation_schema == "InitiativeLLMResponse":
                from src.ai.prompt import InitiativePrompt
                from src.models import PydanticInitiative

                # Convert context to PydanticInitiative objects
                initiatives = []
                for init_data in test_case.context.get("initiatives", []):
                    initiatives.append(PydanticInitiative(**init_data))

                prompt = InitiativePrompt(
                    initiatives=initiatives,
                    messages=messages
                )

            elif test_case.validation_schema == "TaskLLMResponse":
                from src.ai.prompt import TaskPrompt
                from src.models import PydanticTask

                # Convert context to PydanticTask objects
                tasks = []
                for task_data in test_case.context.get("tasks", []):
                    tasks.append(PydanticTask(**task_data))

                prompt = TaskPrompt(
                    tasks=tasks,
                    initiative=None,  # TODO: Handle initiative context
                    messages=messages
                )

            elif test_case.validation_schema == "DiscussResponseModel":
                from src.ai.prompt import DiscussInitiativePrompt
                from src.models import PydanticInitiative

                initiatives = []
                for init_data in test_case.context.get("initiatives", []):
                    initiatives.append(PydanticInitiative(**init_data))

                prompt = DiscussInitiativePrompt(
                    initiatives=initiatives,
                    messages=messages
                )
            else:
                raise ValueError(f"Unknown validation schema: {test_case.validation_schema}")

            # Execute the prompt with tracing callback
            result = await prompt.process_prompt(
                api_key=api_key,
                user_auth_token=user_auth_token,
                workspace_id=workspace_id,
                thread_id=thread_id,
                user_id=user_id,
                callbacks=[callback]
            )

            execution_time = (time.time() - start_time) * 1000

            # Extract structured output
            structured_output = result
            final_answer = getattr(result, "message", str(result))

            # Get performance metrics
            performance_metrics = callback.get_performance_metrics(final_answer)
            performance_metrics.total_latency_ms = execution_time

            # Validate the output
            validation_result = self.validate_output(result, test_case)

            return EvalResult(
                test_case=test_case,
                final_answer=final_answer,
                tool_calls=callback.tool_calls,
                structured_output=structured_output,
                memory_operations=callback.memory_operations,
                performance_metrics=performance_metrics,
                validation_result=validation_result,
                trace_data={"events": callback.trace_events},
                success=validation_result.schema_valid and not validation_result.errors
            )

        except Exception as e:
            logger.exception(f"Error executing agent for test case {test_case.name}: {e}")

            return EvalResult(
                test_case=test_case,
                final_answer="",
                tool_calls=[],
                structured_output=None,
                memory_operations=[],
                performance_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0),
                validation_result=ValidationResult(False, False, [], [], False, False, [str(e)]),
                trace_data={"events": callback.trace_events},
                success=False,
                error_message=str(e)
            )

    def validate_output(self, result: Any, test_case: GoldTestCase) -> ValidationResult:
        """Validate agent output against expected patterns."""

        errors = []
        schema_valid = False
        regex_match = False
        keywords_found = []
        keywords_missing = []
        tool_plan_match = True  # TODO: Implement tool plan validation
        operations_match = True  # TODO: Implement operations validation

        try:
            # Schema validation
            if hasattr(result, "model_validate"):
                schema_valid = True
            elif isinstance(result, (EasyInitiativeLLMResponse, EasyTaskLLMResponse, DiscussResponseModel)):
                schema_valid = True
            else:
                errors.append("Invalid response schema")

            # Extract text for validation
            text_content = getattr(result, "message", str(result))

            # Regex validation
            if test_case.expected_regex:
                regex_match = bool(re.search(test_case.expected_regex, text_content))
                if not regex_match:
                    errors.append(f"Text does not match expected pattern: {test_case.expected_regex}")

            # Keyword validation
            text_lower = text_content.lower()
            for keyword in test_case.must_include:
                if keyword.lower() in text_lower:
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)

            if keywords_missing:
                errors.append(f"Missing required keywords: {keywords_missing}")

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return ValidationResult(
            schema_valid=schema_valid,
            regex_match=regex_match,
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            tool_plan_match=tool_plan_match,
            operations_match=operations_match,
            errors=errors
        )

    @staticmethod
    def load_gold_dataset(file_path: str) -> List[GoldTestCase]:
        """Load test cases from gold dataset JSONL file."""

        test_cases = []

        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        test_case = GoldTestCase(**data)
                        test_cases.append(test_case)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Error parsing line {line_num} in {file_path}: {e}")

        except FileNotFoundError:
            logger.error(f"Gold dataset file not found: {file_path}")
            raise

        logger.info(f"Loaded {len(test_cases)} test cases from {file_path}")
        return test_cases


def extract_metrics(eval_results: List[EvalResult]) -> Dict[str, Any]:
    """Extract summary metrics from a list of evaluation results."""

    if not eval_results:
        return {}

    total_tests = len(eval_results)
    successful_tests = sum(1 for r in eval_results if r.success)

    avg_latency = sum(r.performance_metrics.total_latency_ms for r in eval_results) / total_tests
    avg_tool_calls = sum(r.performance_metrics.tool_call_count for r in eval_results) / total_tests

    # Group by category
    category_stats = {}
    for result in eval_results:
        category = result.test_case.category
        if category not in category_stats:
            category_stats[category] = {"total": 0, "success": 0}
        category_stats[category]["total"] += 1
        if result.success:
            category_stats[category]["success"] += 1

    return {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "success_rate": successful_tests / total_tests,
        "avg_latency_ms": avg_latency,
        "avg_tool_calls": avg_tool_calls,
        "category_stats": category_stats,
        "individual_results": [
            {
                "name": r.test_case.name,
                "success": r.success,
                "latency_ms": r.performance_metrics.total_latency_ms,
                "errors": r.validation_result.errors
            }
            for r in eval_results
        ]
    }