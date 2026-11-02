import pytest


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


@pytest.mark.parametrize(
    "card",
    [
        {"question": "", "answer": "house"},
        {"question": "   ", "answer": "house"},
        {"question": "casa", "answer": ""},
        {"question": "casa", "answer": " \n\t"},
    ],
)
def test_create_card_rejects_empty_or_whitespace_fields(client, auth_headers, card):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(f"/decks/{deck_id}/cards", json=card, headers=auth_headers)

    assert response.status_code == 422
    assert client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json() == []


def test_create_card_strips_surrounding_whitespace(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "  casa ", "answer": "house\n"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert (response.json()["question"], response.json()["answer"]) == ("casa", "house")


@pytest.mark.parametrize("update", [{"question": ""}, {"question": "  "}, {"answer": ""}, {"answer": "\t"}])
def test_update_card_rejects_empty_or_whitespace_fields(client, auth_headers, update):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    ).json()["card_id"]

    response = client.patch(f"/decks/{deck_id}/cards/{card_id}", json=update, headers=auth_headers)

    assert response.status_code == 422
    card = client.get(f"/decks/{deck_id}/cards/{card_id}", headers=auth_headers).json()
    assert (card["question"], card["answer"]) == ("casa", "house")


def bulk_cards(count):
    return [{"question": f"Question {i}", "answer": f"Answer {i}"} for i in range(count)]


def test_bulk_create_cards(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(f"/decks/{deck_id}/cards/bulk", json={"cards": bulk_cards(3)}, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert [card["question"] for card in body] == ["Question 0", "Question 1", "Question 2"]
    assert all(card["deck_id"] == deck_id and "card_id" in card for card in body)
    saved = client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json()
    assert saved == body


def test_bulk_create_accepts_100_cards(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(f"/decks/{deck_id}/cards/bulk", json={"cards": bulk_cards(100)}, headers=auth_headers)

    assert response.status_code == 201
    assert len(client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json()) == 100


@pytest.mark.parametrize("count", [0, 101])
def test_bulk_create_rejects_empty_or_oversized_lists(client, auth_headers, count):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]

    response = client.post(f"/decks/{deck_id}/cards/bulk", json={"cards": bulk_cards(count)}, headers=auth_headers)

    assert response.status_code == 422
    assert client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json() == []


@pytest.mark.parametrize("invalid_card", [{"question": "Question 1"}, {"question": "Question 1", "answer": "   "}])
def test_bulk_create_with_one_invalid_card_saves_nothing(client, auth_headers, invalid_card):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    cards = bulk_cards(3)
    cards[1] = invalid_card

    response = client.post(f"/decks/{deck_id}/cards/bulk", json={"cards": cards}, headers=auth_headers)

    assert response.status_code == 422
    assert client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json() == []


def test_bulk_create_on_another_users_deck_is_forbidden(client, register_and_login):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")
    deck_id = client.post("/decks", json={"name": "A's Deck"}, headers=headers_a).json()["deck_id"]

    response = client.post(f"/decks/{deck_id}/cards/bulk", json={"cards": bulk_cards(2)}, headers=headers_b)

    assert response.status_code == 403
    assert client.get(f"/decks/{deck_id}/cards", headers=headers_a).json() == []


def test_bulk_create_on_missing_deck_returns_404(client, auth_headers):
    response = client.post("/decks/999999/cards/bulk", json={"cards": bulk_cards(2)}, headers=auth_headers)

    assert response.status_code == 404
