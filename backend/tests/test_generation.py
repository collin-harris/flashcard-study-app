import logging
from datetime import timedelta

import pytest
from sqlalchemy import func

from app import config
from app.models.generation_request import GenerationRequest
from app.models.user import User
from app.routers import generation as generation_router
from app.services.card_generation import (
    Card,
    CardGenerationError,
    CardGenerationSetupError,
    GeneratedCards,
    GenerationMetadata,
    GenerationResult,
    Rejection,
)

NOTES = "Mitochondria produce ATP through cellular respiration."

METADATA = GenerationMetadata(
    model="claude-sonnet-5-5",
    prompt_version="v2",
    prompt_hash="abc123def456",
    input_tokens=1200,
    output_tokens=300,
    cost_usd=0.0054,
    latency_seconds=4.2,
)


def ok_result():
    output = GeneratedCards(
        status="ok",
        cards=[Card(question="What do mitochondria produce?", answer="ATP", source=["Mitochondria produce ATP"])],
    )
    return GenerationResult(output=output, metadata=METADATA, raw_text="{}")


def rejected_result():
    output = Rejection(status="rejected", reason="These notes don't contain study material.")
    return GenerationResult(output=output, metadata=METADATA, raw_text="{}")


class FakeGenerate:
    # Stands in for generate_cards: records each call, then returns
    # self.result or raises self.error
    def __init__(self):
        self.calls = []
        self.result = ok_result()
        self.error = None

    def __call__(self, notes, **settings):
        self.calls.append({"notes": notes, **settings})
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def fake_generate(monkeypatch):
    # Replaced where the router looks it up, so no test reaches the API
    fake = FakeGenerate()
    monkeypatch.setattr(generation_router, "generate_cards", fake)
    return fake


def create_deck(client, headers):
    return client.post("/decks", json={"name": "Biology"}, headers=headers).json()["deck_id"]


def generate(client, headers, deck_id, notes=NOTES):
    return client.post(f"/decks/{deck_id}/cards/generate", json={"notes": notes}, headers=headers)


def get_user_id(db_session, email):
    return db_session.query(User).filter(User.email == email).one().user_id


def add_requests(db_session, user_id, count, hours_ago=0.0, status="ok"):
    # Inserts rows directly, timestamped by the database's clock like real ones
    for _ in range(count):
        db_session.add(GenerationRequest(
            user_id=user_id,
            created_at=func.now() - timedelta(hours=hours_ago),
            model="claude-sonnet-5-5",
            prompt_version="v2",
            prompt_hash="abc123def456",
            status=status,
            input_chars=100,
        ))
    db_session.commit()


def all_requests(db_session):
    db_session.expire_all()
    return db_session.query(GenerationRequest).order_by(GenerationRequest.generation_id).all()


# Success and rejection


def test_generate_returns_cards_and_remaining_and_saves_nothing(client, auth_headers):
    deck_id = create_deck(client, auth_headers)

    response = generate(client, auth_headers, deck_id)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "cards": [{"question": "What do mitochondria produce?", "answer": "ATP", "source": ["Mitochondria produce ATP"]}],
        "remaining": 4,
    }
    assert client.get(f"/decks/{deck_id}/cards", headers=auth_headers).json() == []


def test_generate_records_tokens_cost_and_prompt_details(client, auth_headers, db_session):
    deck_id = create_deck(client, auth_headers)

    generate(client, auth_headers, deck_id)

    (row,) = all_requests(db_session)
    assert row.user_id == get_user_id(db_session, "user@example.com")
    assert row.status == "ok"
    assert row.input_chars == len(NOTES)
    assert row.input_tokens == 1200
    assert row.output_tokens == 300
    assert float(row.cost_usd) == pytest.approx(0.0054)
    assert row.latency_seconds == pytest.approx(4.2)
    assert row.model == "claude-sonnet-5-5"
    assert row.prompt_version == "v2"
    assert len(row.prompt_hash) == 12
    assert row.created_at is not None


def test_generate_uses_the_endpoint_timeout_and_retries(client, auth_headers, fake_generate):
    deck_id = create_deck(client, auth_headers)

    generate(client, auth_headers, deck_id)

    assert fake_generate.calls == [{"notes": NOTES, "timeout": 45, "max_retries": 1}]


def test_rejection_returns_200_with_reason_and_remaining(client, auth_headers, fake_generate, db_session):
    fake_generate.result = rejected_result()
    deck_id = create_deck(client, auth_headers)

    response = generate(client, auth_headers, deck_id)

    assert response.status_code == 200
    assert response.json() == {
        "status": "rejected",
        "reason": "These notes don't contain study material.",
        "remaining": 4,
    }
    assert [row.status for row in all_requests(db_session)] == ["rejected"]


def test_rejections_count_toward_the_limit(client, auth_headers, fake_generate):
    fake_generate.result = rejected_result()
    deck_id = create_deck(client, auth_headers)

    for _ in range(5):
        assert generate(client, auth_headers, deck_id).status_code == 200

    assert generate(client, auth_headers, deck_id).status_code == 429


