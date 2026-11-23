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
