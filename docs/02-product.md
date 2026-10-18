# 02 · Product

Target specification. Today the code loads configuration and policy and runs setup checks; serving, storage, retrieval and delivery are not implemented.

## Scope

**Minimum:** one synthetic family and care recipient; verified Admin, Family and Carer Telegram identities; private photo intake with Admin confirmation; confirmed medication/appointment records; reminders; Admin-confirmed group summaries in English and Mandarin; grounded recall; scoped sharing with audit; one reusable scheduled skill; one public-only lookup.

**Optional:** visit debrief from a photographed after-visit summary, teach-by-chat skills, weekly digest, viewer expiry, full six-month fixture, data-map page, OpenShell isolation.

**Out:** audio (no public audio-capable model on Token Factory; voice notes get a fixed reply), multiple care recipients, WhatsApp, clinic/pharmacy/EHR integrations, wearables, payments, clinical advice, arbitrary ACL editing.

## Roles

| Role | Demo member | Permitted view | Actions |
|---|---|---|---|
| Admin | Mei Ling (daughter) | All records | Assign roles, confirm intake and schedules, approve shares |
| Family | Wei Jie (son, overseas), Bee Lian (aunt) | Confirmed medical summary, medication, appointments, own notes | Ask, add own notes, request sharing |
| Carer | Siti (helper) | Confirmed schedule, assigned tasks, care instructions, emergency contacts | Confirm own tasks, submit observations |
| Viewer (optional) | Respite carer | Schedule and assigned tasks while valid | Confirm assigned tasks |

Roles and languages come from `config/members.yaml`, bound to verified Telegram user IDs in `.env`; `/roles` shows the roster to the Admin. A member without a Telegram account can stay in the roster (Bee Lian in the demo): their language still shapes group summaries. Every member opens a DM with the bot first (bots cannot start one). Unknown senders get nothing; in the disposable judge fixture, `/demo` assigns the judge a role.

## Records

Categories: `medical`, `medication`, `appointments`, `tasks`, `observations`, `finance`, `legal`, `admin`, `notes`. A record has a version, category, permitted field projection, source excerpt, creator and timestamps. A document may hold several categories; its original stays Admin-only and derived records reference approved excerpts. The matrix in [03-privacy-boundaries.md](03-privacy-boundaries.md) sets the maximum access; fields narrow it.

## Minimum flows

**Private intake.** Admin sends a photo to Kin in DM. The extractor proposes fields and source spans; Nano/Lightning classifies. Kin shows a draft with uncertain fields marked. Admin confirms category, details, assignee, timezone and whether to post a summary. Only confirmed records create events. (Uploading to the group would expose the original to everyone; group intake is limited to deliberately shared updates.) A photo posted in the group or in another member's DM is not ingested; Kin replies once that documents go to the Admin by DM.

**Schedule and reminders.** Times and assignees come from the confirmed record; Kin never infers doses or times. Conflicts block activation. Superseding a record cancels its future events. Reminders go to the assignee's DM with the source excerpt; restart and retry reuse event IDs so nothing duplicates.

**Group summary.** After confirmation, Kin posts the Admin-approved summary to the group in English and Mandarin. The group never receives finance, legal or raw documents.

**Recall.** The gateway supplies the verified sender and chat. Retrieval returns only the records and fields that role may see; Super composes the answer; Kin attaches the approved excerpt and re-checks the destination before sending. No permitted source → "I don't know", without revealing whether a hidden record exists.

**Sharing.** A finance/legal question in the group gets a neutral acknowledgment. Admin receives a DM naming the requester, the record and the excerpt, with Yes (standing grant for that record), No, or Just this once (one answer). The answer goes to the requester's DM; the decision is audited. Grants are per record, never per category.

**Reusable skill.** One preconfigured, Admin-confirmed instruction survives restart: "Every Monday 08:00, remind Siti to refill the pill organiser and tell Mei Ling when done." Recipients are re-authorised at execution; `/skills` shows permitted descriptions.

**Public lookup.** Public scheme rules (e.g. Home Caregiving Grant, CHAS) via Tavily: the query is the name of a scheme listed in the locale pack, searched on the locale's allow-listed sites, so family names, IDs and record text never enter it. Kin returns the public source and does not decide eligibility.

## Chat conventions

- One clarifying question at a time; short group posts; detail and anything restricted in DM.
- Every personal answer and reminder carries a dated, permitted excerpt.
- Mandarin variants use the same confirmed fields; translation adds no facts: medicine names stay in English as on the label, and a translation missing any name or number is not posted.
- Admin commands: `/roles`, `/who_saw`, `/reminders`, `/revoke`, `/export` (Telegram commands allow only letters, digits and `_`), answered only in the Admin's DM. `/who_saw` and `/revoke` need no IDs: on their own they offer the documents or the active shares as buttons. `/who_saw` reports, by name and local time, who was shown what (answers, shared excerpts, reminders, group posts). Each chat's "/" menu lists only the commands that work there. Every slash command is Kin's; Hermes' own commands are not reachable from the family chats. `/skills` is role-filtered. `/demo` role switch exists only in the disposable judge fixture.
- In the group, Kin answers text only when addressed: its name, an @mention, or a reply to one of its messages. Family members can talk among themselves without Kin chiming in.
- Voice notes are not processed; Kin replies that it can't listen yet and asks for text.
- Group privacy mode is off (or the bot is a group admin) so Kin sees group messages; identity and policy are enforced on every message regardless.