# Input validation


def test_notes_over_2000_characters_return_422_and_create_no_row(client, auth_headers, fake_generate, db_session):
    deck_id = create_deck(client, auth_headers)

    response = generate(client, auth_headers, deck_id, notes="a" * 2001)

    assert response.status_code == 422
    assert all_requests(db_session) == []
    assert fake_generate.calls == []


def test_notes_of_exactly_2000_characters_are_accepted(client, auth_headers):
    deck_id = create_deck(client, auth_headers)

    assert generate(client, auth_headers, deck_id, notes="a" * 2000).status_code == 200


@pytest.mark.parametrize("notes", ["", "   \n\t "])
def test_empty_or_whitespace_notes_return_422_and_create_no_row(client, auth_headers, db_session, notes):
    deck_id = create_deck(client, auth_headers)

    assert generate(client, auth_headers, deck_id, notes=notes).status_code == 422
    assert all_requests(db_session) == []


# Ownership


def test_generate_on_another_users_deck_is_forbidden(client, register_and_login, fake_generate, db_session):
    headers_a = register_and_login(email="a@example.com")
    headers_b = register_and_login(email="b@example.com")
    deck_id = create_deck(client, headers_a)

    assert generate(client, headers_b, deck_id).status_code == 403
    assert all_requests(db_session) == []
    assert fake_generate.calls == []


def test_generate_on_missing_deck_returns_404(client, auth_headers, fake_generate, db_session):
    assert generate(client, auth_headers, 999999).status_code == 404
    assert all_requests(db_session) == []
    assert fake_generate.calls == []


def test_generation_endpoints_require_authentication(client, auth_headers):
    deck_id = create_deck(client, auth_headers)

    assert generate(client, {}, deck_id).status_code == 401
    assert client.get("/generations/remaining").status_code == 401


# Errors


@pytest.mark.parametrize(
    "kind, status_code, metadata",
    [
        ("invalid_output", 502, METADATA),
        ("truncated", 502, METADATA),
        ("refusal", 502, METADATA),
        ("api_error", 503, None),
    ],
)
def test_generation_errors_map_to_status_codes(
    client, auth_headers, fake_generate, db_session, kind, status_code, metadata
):
    fake_generate.error = CardGenerationError(kind, "failed", metadata=metadata)
    deck_id = create_deck(client, auth_headers)

    response = generate(client, auth_headers, deck_id)

    assert response.status_code == status_code
    (row,) = all_requests(db_session)
    assert row.status == kind
    if metadata is None:
        assert (row.input_tokens, row.output_tokens, row.cost_usd, row.latency_seconds) == (None, None, None, None)
    else:
        assert (row.input_tokens, row.output_tokens) == (1200, 300)


def test_retryable_errors_ask_the_user_to_try_again(client, auth_headers, fake_generate):
    fake_generate.error = CardGenerationError("invalid_output", "failed")
    deck_id = create_deck(client, auth_headers)

    assert generate(client, auth_headers, deck_id).json()["detail"] == "Couldn't generate cards. Please try again."


def test_setup_error_returns_500_and_is_logged(client, auth_headers, fake_generate, db_session, caplog):
    fake_generate.error = CardGenerationSetupError("ANTHROPIC_API_KEY environment variable is not set.")
    deck_id = create_deck(client, auth_headers)

    with caplog.at_level(logging.ERROR, logger="app.routers.generation"):
        response = generate(client, auth_headers, deck_id)

    assert response.status_code == 500
    assert [row.status for row in all_requests(db_session)] == ["setup_error"]
    assert "ANTHROPIC_API_KEY" in caplog.text


def test_unexpected_exception_returns_502_and_is_logged(client, auth_headers, fake_generate, db_session, caplog):
    fake_generate.error = KeyError("boom")
    deck_id = create_deck(client, auth_headers)

    with caplog.at_level(logging.ERROR, logger="app.routers.generation"):
        response = generate(client, auth_headers, deck_id)

    assert response.status_code == 502
    assert [row.status for row in all_requests(db_session)] == ["internal_error"]
    assert "KeyError" in caplog.text


@pytest.mark.parametrize(
    "error",
    [
        CardGenerationError("invalid_output", f"input_value='{NOTES}'", raw_text=NOTES, metadata=METADATA),
        CardGenerationError("truncated", NOTES, raw_text=NOTES, metadata=METADATA),
        CardGenerationError("refusal", NOTES, raw_text=NOTES, metadata=METADATA),
        CardGenerationError("api_error", NOTES),
        ValueError(NOTES),
    ],
)
def test_logs_never_contain_the_notes(client, auth_headers, fake_generate, caplog, error):
    # Each error's message quotes the notes, as a real one could
    fake_generate.error = error
    deck_id = create_deck(client, auth_headers)

    with caplog.at_level(logging.DEBUG):
        generate(client, auth_headers, deck_id)

    assert caplog.records
    assert NOTES not in caplog.text


