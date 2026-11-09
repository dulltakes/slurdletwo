import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
STATIC_DIR = PACKAGE_DIR / "static"
TEMPLATES_DIR = PACKAGE_DIR / "templates"

# Shared database and data artifacts
SLURS_DB = DATA_DIR / "slurs.db"
DATA_DIR.mkdir(exist_ok=True)

MIN_SEMANTIC_SIMILARITY = 0.3
MAX_SEMANTIC_SIMILARITY = 0.8
SQLALCHEMY_DATABASE_URI = f"sqlite:///{SLURS_DB}"


class Config:
    """Base application configuration."""

    URL_PREFIX = os.environ.get("URL_PREFIX", "/slurdle")
    APPLICATION_ROOT = os.environ.get("URL_PREFIX", "/slurdle")
    SESSION_COOKIE_PATH = os.environ.get("URL_PREFIX", "/slurdle")
    SESSION_COOKIE_NAME = "slurdle_session"
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    TESTING = False
    DEBUG = False


class DevelopmentConfig(Config):
    """Development configuration with debug mode enabled."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration with testing flag enabled."""

    TESTING = True
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def get_config() -> type[Config]:
    """Resolve active configuration class based on FLASK_ENV or FLASK_DEBUG."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    if env == "testing":
        return TestingConfig
    return DevelopmentConfig
