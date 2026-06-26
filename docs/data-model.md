# Data Model

**Project:** Flashcard & Spaced Repetition Study App  
**Last Updated:** 2026
**Status:** Finalized

---

## Overview

This document describes the relational database schema for the flashcard study app. The database is implemented in PostgreSQL using SQLAlchemy as the ORM layer.

The schema consists of four tables: `User`, `Deck`, `Flashcard`, and `CardReview`. The core design goal is to support the SM-2 spaced repetition algorithm, which requires tracking each user's review history on a per-card basis.

---

## Tables

### User

Stores account information for each registered user.

| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | Serial | Primary Key | Unique identifier for the user |
| name | VARCHAR | NOT NULL | Display name |
| email | VARCHAR | NOT NULL, UNIQUE | Login email address |
| password_hash | VARCHAR | NOT NULL | Bcrypt-hashed password — never store plaintext |

---

### Deck

A named collection of flashcards owned by a single user.

| Column | Type | Constraints | Description |
|---|---|---|---|
| deck_id | Serial | Primary Key | Unique identifier for the deck |
| user_id | Integer | Foreign Key → User | The user who owns this deck |
| name | VARCHAR | NOT NULL | Display name of the deck |

**Relationships:**
- Belongs to one `User` (many-to-one); deleting the user does **not** cascade to delete this row (see note below)
- Contains many `Flashcard` rows (one-to-many)

> **Design note:** The number of cards in a deck is not stored as a column. It is a derived value, computed by counting `Flashcard` rows where `deck_id` matches. Storing it would require manual synchronization on every insert and delete, introducing a potential source of bugs.

> **Design note:** `user_id` does not cascade on deletion of the owning `User`, unlike `Flashcard.deck_id` and the `CardReview` foreign keys, which do. This is dormant rather than a bug — there is currently no `DELETE /users` endpoint, so a user is never actually deleted. See [Future Enhancements](#future-enhancements-out-of-scope) for what would need to change if user deletion is ever implemented.

---

### Flashcard

A single two-sided study card containing a question and an answer.

| Column | Type | Constraints | Description |
|---|---|---|---|
| card_id | Serial | Primary Key | Unique identifier for the card |
| deck_id | Integer | Foreign Key → Deck | The deck this card belongs to |
| question | String | NOT NULL | The front side of the card |
| answer | String | NOT NULL | The back side of the card |

*Stored as SQLAlchemy's generic `String` (unbounded `VARCHAR` in PostgreSQL) — functionally equivalent to `TEXT` for this use case.*

**Relationships:**
- Belongs to one `Deck` (many-to-one); deleting the deck cascades to delete this row
- Has one `CardReview` record per user who studies it (one-to-many)

> **Design note:** A flashcard belongs to exactly one deck. A many-to-many relationship (cards shared across decks) was considered and explicitly descoped to keep the schema simple and the codebase maintainable.

---

### CardReview

Tracks the SM-2 spaced repetition state for a specific user and card pair. This is a weak entity — it cannot exist without both a `User` and a `Flashcard`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | Integer | Primary Key (composite), Foreign Key → User | The user being tracked |
| card_id | Integer | Primary Key (composite), Foreign Key → Flashcard | The card being tracked |
| easiness | FLOAT | NOT NULL | SM-2 easiness factor; reflects historical difficulty |
| repetitions | INTEGER | NOT NULL | Consecutive correct review streak |
| interval | INTEGER | NOT NULL | Days until the next scheduled review |
| next_review_date | DATE | NOT NULL | The date when this card is next due |

**Primary Key:** Composite of (`user_id`, `card_id`)

**Relationships:**
- Belongs to one `User`; deleting the user cascades to delete this row
- Belongs to one `Flashcard`; deleting the card cascades to delete this row

> **Design note:** This table stores only the current SM-2 state, not a full review history. Per-event history (e.g. a log of every review with its timestamp and result) was considered and descoped. The SM-2 algorithm only requires current state to compute the next interval — historical logging is a future enhancement.

> **Design note:** A `CardReview` row is never created in a default or partially-initialized state — it only comes into existence inside the review-submission flow, already populated with the output of the SM-2 calculation. The starting values used on a card's first-ever review (`easiness` 2.5, `repetitions` 0) are inputs the service layer feeds into that calculation, not constraints enforced by the database. Database-level `DEFAULT` values were deliberately not used here, to avoid two sources of truth for a card's starting state — the database and the algorithm logic could drift out of sync if both defined it. The service layer owns these values exclusively.

---

## Entity Relationship Diagram

```
User
 │
 │ one-to-many
 ▼
Deck
 │
 │ one-to-many
 ▼
Flashcard
 │
 │ one-to-many
 ▼
CardReview ◄─── many-to-one ── User
```

One user owns many decks. Each deck contains many flashcards. Each flashcard has one CardReview record per user who studies it. CardReview is jointly owned by User and Flashcard.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Card-to-deck relationship | Many-to-one (one deck per card) | Many-to-many adds a junction table and complexity with minimal user-facing value at this scope |
| Deck-to-user relationship | Many-to-one (one owner per deck) | Shared/public decks descoped; single ownership keeps authorization logic simple |
| Derived values | Not stored (e.g. card count) | Avoids synchronization bugs; compute from the data at query time |
| Review history | Not stored | SM-2 only needs current state; full history logging is a future enhancement |
| Password storage | Hashed via bcrypt | Plaintext passwords must never be stored; the hash is one-way and salted |

---

## SM-2 Algorithm Reference

The `CardReview` table is designed around the SM-2 algorithm. At a high level, after each review the algorithm updates three values:

- **easiness** — adjusted up or down based on the user's self-reported difficulty rating
- **repetitions** — reset to 0 on failure, incremented on success
- **interval** — the number of days until the next review, calculated from easiness and repetitions

The `next_review_date` is set to `now + interval days` after each review. Cards are surfaced for study when `next_review_date <= now`.

The algorithm is implemented server-side in the FastAPI backend, not in the database layer.

---

## Future Enhancements (Out of Scope)

The following were considered during design and intentionally deferred:

- **Review history log** — a separate table recording every individual review event with timestamp and result, enabling analytics and progress charts
- **Shared/public decks** — allowing multiple users to study the same deck, requiring a many-to-many relationship between users and decks
- **Card tagging** — cross-deck organization via tags, requiring a many-to-many relationship between cards and tags
- **User account deletion** — no `DELETE /users` endpoint exists yet; if added, `Deck.user_id` would need an `ondelete="CASCADE"` foreign key (or equivalent cleanup logic) to avoid orphaned decks, matching the cascade behavior already used for `Flashcard.deck_id` and both `CardReview` foreign keys
