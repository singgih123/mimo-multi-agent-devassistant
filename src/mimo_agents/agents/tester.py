"""Tester agent: generates test cases and validates code correctness."""

from __future__ import annotations

import time
from typing import Any

from mimo_agents.agents.base import BaseAgent
from mimo_agents.core.models import AgentRole, DevTask, TaskResult, TaskStatus


class TesterAgent(BaseAgent):
    """Generates comprehensive test suites for the produced code."""

    role = AgentRole.TESTER
    system_prompt = (
        "You are an expert QA engineer and test developer. "
        "Given code and its specification, generate comprehensive tests:\n\n"
        "1. **Unit tests**: Test individual functions and methods\n"
        "2. **Edge cases**: Boundary conditions, empty inputs, large inputs\n"
        "3. **Error handling**: Invalid inputs, exceptions, failure modes\n"
        "4. **Integration tests**: Component interaction and data flow\n\n"
        "Use pytest as the testing framework. Include:\n"
        "- Descriptive test names explaining what is being tested\n"
        "- Proper setup/teardown with fixtures\n"
        "- Parametrized tests for related test cases\n"
        "- Mocks for external dependencies\n"
        "- Assertion messages for clarity\n\n"
        "Aim for >90% code coverage of the submitted code."
    )

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        start = time.monotonic()
        ctx = context or {}

        prompt_parts = [
            f"## Test Generation: {task.title}",
            f"### Description:\n{task.description}",
        ]

        generated_code = ctx.get("generated_code", task.source_code)
        if generated_code:
            prompt_parts.append(
                f"### Code to Test:\n```{task.language}\n{generated_code}\n```"
            )

        plan = ctx.get("plan", "")
        if plan:
            prompt_parts.append(f"### Implementation Plan:\n{plan}")

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nGenerate a comprehensive test suite. "
            "Cover all public interfaces, edge cases, and error paths. "
            "Use pytest with descriptive test names."
        )

        try:
            output, usage = self._call_model(prompt)
            elapsed = int((time.monotonic() - start) * 1000)
            return self._make_result(
                task,
                output=output,
                status=TaskStatus.COMPLETED,
                artifacts={"test_suite": output},
                duration_ms=elapsed,
            )
        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            return self._make_result(
                task,
                output="",
                status=TaskStatus.FAILED,
                error=str(exc),
                duration_ms=elapsed,
            )