# Limits


def test_user_cap_returns_429_without_calling_the_api(client, auth_headers, fake_generate, db_session):
    deck_id = create_deck(client, auth_headers)
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 5)

    response = generate(client, auth_headers, deck_id)

    assert response.status_code == 429
    assert "your card generations" in response.json()["detail"]
    assert len(all_requests(db_session)) == 5
    assert fake_generate.calls == []


def test_demo_account_has_its_own_larger_cap(client, register_and_login, db_session):
    headers = register_and_login(email=config.DEMO_ACCOUNT_EMAIL)
    deck_id = create_deck(client, headers)
    demo_id = get_user_id(db_session, config.DEMO_ACCOUNT_EMAIL)

    add_requests(db_session, demo_id, 5)
    assert generate(client, headers, deck_id).status_code == 200

    add_requests(db_session, demo_id, 14)
    response = generate(client, headers, deck_id)
    assert response.status_code == 429
    assert "shared demo account" in response.json()["detail"]


def test_global_cap_applies_across_users(client, register_and_login, fake_generate, db_session):
    headers = register_and_login(email="a@example.com")
    register_and_login(email="b@example.com")
    deck_id = create_deck(client, headers)
    add_requests(db_session, get_user_id(db_session, "b@example.com"), 100)

    response = generate(client, headers, deck_id)

    assert response.status_code == 429
    assert "overall limit" in response.json()["detail"]
    assert fake_generate.calls == []


def test_only_the_last_24_hours_count(client, auth_headers, db_session):
    deck_id = create_deck(client, auth_headers)
    user_id = get_user_id(db_session, "user@example.com")

    add_requests(db_session, user_id, 5, hours_ago=24 + 1 / 60)
    assert generate(client, auth_headers, deck_id).status_code == 200

    add_requests(db_session, user_id, 4, hours_ago=24 - 1 / 60)
    assert generate(client, auth_headers, deck_id).status_code == 429


def test_pending_rows_count(client, auth_headers, db_session):
    deck_id = create_deck(client, auth_headers)
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 5, status="pending")

    assert generate(client, auth_headers, deck_id).status_code == 429


def test_api_errors_count_toward_the_limit(client, auth_headers, db_session):
    deck_id = create_deck(client, auth_headers)
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 5, status="api_error")

    assert generate(client, auth_headers, deck_id).status_code == 429


def test_setup_errors_do_not_count_toward_any_limit(client, auth_headers, db_session):
    deck_id = create_deck(client, auth_headers)
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 100, status="setup_error")

    assert client.get("/generations/remaining", headers=auth_headers).json()["remaining"] == 5
    assert generate(client, auth_headers, deck_id).status_code == 200


def test_limits_are_read_from_config(client, auth_headers, monkeypatch):
    monkeypatch.setattr(config, "GENERATION_LIMIT_PER_USER", 2)
    deck_id = create_deck(client, auth_headers)

    assert generate(client, auth_headers, deck_id).status_code == 200
    assert generate(client, auth_headers, deck_id).status_code == 200
    assert generate(client, auth_headers, deck_id).status_code == 429


def test_deleting_a_user_keeps_their_rows_for_the_global_count(client, register_and_login, db_session):
    register_and_login(email="gone@example.com")
    gone_id = get_user_id(db_session, "gone@example.com")
    add_requests(db_session, gone_id, 100)

    db_session.query(User).filter(User.user_id == gone_id).delete()
    db_session.commit()

    rows = all_requests(db_session)
    assert len(rows) == 100
    assert {row.user_id for row in rows} == {None}
    headers = register_and_login(email="a@example.com")
    assert generate(client, headers, create_deck(client, headers)).status_code == 429


# Remaining endpoint


def test_remaining_for_a_new_user(client, auth_headers):
    response = client.get("/generations/remaining", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"remaining": 5, "limit": 5}


def test_remaining_counts_down(client, auth_headers, db_session):
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 2)

    assert client.get("/generations/remaining", headers=auth_headers).json() == {"remaining": 3, "limit": 5}


def test_remaining_for_the_demo_account(client, register_and_login):
    headers = register_and_login(email=config.DEMO_ACCOUNT_EMAIL)

    assert client.get("/generations/remaining", headers=headers).json() == {"remaining": 20, "limit": 20}


def test_remaining_reflects_the_global_cap_when_it_is_closer(client, register_and_login, db_session):
    headers = register_and_login(email="a@example.com")
    register_and_login(email="b@example.com")
    add_requests(db_session, get_user_id(db_session, "b@example.com"), 98)

    assert client.get("/generations/remaining", headers=headers).json() == {"remaining": 2, "limit": 5}


def test_remaining_never_goes_below_zero(client, auth_headers, db_session):
    add_requests(db_session, get_user_id(db_session, "user@example.com"), 7)

    assert client.get("/generations/remaining", headers=auth_headers).json()["remaining"] == 0
