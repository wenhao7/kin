# 02 · Product

Target specification. Current code loads configuration/policy and performs setup checks; serving, storage, retrieval and delivery are not implemented.

## Scope

**Minimum:** one synthetic family and care recipient; verified Admin, Family and Carer Telegram identities; private photo intake; confirmed medication/appointment records; one reminder; English/Mandarin authorized summaries; grounded recall; controlled sharing; an access/delivery audit; one reusable scheduled skill; one public-only lookup.

**Optional:** PDF/audio intake, consultation prep/debrief, natural-language skill creation, weekly digests, Viewer expiry, full six-month data and a data-map page. These cannot weaken minimum controls.

**Out:** multiple recipients, WhatsApp, EHR/clinic/pharmacy integrations, wearables, payments and clinical advice. Fine-grained arbitrary ACL editing is out of scope; narrowly scoped approved sharing is part of the minimum.

## Roles and onboarding

| Role | Demo member | Permitted view | Actions |
|---|---|---|---|
| Admin | Mei Ling | All family records | Assign roles, confirm intake/schedules, authorize shares |
| Family | Wei Jie / Bee Lian | Approved medical summary, medication, appointments and shared notes | Ask, add own notes, request sharing |
| Carer | Siti | Confirmed schedule, assigned tasks, approved care instructions and emergency contacts | Confirm own tasks, submit observations |
| Viewer (optional) | Respite carer | Confirmed schedule and assigned tasks while valid | Confirm assigned tasks |

Every member must start a DM with Kin before private delivery is enabled. Admin assignment uses a verified Telegram ID and enrolled family/chat; names, forwarded text and model-supplied IDs never establish identity. Unknown or expired members receive no private information. Viewer access stays disabled until expiry enforcement exists.

## Records and permitted views

Categories: `medical`, `medication`, `appointments`, `tasks`, `observations`, `finance`, `legal`, `admin`, `notes`. Each record carries a version, category, permitted field projection, source spans, creator and timestamps. The policy matrix sets the maximum access level; [03-privacy-boundaries.md](03-privacy-boundaries.md) defines narrower fields, relationships, history and delivery controls.

## Minimum flows

**Private intake.** Caregiver sends a photo to Kin in DM. The D0-selected extraction model proposes fields and source spans; Nano helps classify them. Mixed-category documents are split into typed records while the original stays restricted. Admin reviews categories, uncertain text and conflicts, then explicitly confirms schedule details and any group summary. Only confirmed records create events. Uploading into the group already discloses the original to its members; Kin cannot reverse that disclosure. Group intake is limited to deliberately shared updates.

**Schedule and reminders.** Preserve the clinician's recorded instructions without inferring dose changes or choosing times absent from the source. Admin confirms times, timezone, assignee and start/end details. Conflicts block activation. Superseding a schedule cancels its future events. Delivery checks the assignee's current permission; an outbox and stable event ID handle restart/retry without creating duplicate reminders. Explain the reminder using an authorized source excerpt.

**Grounded ask.** Gateway-authenticated identity and destination define the request. Retrieval supplies only allowed records/fields and source excerpts; Super composes an answer from that projection. Validate references and destination permission before sending. A Family summary does not include the entire medical document. If no permitted source supports the answer, say it is unknown; never disclose whether a hidden record exists.

**Share request.** A finance/legal question gets a neutral group acknowledgment without record details. The requester receives a private request status. Admin sees the requester, exact fields/source excerpt, record version and destination in DM, then chooses Yes, No or Just this once. Yes is a revocable standing grant for that scoped item/view; Just this once authorizes one bounded answer. Neither grants the entire finance/legal category implicitly. Answers go privately to the named requester; a failed delivery cannot expand the audience.

**Reusable skill.** One preconfigured instruction survives restart: “Every Monday remind Siti to refill the pill organiser and send Mei Ling a confirmation.” Admin confirms trigger, assignee, recipients and timezone. The trigger creates a bounded task/reminder; retrieval and each recipient's view are independently authorized at execution. `/skills` displays only an allowed description. Teaching arbitrary skills through chat is optional.

**Public lookup.** Kin can retrieve public scheme rules or clinic hours. Build the Tavily query from a validated public topic and allow-listed public institution; exclude family names, IDs, medical details and private record text. Domain filtering alone does not sanitize a query. Return the public source; do not decide personal eligibility.

## Optional flows

Consultation audio needs separately validated modality support and recorded consent before processing. Transcripts become draft records with source segments; changes require Admin confirmation before superseding schedules. Weekly digests use fresh per-recipient authorized projections, never an Admin digest that is subsequently redacted. Teach-by-chat yields a structured, confirmed skill, not unrestricted code or tool authority.

## Chat conventions

- Short group posts use the intersection of current verified members' views; unknown membership blocks sensitive group delivery. Changes in membership recheck authorization.
- Detailed answers and sensitive intake use DM. Group language variants use the same permitted fields; translation cannot add facts.
- One clarification at a time. Grounded answers/reminders carry a dated, permitted excerpt; raw document/file access is never implied.
- `/roles`, `/who-saw` and `/export` are Admin-only; `/skills` is role-filtered. `/who-saw` reports retrieval/delivery, not proof a human read a message.
- Disable Telegram group privacy mode only for the enrolled demo group if full-message processing is needed; enforce identity and context policy on those messages.
