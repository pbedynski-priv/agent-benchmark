"""Task loader for benchmark tasks.

Loads task definitions from YAML files with filtering support.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TestCase:
    """A single test case for a task."""

    input: str
    expected_output: str
    description: str = ""


@dataclass
class Task:
    """A benchmark task definition."""

    id: str
    category: str
    difficulty: str
    prompt: str
    expected_output: str
    test_cases: list[TestCase] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    time_limit: int = 30
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create a Task from a dictionary.

        Args:
            data: Dictionary with task fields.

        Returns:
            Task instance.
        """
        test_cases = []
        for tc in data.get("test_cases", []):
            test_cases.append(
                TestCase(
                    input=tc.get("input", ""),
                    expected_output=tc.get("expected_output", ""),
                    description=tc.get("description", ""),
                )
            )

        return cls(
            id=data["id"],
            category=data["category"],
            difficulty=data["difficulty"],
            prompt=data["prompt"],
            expected_output=data.get("expected_output", ""),
            test_cases=test_cases,
            tags=data.get("tags", []),
            time_limit=data.get("time_limit", 30),
            description=data.get("description", ""),
        )


class TaskLoader:
    """Loads and manages benchmark tasks from YAML files."""

    def __init__(self, tasks_dir: Path):
        """Initialize the task loader.

        Args:
            tasks_dir: Path to the tasks directory.
        """
        self.tasks_dir = tasks_dir
        self._tasks: dict[str, Task] | None = None

    def load_all(self) -> list[Task]:
        """Load all tasks from the tasks directory.

        Returns:
            List of all loaded tasks.
        """
        if self._tasks is not None:
            return list(self._tasks.values())

        self._tasks = {}
        categories = ["algorithms", "debugging", "data-structures", "hermes"]

        for category in categories:
            category_dir = self.tasks_dir / category
            if not category_dir.exists():
                continue

            # For hermes category, iterate through subdirectories
            if category == "hermes":
                for subdir in category_dir.iterdir():
                    if subdir.is_dir():
                        for yaml_file in subdir.glob("*.yaml"):
                            task = self._load_task_file(yaml_file)
                            if task:
                                self._tasks[task.id] = task
            else:
                for yaml_file in category_dir.glob("*.yaml"):
                    task = self._load_task_file(yaml_file)
                    if task:
                        self._tasks[task.id] = task

        return list(self._tasks.values())

    def load_by_category(self, category: str) -> list[Task]:
        """Load tasks filtered by category.

        Args:
            category: Category name (e.g., 'algorithms', 'debugging', 'hermes-tool-use').

        Returns:
            List of tasks in the specified category.
        """
        all_tasks = self.load_all()
        return [t for t in all_tasks if t.category == category]

    def load_by_difficulty(self, difficulty: str) -> list[Task]:
        """Load tasks filtered by difficulty.

        Args:
            difficulty: Difficulty level ('easy', 'medium', 'hard').

        Returns:
            List of tasks with the specified difficulty.
        """
        all_tasks = self.load_all()
        return [t for t in all_tasks if t.difficulty == difficulty]

    def load_by_ids(self, task_ids: list[str]) -> list[Task]:
        """Load specific tasks by their IDs.

        Args:
            task_ids: List of task IDs to load.

        Returns:
            List of matching tasks.
        """
        all_tasks = self.load_all()
        return [t for t in all_tasks if t.id in task_ids]

    def get_task(self, task_id: str) -> Task | None:
        """Get a single task by ID.

        Args:
            task_id: The task ID.

        Returns:
            Task if found, None otherwise.
        """
        self.load_all()
        return self._tasks.get(task_id) if self._tasks else None

    def get_categories(self) -> list[str]:
        """Get list of available categories.

        Returns:
            List of category names.
        """
        categories = []
        for item in self.tasks_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                if item.name == "hermes":
                    # Add hermes subcategories
                    for subdir in item.iterdir():
                        if subdir.is_dir():
                            categories.append(f"hermes-{subdir.name}")
                else:
                    categories.append(item.name)
        return sorted(categories)

    def _load_task_file(self, path: Path) -> Task | None:
        """Load a single task from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Task if loaded successfully, None otherwise.
        """
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return None

            return Task.from_dict(data)
        except (yaml.YAMLError, KeyError, TypeError) as e:
            print(f"Warning: Failed to load task from {path}: {e}")
            return None

    def load_index(self) -> dict[str, Any]:
        """Load the task index file.

        Returns:
            Index data as dictionary.
        """
        index_path = self.tasks_dir / "index.yaml"
        if not index_path.exists():
            return {}

        with open(index_path, "r") as f:
            return yaml.safe_load(f) or {}
