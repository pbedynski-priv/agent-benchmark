"""Typer-based CLI for Code Benchmark."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import Config
from .task_loader import TaskLoader

app = typer.Typer(
    name="code-benchmark",
    help="Model Code Quality Benchmark Tool - Compare AI code generation models",
    add_completion=False,
)
tasks_app = typer.Typer(help="Manage benchmark tasks")
app.add_typer(tasks_app, name="tasks")

console = Console()


def get_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration."""
    return Config.load(config_path)


@app.command()
def run(
    models: str = typer.Option(
        ...,
        "--models",
        "-m",
        help="Comma-separated list of models to benchmark",
    ),
    tasks_filter: Optional[str] = typer.Option(
        None,
        "--tasks",
        "-t",
        help="Filter tasks by category (e.g., algorithms, debugging)",
    ),
    task_ids: Optional[str] = typer.Option(
        None,
        "--task-ids",
        help="Comma-separated list of specific task IDs",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for results",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Run a benchmark with specified models and tasks.

    Examples:
        code-benchmark run --models qwen3.7-plus,deepseek-v4-flash --tasks algorithms
        code-benchmark run --models kimi-k2.6 --task-ids lru-cache,binary-search
    """
    from .runner import BenchmarkRunner

    config = get_config(config_path)
    model_list = [m.strip() for m in models.split(",")]

    if output_dir:
        config = Config(
            api=config.api,
            models=config.models,
            execution=config.execution,
            scoring=config.scoring,
            project_root=output_dir.parent,
        )

    console.print("[bold blue]Starting benchmark run[/bold blue]")
    console.print(f"  Models: {', '.join(model_list)}")
    if tasks_filter:
        console.print(f"  Tasks: {tasks_filter}")
    if task_ids:
        console.print(f"  Task IDs: {task_ids}")

    runner = BenchmarkRunner(config)

    try:
        asyncio.run(runner.run(model_list, tasks_filter, task_ids))
        console.print("[bold green]Benchmark complete![/bold green]")
    except KeyboardInterrupt:
        console.print("[bold yellow]Benchmark interrupted[/bold yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def report(
    run_id: str = typer.Argument(..., help="Run ID to generate report for"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, markdown",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Generate a report from a previous benchmark run.

    Examples:
        code-benchmark report run-20240101-120000
        code-benchmark report run-20240101-120000 --format json
    """
    from .reporter import Reporter

    config = get_config(config_path)
    reporter = Reporter(config)

    try:
        reporter.generate_report(run_id, format)
    except FileNotFoundError:
        console.print(f"[bold red]Run '{run_id}' not found[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def compare(
    run_ids: str = typer.Argument(..., help="Comma-separated run IDs to compare"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, markdown",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Compare results across multiple benchmark runs.

    Examples:
        code-benchmark compare run-20240101-120000,run-20240102-120000
    """
    from .reporter import Reporter

    config = get_config(config_path)
    reporter = Reporter(config)
    ids = [r.strip() for r in run_ids.split(",")]

    try:
        reporter.compare_runs(ids, format)
    except FileNotFoundError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@tasks_app.command("list")
def tasks_list(
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category",
    ),
    difficulty: Optional[str] = typer.Option(
        None,
        "--difficulty",
        "-d",
        help="Filter by difficulty (easy, medium, hard)",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file",
    ),
) -> None:
    """List all available benchmark tasks.

    Examples:
        code-benchmark tasks list
        code-benchmark tasks list --category algorithms
        code-benchmark tasks list --difficulty hard
    """
    config = get_config(config_path)
    loader = TaskLoader(config.tasks_dir)
    tasks = loader.load_all()

    # Apply filters
    if category:
        tasks = [t for t in tasks if t.category == category]
    if difficulty:
        tasks = [t for t in tasks if t.difficulty == difficulty]

    if not tasks:
        console.print("[yellow]No tasks found matching the filters[/yellow]")
        raise typer.Exit(0)

    # Display as table
    table = Table(title="Available Benchmark Tasks")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="green")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Description", style="white")

    for task in sorted(tasks, key=lambda t: (t.category, t.id)):
        desc = task.description[:60] + "..." if len(task.description) > 60 else task.description
        table.add_row(task.id, task.category, task.difficulty, desc)

    console.print(table)
    console.print(f"\n[dim]Total: {len(tasks)} tasks[/dim]")


@app.command()
def config_show(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Show current configuration."""
    config = get_config(config_path)

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("API Base URL", config.api.base_url)
    table.add_row("API Key Set", "Yes" if config.api.api_key else "No")
    table.add_row("Timeout", f"{config.api.timeout}s")
    table.add_row("Max Retries", str(config.api.max_retries))
    table.add_row("Candidate Models", ", ".join(config.models.candidates))
    table.add_row("Reviewer Model", config.models.reviewer)
    table.add_row("Docker Image", config.execution.docker_image)
    table.add_row("Execution Timeout", f"{config.execution.timeout}s")
    table.add_row("Memory Limit", config.execution.memory_limit)

    console.print(table)

    # Scoring weights
    weights_table = Table(title="Scoring Weights")
    weights_table.add_column("Dimension", style="cyan")
    weights_table.add_column("Weight", style="green")

    for dim, weight in config.scoring.weights.items():
        weights_table.add_row(dim, f"{weight:.0%}")

    console.print(weights_table)


if __name__ == "__main__":
    app()
