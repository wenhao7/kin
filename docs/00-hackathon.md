# 00 · Hackathon context

Source: [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/) and its [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules).

## Dates

- Submission period ends **Fri 30 Oct 2026, 10:00 PDT** (Sat 31 Oct, 01:00 SGT).
- Judging 1–15 Dec 2026. Demo access must remain available until then.
- Winners announced on or around 11 Jan 2027.

## Hard requirements (Stage 1 is pass/fail on these)

1. The project **runs on Nebius Token Factory or Nebius AI Cloud**: a runtime call to the Token Factory inference API, or deployment on Nebius AI Cloud compute (Serverless Jobs, Serverless Endpoints, DevPods).
2. The project uses **at least one NVIDIA open model** (Nemotron, GR00T, Cosmos, Sonic).
3. The project is a genuine attempt at one track's stated goal.

## Tracks

| Track | Brief |
|---|---|
| Coding & Agentic Engineering | Coding agents and developer tools: agents that write, run and test code in Token Factory Sandboxes |
| Best Apps & Agents | Any app or agent people would use; Nemotron on Token Factory; Serverless encouraged |
| Personal AI | Always-on, private assistant with persistent memory, reusable skills, tools and information the user chooses; NVIDIA NemoClaw, OpenShell, Hermes Agent, Nebius Serverless |
| Physical AI | Embodied/edge agents; hardware demo footage required |

## Submission deliverables

- Working project meeting the track requirements.
- Demo URL (hosted app, working demo or test build); free, unrestricted access until judging ends; credentials in testing instructions if private.
- Demo video ≤ 3 minutes, public on YouTube, shows the project working; audio explains how Token Factory and Nemotron (or other NVIDIA open models) were used; no third-party trademarks or copyrighted music.
- Public repo (GitHub/GitLab/Bitbucket) with an OSI license file visible in the About section; README with setup instructions and a section highlighting how Nemotron was used, where Token Factory accelerated the workflow, and other Nebius services used.
- Text description; track selection; written feedback on Token Factory, AI Cloud and NVIDIA tools.
- All materials in English.

## Judging criteria (equal weight)

1. **Technological implementation** — quality of build; effective use of Token Factory / AI Cloud models and Nemotron.
2. **Design** — a complete, coherent product experience, not a proof of concept.
3. **Potential impact** — a credible, specific case for a real problem for a real audience, addressed by what is demonstrated.
4. **Quality of the idea** — creative, non-obvious use of the stack; genuine understanding of the problem space.

## Prizes

Grand $20,000 · 2nd $10,000 · 3rd $6,000 (all tracks). Track winners: NVIDIA Jetson Orin Nano each. **Best Use of Tavily $3,000** (requires a functional runtime Tavily API call). City Winner $500 × 20 (Builders & Brews attendees). Most Valuable Feedback $100 × 10. Each project is eligible for one Overall *or* one Track award, plus one Bonus award.

## Platform facts

- Token Factory inference: OpenAI-compatible API at `https://api.tokenfactory.nebius.com/v1/`.
- Nemotron 3 on Token Factory: Nano 30B-A3B (262K ctx), Nano Omni (text/image/video/audio in, 262K; not in the public `/v1/models` list for our key, see `05-architecture.md`), Super 120B-A12B (256K), Ultra 550B-A55B. Exact IDs: `make models`.
- Token Factory Sandboxes (Contree, beta): VM-isolated execution with git-like branching (fork any checkpoint, parallel runs, rollback), OCI image import, 50 concurrent operations, 180-day checkpoint retention. SDK `contree-sdk` + `contree-client`; CLI `contree-cli`; base URL `https://api.tokenfactory.nebius.com/sandboxes`.
- Nebius AI Cloud Serverless: Endpoints (serve), Jobs (batch), DevPods (dev); per-second billing.
- Credits: $25 via promo code `NEBIUS-DEVPOST-GLOBAL26`; a further $25 and Tavily credits via the Nebius Builders Program.
- Tavily: `search`, `extract`, `map`, `crawl`, `research` endpoints; Python SDK `tavily-python`.
