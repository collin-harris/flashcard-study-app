# API Design

**Project:** Flashcard & Spaced Repetition Study App  
**Last Updated:** 2026  
**Status:** Finalized

---

## Overview

This document describes the REST API contract between the React frontend and the FastAPI backend. All endpoints return JSON. Authentication is required for all endpoints except `/auth/register` and `/auth/login`.

The API is organized around five concerns:

- **Authentication** — account creation and login
- **Decks** — creating and managing flashcard decks
- **Flashcards** — creating and managing cards within decks
- **Study** — driving both free study and spaced repetition sessions
- **AI card generation** — generating candidate cards from pasted notes, within usage limits

---

## Conventions

**Base URL:**
```
http://localhost:8000
```

**HTTP Methods:**

| Method | Purpose |
|---|---|
| GET | Retrieve a resource or collection |
| POST | Create a new resource |
| PATCH | Partially update an existing resource |
| DELETE | Remove a resource |

**Resource Nesting:**

Flashcards are nested under decks in the URL structure to express ownership explicitly:
```
/decks/{deck_id}/cards/{card_id}
```

**Authentication:**

After login, the server returns a token. The frontend includes this token in the header of every subsequent request:
```
Authorization: Bearer <token>
```

> Implementation note: Token-based authentication (JWT) will be handled by the FastAPI backend. The exact implementation is defined in the architecture document.

**Response Format:**

All responses return JSON. Successful responses include the requested data. Error responses include a `detail` field describing what went wrong.

```json
// Success
{ "deck_id": 1, "name": "Biology 101", "user_id": 3 }

// Error
{ "detail": "Deck not found" }
```

---

## Endpoints

### Authentication

---

#### `POST /auth/register`

Create a new user account.

**Request Body:**
```json
{
  "name": "string",
  "email": "string",
  "password": "string"
}
```

**Response `201 Created`:**
```json
{
  "user_id": "integer",
  "name": "string",
  "email": "string"
}
```

> The password is hashed server-side before storage. The hash is never returned in any response.

**Validation (`422`):** the name is stripped of surrounding whitespace and can't be empty ("Name can't be empty."); the password must be at least 8 characters ("Password must be at least 8 characters.") and at most 72 bytes in UTF-8, the most bcrypt uses. Login applies none of these rules, so accounts created before them can still log in.

---

#### `POST /auth/login`

Authenticate an existing user and return an access token.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

### Decks

---

#### `GET /decks`

Retrieve all decks owned by the authenticated user.

**Response `200 OK`:**
```json
[
  { "deck_id": "integer", "user_id": "integer", "name": "string", "card_count": "integer" },
  { "deck_id": "integer", "user_id": "integer", "name": "string", "card_count": "integer" }
]
```

> This is the primary endpoint for the user dashboard. It returns all decks belonging to the logged-in user only — never another user's decks. Unlike every other deck endpoint, this one includes `card_count` — a per-deck flashcard count computed at query time. It exists only here, on `DeckWithCardCount` (a schema that extends the plain `DeckResponse` used everywhere else), because the dashboard is the one place that needs it; `GET /decks/{deck_id}`, `POST /decks`, and `PATCH /decks/{deck_id}` all continue to return the plain shape.

---

#### `GET /decks/{deck_id}`

Retrieve a single deck by ID.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to retrieve |

**Response `200 OK`:**
```json
{
  "deck_id": "integer",
  "name": "string",
  "user_id": "integer"
}
```

---

#### `POST /decks`

Create a new deck for the authenticated user.

**Request Body:**
```json
{
  "name": "string"
}
```

**Response `201 Created`:**
```json
{
  "deck_id": "integer",
  "name": "string",
  "user_id": "integer"
}
```

**Validation (`422`):** the name is stripped of surrounding whitespace and can't be empty ("Deck name can't be empty.").

---

#### `PATCH /decks/{deck_id}`

Update the name of an existing deck.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to update |

**Request Body:**
```json
{
  "name": "string"
}
```

**Response `200 OK`:**
```json
{
  "deck_id": "integer",
  "name": "string",
  "user_id": "integer"
}
```

**Validation (`422`):** same as `POST /decks` when a name is given; omitting `name` leaves it unchanged.

---

#### `DELETE /decks/{deck_id}`

Delete a deck and all of its flashcards.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to delete |

**Response `204 No Content`**

> Deleting a deck cascades to all associated Flashcard and CardReview rows. This is enforced at the database level via cascade delete rules.

---

### Flashcards

---

#### `GET /decks/{deck_id}/cards`

