# Backlog: RideDesk

## Status

**State:** in progress
**Updated:** 2026-11-23
**Now:** S-1 PR #1 open, waiting for merge.
**Done:** Stories written from the build prompt's phases 1 to 9. Backlog approved 11/23/2026. One Notion Action Task per story, each under the RideDesk project and the parent task "RideDesk: backlog and build".
**Next:** S-2 (vertical config schema, loader and adapter interfaces) once S-1 merges.
**Blockers:** S-19 is blocked on the website URL and platform (see `project.md`, Needs from people).
**Notes:** Tickets: the Notion Action Task "RideDesk: backlog and build" tracks the project. Each story also has its own Notion Action Task, linked on its Ticket line. Stories are not mirrored as GitHub issues. Phase grouping: phase 1 is S-1 to S-3, phase 2 is S-4, phase 3 is S-5 to S-9, phase 4 is S-10, phase 5 is S-11 to S-14, phase 6 is S-15 and S-16, phase 7 is S-17, phase 8 is S-18 and S-19, and phase 9 is S-20.

## Stories

### S-1: Backend skeleton, Docker Compose and CI
Tier: Standard · Depends on: none · Status: in progress (PR open) · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881d0baf2ca682586a556) · PR: https://github.com/MalTarDesigns/ridedesk/pull/1
Setup story.
Outcome: A developer can clone the repo and start the API and Postgres with one command, and every later PR runs lint, type checks and tests in CI.

Acceptance criteria:
- S-1.AC-1: `docker compose up` starts the FastAPI backend and Postgres, and `GET /v1/health` returns 200 with the database reachable.
- S-1.AC-2: Alembic runs the first migration, which creates the `businesses` table. Every later table carries a `business_id` foreign key.
- S-1.AC-3: `pytest` passes locally and in GitHub Actions, along with ruff and mypy (strict) on the backend.
- S-1.AC-4: `.env.example` lists every env var with a placeholder, and no real secret is in the repo.

Subtasks:
- [x] Add a `backend/` FastAPI app with a settings module that reads env vars through pydantic-settings
- [x] Add SQLAlchemy 2 models, the Alembic setup and the first migration (`businesses`)
- [x] Add `docker-compose.yml` with backend and Postgres services and a dev volume
- [x] Add the pytest setup with a test database fixture and the health endpoint test
- [x] Add a GitHub Actions workflow running ruff, mypy and pytest on each PR
- [x] Add `.env.example`, `.gitignore` and a minimal README "Run locally" section

### S-2: Vertical config schema, loader and adapter interfaces
Tier: Standard · Depends on: S-1 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881889846e1c5cab545ed) · PR: none
Setup story.
Outcome: The core reads all business rules from `verticals/car_service.yaml` plus database overrides, and every external service has an interface with a working mock.

Acceptance criteria:
- S-2.AC-1: `verticals/car_service.yaml` loads into a Pydantic config model, and an invalid file fails with an error that names the field.
- S-2.AC-2: Per-business overrides stored in the database merge over the YAML defaults, and the merged result is validated again.
- S-2.AC-3: Maps, calendar, email, SMS, payment and LLM interfaces each have a mock implementation, selected by env var.
- S-2.AC-4: A shared contract test suite runs against each adapter implementation and passes for every mock.

Subtasks:
- [ ] Define the config schema (business profile, trip types, form fields, pricing rules, payment methods, templates, agent settings, reminder and report settings)
- [ ] Write `verticals/car_service.yaml` with placeholder values marked as placeholders
- [ ] Add the `business_config_overrides` table and the merge-then-validate loader
- [ ] Define the six adapter interfaces and their mocks
- [ ] Add a parametrized contract test suite per interface
- [ ] Add a check that the core package never imports anything vertical-specific

### S-3: Pricing engine, availability, flags and the booking API
Tier: Standard · Depends on: S-2 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc88112835adb47b96c5d9f) · PR: none
Outcome: A client can request a quote and create a booking through the versioned API, with a correct quote from config and rule-based flags.

Acceptance criteria:
- S-3.AC-1: `POST /v1/businesses/{id}/quotes` returns a quote computed from config plus distance, covering base, per mile, hourly minimum, airport flat rates, after-hours surcharge and gratuity. Each rule has a unit test.
- S-3.AC-2: `POST /v1/businesses/{id}/bookings` validates against the configured form fields, checks availability through the calendar adapter, and saves the booking with status `requested`.
- S-3.AC-3: Rule-based flags (large group, last-minute, long distance, after-hours, missing info) are computed and stored on the booking, with thresholds from config.
- S-3.AC-4: Bookings record their source (`online` or `phone`) and timestamps for created, first response and approved, so response time can be reported later.
- S-3.AC-5: The OpenAPI document at `/v1/docs` lists both endpoints with request and response schemas.

