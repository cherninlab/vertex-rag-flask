import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_upload_page(client):
    response = client.get("/upload")
    assert response.status_code == 200


def test_chat_redirect_without_corpus(client):
    response = client.get("/chat")
    assert response.status_code == 302  # Should redirect to index