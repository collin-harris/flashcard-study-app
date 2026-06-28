# Flashcard & Spaced Repetition Study App

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A full-stack spaced repetition flashcard app built with FastAPI, React,
and PostgreSQL, featuring JWT authentication and an SM-2-based study
algorithm.

## Live Demo

The app is deployed and live:

**Frontend:** https://flashcard-study-app-r3lr.onrender.com

**Demo account:**
- Email: `demo@flashcardapp.com`
- Password: `FlashcardDemo123`

> This is a shared demo account that gets reset periodically by a seed
> script. Don't expect anything you add to it to stick around.

> **Do not register with a real email or password.** This is an
> unmaintained portfolio project with no ongoing security patching or
> support — use the demo account above, or throwaway credentials only.

**Note on first load:** the backend (Render free tier) and database
(Neon, which scales to zero when idle) both spin down after a period
of inactivity. The first request after a quiet stretch can take
30-60 seconds to respond. This is expected, not a bug — every request
after that is fast.

## Features

- Create and manage multiple flashcard decks
- Add, edit, and delete flashcards within a deck
- **Free study mode** — browse all cards in a deck, in any order
- **Review mode** — study only the cards due today, as calculated by
  an SM-2 spaced-repetition algorithm
- Flip-card UI with question/answer sides and a 0-5 recall rating
- JWT-based authentication (register, login, protected routes)
- Per-user data isolation — decks and review history are private to
  the account that created them

## Tech Stack

**Backend**
- Python 3.11, FastAPI
- SQLAlchemy (ORM), Pydantic (validation)
- JWT auth via `python-jose`, password hashing via `passlib`/`bcrypt`

**Database**
- PostgreSQL 15 (Neon in production)

**Frontend**
- React 19, Vite
- React Router v8
- Plain CSS, co-located per component

**Containerization**
- Docker, multi-stage builds (separate `test` and `production` stages)
- Docker Compose (local dev, plus an isolated test-database override)

**Testing**
- pytest + FastAPI's `TestClient`, run against a disposable test DB

**Deployment**
- Backend: Render (Docker)
- Database: Neon (managed Postgres, serverless/scale-to-zero)
- Frontend: Render (static site)

## Architecture Overview

The frontend is a React single-page app that talks to a FastAPI
backend over a JSON REST API, authenticated with a JWT bearer token
stored client-side. The backend persists everything in PostgreSQL via
SQLAlchemy, and the Docker image is built in distinct stages so the
test suite and its dependencies never ship in the production image.

For the full breakdown — data model, endpoint list, and the
reasoning behind key design decisions — see
[docs/architecture.md](docs/architecture.md).

## Local Setup

**Prerequisites:** Docker and Docker Compose, plus Node.js and npm
for running the frontend dev server.

1. Clone the repo:

```bash
git clone https://github.com/collin-harris/flashcard-study-app.git
cd flashcard-study-app
```

2. Set up environment files (copy the examples, adjust if needed):

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

3. Start the database and backend:

```bash
docker compose up --build
```

The API is now available at http://localhost:8000, with interactive
docs (Swagger UI) at http://localhost:8000/docs.

4. In a separate terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The app is now available at http://localhost:5173.

## Running Tests

The backend has an integration test suite (pytest + FastAPI's `TestClient`)
covering authentication, deck/card CRUD, ownership checks, and the SM-2
spaced-repetition flow. Tests run against a dedicated, disposable test
database — never the dev database used for manual testing.

Run the full suite inside Docker:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.test.yml \
  run --rm --build backend pytest
```

This builds the backend's `test` image stage, starts an isolated `db_test`
Postgres container, and runs everything in `backend/tests/`. The `--build`
flag keeps the image in sync with the latest code and dependencies; `--rm`
cleans up the one-off container afterward.

## Project Structure

```
flashcard-study-app/
├── backend/      # FastAPI app, SQLAlchemy models, pytest suite
├── frontend/     # React SPA (Vite)
├── scripts/      # One-off utility scripts (e.g. demo data seeding)
├── docs/         # Data model, API design, and architecture docs
└── docker-compose.yml
```

See [docs/architecture.md](docs/architecture.md) for the full
directory breakdown.

## Documentation

- [Data Model](docs/data-model.md) — database schema and
  relationships
- [API Design](docs/api-design.md) — endpoint reference and
  request/response shapes
- [Architecture](docs/architecture.md) — system design, project
  structure, and key technical decisions

## Notable Technical Decisions

- **SM-2 spaced repetition** — review scheduling uses a simplified
  implementation of the SuperMemo SM-2 algorithm, adjusting each
  card's easiness and interval from a 0-5 recall rating rather than
  a flat right/wrong toggle.
- **Multi-stage Dockerfile** — the backend image builds in stages
  (`base` → `test` / `production`), so test dependencies and the
  test suite itself never ship in the deployed production image.
- **Co-located CSS** — each component/page has its own `.css` file
  next to it, instead of one global stylesheet, keeping styles tied
  to the component they affect.
- **Render + Neon split** — the backend runs on Render while the
  database lives on Neon specifically for its serverless scale-to-
  zero behavior, avoiding a side project's database running (and
  costing) 24/7 against negligible real traffic.
