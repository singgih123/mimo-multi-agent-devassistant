"""Planner agent: decomposes high-level tasks into actionable sub-tasks."""

from __future__ import annotations

import time
from typing import Any

from mimo_agents.agents.base import BaseAgent
from mimo_agents.core.models import AgentRole, DevTask, TaskResult, TaskStatus


class PlannerAgent(BaseAgent):
    """Analyzes requirements and creates structured implementation plans."""

    role = AgentRole.PLANNER
    system_prompt = (
        "You are an expert software architect and project planner. "
        "Given a development task, you produce a structured, step-by-step "
        "implementation plan. Each step should be specific, actionable, and "
        "ordered by dependency. Include:\n"
        "1. Task decomposition into sub-tasks\n"
        "2. Technology choices and rationale\n"
        "3. File structure recommendations\n"
        "4. Potential risks and mitigations\n"
        "5. Estimated complexity per sub-task (low/medium/high)\n\n"
        "Output your plan in a clear, structured format with numbered steps."
    )

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        start = time.monotonic()

        prompt_parts = [
            f"## Task: {task.title}",
            f"### Description:\n{task.description}",
            f"### Language: {task.language}",
        ]

        if task.source_code:
            prompt_parts.append(f"### Existing Code:\n```{task.language}\n{task.source_code}\n```")

        if context:
            prompt_parts.append(f"### Additional Context:\n{context}")

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nCreate a detailed implementation plan. "
            "Structure your response with clear numbered steps, "
            "each with a description, expected output, and complexity rating."
        )

        try:
            output, usage = self._call_model(prompt)
            elapsed = int((time.monotonic() - start) * 1000)
            return self._make_result(
                task,
                output=output,
                status=TaskStatus.COMPLETED,
                artifacts={"plan": output},
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
