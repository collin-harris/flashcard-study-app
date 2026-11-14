from types import SimpleNamespace

import pytest

from app.services import card_generation

OUTPUT = '{"status": "rejected", "reason": "Not study material."}'


@pytest.fixture
def created_clients(monkeypatch):
    # Replaces the SDK client so no request leaves the test. Records the
    # settings each client was created with.
    created = []

    def make_client(**settings):
        created.append(settings)
        response = SimpleNamespace(
            model=card_generation.MODEL,
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            content=[SimpleNamespace(type="text", text=OUTPUT)],
        )
        return SimpleNamespace(messages=SimpleNamespace(create=lambda **request: response))

    monkeypatch.setattr(card_generation.anthropic, "Anthropic", make_client)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return created


def test_timeout_and_retry_overrides_reach_the_client(created_clients):
    card_generation.generate_cards("notes", timeout=45, max_retries=1)

    assert created_clients[0]["timeout"] == 45
    assert created_clients[0]["max_retries"] == 1


def test_defaults_are_unchanged_when_no_overrides_are_passed(created_clients):
    card_generation.generate_cards("notes")

    assert created_clients[0]["timeout"] == card_generation.REQUEST_TIMEOUT_SECONDS == 60
    assert created_clients[0]["max_retries"] == card_generation.MAX_RETRIES == 2


def test_missing_api_key_raises_setup_error_before_creating_a_client(created_clients, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")

    with pytest.raises(card_generation.CardGenerationSetupError):
        card_generation.generate_cards("notes")
    assert created_clients == []
    # Still a RuntimeError, as before the class existed
    assert issubclass(card_generation.CardGenerationSetupError, RuntimeError)
