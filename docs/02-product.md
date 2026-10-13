# 02 · Product

## Scope

**In:** one family, one care recipient; Telegram group + DMs; photo/PDF intake; medication and appointment schedule with reminders; grounded Q&A; role × category boundaries with share requests and audit; appointment prep and debrief; weekly digest; skills taught by chat; allow-listed public scheme lookups; Singapore locale pack (English + Mandarin).

**Out:** audio (voice notes, consult recordings) until an audio-capable model is listed on Token Factory; multiple care recipients; WhatsApp; clinic/pharmacy/EHR integrations; wearables; payments; per-item ACLs and time-bound grants (design hook only); anything clinical.

## Roles

| Role | Demo member | Sees | Does |
|---|---|---|---|
| **Admin** (primary caregiver) | Mei Ling, daughter | Everything | Assigns roles, approves shares, edits records, teaches skills |
| **Family** | Wei Jie, son (overseas); Bee Lian, aunt | Medical summary, medication, appointments; finance/legal only when shared | Asks, receives digests, adds notes |
| **Carer** | Siti, domestic helper | Today's tasks, medication times, what to watch for, emergency contacts | Confirms tasks, reports observations (photo/text) |
| **Viewer** | Respite carer | Medication schedule and own tasks; `expires_at` set | Confirms tasks |

Roles and languages come from `config/members.yaml`, with Telegram user IDs in `.env`; `/roles` shows the roster to the admin. Anyone else in the family group (for example a judge) is treated as `default_role` (family). Members who have no Telegram account can stay in the roster; their language still shapes group posts.

## Data categories

`medical` · `medication` · `appointments` · `tasks` · `observations` · `finance` · `legal` · `admin` (contacts, logistics) · `notes`

Every record carries a category, visibility derived from policy, a source (document/photo/message) and timestamps. Policy matrix: [03-privacy-boundaries.md](03-privacy-boundaries.md).

## Flows

**Intake.** Photo or PDF sent to group or DM → fields and text extracted (Token Factory vision model) → category classified; admin confirms low-confidence classifications in DM → conflict check against existing records (e.g., dose change) → one clarifying question if needed → record + source stored → schedule/events updated → role-appropriate summaries posted (group: medical summary; DM: restricted items).

**Schedule and reminders.** Medication times, refills computed from quantity, appointments, physio. Reminder goes to the responsible person when it matters: Siti at 8 am for morning meds; Mei Ling the evening before an appointment, with the prep list.

**Ask.** Natural-language question → retrieval limited to records the asker's role may see → answer with source attached (photo crop or excerpt with date). If the answer needs records outside the asker's view, Kin says so and offers a share request.

**Share request.** Family member asks about a `finance` item in the group → group receives "I've asked Mei Ling to share that" → admin DM: "Wei Jie asked about the insurance claim. Share the summary? [Yes] [No] [Just this once]" → grant stored and logged → asker answered or told no.

**Appointment prep and debrief.** Before: question list compiled from the period (carer observations, medication changes, pending results), posted to the attendee. After: the attendee photographs the clinic's after-visit summary → intake extracts it → medication changes become superseding records → action items assigned → next appointment captured → per-role summaries.

**Weekly digest.** Sunday evening: admin gets the full digest; Family the overview; Carer next week's tasks and new things to watch for. In each member's language.

**Skills.** "Every Monday remind Siti to refill the pill organiser and send me a photo." "Before each cardiology visit, prepare the question list." "If Siti reports a fall, message me and Wei Jie immediately." The admin teaches them in DM; Kin confirms in plain language, stores, runs on schedule or trigger as the admin. `/skills` lists them.

**Local lookups.** "Is Ah Ma eligible for the Home Caregiving Grant?" "What does CHAS cover for GP visits?" → Tavily restricted to the locale allow-list → answer with public source; eligibility is described, never decided. Queries contain no record content ("Ah Ma" and her details stay out of the query).

## Chat conventions

- Voice notes are not processed; Kin replies once that it can't listen to audio yet and asks for text.
- Natural language first; commands `/help` (anyone) and, for the admin, `/roles`, `/skills`, `/who_saw`, `/export`.
- One clarifying question at a time.
- Every factual answer carries a source; every reminder carries "why" ("from discharge letter, 3 Oct").
- Group messages short; detail in DM or an attached card.
- Language per member; group posts in English with a Mandarin version for members who prefer it.
- Group privacy mode disabled for the family group so Kin sees all messages (per-family setting). In the group Kin reads every photo, but answers text only when addressed: its name, an @mention, or a reply to one of its messages. Family members can talk among themselves without Kin chiming in.
