import os

# Caps on AI card generation, each over a rolling 24 hours. The demo account
# is shared by every visitor, so it gets its own larger cap in place of the
# per-user one. Every user's requests, the demo account's included, also
# count toward the global cap.
GENERATION_LIMIT_PER_USER = int(os.environ.get("GENERATION_LIMIT_PER_USER", "5"))
GENERATION_LIMIT_DEMO = int(os.environ.get("GENERATION_LIMIT_DEMO", "20"))
GENERATION_LIMIT_GLOBAL = int(os.environ.get("GENERATION_LIMIT_GLOBAL", "100"))

DEMO_ACCOUNT_EMAIL = os.environ.get("DEMO_ACCOUNT_EMAIL", "demo@flashcardapp.com")
