# Roadmap

Sequential deliverables. Tick a box only with recorded evidence. No time estimates.

**Fixed dates:** submission closes **Fri 30 Oct 2026, 10:00 PDT (Sat 31 Oct, 01:00 SGT)**; judging ends **15 Dec 2026, 12:00 PST (16 Dec, 04:00 SGT)** and the demo bot stays up until then.

## Status

- The kin service (`kin serve`) holds the store and enforces the policy at retrieval and on every reply; private intake with Admin confirmation, reminders, sharing, the public lookup and the Monday skill work. The containerised Hermes gateway runs on Nebius with the Kin plugin and Kin's persona, its memory/skills/cron/host tools off and the stack isolated from other deployments on the host.
- Live validation on 18–19 Oct with two accounts (Admin on one phone; the second played Wei Jie, then Siti): D0, D2, D3 and D4 passed, including reminders, the restart check and the Monday skill. On 19 Oct the group share request and the new Admin commands (`/who_saw`, `/revoke`, menus) passed too. Requests for an original and requests to post now get fixed replies.
- Nano Omni is dedicated-only; the extractor chosen at D0 is `openbmb/MiniCPM-V-4_5` (`KIN_MODEL_VISION`).
- Upgradient's Sandboxes approval does not affect Kin; D0 and D1 can proceed now.

## D0 · Runtime, identity and models

- [x] Bot created; test group with Admin, Family and Carer accounts; each account has opened a DM with the bot. Evidence: bot (privacy off, `can_read_all_group_messages=True`); Admin account and a second account in the group, both with DMs open; the second account plays Family and Carer in separate takes (`KIN_MEMBER_IDS`).
- [x] Hermes gateway replies in group and DM (container or host install recorded); installed version and native tool/memory paths inventoried. Evidence: container install (official installer into `./hermes/home`); Hermes v0.21.7; replies in the group and in both accounts' DMs; inventory in `docs/05-architecture.md` (Hermes hardening).
- [x] Vision extractor chosen from `make models` and one image call passes (`make check`); Nano or Lightning picked for classification; Super answers a structured call. Audio and Ultra optional. Evidence: Super and Nano return schema-valid JSON (`response_format` json_schema); question classification is only a hint (Super 4/5 with category descriptions, Nano 17–21 s), so boundaries never depend on it. Note: MiniCPM-V 4.5 chosen, `vision:image` passes, and it transcribed the fixture's discharge medication table (6/6 rows exact, 705 input tokens, 4.1 s) and handwritten carer note exactly from clean renders, and every ground-truth value on 2000 px phone photos of the documents on a monitor (70/70 verbatim); on low-resolution photos of printed copies (646–1149 px) it read 68/70 and misread "Glipizide" on both discharge pages, an intake case in `fixtures/expected.json`; Nano picked. No public audio-capable model.
- [ ] Public repo with Apache-2.0 visible in About. Note: GitHub detects Apache-2.0; the repo is private until it is made public.

**Done when:** a synthetic photo sent in Admin DM is described back by the chosen extractor, and a bounded structured text call succeeds or fails truthfully. Met: both discharge-summary photos sent in the Admin's DM came back as one draft (the "Glibpizide" misread flagged). The public repo is part of D5.

## D1 · Minimum synthetic fixture

- [x] Eight documents (discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter, carer note) rendered; four photographed; ground truth with fields, source spans and expected per-role views. Evidence: `fixtures/documents/`, `fixtures/renders/` (`make fixtures`), `fixtures/photos/` (printed copies on a table), `tests/test_fixtures.py`.
- [x] Roster with roles and languages; expected outcomes for confirmation, supersession, denied recall and share flows. Evidence: `config/members.yaml`; `fixtures/expected.json`; `tests/test_fixtures.py`.

**Done when:** fixtures and expected results exist for intake, recall, sharing and the privacy tests. No infrastructure needed. Met: `fixtures/` and `fixtures/expected.json`.

## D2 · Identity, policy store and Hermes isolation

