"""Tests for the Flask routes and HTTP-level behaviour.

Covers:
- Index page rendering and session population
- Correct / incorrect guess JSON responses
- Edge cases: missing session, malformed JSON, empty body
"""

import pytest


class TestIndexRoute:
    """GET /slurdle/ — renders the game page and populates the session."""

    def test_root_redirects_to_slurdle(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert response.headers["Location"] == "/slurdle/"

    def test_returns_200(self, client):
        response = client.get("/slurdle/")
        assert response.status_code == 200

    def test_renders_game_title(self, client):
        response = client.get("/slurdle/")
        assert b"SLURDLE" in response.data

    def test_populates_session_with_correct_target(self, client):
        """After loading /slurdle/, the session must contain the answer."""
        client.get("/slurdle/")
        with client.session_transaction() as sess:
            assert "correct_target" in sess
            assert isinstance(sess["correct_target"], str)
            assert len(sess["correct_target"]) > 0

    def test_populates_session_with_slur(self, client):
        client.get("/slurdle/")
        with client.session_transaction() as sess:
            assert "slur" in sess

    def test_populates_session_with_origin(self, client):
        client.get("/slurdle/")
        with client.session_transaction() as sess:
            assert "origin" in sess

    def test_page_title_is_slur(self, client):
        """The <title> tag should be set to the current question's slur."""
        response = client.get("/slurdle/")
        with client.session_transaction() as sess:
            slur = sess["slur"]
        expected_title = f"<title>{slur}</title>".encode()
        assert expected_title in response.data

    def test_renders_consent_mode_script(self, client):
        """Google Consent Mode v2 default setup must be present in <head>."""
        response = client.get("/slurdle/")
        html = response.data.decode("utf-8")
        assert "gtag('consent', 'default'" in html
        assert "analytics_storage" in html
        assert "ad_storage" in html

    def test_renders_cookie_banner(self, client):
        """The neobrutalist cookie banner elements must be in the page."""
        response = client.get("/slurdle/")
        html = response.data.decode("utf-8")
        assert 'id="cookie-banner"' in html
        assert 'id="consent-yes-btn"' in html
        assert 'id="consent-no-btn"' in html
        assert "Can I set cookies?" in html


class TestGuessRouteCorrect:
    """POST /slurdle/guess — when the user picks the right answer."""

    @pytest.fixture(autouse=True)
    def _seed_session(self, client):
        with client.session_transaction() as sess:
            sess["correct_target"] = "Australians"
            sess["slur"] = "test_slur"
            sess["origin"] = "test_origin"

    def test_correct_guess_returns_200(self, client):
        resp = client.post("/slurdle/guess", json={"target": "Australians"})
        assert resp.status_code == 200

    def test_correct_guess_json_flag(self, client):
        data = client.post("/slurdle/guess", json={"target": "Australians"}).get_json()
        assert data["correct"] is True

    def test_correct_guess_message_contains_target(self, client):
        data = client.post("/slurdle/guess", json={"target": "Australians"}).get_json()
        assert "refers to Australians" in data["message"]

    def test_correct_guess_message_contains_origin(self, client):
        data = client.post("/slurdle/guess", json={"target": "Australians"}).get_json()
        assert "test_origin" in data["message"]


class TestGuessRouteIncorrect:
    """POST /slurdle/guess — when the user picks the wrong answer."""

    @pytest.fixture(autouse=True)
    def _seed_session(self, client):
        with client.session_transaction() as sess:
            sess["correct_target"] = "Australians"
            sess["slur"] = "test_slur"
            sess["origin"] = "test_origin"

    def test_incorrect_guess_returns_200(self, client):
        resp = client.post("/slurdle/guess", json={"target": "Brazilians"})
        assert resp.status_code == 200

    def test_incorrect_guess_json_flag(self, client):
        data = client.post("/slurdle/guess", json={"target": "Brazilians"}).get_json()
        assert data["correct"] is False


class TestGuessRouteEdgeCases:
    """POST /slurdle/guess — boundary and error paths."""

    def test_missing_session_does_not_crash(self, client):
        """If the session expired, the endpoint should still return JSON."""
        resp = client.post("/slurdle/guess", json={"target": "anything"})
        assert resp.status_code == 200
        data = resp.get_json()
        # correct_target is None, so any guess is "incorrect"
        assert data["correct"] is False

    def test_empty_json_body(self, client):
        """An empty JSON body should not cause a 500."""
        resp = client.post("/slurdle/guess", json={})
        assert resp.status_code == 200

    def test_recent_question_fallback_when_active_round_rotated(self, client):
        """If a background probe or refresh advanced correct_target to round 2,
        a guess submitted for round 1's slur must still be recognized."""
        with client.session_transaction() as sess:
            # Active session was rotated to question 2
            sess["correct_target"] = "Bulgarians"
            sess["slur"] = "Burglar"
            sess["origin"] = "origin 2"
            sess["recent_questions"] = {
                "Hoosier": {"target": "Whites", "origin": "origin 1"},
                "Burglar": {"target": "Bulgarians", "origin": "origin 2"},
            }

        # User is still answering "Hoosier" with "Whites"
        resp = client.post(
            "/slurdle/guess", json={"target": "Whites", "slur": "Hoosier"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] is True
        assert "Hoosier refers to Whites" in data["message"]


class TestNextRoute:
    """GET /slurdle/next — returns JSON for next question and updates session."""

    def test_returns_200_json(self, client):
        response = client.get("/slurdle/next")
        assert response.status_code == 200
        data = response.get_json()
        assert "slur" in data
        assert "correct_target" in data
        assert "targets" in data
        assert "origin" in data
        assert len(data["targets"]) == 5

    def test_updates_session_with_next_slur(self, client):
        response = client.get("/slurdle/next")
        data = response.get_json()
        with client.session_transaction() as sess:
            assert sess["slur"] == data["slur"]
            assert sess["correct_target"] == data["correct_target"]


class TestRobotsRoute:
    """GET /robots.txt — serves crawler directives and sitemap reference."""

    def test_returns_200(self, client):
        response = client.get("/robots.txt")
        assert response.status_code == 200

    def test_content_type_plain_text(self, client):
        response = client.get("/robots.txt")
        assert "text/plain" in response.content_type

    def test_contains_user_agent_and_sitemap(self, client):
        response = client.get("/robots.txt")
        text = response.data.decode("utf-8")
        assert "User-agent: *" in text
        assert "Sitemap: https://dulltakes.golf/sitemap.xml" in text
        assert "Disallow: /slurdle/guess" in text
        assert "Disallow: /slurdle/next" in text


class TestSitemapRoute:
    """GET /sitemap.xml — serves valid XML sitemap."""

    def test_returns_200(self, client):
        response = client.get("/sitemap.xml")
        assert response.status_code == 200

    def test_content_type_xml(self, client):
        response = client.get("/sitemap.xml")
        assert "application/xml" in response.content_type

    def test_contains_canonical_url(self, client):
        response = client.get("/sitemap.xml")
        text = response.data.decode("utf-8")
        assert "https://dulltakes.golf/slurdle/" in text
        assert "<urlset" in text