Retrieve all flashcards in a deck. Used for free study mode — returns all cards regardless of review schedule.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck |

**Response `200 OK`:**
```json
[
  { "card_id": "integer", "deck_id": "integer", "question": "string", "answer": "string" },
  { "card_id": "integer", "deck_id": "integer", "question": "string", "answer": "string" }
]
```

---

#### `GET /decks/{deck_id}/cards/{card_id}`

Retrieve a single flashcard by ID.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck |
| card_id | integer | The ID of the card |

**Response `200 OK`:**
```json
{
  "card_id": "integer",
  "deck_id": "integer",
  "question": "string",
  "answer": "string"
}
```

---

#### `POST /decks/{deck_id}/cards`

Create a new flashcard in a deck.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to add the card to |

**Request Body:**
```json
{
  "question": "string",
  "answer": "string"
}
```

> Surrounding whitespace is stripped from both fields. An empty or whitespace-only `question` or `answer` is rejected with `422`.

**Response `201 Created`:**
```json
{
  "card_id": "integer",
  "deck_id": "integer",
  "question": "string",
  "answer": "string"
}
```

---

#### `POST /decks/{deck_id}/cards/bulk`

Create several flashcards in a deck at once. Used to save cards the user has reviewed after AI generation.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to add the cards to |

**Request Body:**
```json
{
  "cards": [
    { "question": "string", "answer": "string" },
    { "question": "string", "answer": "string" }
  ]
}
```

> `cards` holds 1–100 cards, each validated like the body of `POST /decks/{deck_id}/cards`. The cards are saved in one transaction: if any card is invalid, the request fails with `422` and none are saved.

**Response `201 Created`:**
```json
[
  { "card_id": "integer", "deck_id": "integer", "question": "string", "answer": "string" },
  { "card_id": "integer", "deck_id": "integer", "question": "string", "answer": "string" }
]
```

---

#### `PATCH /decks/{deck_id}/cards/{card_id}`

Update the question or answer of an existing flashcard.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck |
| card_id | integer | The ID of the card to update |

**Request Body:**
```json
{
  "question": "string",
  "answer": "string"
}
```

> Both fields are optional. Only include the fields you want to update. A field that is included follows the same rules as in `POST /decks/{deck_id}/cards`: surrounding whitespace is stripped, and an empty or whitespace-only value is rejected with `422`.

**Response `200 OK`:**
```json
{
  "card_id": "integer",
  "deck_id": "integer",
  "question": "string",
  "answer": "string"
}
```

---

#### `DELETE /decks/{deck_id}/cards/{card_id}`

Delete a flashcard.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck |
| card_id | integer | The ID of the card to delete |

**Response `204 No Content`**

> Deleting a card cascades to its associated CardReview row. This is enforced at the database level.

---

### Study Sessions

---

#### `GET /decks/{deck_id}/study`

Retrieve all flashcards in a deck that are due for review today. Used to drive spaced repetition study sessions.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck to study |

**Response `200 OK`:**
```json
[
  { "card_id": "integer", "question": "string", "answer": "string", "next_review_date": "date" },
  { "card_id": "integer", "question": "string", "answer": "string", "next_review_date": "date" }
]
```

> Returns only cards where `next_review_date <= now`. If a card has never been studied, it has no CardReview record and is included by default. An empty array means no cards are due — the frontend should communicate this clearly to the user.

---

#### `POST /decks/{deck_id}/cards/{card_id}/review`

Submit a study result for a flashcard. The backend runs the SM-2 algorithm and updates the CardReview record. If no CardReview exists for this user and card, one is created.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck |
| card_id | integer | The ID of the card that was reviewed |

**Request Body:**
```json
{
  "rating": "integer"
}
```

> `rating` is the user's self-reported difficulty score on a scale of 0–5, as defined by the SM-2 algorithm. 0 = complete blackout, 5 = perfect recall. The backend uses this value to recalculate `easiness`, `repetitions`, `interval`, and `next_review_date`.

**Response `200 OK`:**
```json
{
  "card_id": "integer",
  "easiness": "float",
  "repetitions": "integer",
  "interval": "integer",
  "next_review_date": "date"
}
```

---

### AI Card Generation

Generation is limited over a rolling 24 hours: 5 requests per user, 6 shared by the demo account (in place of the per-user limit), and 10 across all users. These defaults are set low to keep the live demo's costs down. Every request that passes validation and the ownership check counts, whatever its outcome, except one that fails because the server is misconfigured. The limits and the demo account's email are configurable through environment variables (see `.env.example`).

---

