"""Tests for ``src/config.py`` — validates that configuration constants
are well-formed and internally consistent.
"""

from src.config import (
    DATA_DIR,
    MAX_SEMANTIC_SIMILARITY,
    MIN_SEMANTIC_SIMILARITY,
    ROOT_DIR,
    SLURS_DB,
    SQLALCHEMY_DATABASE_URI,
    STATIC_DIR,
    TEMPLATES_DIR,
)


class TestPaths:
    """Verify that all configured paths resolve correctly."""

    def test_root_dir_is_absolute(self):
        assert ROOT_DIR.is_absolute()

    def test_data_dir_exists(self):
        assert DATA_DIR.exists()

    def test_data_dir_is_under_root(self):
        assert str(DATA_DIR).startswith(str(ROOT_DIR))

    def test_static_dir_is_under_root(self):
        assert str(STATIC_DIR).startswith(str(ROOT_DIR))

    def test_templates_dir_is_under_root(self):
        assert str(TEMPLATES_DIR).startswith(str(ROOT_DIR))

    def test_slurs_db_is_under_data_dir(self):
        assert str(SLURS_DB).startswith(str(DATA_DIR))

    def test_sqlalchemy_uri_points_to_slurs_db(self):
        assert SQLALCHEMY_DATABASE_URI == f"sqlite:///{SLURS_DB}"


class TestSimilarityThresholds:
    """Validate the semantic-similarity boundaries."""

    def test_min_is_less_than_max(self):
        assert MIN_SEMANTIC_SIMILARITY < MAX_SEMANTIC_SIMILARITY

    def test_min_is_non_negative(self):
        assert MIN_SEMANTIC_SIMILARITY >= 0.0

    def test_max_is_at_most_one(self):
        assert MAX_SEMANTIC_SIMILARITY <= 1.0

    def test_thresholds_are_floats(self):
        assert isinstance(MIN_SEMANTIC_SIMILARITY, float)
        assert isinstance(MAX_SEMANTIC_SIMILARITY, float)
