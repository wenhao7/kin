# Kin

**The family member who remembers everything — and tells no one who shouldn't know.**

Kin is a private, always-on care coordinator for families looking after an ageing parent. It joins the family's Telegram group as a member. Photograph the discharge letter and the pill boxes: Kin builds the medication schedule, sets reminders on the helper's phone, flags the one question worth asking the pharmacist, and posts a plain-language summary to the group — in English, and in Mandarin for the aunt who prefers it. Months later, when a brother overseas asks "what did Dr Tan change last time?", Kin answers with the exact change and the photo it came from. Ask about the insurance claim in the group and Kin replies privately to the primary caregiver: that's family-admin information, shall I share it?

Kin runs on a machine the family controls (OpenShell/NemoClaw sandboxing planned), with open NVIDIA Nemotron models served through Nebius. Each person sees only what their role allows, enforced where data is retrieved — not by prompt.

Built for the [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/), Personal AI track. Singapore locale; the locale is a swappable pack.

## Why

- 63 million US caregivers (1 in 4 adults), up ~50% since 2015; 55% perform medical/nursing tasks, 22% trained; 1 in 3 finds coordination hard (AARP/NAC 2025).
- Singapore is a super-aged society in 2026 (1 in 5 aged 65+); family eldercare hours projected to rise from 29 to 41 per week; 55% of working caregivers left work for a parent's doctor visit in the past six months.
- Coordination happens in a group chat and a shoebox of paper.
- Funded players (Hera, Cariloop, Wellthy, Caring Village) are human services or cloud apps. None is a private, self-hosted, memory-first agent in the family's existing chat.

Details: [docs/01-problem.md](docs/01-problem.md).

## What it does

| Flow | In chat |
|---|---|
| Intake | Photo of a letter, label, slip or report → structured record with source, filed, scheduled, summarised |
| Schedule & reminders | Medication times, refills, appointments; reminder to the responsible person |
| Ask | "What did the cardiologist change in March?" → answer + source photo |
| Boundaries | Role-based views; sensitive answers to DM; share-request flow; `/who_saw` audit |
| Appointment prep & debrief | Question list before; photo of the after-visit summary → updated records, action items, next appointment after |
| Weekly digest | Role-appropriate summary per member, in their language |
| Skills | "Every Monday remind Siti to refill the pill organiser and send a photo" — taught once |
| Local lookups | Public scheme rules from allow-listed domains; no family data in queries |

Product: [docs/02-product.md](docs/02-product.md). Boundaries: [docs/03-privacy-boundaries.md](docs/03-privacy-boundaries.md).

## How it works

```mermaid
flowchart LR
    TG[Telegram<br/>family group + DMs] <--> GW[Hermes gateway<br/>+ Kin plugin]
    GW --> AG[Hermes agent<br/>Kin persona]
    GW & AG -->|caller from the gateway| KIN[kin service<br/>intake · retrieve · policy · scheduler]
    KIN --> MEM[(Partitioned store<br/>records · docs · events)]
    KIN -->|posts, DMs, reminders| TG
    AG & KIN <--> TF[(Nebius Token Factory<br/>Nemotron 3 Nano · Super<br/>MiniCPM-V vision)]
    KIN --> TV[(Tavily<br/>allow-listed domains)]
    subgraph Host["Family's machine · OpenShell/NemoClaw sandbox planned"]
        GW
        AG
        KIN
        MEM
    end
```

- **Hermes Agent** (MIT): always-on Telegram gateway and conversation runtime. A small Kin plugin gives Kin's tools the sender's identity from the gateway and routes photos and share replies to Kin without a model in the loop.
- **Kin service**: the family's persistent memory (records with sources), intake, `retrieve(query, principal)` with the role × category policy, reminders and skills.
- **OpenShell / NemoClaw** (planned): sandbox, credential proxying, network allow-list.
- **Nemotron 3 Nano** classifies and translates; **Nemotron 3 Super** reasons and drafts; **MiniCPM-V 4.5** reads photos and documents (standing in for Nemotron 3 Nano Omni, which is not listed on the public endpoint for our key); all served via Nebius Token Factory (dedicated Nebius endpoint supported).
- **Tavily**: public scheme information from an allow-list, called by the Kin service.

