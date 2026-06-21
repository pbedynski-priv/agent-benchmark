"""Score calculation for benchmark results."""

from typing import Any


class Scorer:
    """Calculates weighted scores from review results.

    Applies configured weights to individual dimension scores
    to produce a final weighted score.
    """

    def __init__(self, weights: dict[str, float]):
        """Initialize the scorer.

        Args:
            weights: Dictionary mapping dimension names to weights.
                    Weights should sum to 1.0.
        """
        self.weights = weights
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Validate that weights are properly configured."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total:.4f}. "
                f"Weights: {self.weights}"
            )

    def calculate_scores(self, review_result: Any) -> dict[str, float]:
        """Calculate weighted scores from a review result.

        Args:
            review_result: ReviewResult with raw dimension scores (0-1 range).

        Returns:
            Dictionary of weighted scores per dimension.
        """
        raw_scores = review_result.scores if hasattr(review_result, "scores") else review_result
        weighted_scores = {}

        for dimension, weight in self.weights.items():
            raw_score = raw_scores.get(dimension, 0.0)
            weighted_scores[dimension] = round(raw_score * weight, 4)

        return weighted_scores

    def calculate_total(self, scores: dict[str, float]) -> float:
        """Calculate the total weighted score.

        Args:
            scores: Dictionary of weighted scores per dimension.

        Returns:
            Total score (sum of all weighted dimension scores).
        """
        return round(sum(scores.values()), 4)

    def get_dimension_score(self, scores: dict[str, float], dimension: str) -> float:
        """Get the weighted score for a specific dimension.

        Args:
            scores: Dictionary of weighted scores.
            dimension: Dimension name.

        Returns:
            Weighted score for the dimension.
        """
        return scores.get(dimension, 0.0)

    def rank_models(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Rank models by their total scores.

        Args:
            results: List of result dictionaries with 'model' and 'scores' keys.

        Returns:
            Sorted list of results (highest score first) with rank added.
        """
        scored = []
        for result in results:
            total = self.calculate_total(result.get("scores", {}))
            scored.append({**result, "total_score": total})

        scored.sort(key=lambda x: x["total_score"], reverse=True)

        for rank, item in enumerate(scored, 1):
            item["rank"] = rank

        return scored

    def get_summary_stats(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate summary statistics across results.

        Args:
            results: List of result dictionaries.

        Returns:
            Dictionary with summary statistics.
        """
        if not results:
            return {"count": 0}

        totals = [
            self.calculate_total(r.get("scores", {}))
            for r in results
        ]

        # Per-dimension averages
        dimension_avgs = {}
        for dim in self.weights:
            dim_scores = [
                r.get("scores", {}).get(dim, 0.0)
                for r in results
            ]
            if dim_scores:
                dimension_avgs[dim] = round(sum(dim_scores) / len(dim_scores), 4)

        return {
            "count": len(results),
            "mean_total": round(sum(totals) / len(totals), 4),
            "max_total": round(max(totals), 4),
            "min_total": round(min(totals), 4),
            "dimension_averages": dimension_avgs,
        }
