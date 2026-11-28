# RideDesk

Booking and AI intake system for small service businesses. Angular, FastAPI, Postgres, Claude.

> Work in progress. The full README (pitch, architecture, design decisions, demo script) lands with the last story in [`specs/ridedesk/backlog.md`](specs/ridedesk/backlog.md).

## Run locally

With Docker:

```bash
docker compose up --build
curl http://localhost:8000/v1/health
```

The API docs are at <http://localhost:8000/v1/docs>.

Without Docker (needs Python 3.12, [uv](https://docs.astral.sh/uv/) and a Postgres 16 server):

```bash
cd backend
cp ../.env.example .env        # then point the URLs at your Postgres
uv sync
uv run alembic upgrade head
uv run uvicorn --factory ridedesk.main:create_app --reload
```

## Checks

```bash
cd backend
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest                  # needs RIDEDESK_TEST_DATABASE_URL, see .env.example
```

The test suite creates its own throwaway database on the server named by `RIDEDESK_TEST_DATABASE_URL`, migrates it, and drops it at the end.

## Configuration

Nothing about a particular business lives in code. Each business points at a **vertical**, a default config in `backend/verticals/<vertical>.yaml` (car service is the first). Its own changes are stored in the database and merged on top. The result is validated against one Pydantic schema (`backend/ridedesk/config/schema.py`), on load and before any change is saved. A bad value is reported by its path, for example `pricing.per_mile: Input should be a valid decimal`.

Every external service (maps, calendar, email, SMS, payments, the LLM) sits behind an interface in `backend/ridedesk/adapters/`, with a mock that needs no keys. `RIDEDESK_<SERVICE>_PROVIDER` picks the implementation, and every implementation must pass the same contract tests in `backend/tests/contracts/`.
