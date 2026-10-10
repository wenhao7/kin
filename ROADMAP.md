# Roadmap

Sequential deliverables. Each is sized for one working burst and leaves the repo in a working state. No dates except the fixed ones below.

**Fixed dates:** submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judging 1–15 Dec 2026; the demo Telegram group must stay up until 15 Dec.

## Deliverables

### D0 · Spike: runtime and models
- [ ] Telegram bot created; test group with two test accounts.
- [ ] Hermes Agent running; replies in the group and in DM; memory persists across restarts.
- [ ] Nemotron Nano Omni accepts an image and an audio file through Token Factory; Super answers a text call.
- [ ] OpenShell/NemoClaw: Hermes runs inside the sandbox with network allow-list (Telegram, Token Factory, Tavily). If this does not work within the burst, continue without it and revisit at D7.
- [ ] GitHub repo created; Apache-2.0 visible in About.

**Done when:** a photo sent to the group is described back by Kin using Nano Omni.

### D1 · Synthetic family, minimum set
- [ ] Ground-truth JSON for 8 documents: discharge summary, 3 medication labels, 1 appointment slip, 1 clinic memo (Month −4), 1 insurance claim letter, 1 handwritten carer note.
- [ ] Templates render to PDF/PNG; 4 photographed on paper.
- [ ] Member roster with roles and languages.

**Done when:** the 8 documents exist as clean renders, photos, and ground truth.

### D2 · Intake
- [ ] Photo → fields and text (Nano Omni) → category (Nano) → record with source → events (medication times, refills, appointment).
- [ ] Conflict check against existing records; one clarifying question when needed; admin confirm for low-confidence categories.
- [ ] Group summary in English; Mandarin version for members set to `zh`; restricted items to DM.
- [ ] Reminders delivered to the responsible member.

**Done when:** the discharge summary photo produces the medication table, reminders for the carer, and a bilingual group post.

### D3 · Boundaries
- [ ] Data model and partitioned SQLite store.
- [ ] `retrieve(query, principal)` as the only memory read path; policy matrix applied before model context.
- [ ] Share-request flow: group redirect, admin DM with Yes / No / Just this once, grant stored.
- [ ] Audit log; `/who-saw`.

**Done when:** a Family member's finance question in the group completes the share flow and appears in `/who-saw`.

### D4 · Grounded recall and lookups
- [ ] Natural-language questions answered from permitted records with the source image/excerpt attached.
- [ ] One allow-listed Tavily lookup flow (scheme rules or clinic hours), no record content in the query.

**Done when:** "What did Dr Tan change at the last visit?" returns the change and the Month −4 memo photo.

— **Minimum submittable product.** From here every deliverable is optional; never start one that breaks the state above. —

### D5 · Submission skeleton
- [ ] README quick start verified on a clean machine; `.env.example`.
- [ ] "How we use Nebius and NVIDIA" section drafted with real numbers.
- [ ] Judge demo group with invite link and reset script; README test script.
- [ ] Draft Devpost description and feedback notes.

**Done when:** the submission could be filed today.

### D6 · Debrief and skills
- [ ] Consult audio (scripted, pre-recorded) → transcription and summary (Nano Omni) → superseding medication records → action items → per-role posts; consent captured in chat first.
- [ ] Two pre-taught skills running on schedule/trigger; `/skills` lists them; teach-by-chat for a new skill.

**Done when:** the Week +1 consult produces records and tasks, and the Monday reminder fires.

### D7 · Sandbox and privacy proof
- [ ] OpenShell/NemoClaw integration completed if deferred at D0.
- [ ] Data-map view: records by category, audit log, outbound calls made (read-only page or `/export`).
- [ ] Adversarial test set: clinical-advice requests refused; in-family prompt-injection attempts do not leak.

**Done when:** the data-map scene in the video can be recorded from the running system.

### D8 · Full dataset and polish
- [ ] Remaining documents to reach the 20-document set; full six-month timeline loaded.
- [ ] Weekly digest per role and language (Hermes scheduler or Nebius Serverless Job).
- [ ] Respite viewer with `expires_at`.

**Done when:** the demo group can be reset to Week 0 with the full history.

### D9 · Video and submission
- [ ] Script rehearsed; kitchen scene, intake, recall, boundary, debrief, data map recorded live; safety line stated; Token Factory and Nemotron named in audio.
- [ ] Uploaded to YouTube (public); Devpost form complete; feedback submitted; city selected if applicable.

**Done when:** the submission is confirmed on Devpost.

## Order of work

D0 → D1 → D2 → D3 → D4 → D5 → D9 is the shortest path to a valid submission. D6–D8 are inserted between D5 and D9 in the order listed, as far as effort allows. D9 is started no later than the final working burst before the deadline, whatever else is unfinished.
