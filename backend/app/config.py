import os

# Caps on AI card generation, each over a rolling 24 hours, set low to keep
# the live demo's costs down. The demo account is shared by every visitor, so
# it gets its own larger cap in place of the per-user one. Every user's
# requests, the demo account's included, also count toward the global cap.
GENERATION_LIMIT_PER_USER = int(os.environ.get("GENERATION_LIMIT_PER_USER", "5"))
GENERATION_LIMIT_DEMO = int(os.environ.get("GENERATION_LIMIT_DEMO", "6"))
GENERATION_LIMIT_GLOBAL = int(os.environ.get("GENERATION_LIMIT_GLOBAL", "10"))

DEMO_ACCOUNT_EMAIL = os.environ.get("DEMO_ACCOUNT_EMAIL", "demo@flashcardapp.com")

# Tokens are signed with SECRET_KEY, so a missing, short, or publicly known
# key would let anyone forge a login for any account. The app refuses to
# start with one rather than run insecurely. The error never repeats the key.
SECRET_KEY_PLACEHOLDER = "your_secret_key_here"
SECRET_KEY_MIN_LENGTH = 32
_GENERATE_HINT = 'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'


def validate_secret_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise ValueError(f"SECRET_KEY environment variable is not set. {_GENERATE_HINT}")
    if value == SECRET_KEY_PLACEHOLDER:
        raise ValueError(f"SECRET_KEY is still the placeholder from .env.example. {_GENERATE_HINT}")
    if len(value) < SECRET_KEY_MIN_LENGTH:
        raise ValueError(
            f"SECRET_KEY must be at least {SECRET_KEY_MIN_LENGTH} characters long; "
            f"the one set has {len(value)}. {_GENERATE_HINT}"
        )
    return value
