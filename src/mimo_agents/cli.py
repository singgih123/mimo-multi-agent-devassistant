"""CLI interface for MiMo Multi-Agent DevAssistant."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mimo_agents.core.client import MiMoClient
from mimo_agents.core.config import Settings
from mimo_agents.core.models import DevTask

console = Console()


def _get_client() -> MiMoClient:
    settings = Settings.from_env()
    errors = settings.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Error:[/] {err}")
        console.print("\n[yellow]Set MIMO_API_KEY to your MiMo API key.[/]")
        sys.exit(1)
    return MiMoClient(settings)


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """MiMo Multi-Agent DevAssistant - AI-powered development pipeline."""
    pass


@main.command()
@click.argument("description")
@click.option("--title", "-t", default="Dev Task", help="Task title")
@click.option("--language", "-l", default="python", help="Programming language")
@click.option("--code-file", "-f", type=click.Path(exists=True), help="Source code file to analyze")
def run(description: str, title: str, language: str, code_file: str | None) -> None:
    """Run the full multi-agent development pipeline."""
    from mimo_agents.agents.orchestrator import OrchestratorAgent

    client = _get_client()

    source_code = ""
    if code_file:
        with open(code_file) as f:
            source_code = f.read()

    task = DevTask(
        title=title,
        description=description,
        language=language,
        source_code=source_code,
    )

    console.print(Panel("[bold]MiMo Multi-Agent DevAssistant[/]", style="cyan"))
    console.print(f"Task: {task.title}")
    console.print(f"Language: {task.language}\n")

    orchestrator = OrchestratorAgent(client)
    result = orchestrator.process(task)

    console.print("\n" + "=" * 60)
    console.print(result.output)

    usage = client.get_total_usage()
    _print_usage(usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)


@main.command()
@click.argument("code_file", type=click.Path(exists=True))
@click.option("--language", "-l", default="python", help="Programming language")
def review(code_file: str, language: str) -> None:
    """Review a code file using the Reviewer agent."""
    from mimo_agents.agents.reviewer import ReviewerAgent

    client = _get_client()

    with open(code_file) as f:
        source_code = f.read()

    task = DevTask(
        title=f"Code Review: {code_file}",
        description=f"Review the following {language} code for quality and best practices.",
        language=language,
        source_code=source_code,
    )

    console.print(Panel(f"[bold]Reviewing:[/] {code_file}", style="cyan"))

    reviewer = ReviewerAgent(client)
    result = reviewer.process(task, context={"generated_code": source_code})

    console.print(result.output)

    recommendation = result.artifacts.get("recommendation", "N/A")
    color = "green" if recommendation == "APPROVE" else "yellow"
    console.print(f"\n[{color}]Recommendation: {recommendation}[/]")


@main.command()
@click.argument("code_file", type=click.Path(exists=True))
@click.option("--language", "-l", default="python", help="Programming language")
def test(code_file: str, language: str) -> None:
    """Generate tests for a code file."""
    from mimo_agents.agents.tester import TesterAgent

    client = _get_client()

    with open(code_file) as f:
        source_code = f.read()

    task = DevTask(
        title=f"Test Generation: {code_file}",
        description=f"Generate comprehensive tests for the following {language} code.",
        language=language,
        source_code=source_code,
    )

    console.print(Panel(f"[bold]Generating tests for:[/] {code_file}", style="cyan"))

    tester = TesterAgent(client)
    result = tester.process(task, context={"generated_code": source_code})

    console.print(result.output)


@main.command()
@click.argument("description")
@click.option("--language", "-l", default="python", help="Programming language")
def plan(description: str, language: str) -> None:
    """Create an implementation plan for a task."""
    from mimo_agents.agents.planner import PlannerAgent

    client = _get_client()

    task = DevTask(
        title="Implementation Planning",
        description=description,
        language=language,
    )

    console.print(Panel("[bold]Creating Implementation Plan[/]", style="cyan"))

    planner = PlannerAgent(client)
    result = planner.process(task)

    console.print(result.output)


@main.command()
def status() -> None:
    """Show configuration status."""
    settings = Settings.from_env()
    errors = settings.validate()

    table = Table(title="MiMo DevAssistant Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    api_key_display = settings.api_key[:8] + "..." if settings.api_key else "[red]NOT SET[/]"
    table.add_row("API Key", api_key_display)
    table.add_row("Base URL", settings.base_url)
    table.add_row("Reasoning Model", settings.reasoning_model.model_id)
    table.add_row("Multimodal Model", settings.multimodal_model.model_id)
    table.add_row("TTS Model", settings.tts_model.model_id)
    table.add_row("Max Iterations", str(settings.max_agent_iterations))
    table.add_row("Voice Enabled", str(settings.enable_voice))

    console.print(table)

    if errors:
        console.print("\n[yellow]Issues:[/]")
        for err in errors:
            console.print(f"  [red]•[/] {err}")
    else:
        console.print("\n[green]Configuration OK[/]")


def _print_usage(prompt: int, completion: int, total: int) -> None:
    table = Table(title="Token Usage Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Tokens", style="green", justify="right")
    table.add_row("Prompt", f"{prompt:,}")
    table.add_row("Completion", f"{completion:,}")
    table.add_row("Total", f"{total:,}")
    console.print(table)


if __name__ == "__main__":
    main()
