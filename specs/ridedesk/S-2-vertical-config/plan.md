# S-2 plan: Vertical config schema, loader and adapter interfaces

## Status

**State:** verifying
**Updated:** 2026-11-28
**Now:** Opening the PR and waiting for CI.
**Done:** Tasks 1 to 7. Both review rounds fixed (see Notes). Verify green: ruff, ruff format, mypy strict, pytest 58 passed. Smoke run resolved the `car_service` config and applied an override (`tmp/s2-smoke.txt`). Migration `0002` backfills an existing business and downgrades cleanly (`tmp/s2-migration-backfill.txt`). mypy rejects a provider with the wrong signature (`tmp/s2-mypy-probe.txt`).
**Next:** Address the second review, commit, open the PR, and confirm CI.
**Blockers:** None.
**Notes:** The config file lives at `backend/verticals/car_service.yaml`, not at the repo root, so the backend container (which mounts `./backend`) and the tests can read it. Every value in it is a placeholder until Justin sends real prices, vehicle classes, hours and payment handles (see `project.md`, Needs from people).

Changes from review, round 1:
- Times must be quoted strings. YAML reads an unquoted `22:00` as the number 1320, which would otherwise validate as 00:22. Times with a timezone are rejected.
- Cross-section rules (a price for every vehicle class, select options, unique days, unique keys) run in a model validator, so they hold however `BusinessConfig` is built, and each problem carries its own field path.
- Opening hours may run past midnight: a close at or before the open ends the next day, and 00:00 to 00:00 means 24 hours.
- The registry is one typed table per interface, so mypy rejects a provider with the wrong signature. Constructors take `Settings`, and a real provider without its key raises `ProviderNotConfiguredError`, which the contract tests skip.
- `CalendarProvider` methods take a `calendar_id`, so each business has its own availability.
- `PaymentProvider` only creates online payment links (`create_link`). Instructions for manual methods (Zelle, Cash App, cash, check) are built from the config in core code in S-12.
- Overrides are stored in JSON form and saved with an upsert. The setting is renamed to `RIDEDESK_PAYMENTS_PROVIDER`.
- `profile.timezone` was removed: `businesses.timezone` is the one source of truth.
- Migration `0002` adds `vertical` as nullable, backfills `car_service`, then requires it.

Decided now, built later:
- Adapters are synchronous. FastAPI runs sync handlers in a thread pool, and the load is small.
- LLM failures need the raw output and token counts for logging and retry: S-4.
- A production guard that refuses `mock` providers: S-11, before real email goes out, and S-18.
- Validating the timezone name: when the business record is first written through the API.
- The contact email format check (needs `email-validator`): S-9.
- Optimistic concurrency on overrides, and the effect of whole-list replacement on payment methods: S-9.

## Approach

**1. One config model per business.** `ridedesk/config/schema.py` defines `BusinessConfig`, a Pydantic model with these sections:

| Section | Holds |
|---|---|
| `profile` | Name, logo URL, brand colors, fonts, contact details, timezone, weekly hours, service area |
| `vehicle_classes` | Key, label, passenger and luggage capacity |
| `trip_types` | Key and label (airport, hourly, event, point to point, corporate) |
| `form_fields` | Key, label, type, required, options, order |
| `pricing` | Currency, base fare per vehicle class, per mile, hourly rate and minimum hours, airport flat rates, after-hours window and surcharge, gratuity percent |
| `flags` | Thresholds for large group, last-minute, long distance and after-hours |
| `payment_methods` | Key, kind (`manual` or `automatic`), display name, instructions, handle, QR image URL, deposit percent, instant, enabled |
| `templates` | Subject and body per message type |
| `agent` | Tone, instructions, labels, the flags it may suggest, and which actions need approval |
| `reminders`, `reports` | Hours before a ride, auto-send, and report metrics |

- Every model uses `extra="forbid"`, so a typo in a key fails rather than being ignored silently.
- Money uses `Decimal`, never `float`.
- Cross-field rules are validated too. For example, every `pricing.base_fare` key must be a known vehicle class, and every form field key must be unique.
- A top-level `placeholder: true` marks a config that still holds made-up values. Later stories can warn the owner while it is set.

**2. Loader with readable errors.** `ridedesk/config/loader.py`:

- `load_vertical(name)` reads `verticals/<name>.yaml` with `yaml.safe_load`.
- `resolve_config(session, business)` deep-merges the business's stored overrides over the vertical defaults, then validates the result. Mappings merge key by key. Lists replace whole, because merging lists item by item is ambiguous.
- `save_overrides(session, business_id, overrides)` validates the merged result before it writes anything, so an invalid override is never stored. This is the hook S-9's Settings page will call.
- Validation failures raise `ConfigError`. Its message names the source and every bad field by dotted path, for example `car_service.yaml: pricing.per_mile: Input should be a valid decimal`.

