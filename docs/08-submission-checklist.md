# 08 · Submission checklist

Source: [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules). Stage 1 judging is pass/fail on track fit and platform use.

## Requirements

- [ ] Runs on **Nebius Token Factory** (Nemotron inference) and/or **Nebius AI Cloud** (dedicated endpoint; Serverless Job for digests).
- [ ] Uses an **NVIDIA open model**: Nemotron 3 Nano and Super (vision extraction: MiniCPM-V 4.5 on Token Factory, standing in for Nano Omni).
- [ ] **Personal AI** track: always-on, private, persistent memory, skills, tools and information the user chooses; uses NemoClaw/OpenShell, Hermes Agent, Nebius Serverless.
- [ ] **Demo URL**: judge-joinable Telegram group + test script; optional data-map page.
- [ ] **Video** ≤ 3 min, public on YouTube, Kin working live; audio names Token Factory and Nemotron; no third-party trademarks, copyrighted music, or real personal data.
- [ ] **Public repo** with **Apache-2.0** detectable in About.
- [ ] **README**: setup and run instructions; section on how Nemotron, Token Factory, Hermes and OpenShell were used.
- [ ] **Text description** on Devpost.
- [ ] **Track** selected: Personal AI.
- [ ] **Feedback** on Token Factory, AI Cloud, NVIDIA tools (template below).
- [ ] **Tavily** runtime call in the main flow (allow-listed lookups) — Best Use of Tavily eligibility.
- [ ] **Builders & Brews** city selected if attended.
- [ ] English throughout; Mandarin outputs shown alongside English in the video.
- [ ] Testing access free and unrestricted until 15 Dec 2026; demo-group reset procedure documented.

## Repo hygiene

- [ ] `LICENSE` at root; About shows Apache-2.0.
- [ ] `.env.example` (`TELEGRAM_BOT_TOKEN`, `NEBIUS_API_KEY`, `TAVILY_API_KEY`); no secrets committed.
- [ ] Synthetic dataset or generator script with an "all fictional" notice.
- [ ] Safety statement in README.
- [ ] Mermaid diagrams render; locale pack folder visible.
- [ ] Known limitations section.

## Devpost description outline

1. Problem (3 sentences, two numbers, one Singapore-specific).
2. What Kin does (the kitchen-table paragraph).
3. Why private (data sensitivity; no incumbent is self-hosted).
4. Boundaries (role × category, enforced at retrieval, audit).
5. Built with (Nemotron model IDs on Token Factory; Hermes Agent; OpenShell/NemoClaw; Tavily; Serverless).
6. Safety (organises, never advises; grounded).
7. Next (WhatsApp, time-bound grants, more locales).

## Feedback template

Per tool (Token Factory inference incl. Nano Omni missing from the public catalog, NemoClaw/OpenShell, Hermes Agent, Nebius Serverless, Tavily):

- What we tried.
- What worked (specific API, default, doc page).
- What got in the way (reproducible steps, error text, time lost).
- Suggested change.
- Impact if fixed.

Feedback is judged on completeness, viability and potential impact.
