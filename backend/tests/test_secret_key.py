import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "value, reason",
    [
        (None, "is not set"),
        ("", "is not set"),
        ("   ", "is not set"),
        (config.SECRET_KEY_PLACEHOLDER, "placeholder"),
        ("a" * 31, "at least 32 characters"),
    ],
)
def test_unsafe_secret_keys_are_refused(value, reason):
    with pytest.raises(ValueError, match=reason):
        config.validate_secret_key(value)


def test_a_32_character_key_is_accepted():
    assert config.validate_secret_key("a" * 32) == "a" * 32


def test_the_error_explains_how_to_generate_a_key_and_never_repeats_it():
    short_key = "my-short-private-key"
    with pytest.raises(ValueError) as error:
        config.validate_secret_key(short_key)

    assert "secrets.token_urlsafe" in str(error.value)
    assert short_key not in str(error.value)


def start_app(secret_key):
    # A fresh interpreter imports the app as uvicorn would. The key is checked
    # before anything connects to the database.
    env = {**os.environ, "SECRET_KEY": secret_key}
    return subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )


def test_the_app_refuses_to_start_with_an_empty_key():
    result = start_app("")

    assert result.returncode != 0
    assert "SECRET_KEY environment variable is not set" in result.stderr


def test_the_app_refuses_to_start_with_the_example_placeholder():
    result = start_app(config.SECRET_KEY_PLACEHOLDER)

    assert result.returncode != 0
    assert "placeholder" in result.stderr
