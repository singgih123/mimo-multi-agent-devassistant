"""Base agent class with common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mimo_agents.core.client import MiMoClient
from mimo_agents.core.config import ModelConfig
from mimo_agents.core.models import (
    AgentMessage,
    AgentRole,
    DevTask,
    TaskResult,
    TaskStatus,
)


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    role: AgentRole
    system_prompt: str = ""

    def __init__(self, client: MiMoClient) -> None:
        self.client = client
        self._conversation_history: list[dict[str, Any]] = []

    @abstractmethod
    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        """Process a development task and return a result."""

    def _build_messages(
        self, user_prompt: str, include_history: bool = True
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if include_history:
            messages.extend(self._conversation_history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _call_model(
        self,
        prompt: str,
        model_config: ModelConfig | None = None,
        include_history: bool = True,
    ) -> tuple[str, dict[str, int]]:
        messages = self._build_messages(prompt, include_history)
        content, usage = self.client.chat(messages, model_config)

        self._conversation_history.append({"role": "user", "content": prompt})
        self._conversation_history.append({"role": "assistant", "content": content})

        return content, {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    def _make_result(
        self,
        task: DevTask,
        output: str,
        status: TaskStatus = TaskStatus.COMPLETED,
        artifacts: dict[str, str] | None = None,
        error: str | None = None,
        duration_ms: int = 0,
    ) -> TaskResult:
        usage = self.client.get_total_usage()
        return TaskResult(
            task_id=task.task_id,
            agent=self.role,
            status=status,
            output=output,
            artifacts=artifacts or {},
            token_usage=usage,
            error=error,
            duration_ms=duration_ms,
        )

    def send_message(self, recipient: AgentRole, content: str, **meta: Any) -> AgentMessage:
        return AgentMessage(
            sender=self.role,
            recipient=recipient,
            content=content,
            metadata=meta,
        )

    def reset(self) -> None:
        self._conversation_history.clear()
