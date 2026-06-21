"""Code reviewer engine using DeepSeek V4 Pro.

Reviews generated code across multiple quality dimensions.
"""

import json
from typing import Any

from .api_client import APIClient
from .config import Config
from .task_loader import Task


class ReviewResult:
    """Result of a code review."""

    def __init__(self, scores: dict[str, float], feedback: dict[str, str]):
        self.scores = scores
        self.feedback = feedback

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scores": self.scores,
            "feedback": self.feedback,
        }


class Reviewer:
    """Code reviewer using an LLM to evaluate code quality.

    Evaluates code across 8 dimensions:
    - correctness (30%): Does the code produce correct results?
    - efficiency (20%): Time and space complexity
    - completeness (15%): Are all requirements met?
    - style (10%): Code style and conventions
    - error_handling (10%): Edge cases and error management
    - documentation (5%): Comments and docstrings
    - innovation (5%): Creative or optimal approaches
    - security (5%): Security best practices
    """

    REVIEW_PROMPT_TEMPLATE = """Review this Python code for task: {task_id}

Task: {task_prompt}

Code:
```python
{code}
```

Score 0-10 on these 4 dimensions. Reply ONLY with JSON:
{{"scores": {{"correctness": N, "efficiency": N, "completeness": N, "style": N}}, "feedback": "brief"}}
"""

    def __init__(self, config: Config, client: APIClient):
        """Initialize the reviewer.

        Args:
            config: Application configuration.
            client: API client for making model calls.
        """
        self.config = config
        self.client = client

    async def review_code(
        self,
        code: str,
        task: Task,
        model: str,
    ) -> ReviewResult:
        """Review generated code.

        Args:
            code: The generated code to review.
            task: The original task definition.
            model: The model that generated the code.

        Returns:
            ReviewResult with scores and feedback.
        """
        # Format test cases for the prompt
        test_cases_str = ""
        for i, tc in enumerate(task.test_cases, 1):
            test_cases_str += f"\nTest {i}:\n"
            test_cases_str += f"  Input: {tc.input}\n"
            test_cases_str += f"  Expected: {tc.expected_output}\n"
            if tc.description:
                test_cases_str += f"  Description: {tc.description}\n"

        prompt = self.REVIEW_PROMPT_TEMPLATE.format(
            task_id=task.id,
            task_prompt=task.prompt,
            code=code,
        )

        system = "Expert code reviewer. Reply ONLY with JSON scores."

        try:
            response = await self.client.call_model(
                model=self.config.models.reviewer,
                prompt=prompt,
                system=system,
                temperature=0.1,
                max_tokens=4096,  # Reasoning models need more tokens for thinking + response
            )

            return self._parse_review_response(response)
        except Exception as e:
            # Return default scores on review failure
            return ReviewResult(
                scores={dim: 0.0 for dim in self.config.scoring.weights},
                feedback={"error": f"Review failed: {e}"},
            )

    def _parse_review_response(self, response: str) -> ReviewResult:
        """Parse the reviewer's JSON response.

        Args:
            response: Raw response text from the reviewer model.

        Returns:
            Parsed ReviewResult.
        """
        # Try to extract JSON from the response
        try:
            # Try direct JSON parse
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON block in markdown code fences
            import re

            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # Try to find any JSON object
                json_match = re.search(r"\{[^{}]*\{.*?\}[^{}]*\}", response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Could not parse review response as JSON: {response[:200]}")

        # Extract scores and feedback
        scores_data = data.get("scores", {})
        feedback_data = data.get("feedback", {})

        # Normalize scores to 0-1 range
        scores = {}
        for dim in self.config.scoring.weights:
            raw_score = scores_data.get(dim, 0)
            scores[dim] = max(0.0, min(10.0, float(raw_score))) / 10.0

        return ReviewResult(scores=scores, feedback=feedback_data)
