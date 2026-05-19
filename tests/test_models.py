"""Tests for data models."""

from mimo_agents.core.models import (
    AgentMessage,
    AgentRole,
    DevTask,
    TaskResult,
    TaskStatus,
    TokenUsage,
)


def test_agent_role_values():
    assert AgentRole.ORCHESTRATOR == "orchestrator"
    assert AgentRole.PLANNER == "planner"
    assert AgentRole.CODER == "coder"
    assert AgentRole.REVIEWER == "reviewer"
    assert AgentRole.TESTER == "tester"
    assert AgentRole.DOCUMENTER == "documenter"


def test_task_status_values():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


def test_agent_message_creation():
    msg = AgentMessage(
        sender=AgentRole.PLANNER,
        recipient=AgentRole.CODER,
        content="Here is the plan",
    )
    assert msg.sender == AgentRole.PLANNER
    assert msg.recipient == AgentRole.CODER
    assert msg.content == "Here is the plan"
    assert msg.message_id
    assert msg.timestamp


def test_token_usage_defaults():
    usage = TokenUsage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0
    assert usage.model == ""


def test_dev_task_creation():
    task = DevTask(
        title="Build API",
        description="Create a REST API",
        language="python",
    )
    assert task.title == "Build API"
    assert task.status == TaskStatus.PENDING
    assert task.results == []
    assert task.messages == []
    assert task.task_id


def test_task_result_creation():
    result = TaskResult(
        task_id="abc123",
        agent=AgentRole.REVIEWER,
        status=TaskStatus.COMPLETED,
        output="Code looks good",
    )
    assert result.task_id == "abc123"
    assert result.agent == AgentRole.REVIEWER
    assert result.status == TaskStatus.COMPLETED
    assert result.error is None
