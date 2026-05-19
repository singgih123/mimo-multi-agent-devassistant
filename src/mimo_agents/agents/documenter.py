"""Documenter agent: generates documentation with multimodal understanding."""

from __future__ import annotations

import time
from typing import Any

from mimo_agents.agents.base import BaseAgent
from mimo_agents.core.models import AgentRole, DevTask, TaskResult, TaskStatus


class DocumenterAgent(BaseAgent):
    """Generates comprehensive documentation using MiMo multimodal model."""

    role = AgentRole.DOCUMENTER
    system_prompt = (
        "You are a technical documentation expert. Generate clear, comprehensive "
        "documentation for the given code. Include:\n\n"
        "1. **Overview**: High-level purpose and architecture\n"
        "2. **API Reference**: Function signatures, parameters, return types\n"
        "3. **Usage Examples**: Practical code examples for common use cases\n"
        "4. **Architecture Diagram**: ASCII art or Mermaid diagram\n"
        "5. **Configuration**: Environment variables, settings\n"
        "6. **Troubleshooting**: Common issues and solutions\n\n"
        "Format the output as Markdown suitable for a README or docs site."
    )

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        start = time.monotonic()
        ctx = context or {}

        prompt_parts = [
            f"## Documentation Request: {task.title}",
            f"### Description:\n{task.description}",
        ]

        generated_code = ctx.get("generated_code", task.source_code)
        if generated_code:
            prompt_parts.append(
                f"### Code to Document:\n```{task.language}\n{generated_code}\n```"
            )

        plan = ctx.get("plan", "")
        if plan:
            prompt_parts.append(f"### Architecture Plan:\n{plan}")

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nGenerate comprehensive documentation in Markdown format. "
            "Include a Mermaid architecture diagram and practical examples."
        )

        try:
            output, usage = self._call_model(
                prompt, model_config=self.client.settings.multimodal_model
            )
            elapsed = int((time.monotonic() - start) * 1000)
            return self._make_result(
                task,
                output=output,
                status=TaskStatus.COMPLETED,
                artifacts={"documentation": output},
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

    def document_image(self, image_url: str, description: str = "") -> str:
        """Analyze an image (screenshot, diagram) and generate documentation."""
        prompt = (
            "Analyze this image and generate documentation for it. "
            "If it's a UI screenshot, describe the layout and components. "
            "If it's an architecture diagram, explain the system design."
        )
        if description:
            prompt += f"\n\nAdditional context: {description}"

        content, _ = self.client.chat_with_vision(prompt, image_url=image_url)
        return content
