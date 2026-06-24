# Flashcard & Spaced Repetition Study App

A full-stack spaced repetition flashcard application built with 
FastAPI, PostgreSQL, React, and Docker.

> Currently in development — documentation and implementation in progress.

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