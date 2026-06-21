"""Tests for the config module."""

from pathlib import Path

import pytest
import yaml

from src.code_benchmark.config import Config, APIConfig, ScoringConfig


class TestConfig:
    """Test the Config class."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        config = Config.load()
        assert config.api.base_url == "https://opencode.ai/zen/go/v1"
        assert config.models.reviewer == "deepseek-v4-pro"

    def test_tasks_dir_property(self):
        """Test tasks_dir property."""
        config = Config.load()
        assert config.tasks_dir.name == "tasks"
        assert config.tasks_dir.exists()

    def test_scoring_weights_sum(self):
        """Test that scoring weights from config sum to 1.0."""
        config = Config.load()
        total = sum(config.scoring.weights.values())
        assert abs(total - 1.0) < 0.001

    def test_config_yaml_exists(self):
        """Test that config.yaml exists and is valid."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        assert config_path.exists()
        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert "api" in data
        assert "models" in data
        assert "scoring" in data

    def test_api_config_defaults(self):
        """Test API config defaults."""
        api = APIConfig()
        assert api.timeout == 120
        assert api.max_retries == 3
        assert api.api_key_env == "OPENCODE_GO_API_KEY"
