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
    if config is None:
        config_obj = get_config()
    else:
        config_obj = config

    url_prefix = getattr(config_obj, "URL_PREFIX", "/slurdle")
    static_url_path = f"{url_prefix}/static" if url_prefix else "/static"

    app = Flask(
        __name__,
        static_folder="static",
        static_url_path=static_url_path,
        template_folder="templates",
    )

    app.config.from_object(config_obj)

    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from slurdletwo.blueprints.game.routes import game_bp

    app.register_blueprint(game_bp, url_prefix=url_prefix)

    # Provide root redirect and fallback SEO endpoints at domain root
    if url_prefix:
        from flask import Response, redirect

        @app.route("/")
        def root_redirect():
            return redirect(f"{url_prefix}/", code=302)

        @app.route("/robots.txt", methods=["GET"])
        def root_robots_txt() -> Response:
            return app.send_static_file("robots.txt")

        @app.route("/sitemap.xml", methods=["GET"])
        def root_sitemap_xml() -> Response:
            response = app.send_static_file("sitemap.xml")
            response.mimetype = "application/xml"
            return response

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