Subtasks:
- [ ] Add the `bookings` model and migration (with an optional `driver_id`, a source, a status and the timestamps)
- [ ] Add the pricing engine as pure functions with table-driven tests
- [ ] Add the availability check through the calendar adapter
- [ ] Add the rule-based flag evaluator driven by config
- [ ] Add the quote and booking endpoints with API tests
- [ ] Document the API versioning approach in the README

### S-4: Claude free-text parser with fallback and call logging
Tier: Standard · Depends on: S-3 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8818eb446e9730abd603b) · PR: none
Outcome: Free text such as "Mr. Smith, JFK pickup Fri 9pm, 4 people plus golf bags, Escalade, $180, paying Zelle" becomes booking fields with a confidence for each, and nothing breaks when the AI call fails.

Acceptance criteria:
- S-4.AC-1: `POST /v1/businesses/{id}/intake/parse` returns booking fields, a confidence per field, and a list of missing or unclear fields, validated by a Pydantic model.
- S-4.AC-2: Bad JSON from the model is retried once, then the endpoint returns an empty parse with `fallback: true` and not an error.
- S-4.AC-3: Relative dates ("next Fri") resolve against the business's timezone, and a test covers it.
- S-4.AC-4: Every LLM call is saved to `ai_calls` with the input, output, tokens, latency, cost and status.
- S-4.AC-5: Tests run against the mock LLM adapter only, and no test needs an API key.

Subtasks:
- [ ] Add the Anthropic adapter (model from env var) next to the existing mock
- [ ] Define the parse output schema and the prompt, built from the vertical's agent config
- [ ] Add retry-then-fallback handling
- [ ] Add the `ai_calls` table and a logging wrapper around the LLM adapter
- [ ] Add the parse endpoint with tests for good output, bad JSON, timeout and low confidence

### S-5: Angular app, owner login and the bookings dashboard
Tier: Full · Depends on: S-3 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8814990ddeafbea22daaf) · PR: none
Outcome: The owner logs in on his phone and sees his bookings in a list and on a calendar, and can open a booking's detail screen.

Acceptance criteria:
- S-5.AC-1: An Angular workspace (latest stable, standalone components, signals, new control flow, strict TypeScript) builds and runs in Docker Compose next to the backend.
- S-5.AC-2: The owner logs in with a single owner account. Dashboard API routes reject requests that are not logged in, and a test proves it.
- S-5.AC-3: The bookings list and calendar view load from the API and work at a 375px phone width (screenshot proof).
- S-5.AC-4: Unit tests and a Playwright login-and-list test run in CI.
- S-5.AC-5: The README says whether Angular Material or Tailwind was chosen, and why.

Subtasks:
- [ ] Choose Angular Material or Tailwind and record the reason
- [ ] Create the `frontend/` workspace with the dashboard app and an API client service
- [ ] Add owner auth on the backend (hashed password, session or token) and a login screen
- [ ] Build the bookings list, the calendar view and the booking detail screen, mobile first
- [ ] Add the unit test runner and Playwright, and wire both into CI

### S-6: Manual booking form and quick-add
Tier: Standard · Depends on: S-4, S-5 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8815e9b3cce00c75c12a5) · PR: none
Outcome: The owner enters a phone booking in seconds by typing or dictating it, reviews the pre-filled form and taps Book. A plain manual form always works.

Acceptance criteria:
- S-6.AC-1: The quick-add box on the dashboard home sends text to the parse endpoint and opens the booking form pre-filled, with missing or low-confidence fields highlighted.
- S-6.AC-2: The form shows the calculated quote and the availability result. When the owner enters his own price, his price is saved and the difference is logged.
- S-6.AC-3: A phone booking is saved as confirmed, with no approval step, and the owner can choose to send a confirmation or not.
- S-6.AC-4: When parsing fails, the form opens with whatever text it has, and the manual form works with AI turned off (Playwright test).
- S-6.AC-5: An optional mic button uses the Web Speech API where the browser supports it, and is hidden where it does not.

Subtasks:
- [ ] Build the booking form, driven by the configured form fields
- [ ] Add the quick-add box and the pre-fill flow with confidence highlighting
- [ ] Add the price override with a logged difference
- [ ] Add the optional Web Speech button
- [ ] Add Playwright tests for quick-add, AI failure and manual entry

### S-7: Drivers and driver assignment
Tier: Standard · Depends on: S-5 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881499a63f7a8a9a975b1) · PR: none
Outcome: The owner keeps a driver list, assigns a driver to a ride in one tap, and sees which upcoming rides still need one.

