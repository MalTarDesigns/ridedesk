# S-1 plan: Backend skeleton, Docker Compose and CI

## Status

**State:** verifying
**Updated:** 2026-11-23
**Now:** Code review by `maltar:code-reviewer`.
**Done:** Tasks 1 to 7. Local verify green: ruff check, ruff format --check, mypy strict, pytest (7 passed). uvicorn started against the `tmp/` cluster and `/v1/health` returned 200 (`tmp/s1-health-local.txt`).
**Next:** Address review findings, commit, open the PR, and confirm both CI jobs are green.
**Blockers:** None.
**Notes:** Docker is not installed on the development laptop. Local checks run against a throwaway Postgres 16 cluster started with `initdb` under `tmp/` (no root needed). S-1.AC-1 (`docker compose up`) is proven by a CI job that starts the stack and calls the health endpoint, and that job's log is the proof. The secret-scan pattern `sk_test` gives a false positive on `ridedesk_test_` in `tests/conftest.py`. Installing `httpx2`, which a Starlette deprecation warning suggests, was blocked by the auto-mode classifier, so `httpx` stays and the warning is left visible.

## Approach

A small, conventional FastAPI service under `backend/`, managed with `uv` on Python 3.12.

- **Database access** uses SQLAlchemy 2 in sync mode with psycopg 3. FastAPI runs sync endpoints in a thread pool, which is plenty for this load. Async would add complexity without a measurable benefit, and this can change later behind the session dependency.
- **Settings** come from env vars through pydantic-settings, with a `RIDEDESK_` prefix (for example `RIDEDESK_DATABASE_URL`).
- **Multi-tenancy.** A `TenantMixin` adds a non-null, indexed `business_id` foreign key to `businesses.id`. A test walks the SQLAlchemy metadata and fails if any table other than `businesses` lacks `business_id`. That makes the rule from S-1.AC-2 a check, not a convention.
- **Migrations.** Alembic, with the first migration creating `businesses` (UUID `id`, unique `slug`, `name`, `timezone`, `created_at`, `updated_at`). A test runs `alembic upgrade head` against a fresh database, then compares the models with the database so the two cannot drift.
- **Health.** `GET /v1/health` runs `SELECT 1`. It returns 200 `{"status": "ok", "database": "ok"}`, or 503 `{"status": "degraded", "database": "unreachable"}` when the database cannot be reached. Routes live under a `/v1` router from day one, so versioning is set before the first real endpoint.
- **Tests.** pytest, with a session fixture that creates a throwaway database from `RIDEDESK_TEST_DATABASE_URL`, migrates it, and drops it afterwards.
- **Docker Compose** runs `db` (`postgres:16`, with a healthcheck and a named volume) and `backend` (which waits for `db` to be healthy, runs migrations, then starts uvicorn with reload and the source mounted).
- **CI** (GitHub Actions, on every PR and on pushes to `main`) has two jobs. `backend` runs `ruff check`, `ruff format --check`, `mypy --strict` and `pytest` against a Postgres service container. `compose-smoke` runs `docker compose up -d --wait` and calls `/v1/health`.

## Files

| Path | What |
|---|---|
| `backend/pyproject.toml`, `backend/uv.lock` | Dependencies, plus the ruff, mypy and pytest config |
| `backend/ridedesk/main.py` | App factory and the `/v1` router |
| `backend/ridedesk/settings.py` | pydantic-settings `Settings` |
| `backend/ridedesk/db.py` | Engine, session dependency, `Base`, `TenantMixin` |
| `backend/ridedesk/models/business.py` | `Business` model |
| `backend/ridedesk/api/v1/health.py` | Health endpoint |
| `backend/alembic.ini`, `backend/migrations/` | Alembic env and the first revision |
| `backend/tests/` | `conftest.py`, health, migration and tenant-rule tests |
| `backend/Dockerfile` | Dev image |
| `docker-compose.yml` | `db` and `backend` |
| `.github/workflows/ci.yml` | `backend` and `compose-smoke` jobs |
| `.env.example`, `.gitignore`, `README.md` | Placeholders, ignores (including `tmp/` and `.env`), "Run locally" |

## Tasks

1. Scaffold `backend/` with uv (FastAPI, SQLAlchemy, psycopg, Alembic, pydantic-settings; dev: pytest, httpx, ruff, mypy), with strict ruff and mypy config.
2. Settings, database module and `TenantMixin`, test-first with the tenant-rule test.
3. `Business` model and the first Alembic migration, test-first with the upgrade-and-compare test.
4. Health endpoint, test-first for both the 200 and the 503 cases.
5. Dockerfile and `docker-compose.yml`.
6. CI workflow with both jobs.
7. `.env.example`, `.gitignore` and the README "Run locally" section.

## Verify

- Locally: ruff, mypy and pytest are green against the `tmp/` Postgres cluster, and uvicorn is started and `/v1/health` called with curl.
- In CI on the PR: both jobs are green, and the `compose-smoke` log shows the 200 response (S-1.AC-1).
- A secret scan over the diff (grep for key-shaped strings) finds nothing (S-1.AC-4).
