"""Tests for the task loader module."""

from pathlib import Path

import pytest

from src.code_benchmark.task_loader import TaskLoader, Task


class TestTaskLoader:
    """Test the TaskLoader class."""

    @pytest.fixture
    def task_loader(self):
        """Create a TaskLoader with the project's tasks directory."""
        tasks_dir = Path(__file__).parent.parent / "tasks"
        return TaskLoader(tasks_dir)

    def test_load_all_tasks(self, task_loader):
        """Test that all tasks load successfully."""
        tasks = task_loader.load_all()
        assert len(tasks) > 0
        assert len(tasks) >= 70, f"Expected at least 70 tasks, got {len(tasks)}"

    def test_all_tasks_have_required_fields(self, task_loader):
        """Test that all tasks have required fields."""
        tasks = task_loader.load_all()
        for task in tasks:
            assert task.id, f"Task missing id"
            assert task.category, f"Task {task.id} missing category"
            assert task.difficulty, f"Task {task.id} missing difficulty"
            assert task.prompt, f"Task {task.id} missing prompt"

    def test_task_categories(self, task_loader):
        """Test that expected categories exist."""
        categories = task_loader.get_categories()
        assert "algorithms" in categories
        assert "debugging" in categories
        assert "data-structures" in categories
        # Hermes subcategories
        assert "hermes-tool-use" in categories
        assert "hermes-instruction" in categories
        assert "hermes-memory" in categories
        assert "hermes-planning" in categories
        assert "hermes-error-recovery" in categories
        assert "hermes-code-review" in categories

    def test_load_by_category(self, task_loader):
        """Test filtering tasks by category."""
        algo_tasks = task_loader.load_by_category("algorithms")
        assert len(algo_tasks) > 0
        for task in algo_tasks:
            assert task.category == "algorithms"

    def test_load_by_difficulty(self, task_loader):
        """Test filtering tasks by difficulty."""
        easy_tasks = task_loader.load_by_difficulty("easy")
        assert len(easy_tasks) > 0
        for task in easy_tasks:
            assert task.difficulty == "easy"

    def test_get_task_by_id(self, task_loader):
        """Test getting a specific task by ID."""
        task = task_loader.get_task("binary-search")
        assert task is not None
        assert task.id == "binary-search"
        assert task.category == "algorithms"

    def test_get_nonexistent_task(self, task_loader):
        """Test getting a task that doesn't exist."""
        task = task_loader.get_task("nonexistent-task-id")
        assert task is None

    def test_task_ids_unique(self, task_loader):
        """Test that all task IDs are unique."""
        tasks = task_loader.load_all()
        ids = [t.id for t in tasks]
        assert len(ids) == len(set(ids)), "Duplicate task IDs found"
