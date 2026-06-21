"""Tests for the scorer module."""

import pytest
from src.code_benchmark.scorer import Scorer


class TestScorer:
    """Test the Scorer class."""

    @pytest.fixture
    def scorer(self):
        return Scorer({
            "correctness": 0.40,
            "efficiency": 0.25,
            "completeness": 0.20,
            "style": 0.15,
        })

    def test_calculate_total_perfect_scores(self, scorer):
        """Test scoring with perfect raw scores (all 1.0)."""
        # Raw scores in 0-1 range, scorer applies weights
        raw_scores = {
            "correctness": 1.0,
            "efficiency": 1.0,
            "completeness": 1.0,
            "style": 1.0,
        }
        weighted = scorer.calculate_scores(raw_scores)
        total = scorer.calculate_total(weighted)
        assert abs(total - 1.0) < 0.001

    def test_calculate_total_zero_scores(self, scorer):
        """Test scoring with zero raw scores."""
        raw_scores = {
            "correctness": 0.0,
            "efficiency": 0.0,
            "completeness": 0.0,
            "style": 0.0,
        }
        weighted = scorer.calculate_scores(raw_scores)
        total = scorer.calculate_total(weighted)
        assert total == 0.0

    def test_calculate_total_partial_scores(self, scorer):
        """Test scoring with partial raw scores."""
        raw_scores = {
            "correctness": 0.5,
            "efficiency": 0.5,
            "completeness": 0.5,
            "style": 0.5,
        }
        weighted = scorer.calculate_scores(raw_scores)
        total = scorer.calculate_total(weighted)
        assert abs(total - 0.5) < 0.001

    def test_weights_sum_to_one(self, scorer):
        """Test that default weights sum to 1.0."""
        total_weight = sum(scorer.weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_invalid_weights_raises(self):
        """Test that invalid weights raise ValueError."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            Scorer({"correctness": 0.5, "efficiency": 0.1})

    def test_calculate_scores_applies_weights(self, scorer):
        """Test that calculate_scores correctly applies weights."""
        raw_scores = {
            "correctness": 0.8,
            "efficiency": 0.6,
            "completeness": 1.0,
            "style": 0.5,
        }
        weighted = scorer.calculate_scores(raw_scores)
        assert abs(weighted["correctness"] - 0.32) < 0.001  # 0.8 * 0.40
        assert abs(weighted["efficiency"] - 0.15) < 0.001   # 0.6 * 0.25
        assert abs(weighted["completeness"] - 0.20) < 0.001  # 1.0 * 0.20
        assert abs(weighted["style"] - 0.075) < 0.001       # 0.5 * 0.15

    def test_rank_models(self, scorer):
        """Test ranking models by score."""
        results = [
            {"model": "a", "scores": {"correctness": 0.5, "efficiency": 0.5, "completeness": 0.5, "style": 0.5}},
            {"model": "b", "scores": {"correctness": 1.0, "efficiency": 1.0, "completeness": 1.0, "style": 1.0}},
            {"model": "c", "scores": {"correctness": 0.0, "efficiency": 0.0, "completeness": 0.0, "style": 0.0}},
        ]
        ranked = scorer.rank_models(results)
        assert ranked[0]["model"] == "b"
        assert ranked[0]["rank"] == 1
        assert ranked[-1]["model"] == "c"
        assert ranked[-1]["rank"] == 3

    def test_get_summary_stats(self, scorer):
        """Test summary statistics calculation."""
        # get_summary_stats expects already-weighted scores
        results = [
            {"scores": {"correctness": 0.4, "efficiency": 0.25, "completeness": 0.2, "style": 0.15}},  # total=1.0
            {"scores": {"correctness": 0.0, "efficiency": 0.0, "completeness": 0.0, "style": 0.0}},    # total=0.0
        ]
        stats = scorer.get_summary_stats(results)
        assert stats["count"] == 2
        assert abs(stats["mean_total"] - 0.5) < 0.001
        assert abs(stats["max_total"] - 1.0) < 0.001
        assert stats["min_total"] == 0.0
