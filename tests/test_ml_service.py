"""Tests for the ML similarity service (``src/ml_service.py``).

Covers:
- Service initialisation and weight loading
- Similarity lookups for known / unknown targets
- Threshold boundary behaviour
- Graceful handling of empty state
"""

import pytest

from src.config import MAX_SEMANTIC_SIMILARITY, MIN_SEMANTIC_SIMILARITY
from src.ml_service import TargetSimilarityService


class TestTargetSimilarityServiceInit:
    """Tests for the service before and after loading weights."""

    def test_empty_df_on_construction(self):
        service = TargetSimilarityService()
        assert service.weights_df.empty

    def test_get_similar_targets_returns_none_when_unloaded(self):
        service = TargetSimilarityService()
        assert service.get_similar_targets("anything") is None


class TestTargetSimilarityServiceLoaded:
    """Tests that require the ML service to have loaded weight data."""

    @pytest.fixture(autouse=True)
    def _load_service(self, app_context):
        """Use the app context to ensure weights are loaded."""
        self.service = TargetSimilarityService()
        self.service.load()

    def test_weights_df_is_populated_after_load(self):
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        assert not self.service.weights_df.empty

    def test_weights_df_is_square(self):
        """The similarity matrix must be N×N."""
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        rows, cols = self.service.weights_df.shape
        assert rows == cols

    def test_known_target_returns_four_results(self):
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        target = self.service.weights_df.index[0]
        result = self.service.get_similar_targets(target, count=4)
        # Could be None if this target has fewer than 4 valid neighbours.
        if result is not None:
            assert len(result) == 4

    def test_unknown_target_returns_none(self):
        result = self.service.get_similar_targets("ZZZZZ_nonexistent_target")
        assert result is None

    def test_similar_targets_excludes_self(self):
        """The queried target itself must never appear in the results."""
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        target = self.service.weights_df.index[0]
        result = self.service.get_similar_targets(target, count=4)
        if result is not None:
            assert target not in result

    def test_returned_targets_exist_in_index(self):
        """Every returned target must be a valid label from the weight matrix."""
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        target = self.service.weights_df.index[0]
        result = self.service.get_similar_targets(target, count=4)
        if result is not None:
            valid_labels = set(self.service.weights_df.index)
            for t in result:
                assert t in valid_labels

    def test_similarity_thresholds_are_respected(self):
        """All returned targets must have similarity within the configured range."""
        if self.service.weights_df.empty:
            pytest.skip("No weight CSV found on disk")
        target = self.service.weights_df.index[0]
        result = self.service.get_similar_targets(target, count=4)
        if result is not None:
            for t in result:
                sim = self.service.weights_df.loc[target, t]
                assert MIN_SEMANTIC_SIMILARITY < sim < MAX_SEMANTIC_SIMILARITY
