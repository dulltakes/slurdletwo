"""Slurdle application factory and package namespace."""

import os
from typing import Any

from flask import Flask
from flask import url_for as flask_url_for

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

    # Automatic cache-busting for static assets
    def dated_url_for(endpoint: str, **values: Any) -> str:
        if endpoint == "static":
            filename = values.get("filename")
            if isinstance(filename, str) and app.static_folder:
                file_path = os.path.join(app.root_path, app.static_folder, filename)
                if os.path.exists(file_path):
                    values["v"] = int(os.stat(file_path).st_mtime)
        return flask_url_for(endpoint, **values)

    @app.context_processor
    def inject_dated_url_for() -> dict[str, Any]:
        return {"url_for": dated_url_for}

    # Load ML weights into memory once during startup within application context
    with app.app_context():
        ml_service.load()

    return app
