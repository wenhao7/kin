# Kickoff checklist

One-time setup on the development/demo host (a Debian server that stays on; the Hermes gateway is long-lived). Items marked **YOU** need the human. Kickoff qualifies D0, not the product. No real family data anywhere.

Submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judge access must stay up through **16 Dec 2026, 04:00 SGT**.

## 1. Devpost — **YOU**
- [ ] Join the hackathon with the same account as Upgradient; the two entries must be substantially different.

## 2. Nebius Token Factory — **YOU**
- [ ] API key (reuse Upgradient's) → `NEBIUS_API_KEY`. Credits are per account.
- [ ] Nano Omni is dedicated-only. Unless a dedicated endpoint is affordable for the judging period, the extractor is a public vision model on Token Factory; `make models` lists what the key can see. Record the chosen IDs in `.env` (`KIN_MODEL_VISION`, `KIN_MODEL_NANO`, `KIN_MODEL_SUPER`).

## 3. Tavily — **YOU**
- [ ] API key at https://app.tavily.com → `TAVILY_API_KEY`.

## 4. Telegram — **YOU**
- [ ] @BotFather → `/newbot` → token → `TELEGRAM_BOT_TOKEN`. Never paste a token-bearing URL into docs, logs or screenshots.
- [ ] @BotFather → `/mybots` → the bot → **Bot Settings → Group Privacy → Turn off**; remove and re-add the bot to any group it already joined. Alternative: make the bot a group admin.
- [ ] Your numeric user ID (message @userinfobot) → `KIN_ADMIN_TELEGRAM_ID` and `TELEGRAM_ALLOWED_USERS`.
- [ ] Create the test group; add the bot and the second and third test accounts (Family, Carer). Each account must open a DM with the bot and send `/start` once — bots cannot message users who haven't.
- [ ] Group chat ID (starts with `-100`): post one message, then run `curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | jq '.result[].message.chat.id'` from a shell where the token is an env var → `TELEGRAM_GROUP_ALLOWED_CHATS`, `TELEGRAM_HOME_CHANNEL`.

## 5. Host tools — **YOU**
- [ ] `uv`, Docker Engine + Compose v2, `git`, `make`. For `make setup-data` (document rendering): `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`.

## 6. Environment and checks
```bash
make setup          # deps; .env from example; data/ and hermes/home/
$EDITOR .env        # keys, verified Telegram IDs, model IDs
make policy         # validates the matrix shape (runtime enforcement is D2)
make lint && make test
make models         # Nemotron and vision model IDs visible to the key
make check          # live probes: models, one image call to the configured extractor, Telegram getMe, Tavily
```
`Telegram getMe` must show `can_read_all_group_messages=True`. `make check-nospend` still needs network and keys.

## 7. Hermes runtime (D0)
```bash
make docker-build
make up             # kin self-check + hermes gateway; first start installs Hermes into ./hermes/home
make logs
make hermes-doctor
```
Send the bot a message in the group and in DM. If the containerised install fails, install on the host instead (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`, `hermes setup` with provider **Nebius Token Factory**, `hermes gateway setup`, `hermes gateway install && hermes gateway start`); the `kin` service stays in Docker. Record which path worked in ROADMAP D0. Kin MCP stays disabled until D2 binds identity and isolates Hermes memory.

## 8. Community — **YOU**
- [ ] Nebius Discord: https://discord.gg/ZdC3rXMJH · Hermes docs: https://hermes-agent.nousresearch.com/docs/

## Working rhythm
Open `ROADMAP.md`, take the next unchecked item, finish it to its "done when", tick it, commit (conventional commits), push to `main`. `.env`, `data/`, `hermes/home/` and logs stay out of git. D1 (synthetic fixtures) needs no infrastructure and fits any spare burst.
