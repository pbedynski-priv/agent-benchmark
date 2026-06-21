"""Async HTTP client for OpenCode Go API.

Provides retry logic with exponential backoff and rate limiting support.
"""

import asyncio
import time
from typing import Any

import httpx

from .config import Config


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.max_tokens = float(requests_per_minute)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request token is available."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * (self.requests_per_minute / 60.0),
            )
            self.last_refill = now

            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / (self.requests_per_minute / 60.0)
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class RateLimitError(APIClientError):
    """Rate limit exceeded."""

    pass


class APIError(APIClientError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    """Async HTTP client for OpenCode Go API.

    Features:
    - Retry logic with exponential backoff
    - Rate limiting
    - Timeout handling
    - Structured error handling
    """

    def __init__(self, config: Config, rate_limit_rpm: int = 60):
        """Initialize the API client.

        Args:
            config: Application configuration.
            rate_limit_rpm: Maximum requests per minute.
        """
        self.config = config
        self.rate_limiter = RateLimiter(rate_limit_rpm)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "APIClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.api.timeout),
            headers=self._build_headers(),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "code-benchmark/0.1.0",
        }
        api_key = self.config.api.api_key
        if api_key:
            # Both endpoints use Bearer token for OpenCode Go
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _build_anthropic_headers(self) -> dict[str, str]:
        """Build headers for Anthropic-style /messages endpoint."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "code-benchmark/0.1.0",
            "anthropic-version": "2023-06-01",
        }
        api_key = self.config.api.api_key
        if api_key:
            headers["x-api-key"] = api_key
        return headers

    async def call_model(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Call a model with the given prompt.

        Routes to correct endpoint based on model:
        - Anthropic-style /messages: qwen3.7-plus, qwen3.7-max, qwen3.6-plus, minimax-*
        - OpenAI-style /chat/completions: deepseek-*, glm-*, kimi-*, mimo-*
        """
        if not self._client:
            raise APIClientError("Client not initialized. Use async context manager.")

        # Determine endpoint and format based on model
        anthropic_models = {
            "qwen3.7-plus",
            "qwen3.7-max",
            "qwen3.6-plus",
            "minimax-m3",
            "minimax-m2.7",
            "minimax-m2.5",
        }
        use_anthropic = model in anthropic_models or model.startswith("minimax-")

        if use_anthropic:
            payload = self._build_anthropic_payload(model, prompt, system, temperature, max_tokens)
            endpoint = f"{self.config.api.base_url}/messages"
            headers = self._build_anthropic_headers()
        else:
            payload = self._build_openai_payload(model, prompt, system, temperature, max_tokens)
            endpoint = self.config.api.completions_url
            headers = self._build_headers()

        return await self._request_with_retry(payload, endpoint, headers)

    def _build_openai_payload(
        self, model: str, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> dict:
        """Build OpenAI-style chat completions payload."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _build_anthropic_payload(
        self, model: str, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> dict:
        """Build Anthropic-style messages payload."""
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system

        return payload

    async def _request_with_retry(
        self, payload: dict[str, Any], endpoint: str, headers: dict[str, str]
    ) -> str:
        """Execute request with retry logic and exponential backoff.

        Args:
            payload: Request payload.
            endpoint: The API endpoint URL to call.
            headers: HTTP headers for the request.

        Returns:
            Model response text.
        """
        max_retries = self.config.api.max_retries
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                await self.rate_limiter.acquire()
                response = await self._client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(f"Rate limited. Retry after {retry_after}s")

                if response.status_code >= 500:
                    raise APIError(
                        f"Server error: {response.status_code}",
                        status_code=response.status_code,
                    )

                if response.status_code >= 400:
                    raise APIError(
                        f"Client error: {response.status_code} - {response.text}",
                        status_code=response.status_code,
                    )

                data = response.json()
                return self._extract_response(data)

            except RateLimitError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = min(60 * (2**attempt), 300)
                    await asyncio.sleep(wait_time)
                continue

            except APIError as e:
                last_error = e
                if e.status_code and e.status_code < 500:
                    raise  # Don't retry client errors
                if attempt < max_retries:
                    wait_time = min(2**attempt, 30)
                    await asyncio.sleep(wait_time)
                continue

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = min(2**attempt, 30)
                    await asyncio.sleep(wait_time)
                continue

            except httpx.HTTPError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = min(2**attempt, 30)
                    await asyncio.sleep(wait_time)
                continue

        raise APIClientError(f"Request failed after {max_retries + 1} attempts: {last_error}")

    def _extract_response(self, data: dict[str, Any]) -> str:
        """Extract response text from API response.

        Handles both OpenAI-style and Anthropic-style responses,
        including reasoning models that have reasoning_content.
        """
        # Try OpenAI format first: {"choices": [{"message": {"content": "..."}}]}
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            # For reasoning models, content might be empty but reasoning_content has the thinking
            # We want the actual content, not the reasoning
            if content:
                return content
            # If content is empty, check if there's reasoning_content (thinking model)
            # In this case, the model ran out of tokens before producing the actual response
            reasoning = message.get("reasoning_content", "")
            if reasoning:
                # This is a problem - model spent all tokens on reasoning
                # Return empty to trigger error handling
                raise APIError(
                    "Model spent all tokens on reasoning, no actual response generated. Increase max_tokens."
                )

        # Try Anthropic format: {"content": [{"type": "text", "text": "..."}]}
        content_list = data.get("content", [])
        if isinstance(content_list, list):
            for block in content_list:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        return text

        raise APIError(f"Failed to parse response: {data}")
