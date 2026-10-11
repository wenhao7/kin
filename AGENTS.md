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

- Take the next unchecked deliverable in `ROADMAP.md`. Finish it to its "done when", tick the checkbox in the same commit, and stop at a working state. Do not start a deliverable that would break the minimum submittable product once it exists (D0–D5).
- `make setup`, `make check` (or `make check-nospend`), `make policy`, `make lint`, `make test` must pass before a product deliverable commit. CI runs `ruff` and `pytest`. For documentation-only commits, run setup, policy, lint and tests in a disposable checkout without credentials; defer unavailable live checks with the reason recorded in ROADMAP. This never completes a product gate.
- Conventional commits (`feat:`, `fix:`, `docs:`, `build:`, `test:`, `chore:`, `refactor:`), small and focused, imperative subject ≤ 72 chars. Branch `main`; push after each deliverable.
- Keep docs factual and current. When implementation changes a spec in `docs/`, update the doc in the same commit. No decision logs or time estimates in docs; a dated `docs/decisions.md` may be started only when a spike reveals a real fork in the road.
- Secrets live in `.env` (git-ignored) and are passed to the Hermes container by compose. Never commit keys, tokens, `.env`, `data/`, or `hermes/home/`.
- Python ≥ 3.10 locally, 3.12 in Docker; `uv` manages the environment and `uv.lock` is committed. Add dependencies with `uv add` and commit the lock.

## Hackathon requirements and product choices

- The hackathon requires Nebius runtime use, at least one NVIDIA open model and track fit. Kin chooses **Token Factory** inference: Nemotron for text reasoning and a D0-qualified image model. Nano Omni is listed as dedicated-only; an available Token Factory vision model plus Nemotron is an allowed alternative. Audio and Ultra are optional; do not substitute an unapproved inference provider.
- Hermes supplies runtime/Telegram facilities; Kin owns policy-enforced domain memory. One reusable scheduled skill is minimum. Named tools are examples, not all mandatory: OpenShell/NemoClaw and Serverless are optional after the core enforcement gate.
- For the planned Tavily bonus entry, Tavily must be called at runtime in the main flow (allow-listed public lookups) with `include_domains` from the locale pack; queries never contain family data.
- Apache-2.0 license file stays at the root and visible on GitHub.
- Confirm actual credits/expiry and dedicated pricing; reserve judging costs across both submissions. Nano handles bounded text tasks, Super answers, Ultra is optional and capped; private translation caches remain permission-scoped.

## Product guardrails (do not relax)

- Derive identity server-side from authenticated Telegram/gateway context, never a model-supplied principal. Enforce policy before context and before delivery across retrieval, history, native Hermes memory/search, summaries, caches, skills, sources and translations. Disable/isolate all bypass tools; unknown identity/category/qualifier fails closed. Prompts and partition names are not the boundary.
- Kin organises; it never diagnoses, doses or triages. Every statement about the care recipient carries its source; no source → "I don't know".
- Sensitive documents enter through DM. A mixed original stays Admin-only; lower roles receive approved fields/source excerpts. Confirm the exact schedule version before activation; conflicts block changes. No inferred interaction warnings.
- Consent is captured in chat before optional audio is processed; audio-derived changes also require confirmation.
- All demo data is synthetic (fictional people and institutions, invalid-pattern identifiers). No real personal data, ever.
- Group output uses the intersection of the current verified roster; uncertain membership blocks restricted delivery. Grants bind record/version, projection and recipient; consume one-shot grants transactionally. Skills must authorize each recipient separately; restricted answers use initialized DMs.
- Describe storage as self-hosted and inference/Telegram transport as external. Only claim tested isolation; document current config/service gaps. Minimum privacy/safety tests are required before intake is demonstrated as safe.

## When blocked

Record the blocker and what was tried in the relevant `ROADMAP.md` deliverable as a short note, keep the repo in a working state, and continue with any deliverable that does not depend on the blocker (D1 synthetic data never depends on infrastructure). Hermes questions: https://hermes-agent.nousresearch.com/docs/ and the Nous Discord; Nebius questions: the Nebius Discord.
