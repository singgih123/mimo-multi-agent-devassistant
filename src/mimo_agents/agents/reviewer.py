"""Reviewer agent: performs code review with multi-dimensional analysis."""

from __future__ import annotations

import time
from typing import Any

from mimo_agents.agents.base import BaseAgent
from mimo_agents.core.models import AgentRole, DevTask, TaskResult, TaskStatus


class ReviewerAgent(BaseAgent):
    """Reviews code for quality, security, and best practices."""

    role = AgentRole.REVIEWER
    system_prompt = (
        "You are a senior code reviewer with expertise in security, performance, "
        "and software architecture. Perform a thorough multi-dimensional review:\n\n"
        "1. **Correctness**: Logic errors, edge cases, off-by-one errors\n"
        "2. **Security**: Injection vulnerabilities, auth issues, data exposure\n"
        "3. **Performance**: Algorithmic complexity, memory usage, I/O patterns\n"
        "4. **Maintainability**: Code clarity, naming, modularity, DRY violations\n"
        "5. **Testing**: Test coverage gaps, untested edge cases\n"
        "6. **Architecture**: Design pattern usage, separation of concerns\n\n"
        "For each finding, provide:\n"
        "- Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO\n"
        "- Location: file and line reference\n"
        "- Issue description\n"
        "- Suggested fix\n\n"
        "End with an overall score (0-100) and summary recommendation: "
        "APPROVE, REQUEST_CHANGES, or NEEDS_DISCUSSION."
    )

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        start = time.monotonic()
        ctx = context or {}

        prompt_parts = [
            f"## Code Review Request: {task.title}",
            f"### Description:\n{task.description}",
        ]

        generated_code = ctx.get("generated_code", task.source_code)
        if generated_code:
            prompt_parts.append(
                f"### Code to Review:\n```{task.language}\n{generated_code}\n```"
            )

        plan = ctx.get("plan", "")
        if plan:
            prompt_parts.append(f"### Original Plan (for context):\n{plan}")

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nPerform a comprehensive code review. "
            "Be thorough but constructive. Highlight both strengths and areas for improvement."
        )

        try:
            output, usage = self._call_model(prompt)
            elapsed = int((time.monotonic() - start) * 1000)

            recommendation = "APPROVE"
            if "REQUEST_CHANGES" in output.upper():
                recommendation = "REQUEST_CHANGES"
            elif "NEEDS_DISCUSSION" in output.upper():
                recommendation = "NEEDS_DISCUSSION"

            return self._make_result(
                task,
                output=output,
                status=TaskStatus.COMPLETED,
                artifacts={
                    "review": output,
                    "recommendation": recommendation,
                },
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
