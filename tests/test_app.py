import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"SLURDLE" in response.data

def test_guess_route_correct(client):
    with client.session_transaction() as sess:
        sess["correct_target"] = "test_target"
        sess["slur"] = "test_slur"
        sess["origin"] = "test_origin"
        
    response = client.post(
        "/guess",
        json={"target": "test_target"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is True
    assert "refers to test_target" in data["message"]

def test_guess_route_incorrect(client):
    with client.session_transaction() as sess:
        sess["correct_target"] = "test_target"
        sess["slur"] = "test_slur"
        sess["origin"] = "test_origin"
        
    response = client.post(
        "/guess",
        json={"target": "wrong_target"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is False
