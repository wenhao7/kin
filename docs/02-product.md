# 02 · Product

Target specification. Today the code loads configuration and policy and runs setup checks; serving, storage, retrieval and delivery are not implemented.

## Scope

**Minimum:** one synthetic family and care recipient; verified Admin, Family and Carer Telegram identities; private photo intake with Admin confirmation; confirmed medication/appointment records; reminders; Admin-confirmed group summaries in English and Mandarin; grounded recall; scoped sharing with audit; one reusable scheduled skill; one public-only lookup.

**Optional:** audio intake and debrief, teach-by-chat skills, weekly digest, viewer expiry, full six-month fixture, data-map page, OpenShell isolation.

**Out:** multiple care recipients, WhatsApp, clinic/pharmacy/EHR integrations, wearables, payments, clinical advice, arbitrary ACL editing.

## Roles

| Role | Demo member | Permitted view | Actions |
|---|---|---|---|
| Admin | Mei Ling (daughter) | All records | Assign roles, confirm intake and schedules, approve shares |
| Family | Wei Jie (son, overseas), Bee Lian (aunt) | Confirmed medical summary, medication, appointments, shared notes | Ask, add own notes, request sharing |
| Carer | Siti (helper) | Confirmed schedule, assigned tasks, care instructions, emergency contacts | Confirm own tasks, submit observations |
| Viewer (optional) | Respite carer | Schedule and assigned tasks while valid | Confirm assigned tasks |

Roles are bound to verified Telegram user IDs by the Admin. Every member opens a DM with the bot first (bots cannot start one). Unknown senders get nothing.

## Records

Categories: `medical`, `medication`, `appointments`, `tasks`, `observations`, `finance`, `legal`, `admin`, `notes`. A record has a version, category, permitted field projection, source excerpt, creator and timestamps. A document may hold several categories; its original stays Admin-only and derived records reference approved excerpts. The matrix in [03-privacy-boundaries.md](03-privacy-boundaries.md) sets the maximum access; fields narrow it.

## Minimum flows

**Private intake.** Admin sends a photo to Kin in DM. The extractor proposes fields and source spans; Nano/Lightning classifies. Kin shows a draft with uncertain fields marked. Admin confirms category, details, assignee, timezone and whether to post a summary. Only confirmed records create events. (Uploading to the group would expose the original to everyone; group intake is limited to deliberately shared updates.)

**Schedule and reminders.** Times and assignees come from the confirmed record; Kin never infers doses or times. Conflicts block activation. Superseding a record cancels its future events. Reminders go to the assignee's DM with the source excerpt; restart and retry reuse event IDs so nothing duplicates.

**Group summary.** After confirmation, Kin posts the Admin-approved summary to the group in English and Mandarin. The group never receives finance, legal or raw documents.

**Recall.** The gateway supplies the verified sender and chat. Retrieval returns only the records and fields that role may see; Super composes the answer; Kin attaches the approved excerpt and re-checks the destination before sending. No permitted source → "I don't know", without revealing whether a hidden record exists.

**Sharing.** A finance/legal question in the group gets a neutral acknowledgment. Admin receives a DM naming the requester, the record and the excerpt, with Yes (standing grant for that record), No, or Just this once (one answer). The answer goes to the requester's DM; the decision is audited. Grants are per record, never per category.

**Reusable skill.** One preconfigured, Admin-confirmed instruction survives restart: "Every Monday 08:00, remind Siti to refill the pill organiser and tell Mei Ling when done." Recipients are re-authorised at execution; `/skills` shows permitted descriptions.

**Public lookup.** Scheme rules or clinic hours via Tavily, built from a public topic and the locale allow-list; family names, IDs and record text never enter the query. Kin returns the public source and does not decide eligibility.

## Chat conventions

- One clarifying question at a time; short group posts; detail and anything restricted in DM.
- Every personal answer and reminder carries a dated, permitted excerpt.
- Mandarin variants use the same confirmed fields; translation adds no facts.
- Admin commands: `/roles`, `/who-saw`, `/export`. `/skills` is role-filtered. `/demo` role switch exists only in the disposable judge fixture.
- Group privacy mode is off (or the bot is a group admin) so Kin sees group messages; identity and policy are enforced on every message regardless.