Acceptance criteria:
- S-7.AC-1: Settings has a driver list (name, phone, email, active) with add, edit and deactivate.
- S-7.AC-2: The booking detail screen assigns or changes the driver in one tap.
- S-7.AC-3: The dashboard has an Unassigned filter, and a warning badge appears on rides inside the configured window (default 24 hours) that have no driver.
- S-7.AC-4: API and component tests cover assignment and the warning window.

Subtasks:
- [ ] Add the `drivers` model, migration and endpoints
- [ ] Build the driver list in Settings
- [ ] Add one-tap assignment on the booking detail screen
- [ ] Add the Unassigned filter and the warning badge, with the window from config
- [ ] Add tests

### S-8: Online request inbox and approval gate
Tier: Standard · Depends on: S-4, S-5 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8817abcddf83922ae08ec) · PR: none
Outcome: The owner sees new online requests with their flags and quote, and approves, edits or declines each one. Nothing reaches a customer without his approval.

Acceptance criteria:
- S-8.AC-1: The inbox lists `requested` bookings with their rule-based flags, the calculated quote and the template confirmation text.
- S-8.AC-2: Approve, edit-then-approve and decline each move the booking to the right status and record the first-response time.
- S-8.AC-3: For requests that match the configured "unusual" rules, Claude drafts a reply and suggests flags. Both are shown as suggestions and are never sent or applied automatically.
- S-8.AC-4: A test proves that no outbound message is created for a request until it is approved.

Subtasks:
- [ ] Add the inbox endpoint and screen
- [ ] Add the approve, edit and decline actions with status rules
- [ ] Add the reply-drafting and flag-suggestion prompts, behind the LLM adapter and logged
- [ ] Add tests for the gate and for AI failure

### S-9: Settings page with validated overrides
Tier: Standard · Depends on: S-5 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881e59df9ca414fad787b) · PR: none
Outcome: The owner changes his prices, payment handles, hours and message wording from his phone, and bad values are rejected with a clear message.

Acceptance criteria:
- S-9.AC-1: Settings edits prices, payment method handles, business hours and message templates, and nothing else in v1.
- S-9.AC-2: Saving validates the merged config against the schema. An invalid value is rejected with a field-level error, and the old config stays in place.
- S-9.AC-3: A changed price changes the next quote, proven by an API test.

Subtasks:
- [ ] Add the config read and write endpoints for the allowed sections
- [ ] Build the Settings forms, mobile first
- [ ] Show field-level validation errors from the backend
- [ ] Add tests

### S-10: Embeddable booking widget
Tier: Full · Depends on: S-3 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc88125bae6fd876236255f) · PR: none
Outcome: Any website can add a script tag and get a booking widget that takes its branding and fields from the API, shows an instant quote, and confirms the request.

Acceptance criteria:
- S-10.AC-1: The widget builds as an Angular Element (a custom element) into one script bundle, and a plain HTML test page embeds it with a single script tag.
- S-10.AC-2: It loads the business's branding and form fields from the API at load time, so one build serves any business.
- S-10.AC-3: The customer sees an instant estimated quote, submits the request, and sees a "request received" confirmation.
- S-10.AC-4: Styles do not leak into or out of the host page, proven by a screenshot on a deliberately hostile test page.
- S-10.AC-5: A Playwright test books through the embedded widget end to end.

Subtasks:
- [ ] Add a public config endpoint (branding and fields only, no secrets)
- [ ] Create the widget project and the Angular Element build
- [ ] Build the config-driven form, the quote display and the confirmation
- [ ] Isolate styles (Shadow DOM or scoped CSS) and test on a hostile page
- [ ] Add CORS settings per business and the Playwright test
- [ ] Document the embed snippet

### S-11: Confirmations, notifications and templates
Tier: Standard · Depends on: S-8 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8810988aede05fbb3b35a) · PR: none
Outcome: On approval the customer gets a confirmation built from a template, and the owner can send ride details to the assigned driver.

Acceptance criteria:
- S-11.AC-1: Approving a request sends a confirmation by email through the email adapter (mock by default, a real provider behind an env flag).
- S-11.AC-2: Message text comes from the config templates, and a test renders each message type.
- S-11.AC-3: A per-booking toggle sends ride details to the assigned driver by SMS or email.
- S-11.AC-4: Every sent message is stored, so the dashboard shows what went out and when.

Subtasks:
- [ ] Add the template renderer and the `messages` table
- [ ] Add the confirmation send on approval and on phone booking (when chosen in S-6)
- [ ] Add the driver notification with its toggle
- [ ] Add a real email provider adapter behind an env flag, passing the contract tests
- [ ] Add tests

