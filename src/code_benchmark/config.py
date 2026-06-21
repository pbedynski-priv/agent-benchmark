"""Configuration system for Code Benchmark.

Loads configuration from YAML files and supports environment variable overrides.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class APIConfig:
    """API configuration settings."""

    base_url: str = "https://opencode.ai/zen/go/v1"
    api_key_env: str = "OPENCODE_GO_API_KEY"
    timeout: int = 120
    max_retries: int = 3

    @property
    def api_key(self) -> str | None:
        """Get API key from environment variable or Hermes .env file."""
        # First try environment variable
        key = os.environ.get(self.api_key_env)
        if key and len(key) > 10:  # Valid key should be longer than 10 chars
            return key

        # Fallback: read from Hermes .env file
        hermes_env = Path.home() / "AppData" / "Local" / "hermes" / ".env"
        if hermes_env.exists():
            with open(hermes_env, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{self.api_key_env}=") and not line.startswith("#"):
                        return line.split("=", 1)[1]

        return key  # Return whatever we got from env (might be empty/short)

    @property
    def completions_url(self) -> str:
        """Get the chat completions endpoint URL."""
        return f"{self.base_url}/chat/completions"


@dataclass
class ModelsConfig:
    """Model configuration settings."""

    candidates: list[str] = field(
        default_factory=lambda: [
            "qwen3.7-plus",
            "deepseek-v4-flash",
            "kimi-k2.6",
        ]
    )
    reviewer: str = "deepseek-v4-pro"


@dataclass
class ExecutionConfig:
    """Execution environment configuration."""

    docker_image: str = "python:3.11-slim"
    cpu_limit: float = 1.0
    memory_limit: str = "512M"
    timeout: int = 30
    network: bool = False


@dataclass
class ScoringConfig:
    """Scoring weights configuration."""

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "correctness": 0.30,
            "efficiency": 0.20,
            "completeness": 0.15,
            "style": 0.10,
            "error_handling": 0.10,
            "documentation": 0.05,
            "innovation": 0.05,
            "security": 0.05,
        }
    )

    def validate(self) -> None:
        """Validate that weights sum to 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")


@dataclass
class Config:
    """Main configuration container."""

    api: APIConfig = field(default_factory=APIConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    project_root: Path = field(default_factory=lambda: Path.cwd())

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml. If None, searches for it
                        in current directory and parent directories.

        Returns:
            Config instance with loaded settings.
        """
        if config_path is None:
            config_path = cls._find_config_file()

        if config_path and config_path.exists():
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            return cls._from_dict(data, config_path.parent)

        return cls()

    @classmethod
    def _find_config_file(cls) -> Path | None:
        """Search for config.yaml in current and parent directories."""
        current = Path.cwd()
        for _ in range(5):  # Search up to 5 levels
            candidate = current / "config.yaml"
            if candidate.exists():
                return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    @classmethod
    def _from_dict(cls, data: dict[str, Any], project_root: Path) -> "Config":
        """Create Config from dictionary."""
        config = cls(project_root=project_root)

        # API config
        if "api" in data:
            api_data = data["api"]
            config.api = APIConfig(
                base_url=api_data.get("base_url", config.api.base_url),
                api_key_env=api_data.get("api_key_env", config.api.api_key_env),
                timeout=api_data.get("timeout", config.api.timeout),
                max_retries=api_data.get("max_retries", config.api.max_retries),
            )

        # Models config
        if "models" in data:
            models_data = data["models"]
            config.models = ModelsConfig(
                candidates=models_data.get("candidates", config.models.candidates),
                reviewer=models_data.get("reviewer", config.models.reviewer),
            )

        # Execution config
        if "execution" in data:
            exec_data = data["execution"]
            config.execution = ExecutionConfig(
                docker_image=exec_data.get("docker_image", config.execution.docker_image),
                cpu_limit=exec_data.get("cpu_limit", config.execution.cpu_limit),
                memory_limit=exec_data.get("memory_limit", config.execution.memory_limit),
                timeout=exec_data.get("timeout", config.execution.timeout),
                network=exec_data.get("network", config.execution.network),
            )

        # Scoring config
        if "scoring" in data:
            scoring_data = data["scoring"]
            if "weights" in scoring_data:
                config.scoring = ScoringConfig(weights=scoring_data["weights"])

        return config

    @property
    def tasks_dir(self) -> Path:
        """Get the tasks directory path."""
        return self.project_root / "tasks"

    @property
    def results_dir(self) -> Path:
        """Get the results directory path."""
        return self.project_root / "results"