**3. Data model.** Migration `0002` does two things:

- It adds `businesses.vertical`, which is required and has no default.
- It creates `business_config_overrides`, with one row per business: `business_id` (via `TenantMixin`, unique), `data` (JSONB) and timestamps.

**4. Six adapter interfaces, each with a mock.** `ridedesk/adapters/<name>.py` holds a `typing.Protocol`, small Pydantic request and result models, and a `Mock` implementation:

| Interface | Methods (only what later stories need) | Mock behaviour |
|---|---|---|
| `MapsProvider` | `distance(origin, destination) -> Route` (miles, minutes) | Deterministic distance from a hash of the two strings |
| `CalendarProvider` | `is_free(calendar_id, start, end) -> bool`, `add_event(...)`, `remove_event(calendar_id, id)` | In-memory events, kept apart per calendar |
| `EmailSender` | `send(EmailMessage) -> SendResult` | Records the message in an outbox list |
| `SmsSender` | `send(SmsMessage) -> SendResult` | Records the message in an outbox list |
| `PaymentProvider` | `create_link(amount, currency, reference) -> PaymentLink` (URL and provider reference). Online card payments only | Returns a fake https link with a unique provider reference |
| `LlmClient` | `complete_json(system, user, schema) -> LlmResult` (parsed object, tokens, latency) | Returns a canned response registered by the test |

`ridedesk/adapters/registry.py` maps a provider name to its class for each interface. Settings choose the provider through `RIDEDESK_MAPS_PROVIDER`, `RIDEDESK_CALENDAR_PROVIDER`, `RIDEDESK_EMAIL_PROVIDER`, `RIDEDESK_SMS_PROVIDER`, `RIDEDESK_PAYMENTS_PROVIDER` and `RIDEDESK_LLM_PROVIDER`, all defaulting to `mock`. An unknown name fails at startup, and the error lists the valid names.

**5. Contract tests.** `tests/contracts/` has one suite per interface, parametrized over every implementation in the registry. When a real adapter is added later (Anthropic in S-4, an email provider in S-11, Stripe in S-13), registering it is enough to put it under the same suite. Real adapters that need a key skip unless the key is set.

**6. Core stays vertical-free.** A test parses every module under `ridedesk/` with `ast` and fails if any of them imports from `verticals` or contains the literal `car_service`. The vertical is data. Code never names it.

## Files

| Path | What |
|---|---|
| `backend/ridedesk/config/schema.py`, `loader.py`, `__init__.py` | Config model, loader, `ConfigError` |
| `backend/verticals/car_service.yaml` | Placeholder defaults for the car service vertical |
| `backend/ridedesk/models/config_override.py` | `BusinessConfigOverride` model |
| `backend/ridedesk/models/business.py` | Adds `vertical` |
| `backend/migrations/versions/0002_*.py` | `businesses.vertical` and `business_config_overrides` |
| `backend/ridedesk/adapters/{maps,calendar,messages,payments,llm,registry}.py` | Interfaces, mocks, registry (email and SMS share `messages.py`) |
| `backend/ridedesk/settings.py` | Provider settings and `verticals_dir` |
| `backend/tests/test_config_schema.py`, `test_config_loader.py`, `test_adapter_registry.py`, `test_core_is_vertical_free.py` | Unit and database tests |
| `backend/tests/contracts/` | One contract suite per interface |
| `backend/pyproject.toml`, `uv.lock` | Adds `pyyaml` and `types-PyYAML` |
| `.env.example`, `README.md` | Provider variables, and a short "Configuration" section |

## Tasks

1. Config schema with tests for a valid file, an unknown key, a bad type and the cross-field rules (test first).
2. `car_service.yaml` with placeholder values, plus a test that it loads and is marked as a placeholder.
3. Migration `0002`, the override model, and `resolve_config` / `save_overrides`, with database tests for merging, list replacement and an invalid override being rejected with nothing stored (test first).
4. The six interfaces and their mocks, plus the registry and provider settings, with tests for env selection and an unknown name.
5. Contract suites per interface, run against every registered implementation.
6. The vertical-free core check.
7. `.env.example` and the README "Configuration" section.

## Verify

- Locally: ruff, ruff format, mypy strict and pytest all green against the `tmp/` Postgres cluster.
- `uv run python -c` loads `car_service.yaml` through the loader and prints the validated config, as a smoke check.
- On the PR: both CI jobs green, and `test_models_match_migrations` passes with migration `0002`.
