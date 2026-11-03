import pytest

from app.models.user import User
from app.routers import auth


def test_register_new_user(client):
    response = client.post("/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "testpass123",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ada Lovelace"
    assert body["email"] == "ada@example.com"
    assert "user_id" in body
    assert "password_hash" not in body
    assert "password" not in body


def test_register_duplicate_email_is_rejected(client):
    client.post("/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "testpass123",
    })

    response = client.post("/auth/register", json={
        "name": "Someone Else",
        "email": "ada@example.com",
        "password": "differentpass456",
    })

    assert response.status_code == 400


def test_login_with_valid_credentials(client):
    client.post("/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "testpass123",
    })

    response = client.post("/auth/login", json={
        "email": "ada@example.com",
        "password": "testpass123",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_with_wrong_password_is_rejected(client):
    client.post("/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "testpass123",
    })

    response = client.post("/auth/login", json={
        "email": "ada@example.com",
        "password": "wrongpassword",
    })

    assert response.status_code == 401


def test_login_with_unregistered_email_is_rejected(client):
    response = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever123",
    })

    assert response.status_code == 401


def register(client, email, name="Ada Lovelace", password="testpass123"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def login(client, email, password="testpass123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_register_saves_email_lowercased(client, db_session):
    response = register(client, "Ada.Lovelace@Example.COM")

    assert response.status_code == 201
    assert response.json()["email"] == "ada.lovelace@example.com"
    assert db_session.query(User.email).scalar() == "ada.lovelace@example.com"


def test_register_and_login_trim_surrounding_whitespace(client, db_session):
    register(client, "  ada@example.com \n")

    assert db_session.query(User.email).scalar() == "ada@example.com"
    assert login(client, "\tada@example.com  ").status_code == 200


@pytest.mark.parametrize("login_email", ["ada@example.com", "ADA@EXAMPLE.COM", "Ada@Example.com"])
def test_login_works_with_any_capitalization(client, login_email):
    register(client, "ada@example.com")

    assert login(client, login_email).status_code == 200


def test_register_case_variant_duplicate_is_rejected(client, db_session):
    register(client, "ada@example.com")

    response = register(client, "ADA@Example.com", name="Someone Else")

    assert response.status_code == 400
    assert response.json() == {"detail": "User already registered"}
    assert db_session.query(User).count() == 1


def test_existing_mixed_case_account_can_still_log_in(client, db_session):
    # Saved directly, as an account registered before emails were normalized
    db_session.add(User(name="Ada Lovelace", email="Ada@Example.com", password_hash=auth.pwd_context.hash("testpass123")))
    db_session.commit()

    assert login(client, "ada@example.com").status_code == 200
    assert login(client, "Ada@Example.com").status_code == 200
    assert register(client, "ada@example.com").status_code == 400


def test_unique_violation_at_commit_returns_400(client, db_session, monkeypatch):
    # Simulates a concurrent registration for the same email committing
    # between this request's duplicate check and its commit: the other
    # account is saved while this request hashes its password
    original_hash = auth.pwd_context.hash

    def hash_after_concurrent_registration(password):
        db_session.add(User(name="Someone Else", email="ada@example.com", password_hash="hash"))
        db_session.commit()
        return original_hash(password)

    monkeypatch.setattr(auth.pwd_context, "hash", hash_after_concurrent_registration)

    response = register(client, "ada@example.com")

    assert response.status_code == 400
    assert response.json() == {"detail": "User already registered"}
    assert [user.name for user in db_session.query(User).all()] == ["Someone Else"]
