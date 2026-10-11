# Roadmap

Sequential evidence gates. Configuration and documentation are preparation; check a box only when the deployed behavior has passed its acceptance checks.

**Fixed dates:** submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**. Judging runs 1–15 Dec Pacific time; free demo access must remain available through **Wed 16 Dec 2026, 04:00 SGT**.

## Current status

- Configuration/policy loading, setup probes and container templates exist. `kin serve` is a placeholder; authenticated retrieval, persistent domain records, intake and reminders are not implemented.
- Nano Omni is currently listed as dedicated-only. D0 must qualify availability, endpoint, pricing and an image path; current setup checks do not implement an alternative extractor.
- The YAML matrix is validated for shape, not runtime authorization. Shared Hermes memory/history and model-accessible tools remain a design risk until D2 isolates them.
- Upgradient's Sandboxes beta approval is pending. Kin's model/runtime spike and synthetic fixtures can progress independently; no Token Factory Sandbox is required for Kin's local runtime design.
- Documentation-only validation uses a disposable checkout without credentials. Live provider/Telegram/Tavily checks are deferred because credentials and a qualified image endpoint are not supplied to that review environment. No product gate is marked complete by documentation checks.
- Documentation validation: setup, policy validation, Ruff lint/format and all four tests passed in a disposable Python 3.12 checkout with cached locked dependencies and no credentials. These checks cover the scaffold, not the unimplemented product controls.

## D0 · Qualify runtime, identity and actual models

- [ ] Create bot, enrolled test group and verified Admin/Family/Carer identities; each starts a DM with Kin.
- [ ] Hermes replies in isolated synthetic group/DM sessions; pin installed version and inventory native tools/memory paths.
- [ ] Qualify a real image request: dedicated Nano Omni if accessible/affordable, otherwise an available Token Factory vision model plus Nemotron text. Record endpoint/model IDs, pricing, usage and remaining demo-period credits.
- [ ] Nano/Super text and bounded structured tool loop pass malformed-output, empty-answer and timeout cases; audio and Ultra are optional.
- [ ] Verify public repository/license and record actual deployment boundary. OpenShell/NemoClaw integration may follow at D7 without deferring core privacy controls.

**Done when:** a synthetic photo in Admin DM is described with the actual qualified model and a bounded text/tool request succeeds or fails truthfully. This spike does not yet activate schedules or publish medical summaries.

## D1 · Minimum synthetic fixture and ground truth

- [ ] Eight documents: discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter and handwritten carer note.
- [ ] Render all eight; photograph four; retain structured extraction ground truth and approved source crops/projections.
- [ ] Define roster, roles/languages, expected confirmations, supersession and per-recipient views, including unknown-member and adversarial inputs.

**Done when:** files and expected results exist for intake, recall, restricted sharing and privacy tests without real personal data.

## D2 · Policy store, trusted identity and context isolation

- [ ] Versioned SQLite records, restricted originals and approved field/source projections.
- [ ] Server-derived principal/family/chat/destination and authenticated internal MCP/service calls; no model-selected principal.
- [ ] Enforce category, field, relationship and grant policy before retrieval and delivery; group roster intersection and initialized DMs.
- [ ] Disable/isolate unfiltered Hermes memory, session search, raw file/terminal tools and cross-role history/compaction/caches; policy changes invalidate stale restricted context.
- [ ] Scoped versioned standing/one-shot grants, transactional consumption, neutral denials and audit; `/who-saw` Admin-only.
- [ ] Minimum adversarial checks in [privacy boundaries](docs/03-privacy-boundaries.md) pass through real tool/history and delivery paths.

**Done when:** Admin/Family/Carer and unknown identities receive exactly permitted fields/sources; spoofed principals, mixed originals, group/history leaks and revoked grants fail closed. Serving/MCP is enabled only behind this binding.

## D3 · Confirmed intake, scheduling and controlled sharing

