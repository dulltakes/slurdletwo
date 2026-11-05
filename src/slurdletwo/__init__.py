"""Slurdle application factory and package namespace."""

from flask import Flask

from slurdletwo.config import Config, get_config
from slurdletwo.extensions import db
from slurdletwo.ml.service import ml_service


def create_app(config: Config | type[Config] | None = None) -> Flask:
    """Application factory for Slurdle."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    if config is None:
        config_obj = get_config()
    else:
        config_obj = config

    app.config.from_object(config_obj)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from slurdletwo.blueprints.game.routes import game_bp

    app.register_blueprint(game_bp)

    # Load ML weights into memory once during startup within application context
    with app.app_context():
        ml_service.load()

    return app
