import pytest


def test_create_deck(client, auth_headers):
    response = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Spanish Vocab"
    assert "deck_id" in body
    assert "user_id" in body


def test_get_deck(client, auth_headers):
    create_response = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers)
    deck_id = create_response.json()["deck_id"]

    response = client.get(f"/decks/{deck_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Spanish Vocab"


def test_list_decks_returns_only_own_decks(client, register_and_login):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")

    client.post("/decks", json={"name": "A's Deck"}, headers=headers_a)
    client.post("/decks", json={"name": "B's Deck"}, headers=headers_b)

    response = client.get("/decks", headers=headers_a)

    assert response.status_code == 200
    names = [deck["name"] for deck in response.json()]
    assert names == ["A's Deck"]


def test_update_deck_name(client, auth_headers):
    create_response = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers)
    deck_id = create_response.json()["deck_id"]

    response = client.patch(f"/decks/{deck_id}", json={"name": "Spanish Verbs"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Spanish Verbs"


def test_delete_deck(client, auth_headers):
    create_response = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers)
    deck_id = create_response.json()["deck_id"]

    delete_response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/decks/{deck_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_get_nonexistent_deck_returns_404(client, auth_headers):
    response = client.get("/decks/999999", headers=auth_headers)
    assert response.status_code == 404


def test_accessing_another_users_deck_is_forbidden(client, register_and_login):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")

    create_response = client.post("/decks", json={"name": "A's Deck"}, headers=headers_a)
    deck_id = create_response.json()["deck_id"]

    assert client.get(f"/decks/{deck_id}", headers=headers_b).status_code == 403
    assert client.patch(f"/decks/{deck_id}", json={"name": "Hijacked"}, headers=headers_b).status_code == 403
    assert client.delete(f"/decks/{deck_id}", headers=headers_b).status_code == 403


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/decks")
    assert response.status_code == 401


@pytest.mark.parametrize("name", ["", "   ", "\n\t"])
def test_create_deck_rejects_an_empty_name(client, auth_headers, name):
    response = client.post("/decks", json={"name": name}, headers=auth_headers)

    assert response.status_code == 422
    assert [item["msg"] for item in response.json()["detail"]] == ["Deck name can't be empty."]
    assert client.get("/decks", headers=auth_headers).json() == []


def test_create_deck_strips_the_name(client, auth_headers):
    response = client.post("/decks", json={"name": "  Spanish Vocab \n"}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == "Spanish Vocab"


@pytest.mark.parametrize("name", ["", "   "])
def test_update_deck_rejects_an_empty_name_and_keeps_the_old_one(client, auth_headers, name):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.patch(f"/decks/{deck_id}", json={"name": name}, headers=auth_headers)

    assert response.status_code == 422
    assert [item["msg"] for item in response.json()["detail"]] == ["Deck name can't be empty."]
    assert client.get(f"/decks/{deck_id}", headers=auth_headers).json()["name"] == "Spanish Vocab"


def test_update_deck_strips_the_name_and_allows_omitting_it(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    stripped = client.patch(f"/decks/{deck_id}", json={"name": "  Spanish Verbs  "}, headers=auth_headers)
    omitted = client.patch(f"/decks/{deck_id}", json={}, headers=auth_headers)

    assert stripped.json()["name"] == "Spanish Verbs"
    assert omitted.status_code == 200
    assert omitted.json()["name"] == "Spanish Verbs"

