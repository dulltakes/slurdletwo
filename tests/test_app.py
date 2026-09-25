"""Tests for the Flask routes and HTTP-level behaviour.

Covers:
- Index page rendering and session population
- Correct / incorrect guess JSON responses
- Edge cases: missing session, malformed JSON, empty body
"""

import pytest


class TestIndexRoute:
    """GET / — renders the game page and populates the session."""

    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_renders_game_title(self, client):
        response = client.get("/")
        assert b"SLURDLE" in response.data

    def test_populates_session_with_correct_target(self, client):
        """After loading /, the session must contain the answer."""
        client.get("/")
        with client.session_transaction() as sess:
            assert "correct_target" in sess
            assert isinstance(sess["correct_target"], str)
            assert len(sess["correct_target"]) > 0

    def test_populates_session_with_slur(self, client):
        client.get("/")
        with client.session_transaction() as sess:
            assert "slur" in sess

    def test_populates_session_with_origin(self, client):
        client.get("/")
        with client.session_transaction() as sess:
            assert "origin" in sess


class TestGuessRouteCorrect:
    """POST /guess — when the user picks the right answer."""

    @pytest.fixture(autouse=True)
    def _seed_session(self, client):
        with client.session_transaction() as sess:
            sess["correct_target"] = "Australians"
            sess["slur"] = "test_slur"
            sess["origin"] = "test_origin"

    def test_correct_guess_returns_200(self, client):
        resp = client.post("/guess", json={"target": "Australians"})
        assert resp.status_code == 200

    def test_correct_guess_json_flag(self, client):
        data = client.post("/guess", json={"target": "Australians"}).get_json()
        assert data["correct"] is True

    def test_correct_guess_message_contains_target(self, client):
        data = client.post("/guess", json={"target": "Australians"}).get_json()
        assert "refers to Australians" in data["message"]

    def test_correct_guess_message_contains_origin(self, client):
        data = client.post("/guess", json={"target": "Australians"}).get_json()
        assert "test_origin" in data["message"]


class TestGuessRouteIncorrect:
    """POST /guess — when the user picks the wrong answer."""

    @pytest.fixture(autouse=True)
    def _seed_session(self, client):
        with client.session_transaction() as sess:
            sess["correct_target"] = "Australians"
            sess["slur"] = "test_slur"
            sess["origin"] = "test_origin"

    def test_incorrect_guess_returns_200(self, client):
        resp = client.post("/guess", json={"target": "Brazilians"})
        assert resp.status_code == 200

    def test_incorrect_guess_json_flag(self, client):
        data = client.post("/guess", json={"target": "Brazilians"}).get_json()
        assert data["correct"] is False


class TestGuessRouteEdgeCases:
    """POST /guess — boundary and error paths."""

    def test_missing_session_does_not_crash(self, client):
        """If the session expired, the endpoint should still return JSON."""
        resp = client.post("/guess", json={"target": "anything"})
        assert resp.status_code == 200
        data = resp.get_json()
        # correct_target is None, so any guess is "incorrect"
        assert data["correct"] is False

    def test_empty_json_body(self, client):
        """An empty JSON body should not cause a 500."""
        resp = client.post("/guess", json={})
        assert resp.status_code == 200
