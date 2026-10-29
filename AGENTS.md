# Project instructions

Kin is a private family care coordinator in Telegram (Nebius x NVIDIA Global AI Hackathon, Personal AI track). It has persistent memory and role-based boundaries, enforced before retrieval and before delivery. The docs are the specification.

## Read first

1. `README.md`, then `docs/02-product.md` to `docs/06-synthetic-data.md`. `config/policy.yaml` and `config/members.yaml` are the data behind `docs/03-privacy-boundaries.md`.
2. `planning/` (git-ignored, present only on the owner's machine): `ROADMAP.md` is the work queue and `KICKOFF.md` the setup checklist. Items marked **YOU** need the owner.

## How to work

- **Checks:** before a product commit, run `make lint`, `make test`, `make policy` and `make check` (or `make check-nospend`). Docs-only commits need lint and tests.
- **Commits:** conventional, one-line, imperative, ≤ 72 characters, on `main`.
- **Docs:** when code changes a behaviour, update its doc in the same commit. Docs state facts, briefly; there are no decision logs.
- **Shared host:** the development host also runs other deployments, including another Hermes stack. Stay inside the `kin` compose project: no fixed container names, no published ports, capped resources, Kin's own bot token and keys.
- **Secrets:** they live in `.env`, which is git-ignored. Never commit `.env`, `data/`, `hermes/home/`, `planning/` or video files. Add dependencies with `uv add` and commit `uv.lock`.

## Constraints

- **Inference:** only Nebius Token Factory. That means Nemotron for text, plus a public vision model for photos, because Nano Omni is dedicated-only.
- **Runtime:** Hermes Agent supplies the runtime and the Telegram gateway. Kin's Hermes plugin carries identity and routing, and Kin owns memory, policy and skills.
- **Tavily** queries never contain family data. Apache-2.0 stays at the root.

## Guardrails

- **Identity:** it comes from the gateway session, never from the model. Unknown identity, category or qualifier fails closed. Prompts are not the boundary.
- **No advice:** Kin organises and never diagnoses, doses or infers interactions. Every statement about the care recipient carries a permitted source; with no source, it says "I don't know".
- **Documents:** they enter through the admin's private chat, and originals stay with the admin. Schedules activate only after the admin confirms, and conflicts block activation.
- **Delivery:** restricted answers go to private chats; the group gets only admin-approved posts.
- **Data:** synthetic only, never real personal data. Claim only the isolation that is tested.
