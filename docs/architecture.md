# Architecture

**Project:** Flashcard & Spaced Repetition Study App  
**Last Updated:** 2026  
**Status:** Finalized

---

## Overview

This document describes the system architecture of the flashcard study app — how the components are structured, how they communicate, and how they are run in development and production.

The system consists of three main components:

- **Frontend** — a React single-page application running in the browser
- **Backend** — a Python FastAPI server handling business logic and API requests
- **Database** — a PostgreSQL database storing all persistent data

The backend and database are containerized together using Docker and orchestrated with Docker Compose. The frontend runs locally during development and is built to static files for production deployment.

---

## System Diagram

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│                                                  │
│              React Frontend                      │
│         (Vite dev server / static)               │
└─────────────────┬───────────────────────────────┘
                  │ HTTP requests
                  │ JSON responses
                  ▼
┌─────────────────────────────────────────────────┐
│              Docker Compose                      │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │           FastAPI Backend                 │  │
│  │         (Python / Uvicorn)                │  │
│  │                                           │  │
│  │  routers → services → models              │  │
│  └──────────────────┬────────────────────────┘  │
│                     │ SQLAlchemy ORM             │
│  ┌──────────────────▼────────────────────────┐  │
│  │           PostgreSQL Database             │  │
│  │                                           │  │
│  │  users, decks, flashcards, card_reviews   │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Components

### Frontend — React

The frontend is a single-page application (SPA) built with React and scaffolded with Vite. It runs entirely in the browser and communicates with the backend exclusively through the REST API documented in `api-design.md`.

The frontend has no direct access to the database. All data is fetched and mutated through HTTP requests to the FastAPI backend.

**Development:** Vite's local dev server runs on `http://localhost:5173` with hot reloading enabled. The frontend is intentionally kept outside Docker during development to preserve hot reloading performance.

**Production:** React is compiled into a folder of static files via `npm run build`. These files are served by a web server (e.g. Nginx) and require no Node.js runtime to serve.

**Key responsibilities:**
- Render the user interface for deck management, card management, and study sessions
- Handle routing between pages
- Manage authentication tokens and attach them to API requests
- Drive both free study mode and spaced repetition study sessions

---

### Backend — FastAPI

The backend is a Python application built with FastAPI, running on the Uvicorn ASGI server inside a Docker container. It is the sole point of communication between the frontend and the database.

**Runs on:** `http://localhost:8000`

**Key responsibilities:**
- Expose the REST API defined in `api-design.md`
- Validate all incoming request data via Pydantic schemas
- Execute the SM-2 spaced repetition algorithm on study results
- Read and write data to PostgreSQL via SQLAlchemy
- Handle authentication and protect routes from unauthorized access

#### Internal Structure

```
backend/
├── app/
│   ├── main.py         # FastAPI app instantiation; router registration
│   ├── database.py     # SQLAlchemy engine and session configuration
│   ├── models/         # SQLAlchemy ORM models (one file per table)
│   │   ├── user.py
│   │   ├── deck.py
│   │   ├── flashcard.py
│   │   └── card_review.py
│   ├── routers/        # API route handlers (one file per resource group)
│   │   ├── auth.py
│   │   ├── decks.py
│   │   ├── cards.py
│   │   └── study.py
│   ├── schemas/        # Pydantic request/response models
│   │   ├── user.py
│   │   ├── deck.py
│   │   ├── card.py
│   │   └── review.py
│   └── services/       # Business logic decoupled from route handlers
│       └── sm2.py      # SM-2 spaced repetition algorithm
├── tests/              # pytest integration test suite (see Containerization)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_decks.py
│   ├── test_cards.py
│   └── test_study.py
├── Dockerfile
├── requirements.txt
├── requirements-test.txt
└── pytest.ini
```

**Separation of concerns:**