### S-12: Manual payments and payment tracking
Tier: Standard · Depends on: S-11 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881c6bbbfc7d3954fb0d0) · PR: none
Outcome: The confirmation tells the customer how to pay by Zelle, Cash App, Venmo, cash or check, and the owner marks a payment received in one tap.

Acceptance criteria:
- S-12.AC-1: Each manual method is turned on or off and configured (display name, instructions, handle, QR image, deposit percent, whether it counts as instant).
- S-12.AC-2: The confirmation lists the enabled methods with a payment reference code (the booking number) for the memo.
- S-12.AC-3: The owner marks a payment received in one tap, with amount, method and an optional note, and the booking moves through unpaid, deposit paid, paid in full or refunded.
- S-12.AC-4: Adding a new manual method needs only an adapter and config, proven by a test that registers a fake method without touching core code.

Subtasks:
- [ ] Add the `payments` model and the payment status rules
- [ ] Add the manual payment adapter and the method config
- [ ] Add the payment instructions to the confirmation template
- [ ] Add the mark-paid action and screen
- [ ] Add tests, including the fake-method test

### S-13: Stripe payments
Tier: Standard · Depends on: S-12 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881a69da0e7497e5c0ec7) · PR: none
Outcome: A customer can pay by card through a Stripe payment link, and the booking is marked paid automatically.

Acceptance criteria:
- S-13.AC-1: When Stripe is enabled, the confirmation includes a Stripe payment link for the deposit or the full amount, in test mode.
- S-13.AC-2: The Stripe webhook verifies the signature and marks the booking paid. A replayed event is handled once (idempotent).
- S-13.AC-3: The Stripe adapter passes the same payment contract tests as the manual adapter.
- S-13.AC-4: Tests use Stripe fixtures, and no test calls Stripe live.

Subtasks:
- [ ] Add the Stripe adapter (payment link creation)
- [ ] Add the webhook endpoint with signature checks and idempotency
- [ ] Run the contract tests against it
- [ ] Document the Stripe test-mode setup in the README

### S-14: Day-before reminders
Tier: Standard · Depends on: S-11 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc88170a085fc34f153d75a) · PR: none
Outcome: Customers get a reminder the day before their ride, approved by the owner at first and automatic once he turns that on.

Acceptance criteria:
- S-14.AC-1: A scheduled job finds rides due inside the reminder window from config and creates reminder messages.
- S-14.AC-2: With the default setting, reminders wait in the inbox for approval. With auto-send on, they send without approval.
- S-14.AC-3: A ride never gets two reminders, proven by a test that runs the job twice.
- S-14.AC-4: The job runs from an HTTP endpoint guarded by a secret, so Cloud Scheduler can call it in production.

Subtasks:
- [ ] Add the reminder job and its endpoint
- [ ] Add the approval or auto-send setting
- [ ] Add idempotency on reminders
- [ ] Add tests

### S-15: Weekly report
Tier: Standard · Depends on: S-12 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc88189bc84db360c4213df) · PR: none
Outcome: The owner sees each week's bookings, revenue and response time in the dashboard, which also gives the case study its numbers.

Acceptance criteria:
- S-15.AC-1: The report shows the week's bookings, estimated revenue, revenue by payment method, bookings by trip type and by source, busiest days, average response time, and rides per driver.
- S-15.AC-2: Every number comes from a plain query, and tests check them against seeded data.
- S-15.AC-3: An optional plain-English summary from Claude sits at the top, and the report still renders when the AI call fails.

Subtasks:
- [ ] Add the report queries and endpoint
- [ ] Build the report screen, mobile first
- [ ] Add the optional AI summary behind the LLM adapter
- [ ] Add seeded-data tests

### S-16: Weekly report PDF export
Tier: Fix · Depends on: S-15 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8810e8fe8d97240260c6c) · PR: none
Outcome: The owner downloads the weekly report as a PDF. This is the first story to cut if the timebox runs short.

Acceptance criteria:
- S-16.AC-1: An export button downloads a PDF with the same numbers as the screen.
- S-16.AC-2: A test checks that the PDF is created and contains the week's totals.

Subtasks:
- [ ] Add the PDF rendering endpoint
- [ ] Add the export button
- [ ] Add the test

### S-17: Evals and the AI call log viewer
Tier: Standard · Depends on: S-4, S-8 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881c9a7ebd8871603ee90) · PR: none
Outcome: The parser's accuracy is measured per field on 30 realistic samples, and the owner can see every AI call in the dashboard.