#### `POST /decks/{deck_id}/cards/generate`

Generate candidate flashcards from pasted notes. Nothing is saved to the deck: the user reviews and edits the cards, then saves them with `POST /decks/{deck_id}/cards/bulk`.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| deck_id | integer | The ID of the deck the cards are for |

**Request Body:**
```json
{
  "notes": "string"
}
```

> `notes` is 1–2,000 characters after surrounding whitespace is stripped. Invalid notes are rejected with `422` and don't count toward the limits.

**Response `200 OK` (cards generated):**
```json
{
  "status": "ok",
  "cards": [
    { "question": "string", "answer": "string", "source": ["string"] }
  ],
  "remaining": "integer"
}
```

> `source` holds the excerpts of the notes each card is based on.

**Response `200 OK` (notes rejected):**
```json
{
  "status": "rejected",
  "reason": "string",
  "remaining": "integer"
}
```

> The model rejects notes it can't make useful cards from, and `reason` says why. A rejection counts toward the limits.

**Error responses:**

| Status | When |
|---|---|
| `429 Too Many Requests` | A limit was reached. `detail` says whether it was the user's own limit (or the demo account's) or the overall limit |
| `502 Bad Gateway` | The model's output was unusable (invalid, cut off, or a refusal), or an unexpected error occurred. `detail` asks the user to try again |
| `503 Service Unavailable` | The Anthropic API failed or couldn't be reached |
| `500 Internal Server Error` | The server isn't configured for generation (for example, the API key is missing) |

> The call uses a 45-second timeout per attempt and 1 retry. The notes' content is never logged.

---

#### `GET /generations/remaining`

Retrieve how many generations the user has left, so the UI can show it before they generate.

**Response `200 OK`:**
```json
{
  "remaining": "integer",
  "limit": "integer"
}
```

> `limit` is the user's own limit (6 for the demo account, 5 otherwise). `remaining` is what the user can actually do: the smaller of what's left under their own limit and what's left under the overall limit.

---

## Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Log in and receive an access token |
| GET | `/decks` | Get all decks for the logged-in user |
| GET | `/decks/{deck_id}` | Get a specific deck |
| POST | `/decks` | Create a new deck |
| PATCH | `/decks/{deck_id}` | Update a deck name |
| DELETE | `/decks/{deck_id}` | Delete a deck and its cards |
| GET | `/decks/{deck_id}/cards` | Get all cards in a deck (free study) |
| GET | `/decks/{deck_id}/cards/{card_id}` | Get a specific card |
| POST | `/decks/{deck_id}/cards` | Create a new card in a deck |
| POST | `/decks/{deck_id}/cards/bulk` | Create several cards in a deck in one transaction |
| PATCH | `/decks/{deck_id}/cards/{card_id}` | Update a card |
| DELETE | `/decks/{deck_id}/cards/{card_id}` | Delete a card |
| GET | `/decks/{deck_id}/study` | Get cards due for review today (spaced repetition) |
| POST | `/decks/{deck_id}/cards/{card_id}/review` | Submit a study result and update SM-2 state |
| POST | `/decks/{deck_id}/cards/generate` | Generate candidate cards from notes (not saved) |
| GET | `/generations/remaining` | Get the user's remaining generations |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Resource nesting | Cards nested under decks | Expresses ownership in the URL; makes authorization straightforward |
| CardReview endpoints | No direct CRUD endpoints | CardReview is an internal concern managed by the backend as a side effect of `/review`; the frontend never manipulates it directly |
| Single review endpoint | `POST /review` handles both create and update | The frontend does not know or care whether a CardReview record exists yet; the backend resolves this internally |
| Free study vs spaced repetition | Two separate endpoints | `/cards` returns all cards; `/study` returns only due cards — clean separation of concerns with no query parameter flags |
| Cascade deletes | Handled at database level | Deleting a deck or card automatically removes associated CardReview rows; no separate cleanup endpoints needed |
| Generated cards | Returned, not saved | The user reviews and edits generated cards before saving them with `/cards/bulk`, so nothing unreviewed reaches a deck |
| Generation limits | Reserve a counted row before the API call | Concurrent requests can't exceed a limit while one is waiting on the API; a Postgres advisory lock makes the count and the reservation a single step |

---

## Future Enhancements (Out of Scope)

- **`POST /auth/logout`** — token invalidation; deferred pending auth implementation decisions
- **`GET /decks/{deck_id}/stats`** — deck-level performance metrics derived from CardReview history
- **`GET /users/me`** — user profile endpoint; descoped as no profile page is planned
