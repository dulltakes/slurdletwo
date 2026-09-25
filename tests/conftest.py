"""Shared fixtures for the slurdletwo test suite.

Provides the Flask test client, app context, and mock data factories
so individual test modules stay focused on assertions.
"""

import pytest

from app import app as flask_app


@pytest.fixture
def app():
    """Yield the configured Flask app with TESTING mode enabled."""
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    """Yield a Flask test client bound to the app fixture."""
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def app_context(app):
    """Push an application context for DB-dependent tests."""
    with app.app_context():
        yield


class SlurRecordStub:
    """Lightweight stand-in for a ``Slur`` ORM instance.

    Avoids importing the model in tests that only exercise pure logic.
    """

    def __init__(
        self,
        slur: str = "test_slur",
        target: str = "test_target",
        origins: str = "test_origin",
    ):
        self.slur = slur
        self.target = target
        self.origins = origins


@pytest.fixture
def slur_stub() -> SlurRecordStub:
    """Return a default ``SlurRecordStub``."""
    return SlurRecordStub()


@pytest.fixture
def slur_stub_factory():
    """Factory fixture – call with keyword overrides to get a custom stub."""
    def _make(**kwargs) -> SlurRecordStub:
        return SlurRecordStub(**kwargs)
    return _make
