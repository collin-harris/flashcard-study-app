def test_register_new_user(client):
    response = client.post("/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "testpass123",
    })

    assert response.status_code == 200
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
