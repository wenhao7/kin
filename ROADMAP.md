# Roadmap

Sequential deliverables. Each is sized for one working burst and leaves the repo in a working state. No dates except the fixed ones below.

**Fixed dates:** submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judging 1–15 Dec 2026; the demo Telegram group must stay up until 15 Dec.

## Deliverables

### D0 · Spike: runtime and models
- [ ] Telegram bot created; test group with two test accounts. Note: bot, group and admin account done; second account pending.
- [ ] Hermes Agent running; replies in the group and in DM; comes back after a restart. Note: group replies verified; DM and restart pending. Hermes' own memory is off by design; the family's memory is Kin's store (D2).
- [x] A Token Factory vision model accepts an image (`make check` → `vision:image`); Super answers a text call. Note: Nemotron 3 Nano Omni is not in the public catalog for our key, so the vision fallback in `docs/05-architecture.md` applies (`openbmb/MiniCPM-V-4_5` for extraction; Nemotron for classification and answers). No audio-capable model is listed, so audio is out of scope.
- [ ] OpenShell/NemoClaw: Hermes runs inside the sandbox with network allow-list (Telegram, Token Factory, Tavily). If this does not work within the burst, continue without it and revisit at D7. Note: deferred to D7; Hermes runs in plain Docker with host-reaching toolsets disabled.
- [x] GitHub repo created; Apache-2.0 visible in About. Note: repo is private; make it public before submission (D5).

Note: Hermes runs containerised (official installer into `./hermes/home` at first start); the host-install fallback was not needed.

**Done when:** a photo sent to the group is described back by Kin using the Token Factory vision model. Met: a captioned photo in the test group was described correctly.

### D1 · Synthetic family, minimum set
- [ ] Ground-truth JSON for 8 documents: discharge summary, 3 medication labels, 1 appointment slip, 1 clinic memo (Month −4), 1 insurance claim letter, 1 handwritten carer note.
- [ ] Templates render to PDF/PNG (`make setup-data`); 4 printed and photographed on a kitchen table — **YOU**.
- [x] Member roster with roles and languages (`config/members.yaml`; Telegram IDs in `.env`).

**Done when:** the 8 documents exist as clean renders, photos, and ground truth.

### D2 · Bridge and intake
Two bursts; the bridge first ([docs/05-architecture.md](docs/05-architecture.md#hermes--kin)).
- [ ] `kin serve`: kin API (`KIN_API_TOKEN`), SQLite + file store partitioned by visibility, roster loaded, scheduler; compose runs it with `restart: unless-stopped`.
- [ ] Kin plugin (`hermes/plugins/kin`, mounted and enabled): caller identity from the gateway session; `pre_gateway_dispatch` routes photos/PDFs to intake, answers voice notes with the fixed reply, and drops group text not addressed to Kin.
- [ ] Telegram sender in kin (Bot API); a refused DM asks the member in the group to tap Start.
- [ ] Photo → fields and text (vision model) → category and document type (Nano) → record with source → events (medication times, refills, appointment).
- [ ] Conflict check against existing records; one clarifying question when needed; admin confirms a low-confidence category in DM.
- [ ] Group post at the group's computed level, in English plus Mandarin for `zh` members; restricted items to the DMs of members who may see them.
- [ ] Reminders delivered by DM to the responsible member at local time.

**Done when:** the discharge summary photo produces the medication table, reminders for the carer, and a bilingual group post, and the records survive `make down && make up`.

### D3 · Boundaries
- [ ] `retrieve(query, principal)` as the only read path, behind `kin_ask`; policy and grants applied before model context; group questions capped at the group's level.
- [ ] Share-request flow: redirect to the asker, admin DM with the Yes / No / Just this once reply keyboard resolved by the hook, grant stored, asker answered by DM.
- [ ] Audit log; `/who_saw`, `/roles`, `/help`.

**Done when:** a Family member's finance question in the group completes the share flow and appears in `/who_saw`.

### D4 · Grounded recall and lookups
- [ ] Natural-language questions answered from permitted records; Kin sends the source photo or excerpt as a reply to the question, and the answer cites it.
- [ ] One allow-listed Tavily lookup flow (public scheme rules, e.g. Home Caregiving Grant, CHAS) through `kin_lookup`, no names or record content in the query.

**Done when:** "Kin, what did Dr Tan change at the last visit?" returns the change and the Month −4 memo photo.

— **Minimum submittable product.** From here every deliverable is optional; never start one that breaks the state above. —

### D5 · Submission skeleton
- [ ] Repo public; README quick start verified on a clean machine; `.env.example`.
- [ ] "How we use Nebius and NVIDIA" section drafted with real numbers.
- [ ] Demo group "Tan Family" with invite link: judges get `default_role` and a greeting with the test script; `make demo-reset` restores Week 0 (nightly host cron during 1–15 Dec). Test script in the README: intake photo, recall question, finance question (share redirect), scheme lookup, clinical-advice question (refusal).
- [ ] Draft Devpost description and feedback notes.

**Done when:** the submission could be filed today.

### D6 · Visit debrief and skills
- [ ] After-visit summary photo (Week +1) → superseding medication records → action items with owners → next appointment → per-role posts.
- [ ] Skills in Kin's scheduler: two pre-taught (Monday pill-organiser reminder; cardiology prep list); `/skills` lists them; the admin teaches a new one in DM through `kin_teach`.

**Done when:** the Week +1 after-visit summary produces records and tasks, and the Monday reminder fires.

### D7 · Sandbox and privacy proof
- [ ] OpenShell/NemoClaw integration completed if deferred at D0 (one timeboxed burst; if it does not work, the docs and video keep it as planned).
- [ ] Data-map view: records by category, audit log, outbound calls made (read-only page or `/export`).
- [ ] Adversarial test set: clinical-advice requests refused; in-family prompt-injection and impersonation attempts do not leak.

**Done when:** the data-map scene in the video can be recorded from the running system.

### D8 · Full dataset and polish
- [ ] Remaining documents to reach the 20-document set; full six-month timeline loaded.
- [ ] Weekly digest per role and language (Kin's scheduler or a Nebius Serverless Job).
- [ ] Respite viewer with `expires_at`.

**Done when:** the demo group can be reset to Week 0 with the full history.

### D9 · Video and submission
- [ ] Script rehearsed; kitchen scene, intake, recall, boundary, debrief, data map recorded live; safety line stated; Token Factory and Nemotron named in audio.
- [ ] Uploaded to YouTube (public); Devpost form complete; feedback submitted; city selected if applicable.

**Done when:** the submission is confirmed on Devpost.

## Order of work

D0 → D1 → D2 → D3 → D4 → D5 → D9 is the shortest path to a valid submission; D1 needs no infrastructure and can run alongside the others. After D5, the OpenShell/NemoClaw burst (D7's first item) comes first, because it is a named track tool and closes the host-network gap; then D6, the rest of D7 and D8, as far as effort allows. D9 is started no later than the final working burst before the deadline, whatever else is unfinished.