- [x] SQLite store: members, versioned records, restricted originals, approved excerpts, events, grants, audit. Evidence: `kin/store.py`; `make seed` loads Week 0 (`kin/seed.py`).
- [x] Principal derived from the gateway's authenticated sender and chat; `retrieve(query, principal)` is the only read path; category and field projection applied before model context; unknown identity/category fails closed. Evidence: `kin/retrieve.py`; `tests/test_retrieve.py`, `tests/test_api.py`, `tests/test_plugin.py` (Admin, Family, Carer, unknown sender, spoofed chats, forged tool arguments, originals, group-wide field limits).
- [x] Hermes native memory, session search and file/terminal tools disabled over family data; group and DM contexts separated. Evidence: `hermes/config.yaml` applied (`make hermes-config`); `hermes prompt-size --platform telegram` lists clarify, todo and vision only; sessions keyed per chat and user.
- [x] Kin plugin in Hermes (caller from the gateway session, `pre_gateway_dispatch` routing, Kin's tools); kin API on the internal network only with `KIN_API_TOKEN`; `/who_saw` Admin-only. MCP is not used: it carries no caller identity. Evidence: live in the test group and Admin DM: unaddressed group text ignored, group and DM questions answered through `kin_ask` (group capped to every member's fields), voice note and document replies, `/who_saw` refused in the group and answered in DM; audit rows in the kin store.
- [x] Minimum privacy tests pass through the real gateway path (03-privacy-boundaries.md). Evidence, live on 18 Oct:
  - An unknown sender got nothing: Kin ignored it in the group, and Hermes' allow-list blocked its DM.
  - The "This is Mei Ling on Wei Jie's phone" request got the neutral share reply.
  - Family finance questions: neutral reply, then once, standing, revoke and No.
  - The Carer asking for the discharge letter got no original and no diagnoses.
  - Family's blood-pressure question returned no clinical notes.
  - The Mandarin group post held no diagnosis.
  - The lookup sent Tavily only "Home Caregiving Grant: …" (audited).
  - Hermes memory and session search are off.

  Forged tool arguments and direct store access are covered in `tests/test_plugin.py`.

**Done when:** Admin, Family, Carer and an unknown sender each receive exactly their permitted fields; spoofed principals and a mixed original fail closed. Met live for all four on 18 Oct.

## D3 · Intake, confirmation, reminders, sharing

- [x] Admin DM photo → extractor → draft records with source excerpts; mixed originals stay Admin-only. Evidence: `kin/extract.py` (thinking off; section headings detected first, 12/12 on the fixture pages), `kin/intake.py`, `tests/test_intake.py`.
- [x] Admin confirms category, medication/appointment details, assignee, timezone; conflicts and unreadable fields block activation. Evidence: name check (Glibpizide → Glipizide?), 9:30 vs 10:30 conflict, one question at a time, Confirm only when all are settled (`tests/test_intake.py`).
- [x] Activation creates events; supersession cancels future events; restart does not duplicate reminders. Evidence: Metformin 850 mg and Glipizide reminders cancelled, new schedule and course end date, a second tick after restart sends nothing (`tests/test_intake.py`).
- [x] Admin-confirmed summary to the group in English and Mandarin; carer reminder in DM with the source excerpt. Evidence: group post only after "Post to group", group-visible fields only (no diagnoses, finance or IDs); Mandarin via Super with medicine names masked (3/3 live translations kept every name and number).
- [x] Finance question → neutral group reply → Admin DM Yes / No / Just this once (reply keyboard, resolved by the hook) → private answer; audited. Kin sends through the Bot API; a refused DM asks the member to tap Start. Evidence: once, standing (DM only, excerpt only), `/revoke` and No (`tests/test_intake.py`).

**Done when:** a confirmed synthetic intake yields the right reminder and summaries, supersession cancels the old reminder, and sharing works without leaking the original. Met in the automated tests. Live on 18 Oct:
- The discharge photos became one draft, with the misread name flagged.
- On Confirm, the Metformin 850 mg and Glipizide reminders stopped.
- The new schedule went to Siti's DM.
- The English and Mandarin group post was approved and posted.
- Shares worked once, standing, revoked and refused, and back-to-back requests waited their turn.

Live on 19 Oct:
- At 08:00, 08:30 and 13:30, reminders followed the new schedule.
- The restart check passed: after a full `make down && make up` at 13:30:33, the 13:30 reminder (sent at 13:30:20) was not sent again by 13:41.

Fixed during validation: lost Admin questions (`kin/prompts.py`), follow-ups under a standing grant asking again, remapping an account, model citation markers, misleading replies about originals, member names in Mandarin, and a stale "Post to group" tap that let the model claim it had posted (keyboards are now removed when answered; the persona forbids claimed actions).

## D4 · Recall, lookup, reusable skill

