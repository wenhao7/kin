# 00 · Hackathon context

Sources: [overview](https://nebiusglobalaihackathon.devpost.com/), [rules](https://nebiusglobalaihackathon.devpost.com/rules), [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs), [schedule](https://nebiusglobalaihackathon.devpost.com/details/dates).

## Dates

| Event | When |
|---|---|
| Submission closes | **Fri 30 Oct 2026, 10:00 PDT** (Sat 31 Oct, 01:00 SGT) |
| Judging | 1 Dec – **15 Dec 2026, 12:00 PST** (16 Dec, 04:00 SGT); free demo access must stay up until then |
| Winners | ~11 Jan 2027 |

Multiple substantially different entries are permitted. A project that predates 26 Aug 2026 must disclose what changed in the period.

## Requirements (Stage 1 is pass/fail)

1. Runs on **Nebius**: a runtime call to the Token Factory inference API, or deployment on Nebius AI Cloud compute. A Token Factory inference call satisfies this; other components may run elsewhere.
2. Uses at least one **NVIDIA open model** (Nemotron, GR00T, Cosmos, Sonic).
3. A genuine attempt at one track's stated goal. Named tools in a track brief are examples, not a checklist.

| Track | Brief |
|---|---|
| Coding & Agentic Engineering | Agents that write, run and test code in Token Factory Sandboxes |
| Best Apps & Agents | Any app or agent people would use; Nemotron on Token Factory; Serverless encouraged |
| Personal AI | Always-on private assistant with persistent memory, reusable skills, chosen tools; NemoClaw, OpenShell, Hermes Agent, Serverless |
| Physical AI | Embodied/edge agents; hardware footage required |

## Deliverables

- Working project; URL to a working demo, hosted app or test build, free of charge until judging ends (credentials in testing instructions if private). Judges may also judge from the description and video alone.
- Video ≤ 3 min (target 2:50), public on YouTube, shows the project working; audio names Token Factory and the NVIDIA models used; no third-party trademarks or copyrighted music.
- Public repo with an OSI license visible in About; README with setup/run instructions and how Nemotron, Token Factory and other Nebius services were used.
- Text description, track selection, written feedback on Token Factory, AI Cloud and NVIDIA tools. English throughout.

## Judging (equal weight)

Technological implementation · Design (complete product, not a PoC) · Potential impact (specific problem, specific audience, demonstrated) · Quality of the idea.

## Prizes

Grand $20k · 2nd $10k · 3rd $6k · track winners: Jetson Orin Nano · **Best Use of Tavily $3k** (functional runtime Tavily call) · City $500 × 20 (attended Builders & Brews) · Most Valuable Feedback $100 × 10. One Overall *or* one Track award, plus one Bonus, per project.

## Platform facts

- Inference: OpenAI-compatible API at `https://api.tokenfactory.nebius.com/v1/`.
- Public Nemotron endpoints and list prices (per 1M in/out tokens): `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` $0.06/$0.24 (262K ctx); `nvidia/Nemotron-3_5-Lightning` $0.06/$0.24 (1M ctx; agentic coding/tool use); `nvidia/nemotron-3-super-120b-a12b` $0.30/$0.90 (256K); `nvidia/Nemotron-3-Ultra-550b-a55b` $1.00/$3.00 (1M). `Nemotron-3-Nano-Omni` is dedicated-only. Kin's chosen public extractor: `openbmb/MiniCPM-V-4_5` $0.66/$1.11 (32K ctx; text+image). Verify with `make models`.
- Sandboxes (beta): operations run from immutable images on fresh compute; save state before submission and continue from the returned image UUID. Operation `SUCCESS` is distinct from the process exit code. Limits: 50 simultaneous operations, 180-day image retention. SDK `contree-sdk` 0.3.6 reads `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID`. Base URL `https://api.tokenfactory.nebius.com/sandboxes`. Beta access is requested per project.
- Credits: $25 via promo code `NEBIUS-DEVPOST-GLOBAL26` plus $25 and Tavily credits via the Builders Program, per account (shared by both entries).
- Tavily: `search`, `extract`, `map`, `crawl`, `research`; SDK `tavily-python`.