Acceptance criteria:
- S-17.AC-1: `evals/` holds 30 samples (shorthand, typos, relative dates, missing fields, multiple stops, price and payment mentioned or not, spam), each with expected fields and an expected missing-field list.
- S-17.AC-2: One command runs the evals and prints accuracy per field, plus a table the README can include.
- S-17.AC-3: A GitHub Actions workflow runs the evals on manual trigger only.
- S-17.AC-4: The dashboard lists AI calls with input, output, tokens, latency and cost.

Subtasks:
- [ ] Write the 30 samples and their expected output
- [ ] Add the eval runner and the per-field scoring
- [ ] Add the manual-trigger workflow
- [ ] Build the AI call log screen
- [ ] Put the first results table in the README

### S-18: Production deploy
Tier: Standard · Depends on: S-10, S-13, S-14 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc881798d7ce875f54a3249) · PR: none
Outcome: The API, dashboard and widget run in production, deployed by GitHub Actions, and every step is documented.

Acceptance criteria:
- S-18.AC-1: The choice between Cloud SQL and Neon is recorded with its reason, and is approved before any paid resource is created.
- S-18.AC-2: A GitHub Actions workflow builds the images and deploys to Cloud Run on merge to `main`, and migrations run as part of the deploy.
- S-18.AC-3: The production health endpoint returns 200, and the dashboard login works on the live URL (proof captured).
- S-18.AC-4: `docs/deploy.md` lists every step, from an empty project to a live deploy.
- S-18.AC-5: The Cloud Scheduler job for reminders is set up and has called the reminder endpoint once.

Subtasks:
- [ ] Write production Dockerfiles for the backend and the frontend
- [ ] Decide the database host and get approval
- [ ] Add the deploy workflow with secrets from GitHub environments
- [ ] Set up Cloud Run, the database, the scheduler and secrets (each behind approve-action)
- [ ] Write `docs/deploy.md`

### S-19: Live embed on Justified Transport's site
Tier: Standard · Depends on: S-18 · Status: blocked, waiting on Justin for the website URL and platform · Ticket: [Notion](https://app.notion.com/p/421cb0375bc8818e8b8ef81647f1e414) · PR: none
Outcome: Customers can book from the widget on Justified Transport's live website.

Acceptance criteria:
- S-19.AC-1: The widget renders and submits a test booking on the live site (screenshot proof).
- S-19.AC-2: The business's real config (prices, vehicle classes, hours, payment methods, drivers) is loaded, replacing the placeholders.
- S-19.AC-3: Production CORS allows only the business's domain.
- S-19.AC-4: The steps for that site platform are documented.

Subtasks:
- [ ] Load the real business config
- [ ] Add the embed snippet to the site (behind approve-action, since it changes a live site)
- [ ] Lock CORS to the site's domain
- [ ] Run a test booking end to end, then remove it

### S-20: README, diagrams and the demo script
Tier: Standard · Depends on: S-17, S-18 · Status: todo · Ticket: [Notion](https://app.notion.com/p/421cb0375bc88176a62fd1580a9a071e) · PR: none
Outcome: A recruiter, a hiring manager and a business owner can each understand RideDesk from the README in a few minutes.

Acceptance criteria:
- S-20.AC-1: The README has every section in the build prompt's "README must include" list: the two pitches, a Mermaid architecture diagram, screenshots or a GIF on mobile, a local run in 5 commands or fewer, the eval results table, design decisions, adding a vertical, adding a payment method, using the API from another app, and the demo script.
- S-20.AC-2: The local run steps work from a fresh clone, proven by running them.
- S-20.AC-3: The cost-per-booking estimate is computed from real `ai_calls` data, not guessed.

Subtasks:
- [ ] Write the pitches and the design decisions section
- [ ] Draw the Mermaid architecture diagram
- [ ] Capture mobile screenshots or a GIF of the widget and dashboard
- [ ] Write the "adding a vertical" (funeral home), "adding a payment method" and "using the API" sections
- [ ] Write the 2-minute demo script
- [ ] Test the local run steps from a fresh clone

## Out of scope

- Driver GPS tracking: excluded by the build prompt.
- Live dispatch or routing: excluded by the build prompt.
- A driver app or driver accounts: excluded. Drivers are a contact list in v1.
- Fleet maintenance: excluded by the build prompt.
- A second vertical (funeral home): v1 ships car service only. S-20 documents how to add one.
- Multiple owner accounts and roles: v1 has a single owner account.
- Settings beyond prices, payment handles, hours, drivers and message wording: cut for v1.
- The Loom demo recording and the /agencies case study write-up: owned by Jamal, outside the repo.
