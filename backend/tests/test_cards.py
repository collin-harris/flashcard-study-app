def test_create_card(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["question"] == "casa"
    assert body["answer"] == "house"
    assert body["deck_id"] == deck_id
    assert "card_id" in body


def test_get_card(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    ).json()["card_id"]

    response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["question"] == "casa"


def test_list_cards_in_deck(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    client.post(f"/decks/{deck_id}/cards", json={"question": "casa", "answer": "house"}, headers=auth_headers)
    client.post(f"/decks/{deck_id}/cards", json={"question": "perro", "answer": "dog"}, headers=auth_headers)

    response = client.get(f"/decks/{deck_id}/cards", headers=auth_headers)

    assert response.status_code == 200
    questions = [card["question"] for card in response.json()]
    assert questions == ["casa", "perro"]


def test_update_card(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    ).json()["card_id"]

    response = client.patch(
        f"/decks/{deck_id}/cards/{card_id}",
        json={"answer": "home"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "casa"
    assert body["answer"] == "home"


def test_delete_card(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    ).json()["card_id"]

    delete_response = client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_get_nonexistent_card_returns_404(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.get(f"/decks/{deck_id}/cards/999999", headers=auth_headers)
    assert response.status_code == 404


def test_accessing_another_users_card_is_forbidden(client, register_and_login):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")

    deck_id = client.post("/decks", json={"name": "A's Deck"}, headers=headers_a).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=headers_a,
    ).json()["card_id"]

    assert client.get(f"/decks/{deck_id}/cards/{card_id}", headers=headers_b).status_code == 403
    assert client.patch(
        f"/decks/{deck_id}/cards/{card_id}", json={"answer": "hijacked"}, headers=headers_b
    ).status_code == 403
    assert client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=headers_b).status_code == 403


def test_unauthenticated_request_is_rejected(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.get(f"/decks/{deck_id}/cards")
    assert response.status_code == 401
