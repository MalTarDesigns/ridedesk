# Project: RideDesk

## Status

**State:** in progress
**Updated:** 2026-11-23
**Now:** Backlog approved and mirrored to Notion (20 story tasks). Waiting for approve-start on S-1.
**Done:** Triage (Build, Project tier). Public repo `MalTarDesigns/ridedesk` created. Notion Action Task "RideDesk: backlog and build" opened and set to IN PROGRESS.
**Next:** Start S-1.
**Blockers:** None for S-1 to S-18. S-19 (live embed) is blocked on the website URL and platform.
**Notes:** Tickets live in Notion only, so stories are tracked in `backlog.md` and not mirrored as GitHub issues. The prompt's phases 1 to 9 are the grouping. Phases 3 and 5 were split because each is too big for one PR. Basic CI moved forward from phase 8 into S-1, so every story after it lands with lint, type checks and tests running.

## Goal

RideDesk is a booking and AI intake system for small service businesses. Its first user is Justified Transport, a luxury car service. It has three jobs:

1. Give Justified Transport a booking system the owner actually uses, both on his website and from his phone.
2. Serve as a case study for white-label AI automation work with marketing and web agencies.
3. Show hiring managers for Senior Angular and Applied AI / Forward Deployed Engineer roles a production-quality, full-stack AI system. Recruiters and interviewers will read this repo, so code quality, tests and docs count as much as features.

## Who it is for

- **The owner** runs the business from his phone. He takes many bookings by phone, approves online requests, assigns drivers later, and tracks payments.
- **Customers** book from a widget on the business's website.
- **Other apps and other businesses** reuse the engine through a versioned REST API and a config file per vertical.

## Key decisions (already made)

- **Stack:** the latest stable Angular (standalone components, signals, the new control flow syntax, strict TypeScript), with the booking widget built as an Angular Element. The backend is Python 3.12+, FastAPI, Pydantic v2, PostgreSQL with Alembic, and the Anthropic Python SDK. It runs in Docker and ships through GitHub Actions to Google Cloud Run. The stack does not change without asking.
- **Code first, AI only where input is messy.** Pricing, availability, validation, rule-based flags, messages, payments and reports are plain code. Claude does three things: it parses free text into booking fields, drafts replies for unusual requests, and suggests flags. AI never sets a price. Everything works when the AI call fails, by falling back to the normal form.
- **Owner quick-add.** The owner types or dictates a booking, Claude fills in the form, code computes the quote and checks availability, and he reviews it and taps Book. A plain manual form is always there. If he enters a price, his price wins, and the difference from the calculated quote is logged.
- **Driver is optional and empty at booking.** It is assigned later in one tap. The dashboard has an Unassigned filter and a warning badge on upcoming rides that have no driver.
- **Config-driven verticals.** Defaults live in `verticals/<vertical>.yaml`, and per-business overrides live in the database. Config is validated by a Pydantic schema. Car service is the only vertical in v1. A funeral home is next, so no car-service logic goes into the core.
- **Multi-tenant from day one.** Every record carries a `business_id`.
- **Adapters with mocks.** Maps, calendar, email, SMS, payments and the LLM each sit behind an interface, with a mock as the default. Every implementation of an interface passes the same contract tests.
- **Pluggable payments.** Stripe is automatic (a payment link plus a webhook). Zelle, Cash App, Venmo, cash and check are manual: the owner marks them paid.
- **Approval gate.** Online requests wait for the owner to approve them. Nothing AI-drafted reaches a customer without his approval. Phone bookings he enters himself skip the gate, because he is the one approving.
- **v1 Settings exposes only what the owner will change:** prices, payment handles, hours, drivers and message wording.

## Constraints

- **Timebox:** 2 weeks, 11/23/2026 to 12/07/2026. If phases 4 to 6 drag, cut the PDF export (S-16) first.
- **Built as a showcase of the engineer's own work.** Commits are small, with conventional messages. Commits and PRs carry no tool or AI attribution. Each story ships as its own reviewed PR.
- **Secrets** come from env vars only. The repo holds `.env.example` with placeholders and never a real key.
- **Model** name comes from an env var, defaulting to `claude-sonnet-5-5`.

## Out of scope

No driver GPS tracking, no live dispatch or routing, no driver app, no fleet maintenance. RideDesk covers booking, quoting, simple driver assignment, payment tracking and customer messages only.

## Risks and shaky assumptions

- **The timebox is tight.** 20 stories in 2 weeks is aggressive. The cut order is S-16 (PDF export), then the optional parts of S-11 (driver SMS) and S-15 (the AI summary).
- **Real business data has not arrived yet.** Placeholders in `verticals/car_service.yaml` keep the build moving, but the quote engine's tests should be re-run against real prices before go-live.
- **The website platform is unknown.** The Angular Element approach assumes the site accepts a custom script tag. Some hosted builders limit that, which would change S-19.
- **Hosting cost.** Cloud Run plus Cloud SQL has a monthly floor. Neon Postgres may be cheaper. S-18 decides, behind an approval before anything is created.

## Needs from people

| Input | Owed by | Needed for |
|---|---|---|
| Website URL and the platform it runs on | Justin | S-19, and confirms the S-10 embed approach |
| Real pricing: base, per mile, hourly minimum, airport flat rates, after-hours, gratuity | Justin | Go-live (placeholders until then) |
| Vehicle classes | Justin | Go-live (placeholders until then) |
| Service area and business hours | Justin | Go-live (placeholders until then) |
| Payment methods he accepts, with handles, and whether he takes deposits | Justin | S-12 real config |
| Driver list (name, phone) | Justin | S-7 real data |
| Google Business Profile status | Justin | Case study, not blocking |
| Anthropic API key for dev and prod | Jamal | S-4 live calls (mock until then) |
| Stripe test account keys | Jamal | S-13 |
| Email and SMS provider choice and keys | Jamal | S-11 real sending (mock until then) |
| Maps API key (distance) | Jamal | S-3 real distance (mock until then) |
| Google Cloud project, or a Neon account, for deploy | Jamal | S-18 |

## Deliverables outside the repo

These are owned by Jamal and are not stories: the 2-minute Loom demo (S-20 writes its script), and the case study write-up for the /agencies page.

## Case study metrics

The data model records them from S-3 onward, and S-15 reports them: bookings per week by source (online or phone quick-add), average response time to a request, and payments collected by method. Hours saved per week is reported by the owner and not measured by the system.

## Done means

- The repo has tests, CI and a README that meets the list in the build prompt.
- The widget is live on Justified Transport's site, and the owner dashboard is deployed.
- The owner has taken at least one real booking through it.
