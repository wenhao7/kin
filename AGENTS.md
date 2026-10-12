# Project instructions

Kin is a hackathon submission (Nebius x NVIDIA Global AI Hackathon, Personal AI track, deadline 30 Oct 2026 10:00 PDT). The product is a private, always-on family care coordinator living in a Telegram group, with persistent memory and role × category boundaries enforced at retrieval. This repository is documentation-first: the docs are the specification, and the roadmap is the work queue.

## Read first, in this order

1. `README.md` — what it is, commands, stack.
2. `ROADMAP.md` — sequential deliverables D0–D9 with "done when" criteria. The next unchecked deliverable is the current task.
3. `docs/02-product.md` — roles, categories, flows, chat conventions.
4. `docs/03-privacy-boundaries.md` — the boundary model and enforcement rules; `config/policy.yaml` is its data.
5. `docs/04-safety.md` — organise-not-advise rules, grounding, consent.
6. `docs/05-architecture.md` — components, data model, flows, models, integrations (Hermes Agent, OpenShell/NemoClaw, Telegram, Tavily).
7. `docs/06-synthetic-data.md` and `docs/07-demo-plan.md` — demo family, documents, video.
8. `docs/00-hackathon.md` — requirements and judging criteria; `docs/08-submission-checklist.md` before submitting.
9. `KICKOFF.md` — one-time setup; items marked **YOU** need the human.

## How to work

- Take the next unchecked deliverable in `ROADMAP.md`. Finish it to its "done when", tick the checkbox in the same commit, and stop at a working state. Do not start a deliverable that would break the minimum submittable product once it exists (D0–D4).
- `make setup`, `make check` (or `make check-nospend`), `make policy`, `make lint`, `make test` must pass before a commit. CI runs `ruff` and `pytest`.
- Conventional commits (`feat:`, `fix:`, `docs:`, `build:`, `test:`, `chore:`, `refactor:`), small and focused, imperative subject ≤ 72 chars. Branch `main`; push after each deliverable.
- Keep docs factual and current. When implementation changes a spec in `docs/`, update the doc in the same commit. No decision logs or time estimates in docs; a dated `docs/decisions.md` may be started only when a spike reveals a real fork in the road.
- Secrets live in `.env` (git-ignored) and are passed to the Hermes container by compose. Never commit keys, tokens, `.env`, `data/`, or `hermes/home/`.
- Python ≥ 3.10 locally, 3.12 in Docker; `uv` manages the environment and `uv.lock` is committed. Add dependencies with `uv add` and commit the lock.

## Constraints that come from the hackathon

- Inference goes through **Nebius Token Factory** (MiniCPM-V 4.5 for photos/documents, standing in for Nemotron 3 Nano Omni until Token Factory lists it for our key; Nemotron Nano for classification and translation, Super for answers; Ultra capped). Hermes uses its first-class `nebius` provider. Do not substitute other model providers in the product path.
- Use the track's named tools where they fit: Hermes Agent (runtime, memory, skills, Telegram gateway), OpenShell/NemoClaw (sandbox, credential proxy, network allow-list; deferrable to D7 if it blocks D0), Nebius Serverless (optional, digests).
- Tavily must be called at runtime in the main flow (allow-listed public lookups) with `include_domains` from the locale pack; queries never contain family data.
- Apache-2.0 license file stays at the root and visible on GitHub.
- Credits are limited (~$50): vision model/Nano for volume, Super for answers, Ultra capped, translations cached.

## Product guardrails (do not relax)

- Policy is enforced **before retrieval**: the agent reads memory only through `retrieve(query, principal)`; the store is partitioned by visibility and fails closed. Prompts are not the boundary.
- Kin organises; it never diagnoses, doses or triages. Every statement about the care recipient carries its source; no source → "I don't know".
- Consent is captured in chat before any audio is processed.
- All demo data is synthetic (fictional people and institutions, invalid-pattern identifiers). No real personal data, ever.
- The family group never receives detail that any member of the group cannot see; restricted answers go to DM; `finance`/`legal` trigger the share-request flow.

## When blocked

Record the blocker and what was tried in the relevant `ROADMAP.md` deliverable as a short note, keep the repo in a working state, and continue with any deliverable that does not depend on the blocker (D1 synthetic data never depends on infrastructure). Hermes questions: https://hermes-agent.nousresearch.com/docs/ and the Nous Discord; Nebius questions: the Nebius Discord.
