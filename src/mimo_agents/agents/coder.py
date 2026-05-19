"""Coder agent: generates and modifies code based on plans and specifications."""

from __future__ import annotations

import time
from typing import Any

from mimo_agents.agents.base import BaseAgent
from mimo_agents.core.models import AgentRole, DevTask, TaskResult, TaskStatus


class CoderAgent(BaseAgent):
    """Generates high-quality code based on implementation plans."""

    role = AgentRole.CODER
    system_prompt = (
        "You are an expert software developer. Given a task and an implementation plan, "
        "you write clean, production-ready code. Follow these principles:\n"
        "1. Write idiomatic code for the target language\n"
        "2. Include proper error handling and edge cases\n"
        "3. Add type hints and minimal inline documentation\n"
        "4. Follow SOLID principles and clean architecture\n"
        "5. Make code testable with clear interfaces\n"
        "6. Use established patterns and best practices\n\n"
        "Output complete, runnable code. Wrap each file in a code block "
        "with the filename as a comment on the first line."
    )

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        start = time.monotonic()
        ctx = context or {}

        prompt_parts = [
            f"## Task: {task.title}",
            f"### Description:\n{task.description}",
            f"### Language: {task.language}",
        ]

        plan = ctx.get("plan", "")
        if plan:
            prompt_parts.append(f"### Implementation Plan:\n{plan}")

        if task.source_code:
            prompt_parts.append(
                f"### Existing Code to Modify:\n```{task.language}\n{task.source_code}\n```"
            )

        review_feedback = ctx.get("review_feedback", "")
        if review_feedback:
            prompt_parts.append(f"### Review Feedback to Address:\n{review_feedback}")

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nGenerate the complete implementation. "
            "Each file should be in its own code block with the path as the first comment. "
            "Ensure the code is production-ready with proper error handling."
        )

        try:
            output, usage = self._call_model(prompt)
            elapsed = int((time.monotonic() - start) * 1000)

            artifacts = {"generated_code": output}
            code_blocks = self._extract_code_blocks(output)
            for filename, code in code_blocks.items():
                artifacts[f"file:{filename}"] = code

            return self._make_result(
                task,
                output=output,
                status=TaskStatus.COMPLETED,
                artifacts=artifacts,
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

    @staticmethod
    def _extract_code_blocks(text: str) -> dict[str, str]:
        """Extract named code blocks from the model output."""
        blocks: dict[str, str] = {}
        lines = text.split("\n")
        current_file = ""
        current_code: list[str] = []
        in_block = False

        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                current_code = []
            elif line.startswith("```") and in_block:
                in_block = False
                if current_code:
                    first_line = current_code[0].strip()
                    if first_line.startswith("# ") or first_line.startswith("// "):
                        current_file = first_line.lstrip("# /").strip()
                        current_code = current_code[1:]
                    if current_file:
                        blocks[current_file] = "\n".join(current_code)
                    current_file = ""
            elif in_block:
                current_code.append(line)

        return blocks