- [x] Recall answers from permitted records with the approved excerpt; destination re-checked before delivery. Evidence: every reply passes Kin's reply check (plugin `transform_llm_output` → `/outbound`, `kin/answer.py`). Wei Jie's group question gets the Month −4 change with “Plan: start losartan 50 mg once a day in the morning.” appended. Replies holding something the chat may not see are withheld: the memo's blood-pressure note in Wei Jie's DM, the insurer's name in the group. Echoing the asker's own words is not withheld, so a question can't probe for a hidden diagnosis. Excerpts come only from this turn's records and aren't repeated when quoted. Confirmed intakes file their printed lines as excerpts. Kin names the care recipient (Ah Ma) from `config/members.yaml` and lists each medicine once (`tests/test_recall.py`, `tests/test_plugin.py`). Fixed on the way: in the group, fields were intersected at the capped level, which hid care instructions from group answers and posts; each role now contributes its own projection.
- [x] One Tavily lookup in the main flow with a public-only query and the locale allow-list. Evidence: `kin_lookup` matches a scheme in `locale/sg/locale.yaml` (`lookup_topics`) and sends only its name ("Home Caregiving Grant: eligibility, amount and how to apply"), with `include_domains` from the allow-list. Other domains are dropped, the reply gets the source link and the query is audited. On the deployed stack it returned pages from moh.gov.sg, aic.sg and ask.gov.sg.
- [x] One preconfigured Monday skill in Kin's scheduler survives restart; `/skills` shows it; recipients are authorised at execution. Evidence: `kin/skills.py`, a `tasks` record plus a weekly event, seeded as Admin-confirmed in Week 0. At Mon 08:00 after a restart it sends Siti one DM with a Done button, and a second tick after another restart sends nothing. Done reaches Mei Ling. `/skills` lists it in DM for Admin, Family and Carer, with the last run. With Siti removed from the roster nothing is sent and the Admin is told (`tests/test_skills.py`).

**Done when:** a Family member gets the Month −4 change with its excerpt, a cited public lookup works, and the Monday reminder fires after a restart. Met in the automated tests and through the plugin's code path against the deployed kin API (recall excerpt, withheld leak, live Tavily lookup). Live on 18 Oct: recall in the group and in DM ended with the plan excerpt; Super chose `kin_lookup` and answered with AIC and MOH links without deciding eligibility; `/skills` was role-filtered and DM-only. Live on 19 Oct, the Monday skill fired at 08:00 as its own message with a Done button. Siti's Done reached Mei Ling, and `/skills` showed the last run.

## D5 · Submission package and judge access

- [ ] README separates implemented from planned; "How we use Nebius and NVIDIA" filled with measured values.
- [ ] Self-service synthetic demo: judge joins a disposable fixture, uses `/demo` to act as Admin or Family, follows the test script (intake photo supplied, confirm, recall, share, `/skills`); `make demo-reset` (nightly during judging) isolates sessions. Repo public. Entrant-funded.
- [ ] Devpost text and feedback drafted; access verified from a clean session.

**Done when:** the submission could be filed with working memory, confirmed intake, sharing and the reusable skill.

— **Minimum submittable product: D0–D5 and D9. D6–D8 are optional.** —

## D6 · Visit debrief and teach-by-chat

- [ ] After-visit summary photo (Week +1) → drafts → Admin confirmation → superseding records, tasks with owners, next appointment. Audio stays out unless a dedicated Nano Omni endpoint is affordable; it would then need consent in chat first.
- [ ] Teach-by-chat yields a structured skill with confirmed trigger and recipients.

## D7 · Hardening and isolation

- [ ] Versioned grant binding (record/version, projection, recipient), transactional one-shot consumption, roster-intersection check for group posts, policy-version cache invalidation, delivery reconciliation, viewer expiry, deletion workflow.
- [ ] OpenShell/NemoClaw isolation (one timeboxed burst, first after D5; also closes the host-network gap); Admin data-map/export; privacy tests repeated after runtime changes.

## D8 · Breadth and polish

- [ ] Full 20-document, six-month fixture; weekly per-role digest; cached translations with permissions.

## D9 · Video and submission

- [ ] 2:50 script recorded from the real minimum: intake and confirmation, reminder, recall, sharing, skill, data flow.
- [ ] Public YouTube upload; Devpost fields, feedback, city declaration; judge access through 16 Dec, 04:00 SGT.

**Done when:** Devpost confirms submission. Start recording no later than the final working burst.

## Order of work

D0 → D1 → D2 → D3 → D4 → D5 → D9. D1 fits any spare burst. After D5, the OpenShell burst comes first among the optional items. Upgradient's verified minimum takes priority once Sandboxes access arrives; if Kin has not reached D5 when the final burst begins, submit Upgradient first.
