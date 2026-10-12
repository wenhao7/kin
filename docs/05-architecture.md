# 05 · Architecture

## Constraints

- Always-on; one family; Telegram.
- Single retrieval chokepoint; store partitioned by visibility; fails closed.
- Inference via Nebius Token Factory; a dedicated Nebius endpoint is supported for tenant isolation.
- Hackathon credits ≈ $50: Nano and the vision model for volume; Super for answers; Ultra capped.

## Components

```mermaid
flowchart TB
    subgraph Telegram
        G[Family group]
        D[DMs per member]
    end
    subgraph Sandbox["OpenShell / NemoClaw sandbox — always-on"]
        GW[Gateway<br/>Telegram ↔ events]
        AG[Kin agent<br/>Hermes Agent runtime<br/>skills · scheduler]
        IN[Intake pipeline<br/>extract · classify · conflict check]
        PE[Policy engine<br/>role × category · grants · audit]
        RET["retrieve(query, principal)"]
        MEM[(Memory store<br/>records · documents · events<br/>partitioned by visibility)]
        LOC[Locale pack<br/>languages · allow-list · templates]
    end
    subgraph Nebius
        TF[(Token Factory<br/>Nemotron 3 Nano · Super<br/>MiniCPM-V vision)]
        SE[Serverless Job / Endpoint<br/>weekly digest · optional data-map page]
    end
    TV[(Tavily · allow-listed domains)]

    G & D <--> GW <--> AG
    AG --> IN --> MEM
    AG --> RET --> PE --> MEM
    AG <--> TF
    IN <--> TF
    AG --> TV
    AG --> LOC
    AG -.-> SE
```

## Data model

- **Member**: `telegram_id`, `name`, `role`, `language`, `expires_at?`
- **Record**: `id`, `category`, `visibility`, `fields` (typed per category, e.g. medication {name, dose, frequency, start, end, prescriber}), `source_ref`, `created_by`, `created_at`, `supersedes?`
- **Document**: `id`, `type` (photo | pdf | audio), `storage_ref`, `extracted_text`, `pages/segments`, `created_at`
- **Event**: reminders, appointments, tasks — `assignee`, `due_at`, `status`, `record_ref`
- **Grant**: `record_or_category`, `grantee`, `scope`, `granted_by`, `at`
- **Audit**: `principal`, `query`, `records_shown`, `decision`, `at`
- **Skill**: `trigger` (cron | event), `principal`, `instruction`, `last_run`

Storage: SQLite + file store on the sandbox volume, partitioned by visibility class.

## Flows

**Intake.** Media message → Gateway → Intake: the vision model extracts fields/text → Nano classifies category → conflict check → clarifying question if confidence low → Record + Document stored (visibility from policy) → Events created → role-appropriate posts.

**Ask.** Message → intent → `retrieve(query, principal)` (policy applied before context) → Super composes answer with source references → Gateway attaches source crop/excerpt → Audit entry.

**Share request.** `retrieve` reports a policy block → admin DM with options → Grant stored → asker answered or declined → Audit.

**Debrief.** Audio + consent flag → Nano Omni transcription and summary (pending: no audio-capable model on the public Token Factory endpoint for our key) → superseding medication Records → Events → per-role posts.

**Skills.** Hermes skill store; scheduler fires with the skill's principal; output passes through the policy path.

**Digest.** Weekly job (Hermes scheduler or Nebius Serverless Job) renders per-role digests per language.

## Models

| Task | Model |
|---|---|
| Photo/PDF understanding; field extraction | MiniCPM-V 4.5 (`openbmb/MiniCPM-V-4_5`), vision fallback for Nemotron 3 Nano Omni |
| Audio transcription and summary (debrief) | Nemotron 3 Nano Omni, once listed on Token Factory |
| Category classification; conflict detection; short answers; translation | Nemotron 3 Nano 30B-A3B |
| Grounded answers; appointment prep; digests; skill interpretation | Nemotron 3 Super 120B-A12B |
| Hard record conflicts (capped) | Nemotron 3 Ultra 550B-A55B |

Served via Token Factory (OpenAI-compatible API).

**Vision fallback.** Nemotron 3 Nano Omni is not in the public Token Factory catalog (`/v1/models`) for our key. Of the contingency options (a dedicated Nano Omni endpoint; another Token Factory vision model for extraction only; text-only PDF intake), Kin uses the second: `openbmb/MiniCPM-V-4_5` reads photos and documents, and Nemotron classifies, answers and drafts. The kin service reads it from `KIN_MODEL_VISION`; Hermes uses it through `auxiliary.vision` with `agent.image_input_mode: text` (Super is text-only, so Hermes passes Super the vision model's description of an inbound photo). `kin check` sends one image to it (`vision:image`). The hard requirement of an NVIDIA open model in the product path is met by Nano and Super. When `make models` lists Nano Omni, set `KIN_MODEL_VISION` and `auxiliary.vision.model` to its ID. Audio input (debrief) waits on the same: no audio-capable model is listed on the public endpoint.

## Integrations

- **Telegram Bot API** — group + DMs; group privacy mode disabled for the family group.
- **Hermes Agent** — runtime, memory interface, skills, gateway. Policy engine and `retrieve` are the only memory access path.
- **OpenShell / NemoClaw** — sandbox, credential proxying, network allow-list (Telegram API, Token Factory, Tavily, locale allow-list domains).
- **Tavily** — `search`/`extract` with `include_domains` from the locale pack; no record content in queries.
- **Locale pack** — folder: languages, lookup allow-list, document templates and label formats, local terms. Swapping the locale replaces the folder.

## Deployment

Kin runs as the `kin` compose project (kin service + Hermes gateway) on a host shared with other deployments, including a separate Hermes stack. It stays self-contained:

- Own compose project, default network and images (`kin:dev`, `kin-hermes:dev`); no fixed container names.
- Own credentials: Kin's Telegram bot token (Telegram allows one poller per token), Nebius and Tavily keys.
- No ports on public interfaces: the Hermes gateway publishes none (Telegram is outbound polling); the kin MCP port is bound to `127.0.0.1` for debugging (`KIN_MCP_PORT`), and Hermes reaches kin over the compose network.
- Capped resources and rotated logs (`mem_limit`, `cpus`, `pids_limit`, `local` log driver).
- Hermes toolsets that could reach other host services or read the volume (terminal, code execution, browser, file, delegation) and Hermes' own web search are disabled in `hermes/config.yaml`. Containers on the compose network can still open connections to host ports bound to all interfaces; the OpenShell/NemoClaw network allow-list (D7) is the network-level control.
- Hermes is installed into `./hermes/home` inside its container; nothing is installed on the host.
