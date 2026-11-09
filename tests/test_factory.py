"""Tests for the Flask application factory (``slurdletwo.create_app``)."""

from slurdletwo import create_app
from slurdletwo.config import ProductionConfig, TestingConfig


class TestApplicationFactory:
    """Verifies that create_app configures Flask instances correctly."""

    def test_create_app_with_testing_config(self):
        app = create_app(TestingConfig)
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is True

    def test_create_app_with_production_config(self):
        app = create_app(ProductionConfig)
        assert app.config["TESTING"] is False
        assert app.config["DEBUG"] is False

    def test_create_app_default(self):
        app = create_app()
        assert app is not None
        assert app.static_folder is not None and app.static_folder.endswith("static")
        assert app.template_folder is not None and app.template_folder.endswith(
            "templates"
        )

    def test_create_app_blueprint_registered(self):
        app = create_app(TestingConfig)
        assert "game" in app.blueprints
        assert app.static_url_path == "/slurdle/static"
