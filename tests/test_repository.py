"""Tests for the data-access layer (``src/repository.py``).

Covers:
- get_random_slur_record returns a valid ORM instance
- get_all_unique_targets returns deduplicated strings
- get_targets_excluding_substrings respects exclusion rules
"""

from src.repository import (
    get_all_unique_targets,
    get_random_slur_record,
    get_targets_excluding_substrings,
)


class TestGetRandomSlurRecord:
    """Verify random record retrieval from the DB."""

    def test_returns_non_none(self, app_context):
        record = get_random_slur_record()
        assert record is not None

    def test_record_has_slur_attribute(self, app_context):
        record = get_random_slur_record()
        assert record is not None
        assert hasattr(record, "slur")
        assert isinstance(record.slur, str)

    def test_record_has_target_attribute(self, app_context):
        record = get_random_slur_record()
        assert record is not None
        assert hasattr(record, "target")
        assert isinstance(record.target, str)

    def test_record_has_origins_attribute(self, app_context):
        record = get_random_slur_record()
        assert record is not None
        assert hasattr(record, "origins")

    def test_randomness_varies_across_calls(self, app_context):
        """Multiple calls should eventually return different records."""
        seen_slurs: set[str] = set()
        for _ in range(20):
            record = get_random_slur_record()
            if record:
                seen_slurs.add(record.slur)
        # With hundreds of slurs in the DB, 20 random draws should
        # yield at least 2 distinct slurs.
        assert len(seen_slurs) > 1


class TestGetAllUniqueTargets:
    """Verify the unique-targets query."""

    def test_returns_list(self, app_context):
        result = get_all_unique_targets()
        assert isinstance(result, list)

    def test_all_elements_are_strings(self, app_context):
        result = get_all_unique_targets()
        assert all(isinstance(t, str) for t in result)

    def test_no_duplicates(self, app_context):
        result = get_all_unique_targets()
        assert len(result) == len(set(result))

    def test_nonempty(self, app_context):
        result = get_all_unique_targets()
        assert len(result) > 0


class TestGetTargetsExcludingSubstrings:
    """Verify the substring-exclusion fallback query."""

    def test_returns_list(self, app_context):
        result = get_targets_excluding_substrings("Australians")
        assert isinstance(result, list)

    def test_correct_target_not_in_results(self, app_context):
        target = "Australians"
        result = get_targets_excluding_substrings(target)
        assert target not in result

    def test_respects_limit_parameter(self, app_context):
        result = get_targets_excluding_substrings("Australians", limit=2)
        assert len(result) <= 2

    def test_excludes_substring_matches(self, app_context):
        """If the target is 'Australians', results should not contain
        targets that share the root word 'Australian'."""
        result = get_targets_excluding_substrings("Australians", limit=10)
        for t in result:
            assert "Australian" not in t

    def test_handles_slash_separated_target(self, app_context):
        """Targets like 'Native Americans/First Nations' are split on '/'."""
        result = get_targets_excluding_substrings(
            "Native Americans/First Nations", limit=4
        )
        assert isinstance(result, list)

    def test_handles_short_target(self, app_context):
        """Very short targets (≤2 chars per word) should not crash."""
        result = get_targets_excluding_substrings("Al", limit=4)
        assert isinstance(result, list)
