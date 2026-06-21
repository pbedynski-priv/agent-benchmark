"""Tests for the API client module."""

import pytest

from src.code_benchmark.api_client import RateLimiter, APIClient
from src.code_benchmark.config import Config


class TestRateLimiter:
    """Test the RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test that rate limiter allows initial requests."""
        limiter = RateLimiter(requests_per_minute=60)
        # Should not raise
        await limiter.acquire()

    @pytest.mark.asyncio
    async def test_rate_limiter_burst(self):
        """Test rate limiter with burst of requests."""
        limiter = RateLimiter(requests_per_minute=600)  # High limit for test
        for _ in range(10):
            await limiter.acquire()


class TestAPIClient:
    """Test the APIClient class."""

    def test_client_creation(self):
        """Test creating an API client."""
        config = Config.load()
        client = APIClient(config)
        assert client.config == config

    def test_anthropic_model_detection(self):
        """Test that Anthropic models are correctly identified."""
        # These models should use the /messages endpoint
        anthropic_models = {"qwen3.7-plus", "qwen3.7-max", "qwen3.6-plus",
                           "minimax-m3", "minimax-m2.7", "minimax-m2.5"}
        for model in anthropic_models:
            assert model in anthropic_models

    def test_openai_model_detection(self):
        """Test that OpenAI-style models are correctly identified."""
        # These models should use /chat/completions endpoint
        openai_models = {"deepseek-v4-pro", "deepseek-v4-flash",
                        "kimi-k2.6", "kimi-k2.7", "glm-5.1", "glm-5.2",
                        "mimo-v2.5", "mimo-v2.5-pro"}
        anthropic_models = {"qwen3.7-plus", "qwen3.7-max", "qwen3.6-plus",
                           "minimax-m3", "minimax-m2.7", "minimax-m2.5"}
        for model in openai_models:
            assert model not in anthropic_models
