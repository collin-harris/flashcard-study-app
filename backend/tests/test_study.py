from app.models.card_review import CardReview


def test_review_updates_sm2_state_across_multiple_submissions(client, auth_headers, db_session):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards",
        json={"question": "casa", "answer": "house"},
        headers=auth_headers,
    ).json()["card_id"]

    first = client.post(f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}, headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["repetitions"] == 1

    second = client.post(f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}, headers=auth_headers)
    assert second.json()["repetitions"] == 2

    failing = client.post(f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 1}, headers=auth_headers)
    failing_body = failing.json()
    assert failing_body["repetitions"] == 0

    # Confirm what's actually persisted matches what the endpoint claims, rather
    # than trusting the response body alone.
    stored = db_session.query(CardReview).filter_by(card_id=card_id).one()
    assert stored.repetitions == 0
    assert stored.easiness == failing_body["easiness"]
    assert stored.next_review_date.isoformat() == failing_body["next_review_date"]


def test_due_cards_excludes_recently_reviewed_cards(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_ids = [
        client.post(f"/decks/{deck_id}/cards", json={"question": q, "answer": a}, headers=auth_headers).json()["card_id"]
        for q, a in [("casa", "house"), ("perro", "dog"), ("gato", "cat")]
    ]

    initial = client.get(f"/decks/{deck_id}/study", headers=auth_headers)
    assert {card["card_id"] for card in initial.json()} == set(card_ids)

    client.post(f"/decks/{deck_id}/cards/{card_ids[0]}/review", json={"rating": 5}, headers=auth_headers)

    after_review = client.get(f"/decks/{deck_id}/study", headers=auth_headers)
    remaining_ids = {card["card_id"] for card in after_review.json()}
    assert remaining_ids == {card_ids[1], card_ids[2]}


def test_free_study_includes_all_cards_regardless_of_review_state(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards", json={"question": "casa", "answer": "house"}, headers=auth_headers
    ).json()["card_id"]

    client.post(f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}, headers=auth_headers)

    free_study = client.get(f"/decks/{deck_id}/cards", headers=auth_headers)
    assert [card["card_id"] for card in free_study.json()] == [card_id]

    spaced_repetition = client.get(f"/decks/{deck_id}/study", headers=auth_headers)
    assert spaced_repetition.json() == []


def test_study_and_review_require_authentication(client, auth_headers):
    deck_id = client.post("/decks", json={"name": "Spanish Vocab"}, headers=auth_headers).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards", json={"question": "casa", "answer": "house"}, headers=auth_headers
    ).json()["card_id"]

    assert client.get(f"/decks/{deck_id}/study").status_code == 401
    assert client.post(f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}).status_code == 401


def test_study_and_review_enforce_ownership(client, register_and_login):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")

    deck_id = client.post("/decks", json={"name": "A's Deck"}, headers=headers_a).json()["deck_id"]
    card_id = client.post(
        f"/decks/{deck_id}/cards", json={"question": "casa", "answer": "house"}, headers=headers_a
    ).json()["card_id"]

    assert client.get(f"/decks/{deck_id}/study", headers=headers_b).status_code == 403
    assert client.post(
        f"/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}, headers=headers_b
    ).status_code == 403
