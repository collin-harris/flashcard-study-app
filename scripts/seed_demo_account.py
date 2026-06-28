#!/usr/bin/env python3
"""Seeds the demo account with a clean, varied set of decks/cards/review history.

Safe to run repeatedly: it logs into the existing demo account (registering it
on first run only) and replaces its decks each time, so the visible content is
the same after every run. It never deletes or recreates the demo user itself.

Usage:
    python3 scripts/seed_demo_account.py
    SEED_API_BASE_URL=http://localhost:8000 python3 scripts/seed_demo_account.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("SEED_API_BASE_URL", "https://flashcard-study-app-backend.onrender.com")
TIMEOUT = 30  # generous, to tolerate a cold-started backend/database

DEMO_NAME = "Demo User"
DEMO_EMAIL = "demo@flashcardapp.com"
DEMO_PASSWORD = "FlashcardDemo123"

DECKS = {
    "Geography": [
        ("What is the capital of France?", "Paris"),
        ("What is the capital of Japan?", "Tokyo"),
        ("What is the capital of the United States?", "Washington, D.C."),
        ("What is the largest ocean on Earth?", "The Pacific Ocean"),
        ("What is the largest country in the world by area?", "Russia"),
        ("How many continents are there?", "Seven"),
        ("What is the capital of Germany?", "Berlin"),
        ("What is the smallest country in the world by area?", "Vatican City"),
        ("What is the capital of Italy?", "Rome"),
    ],
    "History": [
        ("In what year did World War II end?", "1945"),
        ("Who was the first President of the United States?", "George Washington"),
        ("In what year did World War I begin?", "1914"),
        ("What ancient civilization built the pyramids of Giza?", "The ancient Egyptians"),
        ("In what year was the Declaration of Independence signed?", "1776"),
        ("Who was the first Emperor of Rome?", "Augustus"),
        ("In what year did the Titanic sink?", "1912"),
        ("Who was the first person to walk on the Moon?", "Neil Armstrong"),
        ("In what year did the Berlin Wall fall?", "1989"),
    ],
    "Biology": [
        ("What is the powerhouse of the cell?", "The mitochondria"),
        ("How many chambers does the human heart have?", "Four"),
        ("What is the largest organ in the human body?", "The skin"),
        ("What gas do plants absorb from the atmosphere for photosynthesis?", "Carbon dioxide"),
        ("What is the basic unit of life?", "The cell"),
        ("How many bones are in the adult human body?", "206"),
        ("What part of the cell contains genetic material?", "The nucleus"),
        ("What is the process by which plants make food using sunlight called?", "Photosynthesis"),
        ("How many pairs of chromosomes do humans have?", "23"),
    ],
}

# Cycled per deck to give each one a mix of review states.
REVIEW_PATTERN = [
    "mastered", "struggling", "untouched",
    "mastered", "struggling", "mastered",
    "struggling", "untouched", "mastered",
]

# Real rating submissions (in order) used to produce each treatment via the
# live SM-2 endpoint. "untouched" submits nothing at all.
RATING_SEQUENCES = {
    "mastered": [5, 5, 4, 5],
    "struggling": [2, 1],
    "untouched": [],
}


def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw.decode(errors="replace")


def get_demo_token():
    status, body = request("POST", "/auth/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if status == 200:
        return body["access_token"]

    if status != 401:
        sys.exit(f"ERROR: unexpected login response: {status} {body}")

    print(f"Demo account doesn't exist yet, registering {DEMO_EMAIL}")
    status, body = request("POST", "/auth/register", {
        "name": DEMO_NAME, "email": DEMO_EMAIL, "password": DEMO_PASSWORD,
    })
    if status != 201:
        sys.exit(f"ERROR: registration failed: {status} {body}")

    status, body = request("POST", "/auth/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if status != 200:
        sys.exit(f"ERROR: login after registration failed: {status} {body}")
    return body["access_token"]


def delete_existing_decks(token):
    status, decks = request("GET", "/decks", token=token)
    if status != 200:
        sys.exit(f"ERROR: failed to list decks: {status} {decks}")

    for deck in decks:
        status, _ = request("DELETE", f"/decks/{deck['deck_id']}", token=token)
        if status != 204:
            sys.exit(f"ERROR: failed to delete deck {deck['deck_id']}: {status}")

    print(f"Deleted {len(decks)} existing deck(s)")


def seed_decks(token):
    total_cards = 0
    total_reviewed = 0

    for deck_name, cards in DECKS.items():
        status, deck = request("POST", "/decks", {"name": deck_name}, token=token)
        if status != 201:
            sys.exit(f"ERROR: failed to create deck '{deck_name}': {status} {deck}")
        deck_id = deck["deck_id"]

        for i, (question, answer) in enumerate(cards):
            status, card = request(
                "POST", f"/decks/{deck_id}/cards",
                {"question": question, "answer": answer}, token=token,
            )
            if status != 201:
                sys.exit(f"ERROR: failed to create card in '{deck_name}': {status} {card}")
            card_id = card["card_id"]
            total_cards += 1

            treatment = REVIEW_PATTERN[i % len(REVIEW_PATTERN)]
            ratings = RATING_SEQUENCES[treatment]
            for rating in ratings:
                status, _ = request(
                    "POST", f"/decks/{deck_id}/cards/{card_id}/review",
                    {"rating": rating}, token=token,
                )
                if status != 200:
                    sys.exit(f"ERROR: failed to submit review for card {card_id}: {status}")
            if ratings:
                total_reviewed += 1

        print(f"Created {deck_name} deck with {len(cards)} cards")

    print(f"Seeded review history for {total_reviewed} of {total_cards} cards")


def main():
    print(f"Target API: {BASE_URL}")
    token = get_demo_token()
    delete_existing_decks(token)
    seed_decks(token)
    print("Done.")


if __name__ == "__main__":
    main()
