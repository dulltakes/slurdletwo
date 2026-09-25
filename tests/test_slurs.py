"""Tests for the game logic in ``src/slurs.py``.

Covers:
- assemble_question structure and content
- get_other_targets integration (requires DB + ML service)
- Edge cases: special characters in targets, long target names
"""

import pytest

from src.repository import get_random_slur_record
from src.slurs import assemble_question, get_other_targets


class TestAssembleQuestion:
    """Pure-logic tests for ``assemble_question`` — no DB required."""

    def test_returns_dict_with_required_keys(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        assert set(result.keys()) == {"slur", "correct_target", "targets", "origin"}

    def test_correct_target_is_preserved(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        assert result["correct_target"] == "test_target"

    def test_targets_list_contains_correct_answer(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        assert "test_target" in result["targets"]

    def test_targets_list_length_is_five(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        assert len(result["targets"]) == 5

    def test_all_other_targets_present(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        for t in other:
            assert t in result["targets"]

    def test_origin_is_preserved(self, slur_stub):
        other = ["A", "B", "C", "D"]
        result = assemble_question(slur_stub, other)
        assert result["origin"] == "test_origin"

    def test_targets_are_shuffled_across_runs(self, slur_stub):
        """Run assembly many times; the correct answer should NOT always be
        in the same position, proving that shuffling occurs."""
        other = ["A", "B", "C", "D"]
        positions = set()
        for _ in range(50):
            result = assemble_question(slur_stub, other)
            positions.add(result["targets"].index("test_target"))
        # With 5 slots and 50 attempts, it's astronomically unlikely
        # to land in the same position every time.
        assert len(positions) > 1

    def test_special_characters_in_target(self, slur_stub_factory):
        """Target names with slashes and parentheses must survive assembly."""
        stub = slur_stub_factory(target="Native Americans/First Nations")
        other = ["A", "B", "C", "D"]
        result = assemble_question(stub, other)
        assert result["correct_target"] == "Native Americans/First Nations"
        assert "Native Americans/First Nations" in result["targets"]

    def test_empty_origin_string(self, slur_stub_factory):
        stub = slur_stub_factory(origins="")
        other = ["A", "B", "C", "D"]
        result = assemble_question(stub, other)
        assert result["origin"] == ""


class TestGetOtherTargets:
    """Integration tests for ``get_other_targets`` — requires app context."""

    def test_returns_four_targets(self, app_context):
        record = get_random_slur_record()
        if record is None:
            pytest.skip("No slurs in DB")
        targets = get_other_targets(record)
        assert len(targets) == 4

    def test_correct_target_not_in_distractors(self, app_context):
        record = get_random_slur_record()
        if record is None:
            pytest.skip("No slurs in DB")
        targets = get_other_targets(record)
        assert record.target not in targets

    def test_all_distractors_are_strings(self, app_context):
        record = get_random_slur_record()
        if record is None:
            pytest.skip("No slurs in DB")
        targets = get_other_targets(record)
        assert all(isinstance(t, str) for t in targets)

    def test_distractors_are_nonempty_strings(self, app_context):
        record = get_random_slur_record()
        if record is None:
            pytest.skip("No slurs in DB")
        targets = get_other_targets(record)
        assert all(len(t) > 0 for t in targets)

    def test_no_duplicate_distractors(self, app_context):
        """Each distractor should be unique."""
        record = get_random_slur_record()
        if record is None:
            pytest.skip("No slurs in DB")
        targets = get_other_targets(record)
        assert len(targets) == len(set(targets))