| Layer | Responsibility |
|---|---|
| `routers/` | Receive HTTP requests, validate input, return responses |
| `services/` | Execute business logic (SM-2 algorithm) |
| `models/` | Define database table structure via SQLAlchemy |
| `schemas/` | Define and validate the shape of API request and response data |
| `database.py` | Configure the database connection and provide sessions |

> **Why separate models and schemas?** A SQLAlchemy model maps directly to a database table. A Pydantic schema defines what data is allowed into or out of the API. Keeping them separate means your database structure and your API contract can evolve independently, and sensitive fields (like `password_hash`) can be excluded from responses without special handling.

---

### Database — PostgreSQL

PostgreSQL runs in its own Docker container, managed by Docker Compose alongside the backend. It is not exposed to the host machine in production — only the backend container communicates with it directly.

The schema is defined in `docs/data-model.md` and managed in code via SQLAlchemy models. SQLAlchemy creates and manages the tables on application startup.

**Tables:** `users`, `decks`, `flashcards`, `card_reviews`

**Connection:** The backend connects via a `DATABASE_URL` environment variable of the form:
```
postgresql://user:password@db:5432/flashcard_db
```

> The hostname `db` refers to the PostgreSQL service name defined in `docker-compose.yml` — Docker Compose's internal networking resolves this automatically.

---

## Containerization

### Docker

Each containerized component has its own `Dockerfile` — a recipe that defines how to build that component's image.

The backend `Dockerfile` is multi-stage, with three stages building on each other:

1. **`base`** — starts from an official Python base image, sets the working directory, copies `requirements.txt` and installs dependencies, then copies the application code. Both later stages build on this without repeating any of it.
2. **`test`** — extends `base`; adds `requirements-test.txt` and `pytest.ini`, installs the test-only dependencies (`pytest`, `httpx`), and copies in `tests/`. This is the stage `docker-compose.test.yml` tells the backend service to build when running the test suite.
3. **`production`** — extends `base` directly, skipping the `test` stage entirely, and starts the Uvicorn server. Because it branches from `base` rather than `test`, the deployed image never contains `pytest`, `httpx`, or the test suite — not installed-then-ignored, genuinely never copied in. This keeps the deployed container lean and free of dev/test dependencies.

### Docker Compose

`docker-compose.yml` lives at the project root and orchestrates both containers together. It defines:

- The **backend** service — built from `backend/Dockerfile`, exposed on port 8000
- The **db** service — pulled from the official PostgreSQL image, configured with credentials via environment variables
- A shared **network** — allows the backend and database containers to communicate with each other by service name
- A **volume** — persists PostgreSQL data so the database survives container restarts

```
flashcard-study-app/
├── docker-compose.yml         ← orchestrates both containers
├── docker-compose.test.yml    ← layers on top, for running tests in isolation
    backend/
    └── Dockerfile             ← recipe for the backend image
```

A second compose file, `docker-compose.test.yml`, layers on top of `docker-compose.yml` (via `docker compose -f docker-compose.yml -f docker-compose.test.yml ...`) without modifying it. It overrides the **backend** service to build from the `test` stage instead of `production`, and adds a **db_test** service — an isolated Postgres instance used only by the integration test suite, so tests never run against the development or production database.

**Startup ordering:** the `db` service defines a `healthcheck` (`pg_isready`), and the `backend` service declares `depends_on: db: condition: service_healthy`. This means `backend` doesn't just wait for the `db` *container* to start — it waits for Postgres itself to actually be ready to accept connections before starting. This closes a known fragility identified back in Milestone 1: a container reporting "started" doesn't mean the process inside it has finished initializing.

> The backend's `GET /` endpoint (in `main.py`, returns `{"status": "ok"}`) is a separate, simpler thing — a plain route useful as a manual sanity check that the backend is running. It is **not** currently wired into Docker Compose as an actual `healthcheck:` the way `db`'s `pg_isready` is; `backend` has no `healthcheck:` block of its own in `docker-compose.yml`.

### Environment Variables

Sensitive configuration is never hardcoded. The following values are stored in a `.env` file at the project root and loaded by Docker Compose at runtime:

| Variable | Description |
|---|---|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |
| `DATABASE_URL` | Full connection string used by SQLAlchemy |
| `SECRET_KEY` | Secret used for signing JWT authentication tokens |

> `.env` is listed in `.gitignore` and must never be committed to the repository. A `.env.example` file with placeholder values should be committed instead so other developers know what variables are required.

---

## Project Structure

```
flashcard-study-app/
├── docs/
│   ├── data-model.md
│   ├── api-design.md
│   └── architecture.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── deck.py
│   │   │   ├── flashcard.py
│   │   │   └── card_review.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── decks.py
│   │   │   ├── cards.py
│   │   │   └── study.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── deck.py
│   │   │   ├── card.py
│   │   │   └── review.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── sm2.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_decks.py
│   │   ├── test_cards.py
│   │   └── test_study.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-test.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── validation.js
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── Header.css
│   │   │   ├── ProtectedLayout.jsx
│   │   │   ├── ProtectedLayout.css
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── PasswordInput.jsx
│   │   │   └── PasswordInput.css
│   │   └── pages/
│   │       ├── HomePage.jsx
│   │       ├── HomePage.css
│   │       ├── LoginPage.jsx
│   │       ├── LoginPage.css
│   │       ├── RegisterPage.jsx
│   │       ├── RegisterPage.css
│   │       ├── DashboardPage.jsx
│   │       ├── DashboardPage.css
│   │       ├── CreateDeckPage.jsx
│   │       ├── CreateDeckPage.css
│   │       ├── DeckDetailPage.jsx
│   │       ├── DeckDetailPage.css
│   │       ├── StudySessionPage.jsx
│   │       └── StudySessionPage.css
│   ├── index.html
│   └── package.json
├── scripts/
│   └── seed_demo_account.py
├── .env
├── .env.example
├── .gitignore             ← frontend/ has its own separate .gitignore too
├── docker-compose.yml
├── docker-compose.test.yml
└── README.md
```

---

## Development Workflow

```
1. Start backend + database:
   $ docker compose up

2. Start frontend (separate terminal):
   $ cd frontend && npm run dev

3. Frontend available at:  http://localhost:5173
   Backend available at:   http://localhost:8000
   API docs (FastAPI auto-generates): http://localhost:8000/docs
```

> FastAPI automatically generates interactive API documentation at `/docs` using the Swagger UI. This is useful for testing endpoints during development without needing a frontend.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend outside Docker in development | Local Vite dev server | Preserves hot reloading; Docker adds latency that makes frontend development slow |
| Backend and database in Docker | Docker Compose | Ensures consistent environment for the server-side stack; simplifies onboarding |
| SQLAlchemy as ORM | SQLAlchemy | Industry standard for Python database access; abstracts SQL while remaining explicit |
| Pydantic schemas separate from ORM models | Separate `schemas/` layer | Decouples API contract from database structure; prevents sensitive fields from leaking into responses |
| Environment variables for secrets | `.env` file via Docker Compose | Secrets never hardcoded; `.env` excluded from version control via `.gitignore` |
| SM-2 logic in `services/` | `sm2.py` | Business logic decoupled from route handlers; easier to test in isolation |
| Multi-stage Dockerfile | `base` → `test` / `production` | Keeps `pytest`/`httpx` and the test suite out of the deployed image entirely |
| Co-located CSS per component | One `.css` file per page/component, plus a global `index.css` for shared tokens | Keeps styles tied to the component they affect; avoids orphaned styles and global CSS collisions |

---

## Future Enhancements (Out of Scope)

- **Frontend containerization** — Dockerfile and Nginx configuration for serving the production React build as a container
- **Database migrations** — Alembic integration for managing schema changes over time without dropping and recreating tables
- **CI/CD pipeline** — GitHub Actions workflow to run tests and build Docker images on every push
- **Production deployment** — deploying the Docker Compose stack to a cloud provider (e.g. Railway, Render, or a VPS)
