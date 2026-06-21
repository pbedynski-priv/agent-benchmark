"""Report generation for benchmark results.

Supports multiple output formats: Rich tables, JSON, and Markdown.
"""

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from .config import Config
from .scorer import Scorer

console = Console()


class Reporter:
    """Generates reports from benchmark results."""

    def __init__(self, config: Config):
        """Initialize the reporter.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.scorer = Scorer(config.scoring.weights)

    def _load_run(self, run_id: str) -> dict[str, Any]:
        """Load a benchmark run from disk.

        Args:
            run_id: The run identifier.

        Returns:
            Run data dictionary.

        Raises:
            FileNotFoundError: If run not found.
        """
        filepath = self.config.results_dir / f"{run_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Run '{run_id}' not found at {filepath}")

        with open(filepath, "r") as f:
            return json.load(f)

    def generate_report(self, run_id: str, format: str = "table") -> None:
        """Generate a report for a benchmark run.

        Args:
            run_id: The run identifier.
            format: Output format ('table', 'json', 'markdown').
        """
        run_data = self._load_run(run_id)

        if format == "table":
            self._render_table_report(run_data)
        elif format == "json":
            self._render_json_report(run_data)
        elif format == "markdown":
            self._render_markdown_report(run_data)
        else:
            raise ValueError(f"Unknown format: {format}")

    def compare_runs(self, run_ids: list[str], format: str = "table") -> None:
        """Compare multiple benchmark runs.

        Args:
            run_ids: List of run identifiers to compare.
            format: Output format.
        """
        runs = []
        for run_id in run_ids:
            runs.append(self._load_run(run_id))

        if format == "table":
            self._render_comparison_table(runs)
        elif format == "json":
            self._render_comparison_json(runs)
        elif format == "markdown":
            self._render_comparison_markdown(runs)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _render_table_report(self, run_data: dict[str, Any]) -> None:
        """Render a table format report."""
        run_id = run_data["run_id"]
        models = run_data["models"]
        results = run_data["results"]

        console.print(f"\n[bold]Benchmark Report: {run_id}[/bold]")
        console.print(f"Models: {', '.join(models)}")
        console.print(f"Started: {run_data.get('started_at', 'N/A')}")
        console.print(f"Completed: {run_data.get('completed_at', 'N/A')}")
        console.print()

        # Summary table by model
        table = Table(title="Model Scores Summary")
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Tasks", justify="right")
        table.add_column("Avg Score", justify="right", style="green")
        table.add_column("Correctness", justify="right")
        table.add_column("Efficiency", justify="right")
        table.add_column("Style", justify="right")

        for model in models:
            model_results = [r for r in results if r["model"] == model]
            if not model_results:
                continue

            stats = self.scorer.get_summary_stats(model_results)
            table.add_row(
                model,
                str(stats["count"]),
                f"{stats['mean_total']:.4f}",
                f"{stats['dimension_averages'].get('correctness', 0):.4f}",
                f"{stats['dimension_averages'].get('efficiency', 0):.4f}",
                f"{stats['dimension_averages'].get('style', 0):.4f}",
            )

        console.print(table)

        # Detailed results per task
        task_ids = sorted(set(r["task_id"] for r in results))
        for task_id in task_ids:
            task_results = [r for r in results if r["task_id"] == task_id]
            task_table = Table(title=f"Task: {task_id}")
            task_table.add_column("Model", style="cyan")
            task_table.add_column("Total Score", justify="right", style="green")
            task_table.add_column("Duration (ms)", justify="right")
            task_table.add_column("Status", style="yellow")

            for result in sorted(task_results, key=lambda r: r.get("total_score", 0), reverse=True):
                status = "✓" if not result.get("error") else f"✗ {result['error'][:30]}"
                task_table.add_row(
                    result["model"],
                    f"{result.get('total_score', 0):.4f}",
                    str(result.get("duration_ms", 0)),
                    status,
                )

            console.print(task_table)

    def _render_json_report(self, run_data: dict[str, Any]) -> None:
        """Render a JSON format report."""
        # Add computed fields
        for result in run_data.get("results", []):
            scores = result.get("scores", {})
            result["total_score"] = self.scorer.calculate_total(scores)

        console.print_json(json.dumps(run_data, indent=2))

    def _render_markdown_report(self, run_data: dict[str, Any]) -> None:
        """Render a Markdown format report."""
        lines = []
        run_id = run_data["run_id"]
        models = run_data["models"]
        results = run_data["results"]

        lines.append(f"# Benchmark Report: {run_id}\n")
        lines.append(f"**Models:** {', '.join(models)}")
        lines.append(f"**Started:** {run_data.get('started_at', 'N/A')}")
        lines.append(f"**Completed:** {run_data.get('completed_at', 'N/A')}\n")

        # Summary table
        lines.append("## Model Summary\n")
        lines.append("| Model | Tasks | Avg Score | Correctness | Efficiency | Style |")
        lines.append("|-------|-------|-----------|-------------|------------|-------|")

        for model in models:
            model_results = [r for r in results if r["model"] == model]
            if not model_results:
                continue
            stats = self.scorer.get_summary_stats(model_results)
            lines.append(
                f"| {model} | {stats['count']} | {stats['mean_total']:.4f} | "
                f"{stats['dimension_averages'].get('correctness', 0):.4f} | "
                f"{stats['dimension_averages'].get('efficiency', 0):.4f} | "
                f"{stats['dimension_averages'].get('style', 0):.4f} |"
            )

        # Detailed results
        lines.append("\n## Detailed Results\n")
        task_ids = sorted(set(r["task_id"] for r in results))
        for task_id in task_ids:
            task_results = [r for r in results if r["task_id"] == task_id]
            lines.append(f"### Task: {task_id}\n")
            lines.append("| Model | Total Score | Duration (ms) | Status |")
            lines.append("|-------|-------------|---------------|--------|")

            for result in sorted(task_results, key=lambda r: r.get("total_score", 0), reverse=True):
                status = "✓" if not result.get("error") else f"✗ {result['error'][:30]}"
                lines.append(
                    f"| {result['model']} | {result.get('total_score', 0):.4f} | "
                    f"{result.get('duration_ms', 0)} | {status} |"
                )
            lines.append("")

        output = "\n".join(lines)
        console.print(output)

        # Save to file
        output_path = self.config.results_dir / f"{run_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output)
        console.print(f"\n[dim]Report saved to {output_path}[/dim]")

    def _render_comparison_table(self, runs: list[dict[str, Any]]) -> None:
        """Render a comparison table for multiple runs."""
        table = Table(title="Run Comparison")
        table.add_column("Run ID", style="cyan")
        table.add_column("Models", style="green")
        table.add_column("Tasks", justify="right")
        table.add_column("Avg Score", justify="right", style="yellow")
        table.add_column("Best Model", style="magenta")

        for run_data in runs:
            run_id = run_data["run_id"]
            models = run_data["models"]
            results = run_data["results"]

            # Calculate per-model averages
            model_scores: dict[str, list[float]] = {}
            for result in results:
                model = result["model"]
                total = self.scorer.calculate_total(result.get("scores", {}))
                model_scores.setdefault(model, []).append(total)

            model_avgs = {
                m: sum(scores) / len(scores)
                for m, scores in model_scores.items()
            }
            best_model = max(model_avgs, key=model_avgs.get) if model_avgs else "N/A"
            overall_avg = (
                sum(sum(s) for s in model_scores.values()) / len(results)
                if results
                else 0
            )

            table.add_row(
                run_id,
                ", ".join(models),
                str(len(results)),
                f"{overall_avg:.4f}",
                best_model,
            )

        console.print(table)

    def _render_comparison_json(self, runs: list[dict[str, Any]]) -> None:
        """Render comparison as JSON."""
        comparison = []
        for run_data in runs:
            results = run_data["results"]
            model_scores: dict[str, list[float]] = {}
            for result in results:
                model = result["model"]
                total = self.scorer.calculate_total(result.get("scores", {}))
                model_scores.setdefault(model, []).append(total)

            model_avgs = {
                m: round(sum(scores) / len(scores), 4)
                for m, scores in model_scores.items()
            }

            comparison.append({
                "run_id": run_data["run_id"],
                "models": run_data["models"],
                "model_averages": model_avgs,
            })

        console.print_json(json.dumps(comparison, indent=2))

    def _render_comparison_markdown(self, runs: list[dict[str, Any]]) -> None:
        """Render comparison as Markdown."""
        lines = ["# Run Comparison\n"]
        lines.append("| Run ID | Models | Tasks | Avg Score | Best Model |")
        lines.append("|--------|--------|-------|-----------|------------|")

        for run_data in runs:
            run_id = run_data["run_id"]
            models = run_data["models"]
            results = run_data["results"]

            model_scores: dict[str, list[float]] = {}
            for result in results:
                model = result["model"]
                total = self.scorer.calculate_total(result.get("scores", {}))
                model_scores.setdefault(model, []).append(total)

            model_avgs = {
                m: sum(scores) / len(scores)
                for m, scores in model_scores.items()
            }
            best_model = max(model_avgs, key=model_avgs.get) if model_avgs else "N/A"
            overall_avg = (
                sum(sum(s) for s in model_scores.values()) / len(results)
                if results
                else 0
            )

            lines.append(
                f"| {run_id} | {', '.join(models)} | {len(results)} | "
                f"{overall_avg:.4f} | {best_model} |"
            )

        output = "\n".join(lines)
        console.print(output)