- [ ] Admin DM photo → source-supported draft records; mixed originals stay Admin-only.
- [ ] Exact-version confirmation of category, medication/appointment details, assignee, timezone and intended sharing; uncertainty/conflicts block events.
- [ ] Atomic activation/supersession, future-event cancellation and durable idempotent outbox; restart/retry does not duplicate reminders.
- [ ] Per-recipient approved summary in English/Mandarin; no inferred clinical interaction warnings.
- [ ] Finance question → neutral acknowledgment → Admin DM approves exact view/version/recipient → requester DM; denial, one-shot retry and revocation tested.

**Done when:** confirmed synthetic intake creates the intended reminder and authorized summaries; supersession cancels the old future reminder; controlled sharing works without original-document leakage.

## D4 · Grounded recall, public lookup and one reusable skill

- [ ] Recall answers use permitted records and approved excerpts/crops; validate sources and destination before delivery.
- [ ] One Tavily public-only lookup in the main flow with query sanitization and locale domain allow-list.
- [ ] One persistent preconfigured scheduled skill survives restart and authorizes each recipient independently; `/skills` shows permitted descriptions.

**Done when:** a Family member sees the documented Month −4 change and allowed source crop, a cited public lookup works, and the reusable Monday task/reminder runs within current permissions.

## D5 · Minimum submission package and free judge access

- [ ] README distinguishes implemented/planned behavior; clean setup and usage section includes measured models/usage and external data flows.
- [ ] Entrant-funded demo with DM onboarding, Admin and Family test interactions, independent synthetic sessions/reset and documented instructions. No manual entrant wait.
- [ ] Draft Devpost fields/feedback; test access through an intake/confirmation, recall and share flow.

**Done when:** the submission could be filed with functioning Personal AI memory and a reusable skill. Judges can complete both sides of the permission workflow.

— **Minimum submittable product: D0–D5 and D9. D6–D8 are optional.** —

## D6 · Optional audio debrief and teaching skills

- [ ] Separately qualify audio endpoint/format/cost and capture consent before processing scripted consultation audio.
- [ ] Transcripts propose draft records/tasks; Admin confirms changes before schedules are superseded.
- [ ] Teach-by-chat produces a bounded structured skill with explicit trigger/recipient confirmation, no unrestricted tool authority.

**Done when:** demonstrated audio and taught-skill flows preserve all minimum safety and permission gates.

## D7 · Optional isolation integration and data map

- [ ] Qualify OpenShell/NemoClaw network/credential isolation if selected; record actual deployed boundary.
- [ ] Admin-only data map/export of categories, authorized access/delivery audit and outbound calls.
- [ ] Repeat relevant bypass tests after runtime/tool changes. Minimum privacy checks were already required at D2.

**Done when:** additional isolation and visibility are evidenced; no claim that OpenShell enforces family roles.

## D8 · Optional breadth and polish

- [ ] Expand to the full six-month, 20-document set.
- [ ] Per-recipient grounded weekly digest and cached translations with current permissions.
- [ ] Viewer expiry enforced at retrieval and delivery, including queued events and stale context.

**Done when:** optional features can reset and run without weakening the minimum.

## D9 · Video and submission

- [ ] Rehearse and record the actual 2:50 minimum script: private intake/confirmation, reminder, recall, controlled sharing, persistent skill and deployed data flows.
- [ ] Public YouTube, public licensed source, testing instructions, Devpost feedback and city attendance declaration verified.
- [ ] Fund and maintain self-service access through 16 Dec, 04:00 SGT.

**Done when:** submission confirmed on Devpost. Record optional scenes only when their gates passed.

## Order of work

D0 → D1 → D2 → D3 → D4 → D5 → D9. D1 is independent of infrastructure. Qualify Kin's image/model path early while Upgradient waits for beta approval; prioritize Upgradient's verified minimum once access is available. Insert D6–D8 only after D5 without jeopardizing submission. Privacy, confirmation and the reusable skill are minimum scope.
