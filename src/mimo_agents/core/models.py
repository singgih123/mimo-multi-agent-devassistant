"""Data models for the MiMo multi-agent system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentRole(str, Enum):
    """Roles for specialized agents in the system."""

    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    NARRATOR = "narrator"


class TaskStatus(str, Enum):
    """Status of a task in the pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """A message exchanged between agents."""

    sender: AgentRole
    recipient: AgentRole
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TokenUsage:
    """Track token consumption per request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


@dataclass
class TaskResult:
    """Result produced by an agent for a given task."""

    task_id: str
    agent: AgentRole
    status: TaskStatus
    output: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    error: str | None = None
    duration_ms: int = 0


@dataclass
class DevTask:
    """A development task to be processed by the multi-agent pipeline."""

    task_id: str = field(default_factory=lambda: uuid4().hex[:12])
    title: str = ""
    description: str = ""
    source_code: str = ""
    language: str = "python"
    status: TaskStatus = TaskStatus.PENDING
    results: list[TaskResult] = field(default_factory=list)
    messages: list[AgentMessage] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_tokens: int = 0
