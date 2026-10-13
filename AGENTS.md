# Project instructions

Kin is a hackathon submission (Nebius x NVIDIA Global AI Hackathon, Personal AI track, deadline 30 Oct 2026 10:00 PDT): a private, always-on family care coordinator in a Telegram group, with persistent memory and role-based boundaries enforced before retrieval and before delivery. The docs are the specification; `ROADMAP.md` is the work queue.

## Read first, in this order

1. `README.md` · 2. `ROADMAP.md` (next unchecked deliverable = current task) · 3. `docs/02-product.md` · 4. `docs/03-privacy-boundaries.md` (`config/policy.yaml` and `config/members.yaml` are its data) · 5. `docs/04-safety.md` · 6. `docs/05-architecture.md` · 7. `docs/06-synthetic-data.md`, `docs/07-demo-plan.md` · 8. `docs/00-hackathon.md`, `docs/08-submission-checklist.md` · 9. `KICKOFF.md` (items marked **YOU** need the human).

## How to work

- Take the next unchecked deliverable, finish it to its "done when", tick it in the same commit, stop at a working state. Tick a gate only with recorded evidence. Never start work that breaks the minimum submittable product (D0–D5) once it exists.
- Before a product commit: `make lint`, `make test`, `make policy`, and `make check` (or `make check-nospend`). Docs-only commits need lint and tests only.
- Conventional commits, small and focused, imperative subject ≤ 72 chars. Branch `main`; push after each deliverable.
- When implementation changes a spec, update the doc in the same commit. Docs state facts; no decision logs or time estimates.
- The development host is shared with other deployments, including another Hermes stack. Keep everything inside the `kin` compose project: no fixed container names, no published ports, capped resources, Kin's own bot token and keys (`docs/05-architecture.md`, Deployment).
- Secrets live in `.env` (git-ignored) and reach the Hermes container via compose. Never commit keys, `.env`, `data/` or `hermes/home/`. `uv` manages the environment; add dependencies with `uv add` and commit `uv.lock`.

## Hackathon constraints

- Inference is **Nemotron on Token Factory** for text (Nano or Lightning for classification, Super for answers, Ultra optional and capped) plus a **public vision model on Token Factory** for photo extraction, because Nano Omni is dedicated-only. D0 records the chosen IDs (extractor: `openbmb/MiniCPM-V-4_5`). No other inference providers.
- Hermes Agent supplies runtime and Telegram gateway; Kin's Hermes plugin bridges identity and routing; Kin owns domain memory, policy and skills. One reusable scheduled skill is in the minimum. OpenShell/NemoClaw and Serverless are optional.
- Tavily is called at runtime in the main flow with the locale allow-list; queries never contain family data.
- Apache-2.0 stays at the root. Credits are per account and shared with Upgradient.

## Product guardrails

- Identity comes from the authenticated Telegram/gateway context, never from a model-supplied principal: Kin's Hermes plugin reads the sender from the gateway session (MCP tool calls carry none). Policy is applied before retrieval and before delivery; Hermes' native memory, session search, skills, cron and file/terminal tools stay off. Unknown identity, category or qualifier fails closed. Prompts are not the boundary.
- Kin organises; it never diagnoses, doses, triages or infers drug interactions. Every statement about the care recipient carries a permitted source; no source → "I don't know".
- Sensitive documents enter through Admin DM. A mixed original stays Admin-only; other roles receive approved fields and excerpts. Schedules activate only after Admin confirms the exact record version; conflicts block activation.
- Restricted answers go to DM; the group receives only Admin-confirmed summaries. Audio is not processed (no public audio model; voice transcription off); if it is ever added, consent is captured in chat first.
- All demo data is synthetic. No real personal data, ever.
- Claim only tested isolation; storage is self-hosted, inference and Telegram transport are external.

## When blocked

Note the blocker and what was tried in the relevant ROADMAP item, keep the repo working, continue with independent work (D1 fixtures need no infrastructure). Hermes: https://hermes-agent.nousresearch.com/docs/ and the Nous Discord; Nebius: the Nebius Discord. Do not contact others without the owner's authorisation.
