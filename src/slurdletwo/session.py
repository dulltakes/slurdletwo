"""Resilient session interface that resolves duplicate cookies across paths."""

import logging
from typing import Any

from flask import Flask, Request, Response
from flask.sessions import SecureCookieSessionInterface, SessionMixin
from itsdangerous import BadData

logger = logging.getLogger(__name__)


class ResilientSessionInterface(SecureCookieSessionInterface):
    """Session interface that safely resolves duplicate cookies.

    Browsers differentiate cookies by (domain, path, name), but transmit
    only names and values in the HTTP Cookie header without path metadata.
    When an app moves from '/' to a subpath like '/slurdle', legacy cookies
    at Path='/' and new cookies at Path='/slurdle' collide in request headers.

    This interface inspects all cookie candidates, validates signatures,
    and selects the active session with valid game state, while automatically
    instructing the browser to delete stale root-level cookies.
    """

    def open_session(self, app: Flask, request: Request) -> SessionMixin | None:
        s = self.get_signing_serializer(app)
        if s is None:
            return None

        cookie_name = self.get_cookie_name(app)
        # Collect candidates from both the configured cookie name and legacy 'session'
        candidates = request.cookies.getlist(cookie_name)
        if not candidates and cookie_name != "session":
            candidates = request.cookies.getlist("session")

        if not candidates:
            return self.session_class()

        max_age = int(app.permanent_session_lifetime.total_seconds())
        best_data: dict[str, Any] | None = None

        # Inspect candidates in reverse order (browsers typically append or prepend by path specificity)
        for candidate in reversed(candidates):
            try:
                data = s.loads(candidate, max_age=max_age)
                if isinstance(data, dict):
                    # If this candidate has active game state, prioritize it immediately
                    if "correct_target" in data or "slur" in data:
                        return self.session_class(data)
                    if best_data is None:
                        best_data = data
            except (BadData, ValueError) as err:
                logger.debug("Skipping invalid session candidate: %s", err)
                continue

        if best_data is not None:
            return self.session_class(best_data)

        return self.session_class()

    def save_session(
        self, app: Flask, session: SessionMixin, response: Response
    ) -> None:
        super().save_session(app, session, response)

        # Actively purge any legacy root cookies that may be lingering in the browser
        cookie_name = self.get_cookie_name(app)
        response.delete_cookie("session", path="/")
        if cookie_name != "session":
            response.delete_cookie(cookie_name, path="/")