Architecture: [docs/05-architecture.md](docs/05-architecture.md).

## Safety

Kin organises; it does not diagnose or dose. Every statement about the care recipient carries its source. Audio is not processed; any future recording needs consent in chat first. [docs/04-safety.md](docs/04-safety.md).

## Demo

All demo data is synthetic: fictional family, fictional institutions, generated documents. [docs/06-synthetic-data.md](docs/06-synthetic-data.md) · [docs/07-demo-plan.md](docs/07-demo-plan.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12 is fetched automatically) and Docker with Compose v2 for the runtime.

```bash
make setup             # .venv + dependencies; creates data/, hermes/home/; copies .env.example → .env
$EDITOR .env           # NEBIUS_API_KEY, TAVILY_API_KEY, TELEGRAM_BOT_TOKEN, KIN_ADMIN_TELEGRAM_ID, TELEGRAM_* allow-lists
make check             # keys · policy/locale · models · one vision call · Telegram getMe · Tavily
make policy            # print and validate the role × category matrix
make up                # kin service + Hermes gateway (first start installs Hermes into ./hermes/home)
make hermes-config     # after editing hermes/config.yaml or hermes/SOUL.md
make logs
```

`hermes/config.yaml` and `hermes/SOUL.md` (Kin's persona) are seeded into the Hermes home on first start; `make hermes-config` re-applies them after a change. They set the Nebius Token Factory provider and turn off Hermes features that would bypass Kin's boundaries; Kin's tools arrive as a Hermes plugin in ROADMAP D2 ([docs/05-architecture.md](docs/05-architecture.md#hermes--kin)). `make hermes-shell` opens a shell with `hermes` on the PATH for `hermes doctor`, `hermes model`, `hermes gateway setup`.

Layout:

```
kin/
  README.md · AGENTS.md · KICKOFF.md · ROADMAP.md · LICENSE (Apache-2.0)
  pyproject.toml · uv.lock · .python-version · .env.example
  Makefile · Dockerfile · docker-compose.yml
  kin/               # package: config, policy, members, cli, setup_check, hermes_config; intake/retrieve/serve land per ROADMAP
  config/policy.yaml # default role × category matrix
  config/members.yaml # demo roster: personas, roles, languages (Telegram IDs in .env)
  locale/sg/         # Singapore locale pack (languages, lookup allow-list, terms, document types)
  hermes/            # config.yaml template, SOUL.md persona, plugins/kin (D2); home/ is the gateway's volume (git-ignored)
  docker/hermes/     # Hermes container (installs on first start, runs `hermes gateway run`)
  data/              # family data volume (git-ignored)
  tests/ · docs/ · .github/workflows/ci.yml
```

## How we use Nebius and NVIDIA

_Required by the hackathon. To be filled with model IDs, endpoint type, tokens per intake, where Token Factory accelerated the workflow, how OpenShell/NemoClaw is used._

## Docs

| Doc | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | Instructions for coding agents: reading order, conventions, constraints, guardrails |
| [KICKOFF.md](KICKOFF.md) | One-time setup; items needing the human are marked |
| [ROADMAP.md](ROADMAP.md) | Sequential deliverables and order of work |
| [00-hackathon.md](docs/00-hackathon.md) | Hackathon requirements, judging criteria, dates, platform facts |
| [01-problem.md](docs/01-problem.md) | Problem, evidence, users, landscape ([sources](docs/sources.md)) |
| [02-product.md](docs/02-product.md) | Scope, roles, categories, flows, chat conventions |
| [03-privacy-boundaries.md](docs/03-privacy-boundaries.md) | Boundary model, policy matrix, enforcement, audit |
| [04-safety.md](docs/04-safety.md) | Organiser-not-adviser rules, grounding, consent, data protection |
| [05-architecture.md](docs/05-architecture.md) | Components, data model, flows, models, integrations |
| [06-synthetic-data.md](docs/06-synthetic-data.md) | Demo family, timeline, document set, generation |
| [07-demo-plan.md](docs/07-demo-plan.md) | Video script, judge access |
| [08-submission-checklist.md](docs/08-submission-checklist.md) | Devpost requirements, feedback template |

## License

Apache-2.0.
