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

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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


def get_config() -> type[Config]:
    """Resolve active configuration class based on FLASK_ENV or FLASK_DEBUG."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    if env == "testing":
        return TestingConfig
    return DevelopmentConfig
