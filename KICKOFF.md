# Kickoff checklist

One-time setup on the development host (a Debian server that stays on; the Hermes gateway is long-lived). The scaffold (`uv` environment, Docker images, compose stack, `.env.example`, `make check` self-tests) is in the repo; items marked **YOU** need the human. Done when `make check` passes and `make up` leaves the gateway running.

Fixed dates: submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judging 1–15 Dec 2026. The demo Telegram group must stay up until judging ends.

## 1. Devpost — **YOU**
- [ ] Join the hackathon: https://nebiusglobalaihackathon.devpost.com/ → **Join hackathon** (same account as the Upgradient entry).

## 2. Nebius Token Factory — **YOU**
- [ ] Console https://tokenfactory.nebius.com → **API keys** → `NEBIUS_API_KEY` (the Upgradient key can be reused).
- [ ] Credits as per the Upgradient kickoff (promo code `NEBIUS-DEVPOST-GLOBAL26`; Builders Program).

## 3. Tavily — **YOU**
- [ ] API key at https://app.tavily.com → `TAVILY_API_KEY`.

## 4. Telegram — **YOU**
- [ ] @BotFather → `/newbot` → token → `TELEGRAM_BOT_TOKEN`.
- [ ] @BotFather → `/mybots` → the bot → **Bot Settings → Group Privacy → Turn off**. Remove and re-add the bot to any group it already joined (Telegram caches the setting). Alternative: make the bot a group admin.
- [ ] Your numeric user ID (message @userinfobot) → `KIN_ADMIN_TELEGRAM_ID` and `TELEGRAM_ALLOWED_USERS`.
- [ ] Create the test group "Tan Family"; add the bot and a second account. Post one message, then read the chat ID (negative; `-100…` once Telegram upgrades the group to a supergroup, which changes the ID) from `https://api.telegram.org/bot<TOKEN>/getUpdates` → `TELEGRAM_GROUP_ALLOWED_CHATS` and `TELEGRAM_HOME_CHANNEL`.

## 5. Host tools — **YOU**
- [ ] `uv`, Docker Engine + Compose v2, `git`, `make`. For synthetic-document generation (`make setup-data`): `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`.

## 6. Environment
```bash
make setup          # .venv + deps; creates data/ and hermes/home/; copies .env.example → .env if missing
$EDITOR .env        # NEBIUS_API_KEY, TAVILY_API_KEY, TELEGRAM_BOT_TOKEN, KIN_ADMIN_TELEGRAM_ID, TELEGRAM_* allow-lists
```

## 7. Self-check
```bash
make check          # keys · policy/locale · model IDs · one vision call · Telegram getMe · Tavily (allow-listed)
make models         # exact Nemotron and configured IDs; fix .env if a model shows "not found"
make policy         # prints and validates the role × category matrix
```
`Telegram getMe` must show `can_read_all_group_messages=True`. `vision:image` must PASS (reply "Red"): the vision model (`KIN_MODEL_VISION`) is the Token Factory fallback for Nemotron 3 Nano Omni, which is not in the public catalog for our key (`docs/05-architecture.md`, Vision fallback).

## 8. Hermes runtime (ROADMAP D0)
```bash
make docker-build
make up             # kin service + hermes gateway; first hermes start installs Hermes into ./hermes/home
make logs           # watch the install, config seeding, gateway start
make hermes-doctor
```
Then send the bot a message in the test group. If the containerised install misbehaves, fall back to a host install (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`, `hermes setup` with provider **Nebius Token Factory**, `hermes gateway setup` for Telegram, `hermes gateway install && hermes gateway start`); the `kin` service stays in Docker either way. Record which path worked in `ROADMAP.md` D0. On a shared host, keep Hermes containerised: a host install uses `~/.hermes` and installs a gateway service, which collide with any other host-level Hermes. The compose stack is self-contained (`docs/05-architecture.md`, Deployment).

## 9. Community — **YOU**
- [ ] Nebius Discord: https://discord.gg/ZdC3rXMJH. Hermes docs: https://hermes-agent.nousresearch.com/docs/.

## Working rhythm
Each burst: open `ROADMAP.md`, take the next unchecked deliverable, finish it to its "done when", tick it, commit (conventional commits), push to `main`. Secrets stay in `.env`; `data/` and `hermes/home/` never enter git.

Order across repos: Upgradient to its minimum submittable product first; Kin D1 (synthetic documents) can be done in any spare burst because it needs no infrastructure.
