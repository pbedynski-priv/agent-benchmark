"""Benchmark runner - orchestrates the benchmark execution."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .api_client import APIClient, APIClientError
from .config import Config
from .reviewer import Reviewer
from .scorer import Scorer
from .task_loader import Task, TaskLoader

console = Console()


class BenchmarkResult:
    """Result of a single model-task execution."""

    def __init__(
        self,
        model: str,
        task_id: str,
        response: str,
        scores: dict[str, float] | None = None,
        error: str | None = None,
        duration_ms: int = 0,
    ):
        self.model = model
        self.task_id = task_id
        self.response = response
        self.scores = scores or {}
        self.error = error
        self.duration_ms = duration_ms

    @property
    def total_score(self) -> float:
        """Calculate total weighted score."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "model": self.model,
            "task_id": self.task_id,
            "response": self.response,
            "scores": self.scores,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "total_score": self.total_score,
        }


class BenchmarkRun:
    """A complete benchmark run with multiple models and tasks."""

    def __init__(self, run_id: str, models: list[str], config: Config):
        self.run_id = run_id
        self.models = models
        self.config = config
        self.results: list[BenchmarkResult] = []
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a result to the run."""
        self.results.append(result)

    def get_results_by_model(self, model: str) -> list[BenchmarkResult]:
        """Get all results for a specific model."""
        return [r for r in self.results if r.model == model]

    def get_results_by_task(self, task_id: str) -> list[BenchmarkResult]:
        """Get all results for a specific task."""
        return [r for r in self.results if r.task_id == task_id]

    def to_dict(self) -> dict[str, Any]:
        """Serialize run to dictionary."""
        return {
            "run_id": self.run_id,
            "models": self.models,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": [r.to_dict() for r in self.results],
        }

    def save(self, output_dir: Path) -> Path:
        """Save run results to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{self.run_id}.json"
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return filepath


class BenchmarkRunner:
    """Orchestrates benchmark execution."""

    SYSTEM_PROMPT = """You are an expert programmer. You will be given a coding task.
Write clean, efficient, well-documented code in Python.
Include proper error handling and follow best practices.
Return ONLY the code, no explanations outside of code comments."""

    def __init__(self, config: Config):
        self.config = config
        self.task_loader = TaskLoader(config.tasks_dir)
        self.scorer = Scorer(config.scoring.weights)

    async def run(
        self,
        models: list[str],
        category_filter: str | None = None,
        task_ids_str: str | None = None,
    ) -> BenchmarkRun:
        """Execute a benchmark run.

        Args:
            models: List of model names to benchmark.
            category_filter: Optional category to filter tasks.
            task_ids_str: Optional comma-separated task IDs.

        Returns:
            Completed BenchmarkRun with all results.
        """
        # Generate run ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_id = f"run-{timestamp}-{uuid.uuid4().hex[:6]}"
        run = BenchmarkRun(run_id, models, self.config)
        run.started_at = datetime.now(timezone.utc)

        # Load tasks
        if task_ids_str:
            task_ids = [t.strip() for t in task_ids_str.split(",")]
            tasks = self.task_loader.load_by_ids(task_ids)
        elif category_filter:
            tasks = self.task_loader.load_by_category(category_filter)
        else:
            tasks = self.task_loader.load_all()

        if not tasks:
            console.print("[yellow]No tasks to run[/yellow]")
            return run

        console.print(f"Running {len(tasks)} tasks across {len(models)} models...")

        # Execute benchmark
        async with APIClient(self.config) as client:
            reviewer = Reviewer(self.config, client)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                total = len(models) * len(tasks)
                task_progress = progress.add_task("Benchmarking...", total=total)

                # Run models concurrently
                model_tasks = []
                for model in models:
                    for task in tasks:
                        model_tasks.append(
                            self._execute_task(client, reviewer, model, task)
                        )
                
                # Execute all tasks concurrently with progress tracking
                results = []
                for coro in asyncio.as_completed(model_tasks):
                    result = await coro
                    results.append(result)
                    run.add_result(result)
                    progress.advance(task_progress)

        run.completed_at = datetime.now(timezone.utc)

        # Save results
        output_path = run.save(self.config.results_dir)
        console.print(f"\n[green]Results saved to {output_path}[/green]")

        return run

    async def _execute_task(
        self,
        client: APIClient,
        reviewer: Reviewer,
        model: str,
        task: Task,
    ) -> BenchmarkResult:
        """Execute a single task with a model and review the result.

        Args:
            client: API client.
            reviewer: Code reviewer.
            model: Model name.
            task: Task to execute.

        Returns:
            BenchmarkResult with scores.
        """
        import time

        start_time = time.monotonic()

        try:
            # Get model response
            response = await client.call_model(
                model=model,
                prompt=task.prompt,
                system=self.SYSTEM_PROMPT,
            )

            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Review the code
            review = await reviewer.review_code(
                code=response,
                task=task,
                model=model,
            )

            # Calculate scores
            scores = self.scorer.calculate_scores(review)

            return BenchmarkResult(
                model=model,
                task_id=task.id,
                response=response,
                scores=scores,
                duration_ms=duration_ms,
            )

        except APIClientError as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return BenchmarkResult(
                model=model,
                task_id=task.id,
                response="",
                error=str(e),
                duration_ms=duration_ms,
            )
