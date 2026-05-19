"""Orchestrator agent: coordinates the multi-agent pipeline."""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from mimo_agents.agents.base import BaseAgent
from mimo_agents.agents.coder import CoderAgent
from mimo_agents.agents.documenter import DocumenterAgent
from mimo_agents.agents.planner import PlannerAgent
from mimo_agents.agents.reviewer import ReviewerAgent
from mimo_agents.agents.tester import TesterAgent
from mimo_agents.core.client import MiMoClient
from mimo_agents.core.models import (
    AgentMessage,
    AgentRole,
    DevTask,
    TaskResult,
    TaskStatus,
)

console = Console()


class OrchestratorAgent(BaseAgent):
    """Coordinates the full development pipeline across specialized agents."""

    role = AgentRole.ORCHESTRATOR

    def __init__(self, client: MiMoClient) -> None:
        super().__init__(client)
        self.planner = PlannerAgent(client)
        self.coder = CoderAgent(client)
        self.reviewer = ReviewerAgent(client)
        self.tester = TesterAgent(client)
        self.documenter = DocumenterAgent(client)
        self._pipeline_messages: list[AgentMessage] = []

    def process(self, task: DevTask, context: dict[str, Any] | None = None) -> TaskResult:
        """Run the full multi-agent development pipeline."""
        start = time.monotonic()
        task.status = TaskStatus.IN_PROGRESS

        console.print(Panel(f"[bold cyan]Starting Pipeline[/]\n{task.title}", expand=False))

        pipeline_context: dict[str, Any] = {}

        # Phase 1: Planning
        plan_result = self._run_phase("Planning", self.planner, task, pipeline_context)
        if plan_result.status == TaskStatus.FAILED:
            return self._finalize(task, plan_result, start)
        pipeline_context["plan"] = plan_result.artifacts.get("plan", plan_result.output)

        # Phase 2: Code Generation
        code_result = self._run_phase("Code Generation", self.coder, task, pipeline_context)
        if code_result.status == TaskStatus.FAILED:
            return self._finalize(task, code_result, start)
        pipeline_context["generated_code"] = code_result.artifacts.get(
            "generated_code", code_result.output
        )

        # Phase 3: Code Review
        review_result = self._run_phase("Code Review", self.reviewer, task, pipeline_context)
        if review_result.status == TaskStatus.FAILED:
            return self._finalize(task, review_result, start)
        recommendation = review_result.artifacts.get("recommendation", "APPROVE")

        # Phase 3b: Iterative refinement if review requests changes
        iteration = 0
        max_iterations = self.client.settings.max_agent_iterations
        while recommendation == "REQUEST_CHANGES" and iteration < max_iterations:
            iteration += 1
            console.print(f"  [yellow]Iteration {iteration}: Addressing review feedback[/]")

            pipeline_context["review_feedback"] = review_result.output
            code_result = self._run_phase(
                f"Refinement #{iteration}", self.coder, task, pipeline_context
            )
            if code_result.status == TaskStatus.FAILED:
                break
            pipeline_context["generated_code"] = code_result.artifacts.get(
                "generated_code", code_result.output
            )

            review_result = self._run_phase(
                f"Re-Review #{iteration}", self.reviewer, task, pipeline_context
            )
            recommendation = review_result.artifacts.get("recommendation", "APPROVE")

        # Phase 4: Test Generation
        test_result = self._run_phase("Test Generation", self.tester, task, pipeline_context)

        # Phase 5: Documentation
        doc_result = self._run_phase("Documentation", self.documenter, task, pipeline_context)

        # Aggregate results
        elapsed = int((time.monotonic() - start) * 1000)
        final_output = self._build_summary(
            plan_result, code_result, review_result, test_result, doc_result
        )

        task.status = TaskStatus.COMPLETED
        task.results = [plan_result, code_result, review_result, test_result, doc_result]
        task.messages = list(self._pipeline_messages)

        total_usage = self.client.get_total_usage()
        task.total_tokens = total_usage.total_tokens

        console.print(
            Panel(
                f"[bold green]Pipeline Complete[/]\n"
                f"Total tokens: {total_usage.total_tokens:,}\n"
                f"Duration: {elapsed / 1000:.1f}s",
                expand=False,
            )
        )

        return self._make_result(
            task,
            output=final_output,
            status=TaskStatus.COMPLETED,
            artifacts={
                "plan": plan_result.artifacts.get("plan", ""),
                "generated_code": pipeline_context.get("generated_code", ""),
                "review": review_result.artifacts.get("review", ""),
                "test_suite": test_result.artifacts.get("test_suite", ""),
                "documentation": doc_result.artifacts.get("documentation", ""),
                "recommendation": recommendation,
                "iterations": str(iteration),
            },
            duration_ms=elapsed,
        )

    def _run_phase(
        self,
        phase_name: str,
        agent: BaseAgent,
        task: DevTask,
        context: dict[str, Any],
    ) -> TaskResult:
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[cyan]{phase_name}[/] ({agent.role.value})..."),
            console=console,
        ) as progress:
            progress.add_task("", total=None)
            result = agent.process(task, context)

        status_icon = "[green]OK[/]" if result.status == TaskStatus.COMPLETED else "[red]FAIL[/]"
        console.print(f"  {status_icon} {phase_name} — {result.duration_ms}ms")

        msg = AgentMessage(
            sender=agent.role,
            recipient=self.role,
            content=f"{phase_name}: {result.status.value}",
            metadata={"duration_ms": result.duration_ms},
        )
        self._pipeline_messages.append(msg)

        return result

    @staticmethod
    def _build_summary(*results: TaskResult) -> str:
        parts = ["# Multi-Agent Pipeline Summary\n"]
        for r in results:
            icon = "passed" if r.status == TaskStatus.COMPLETED else "failed"
            parts.append(f"## {r.agent.value.title()} — {icon}")
            parts.append(f"Duration: {r.duration_ms}ms\n")
            if r.output:
                preview = r.output[:500] + ("..." if len(r.output) > 500 else "")
                parts.append(preview)
            parts.append("")
        return "\n".join(parts)

    def _finalize(self, task: DevTask, failed_result: TaskResult, start: float) -> TaskResult:
        elapsed = int((time.monotonic() - start) * 1000)
        task.status = TaskStatus.FAILED
        console.print(
            f"[red]Pipeline failed at {failed_result.agent.value}: {failed_result.error}[/]"
        )
        return self._make_result(
            task,
            output=failed_result.output,
            status=TaskStatus.FAILED,
            error=f"Pipeline failed at {failed_result.agent.value}: {failed_result.error}",
            duration_ms=elapsed,
        )
