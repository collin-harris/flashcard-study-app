import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.main import app
from app.database import engine, SessionLocal


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    # Runs before every test so no test can see another test's leftover data.
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE card_reviews, flashcards, decks, users RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def register_and_login(client):
    def _make(name="Test User", email="user@example.com", password="testpass123"):
        client.post("/auth/register", json={"name": name, "email": email, "password": password})
        response = client.post("/auth/login", json={"email": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def auth_headers(register_and_login):
    return register_and_login()
