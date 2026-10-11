# Roadmap

Sequential deliverables. Tick a box only with recorded evidence. No time estimates.

**Fixed dates:** submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judging ends **15 Dec 2026, 12:00 PST (16 Dec, 04:00 SGT)** and the demo bot stays up until then.

## Status

- Configuration, policy loading, setup checks and container templates exist. `kin serve`, memory, intake, reminders and enforcement are not implemented.
- Nano Omni is dedicated-only; the extractor is a public vision model chosen at D0 (`KIN_MODEL_VISION`).
- Upgradient's Sandboxes approval does not affect Kin; D0 and D1 can proceed now.

## D0 · Runtime, identity and models

- [ ] Bot created; test group with Admin, Family and Carer accounts; each account has opened a DM with the bot.
- [ ] Hermes gateway replies in group and DM (container or host install recorded); installed version and native tool/memory paths inventoried.
- [ ] Vision extractor chosen from `make models` and one image call passes (`make check`); Nano or Lightning picked for classification; Super answers a structured call. Audio and Ultra optional.
- [ ] Public repo with Apache-2.0 visible in About.

**Done when:** a synthetic photo sent in Admin DM is described back by the chosen extractor, and a bounded structured text call succeeds or fails truthfully.

## D1 · Minimum synthetic fixture

- [ ] Eight documents (discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter, carer note) rendered; four photographed; ground truth with fields, source spans and expected per-role views.
- [ ] Roster with roles and languages; expected outcomes for confirmation, supersession, denied recall and share flows.

**Done when:** fixtures and expected results exist for intake, recall, sharing and the privacy tests. No infrastructure needed.

## D2 · Identity, policy store and Hermes isolation

- [ ] SQLite store: members, versioned records, restricted originals, approved excerpts, events, grants, audit.
- [ ] Principal derived from the gateway's authenticated sender and chat; `retrieve(query, principal)` is the only read path; category and field projection applied before model context; unknown identity/category fails closed.
- [ ] Hermes native memory, session search and file/terminal tools disabled over family data; group and DM contexts separated.
- [ ] Kin MCP served to Hermes on the internal network only; `/who-saw` Admin-only.
- [ ] Minimum privacy tests pass through the real gateway path (03-privacy-boundaries.md).

**Done when:** Admin, Family, Carer and an unknown sender each receive exactly their permitted fields; spoofed principals and a mixed original fail closed.

## D3 · Intake, confirmation, reminders, sharing

- [ ] Admin DM photo → extractor → draft records with source excerpts; mixed originals stay Admin-only.
- [ ] Admin confirms category, medication/appointment details, assignee, timezone; conflicts and unreadable fields block activation.
- [ ] Activation creates events; supersession cancels future events; restart does not duplicate reminders.
- [ ] Admin-confirmed summary to the group in English and Mandarin; carer reminder in DM with the source excerpt.
- [ ] Finance question → neutral group reply → Admin DM Yes / No / Just this once → private answer; audited.

**Done when:** a confirmed synthetic intake yields the right reminder and summaries, supersession cancels the old reminder, and sharing works without leaking the original.

## D4 · Recall, lookup, reusable skill

- [ ] Recall answers from permitted records with the approved excerpt; destination re-checked before delivery.
- [ ] One Tavily lookup in the main flow with a public-only query and the locale allow-list.
- [ ] One preconfigured Monday skill survives restart; `/skills` shows it; recipients are authorised at execution.

**Done when:** a Family member gets the Month −4 change with its excerpt, a cited public lookup works, and the Monday reminder fires after a restart.

## D5 · Submission package and judge access

- [ ] README separates implemented from planned; "How we use Nebius and NVIDIA" filled with measured values.
- [ ] Self-service synthetic demo: judge joins a disposable fixture, uses `/demo` to act as Admin or Family, follows the test script (intake photo supplied, confirm, recall, share, `/skills`); reset isolates sessions. Entrant-funded.
- [ ] Devpost text and feedback drafted; access verified from a clean session.

**Done when:** the submission could be filed with working memory, confirmed intake, sharing and the reusable skill.

— **Minimum submittable product: D0–D5 and D9. D6–D8 are optional.** —

## D6 · Audio debrief and teach-by-chat

- [ ] Audio endpoint/cost qualified; consent captured in chat; transcript → drafts → Admin confirmation.
- [ ] Teach-by-chat yields a structured skill with confirmed trigger and recipients.

## D7 · Hardening and isolation

- [ ] Versioned grant binding (record/version, projection, recipient), transactional one-shot consumption, roster-intersection check for group posts, policy-version cache invalidation, delivery reconciliation, viewer expiry, deletion workflow.
- [ ] OpenShell/NemoClaw isolation; Admin data-map/export; privacy tests repeated after runtime changes.

## D8 · Breadth and polish

- [ ] Full 20-document, six-month fixture; weekly per-role digest; cached translations with permissions.

## D9 · Video and submission

- [ ] 2:50 script recorded from the real minimum: intake and confirmation, reminder, recall, sharing, skill, data flow.
- [ ] Public YouTube upload; Devpost fields, feedback, city declaration; judge access through 16 Dec, 04:00 SGT.

**Done when:** Devpost confirms submission. Start recording no later than the final working burst.

## Order of work

D0 → D1 → D2 → D3 → D4 → D5 → D9. D1 fits any spare burst. Upgradient's verified minimum takes priority once Sandboxes access arrives; if Kin has not reached D5 when the final burst begins, submit Upgradient first.
