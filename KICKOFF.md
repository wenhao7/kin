# Kickoff checklist

One-time setup on the intended development/demo host. The repository has setup probes and container templates; `kin serve` and domain flows are not implemented. Kickoff qualifies D0, not the whole product. Keep real family information out of the environment.

Submission closes **30 Oct 2026, 10:00 PDT (31 Oct, 01:00 SGT)**. Judge access must remain free and available through **16 Dec 2026, 04:00 SGT**.

## 1. Devpost — YOU

- [ ] Join the [hackathon](https://nebiusglobalaihackathon.devpost.com/) with the same account as Upgradient. The two entries must be substantially different.

## 2. Nebius Token Factory — YOU

- [ ] Create an API key at [Token Factory](https://tokenfactory.nebius.com); store it only in `.env`/deployment secrets.
- [ ] Confirm credited balance and expiry; budget both submissions together, including judge-period operation.
- [ ] Confirm Nano Omni dedicated endpoint availability and pricing before starting paid compute. If unsuitable, qualify an available Token Factory image model plus NVIDIA Nemotron text as described in [architecture](docs/05-architecture.md).
- [ ] Record exact endpoint/model IDs, request format and an image result. Audio needs a separate optional test. Upgradient's pending Sandboxes beta approval does not qualify or block this model path.

## 3. Tavily — YOU

- [ ] Obtain a key at [Tavily](https://app.tavily.com); use validated public-only topics and the locale allow-list. Never send family record text as a search query.

## 4. Telegram — YOU

- [ ] Use @BotFather to create the bot; store `TELEGRAM_BOT_TOKEN` privately.
- [ ] Configure group privacy/admin settings only as needed for the enrolled synthetic group. Enforce verified sender and membership restrictions independently of that setting.
- [ ] Set verified numeric Admin/user/group IDs and the `TELEGRAM_*` allow-lists in `.env`; never take authority from a display name or model-generated ID.
- [ ] Enroll Admin, Family and Carer test identities and languages. Each person starts a private chat with the bot before any DM delivery test.
- [ ] Use synthetic DMs for sensitive intake; a group upload has already exposed the original. Check unknown-member behavior before group summaries.

Do not paste a token-bearing Telegram API URL into docs, logs or screenshots. The bot cannot initiate a private conversation with a user who has not started it. [Telegram bot guidance](https://core.telegram.org/bots)

## 5. Host tools — YOU

- [ ] `uv`, Docker Engine + Compose v2, `git`, `make`. For optional synthetic render tooling (`make setup-data`), install the Pango libraries required by the selected renderer.

## 6. Local environment and checks

```bash
make setup          # dependencies; example .env; data/ and hermes/home/
$EDITOR .env        # keys, verified IDs, endpoint/model configuration
make policy         # validates matrix shape, not runtime enforcement
make lint
make test
make models         # discover actual Nemotron IDs visible to the account
make check          # live probes, including configured image request
```

`make check-nospend` skips paid inference but still requires credentials/network; it is not an offline validation mode. Current `make check` uses the scaffold's configured Omni probe. Selecting an alternative extractor requires a later D0 implementation/config change, not merely changing this documentation. Preserve failed access/modality evidence without declaring model inability from a connectivity failure.

## 7. Hermes/runtime spike

```bash
make docker-build
make up             # starts scaffold services; does not implement kin serve
make logs
make hermes-doctor
```

Qualify synthetic group/DM replies and inspect the installed Hermes version, tools and persistent history. Before enabling Kin MCP or ingesting domain data, D2 must bind trusted identity, protect the service and disable/isolate unrestricted native memory/history/files. A shared persistent Hermes home is not proof of role isolation. Do not weaken volume, credential or tool boundaries merely to make setup pass.

OpenShell/NemoClaw can be qualified later, but the minimum policy boundary cannot be deferred. Record the deployed runtime and outstanding gaps in ROADMAP. No external support messages are sent without the owner's authorization.

## Working rhythm

Read ROADMAP, finish one evidence gate, update its status and make a focused conventional commit; product deliverables follow repository push conventions. Documentation-only work uses the recorded credential-free validation exception. `.env`, `data/`, Hermes home and runtime logs stay out of Git.

While Upgradient beta approval is pending, Kin D0/D1 and deterministic Upgradient preparation can progress independently. A fixture or setup probe never completes an application gate.
