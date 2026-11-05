"""Unit tests for src/jev_weights.py.

Verifies:
- Key generation symmetry and determinism
- Checkpoint loading and saving mechanics
- Matrix symmetry, diagonal 1.0 values, and checkpoint resumption using mock TypeSafeClient
- Missing API key error handling
- qa_weights execution and boundary metrics
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.jev_weights import (
    _load_pairwise_checkpoint,
    _make_pair_key,
    _save_pairwise_checkpoint,
    generate_jev_weights,
    qa_weights,
)


class TestPairKeysAndCheckpoints:
    """Tests for pure helper functions."""

    def test_make_pair_key_is_symmetric(self):
        assert (
            _make_pair_key("Australians", "New Zealanders")
            == "Australians|||New Zealanders"
        )
        assert (
            _make_pair_key("New Zealanders", "Australians")
            == "Australians|||New Zealanders"
        )

    def test_checkpoint_roundtrip(self, tmp_path):
        checkpoint_file = tmp_path / "checkpoint.json"
        data = {"A|||B": 0.75, "C|||D": 0.12}

        _save_pairwise_checkpoint(checkpoint_file, data)
        assert checkpoint_file.exists()

        loaded = _load_pairwise_checkpoint(checkpoint_file)
        assert loaded == data

    def test_checkpoint_nonexistent_returns_empty(self, tmp_path):
        missing_file = tmp_path / "does_not_exist.json"
        assert _load_pairwise_checkpoint(missing_file) == {}

    def test_checkpoint_corrupt_returns_empty(self, tmp_path):
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("not-json", encoding="utf-8")
        assert _load_pairwise_checkpoint(corrupt_file) == {}


class TestGenerateJevWeights:
    """Tests for the generator with mocked TypeSafeClient."""

    def test_missing_api_key_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key missing"):
            generate_jev_weights(api_key=None)

    @patch("src.jev_weights.fetch_unique_demographic_targets")
    @patch("src.jev_weights.TypeSafeClient")
    def test_generate_builds_symmetric_matrix(
        self, mock_client_cls, mock_fetch_targets, tmp_path
    ):
        mock_fetch_targets.return_value = ["Australians", "Germans", "New Zealanders"]

        # Mock TypeSafeClient context manager
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client

        # Mock response from system_one
        mock_answer_1 = MagicMock()
        mock_answer_1.noul = 0.25
        mock_answer_2 = MagicMock()
        mock_answer_2.noul = 0.77

        mock_response = MagicMock()
        mock_response.nouls = {"rel_0": mock_answer_1, "rel_1": mock_answer_2}
        mock_client.system_one.return_value = mock_response

        out_csv = tmp_path / "test_weights.csv"
        checkpoint_file = tmp_path / "test_checkpoint.json"

        df = generate_jev_weights(
            batch_size=10,
            sample_limit=3,
            checkpoint_path=checkpoint_file,
            output_path=out_csv,
            api_key="mock_key",
        )

        assert out_csv.exists()
        assert df.shape == (3, 3)

        # Diagonal must all be 1.0
        for i in range(3):
            assert df.iloc[i, i] == 1.0

        # Matrix must be symmetric
        for r in range(3):
            for c in range(3):
                assert df.iloc[r, c] == df.iloc[c, r]

    @patch("src.jev_weights.fetch_unique_demographic_targets")
    @patch("src.jev_weights.TypeSafeClient")
    def test_resumes_from_checkpoint_without_reissuing_requests(
        self, mock_client_cls, mock_fetch_targets, tmp_path
    ):
        mock_fetch_targets.return_value = ["Australians", "New Zealanders"]

        checkpoint_file = tmp_path / "resume_checkpoint.json"
        _save_pairwise_checkpoint(
            checkpoint_file, {"Australians|||New Zealanders": 0.77}
        )

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client

        out_csv = tmp_path / "resume_weights.csv"

        df = generate_jev_weights(
            checkpoint_path=checkpoint_file,
            output_path=out_csv,
            api_key="mock_key",
        )

        # No new pairs to compute, system_one should not be called
        mock_client.system_one.assert_not_called()
        assert df.loc["Australians", "New Zealanders"] == 0.77
        assert df.loc["New Zealanders", "Australians"] == 0.77


class TestQAWeights:
    """Tests for qa_weights analysis."""

    def test_qa_weights_missing_file(self, capsys, tmp_path):
        missing = tmp_path / "missing.csv"
        qa_weights(missing)
        captured = capsys.readouterr().out
        assert "not found" in captured

    def test_qa_weights_valid_file(self, capsys, tmp_path):
        csv_file = tmp_path / "sample_weights.csv"
        df = pd.DataFrame(
            [
                [1.0, 0.75, 0.15],
                [0.75, 1.0, 0.85],
                [0.15, 0.85, 1.0],
            ],
            index=["A", "B", "C"],
            columns=["A", "B", "C"],
        )
        df.to_csv(csv_file)

        qa_weights(csv_file)
        captured = capsys.readouterr().out

        assert "QA ANALYSIS" in captured
        assert "TOP 25 CLOSEST" in captured
        assert "CORRIDOR DISTRIBUTION" in captured
        assert "Viable Distractors" in captured
