# 10 · Video script

The submission video: at most 3:00 (target 2:50), public on YouTube, English, showing the real product. The narration names Nebius Token Factory and the models used. No copyrighted music; third-party logos only where the app shows them. Waits are cut and captioned ("cut: 10 s"). Plan: [07-demo-plan.md](07-demo-plan.md).

## Setup

- **Mode:** the family setup, not the judge demo: `KIN_DEMO=false`, `TELEGRAM_ALLOW_ALL_USERS=false`, Phone A as Mei Ling (`KIN_ADMIN_TELEGRAM_ID`) and Phone B as Wei Jie (`KIN_MEMBER_IDS=wei_jie:<id>`). Then `make seed` for Week 0.
- **Order:** send the slip only after answering "Post this to the group?": a document sent while a question is open waits its turn. Scenes are shot in table order.
- **Phones:** Telegram display names "Mei Ling" and "Wei Jie"; larger chat text; status bars clean; no phone numbers on screen. Record each phone's screen; scenes 5 and 6 are shown side by side. Telegram Desktop or Telegram Web works as well: one window per account (a second Desktop instance with `-workdir`, or a second browser profile), interface scale 125–150%. Keep the camera shot of the paper and Siti's reminder arriving on a phone.
- **Paper:** the printed discharge summary (pages 1 and 2) and the appointment slip, photographed with the phone camera inside Telegram.
- **Scene 7:** re-map Phone B to Siti (`KIN_MEMBER_IDS=siti:<id>`, `docker compose up -d kin`), then `make tick AT=2026-10-26T08:00` sends Monday 08:00. Film `make down && make up` in a terminal, then `/skills`.

## Script

| Time | Scene | On screen | Narration |
|---|---|---|---|
| 0:00–0:15 | The problem | The printed discharge summary and a pill organiser on a table; the family's Telegram group | When Ah Ma came home from hospital, her care ran on a group chat and a shoebox of paper. Her daughter Mei Ling retyped every change, answered every question, and decided, message by message, who should see what. |
| 0:15–0:25 | Kin | Title: "Kin: the family member who remembers everything, and tells no one who shouldn't know." | Kin lives in the family's Telegram. It runs on NVIDIA Nemotron 3 Super and MiniCPM-V, on Nebius Token Factory. |
| 0:25–0:50 | Intake | Phone A, Mei Ling's DM: photograph page 1, then page 2 → "Reading it now…" (cut) → the draft → **Confirm** → "Replaced 5 older medicine records; reminders now follow the Discharge summary, 23 Oct 2026." | Mei Ling photographs the discharge summary in a private chat. MiniCPM-V reads it, and nothing is filed or scheduled until she confirms. |
| 0:50–1:05 | One update | **Post to group** → the group shows the English update, then the Mandarin one | She approves one update for the whole family, in English and, for her aunt, in Mandarin, written by Nemotron with every medicine name and dose kept exactly. |
| 1:05–1:15 | Kin asks | The appointment slip → "this says 10:30 am, the Discharge summary says 9:30 am" → tap **10:30 am (this document)** → **Confirm** → **Don't post** | Kin checks every new document against what it already knows. When the slip and the summary disagree on the time, it asks. It never guesses. |
| 1:15–1:45 | The boundary | Side by side, both phones ask `What happened at Ah Ma's June review with Dr Tan?` Phone A: blood pressure, kidney tests, Losartan. Phone B: the review and the Losartan plan, with Dr Tan's quoted line | Months later, the same question gets different answers. Mei Ling sees the clinical notes. Her brother Wei Jie sees the medicine change, in Dr Tan's own words. The boundary is in code: Kin filters the records before the model sees them, and checks every reply before it is sent. |
| 1:45–2:15 | Sharing | Phone B in the group: `Kin, has the insurance claim gone through?` → "I've asked Mei Ling to share that." Phone A: the request with buttons → **Just this once** → Phone B's DM: the insurer's words. Phone A: `/who_saw` → the report | Ask about money in the group and Kin replies neutrally, then asks Mei Ling privately: share it, just this once, or not. Wei Jie gets the insurer's words, never the letter, and Mei Ling can see exactly who was shown what. |
| 2:15–2:35 | Always on | Phone B as Siti: the 08:00 medicines, then the pill-organiser reminder → **Done** → Phone A: "Siti has done it". Terminal: `make down && make up`; `/skills` shows the last run. Group: `Kin, is Ah Ma eligible for the Home Caregiving Grant?` → the AIC link | Kin is always on. Every Monday it reminds Siti to refill the pill organiser and tells Mei Ling when it's done, a skill that survives restarts. For public schemes it searches government sites with Tavily, sending only the scheme's name. |
| 2:35–2:50 | Close | Diagram: Telegram ↔ Hermes and the Kin plugin ↔ Kin's store; Nemotron Super and MiniCPM-V on Token Factory; Tavily. Then "Try it: link below" | Records stay on the family's own server, Telegram carries the messages, and Token Factory does the thinking. Kin organises: it never diagnoses or changes a dose, and every answer shows its source. |

About 360 words of narration: a calm pace for 2:50.

## Notes

- Scenes 3 and 6 depend on the live models: retake until the reply matches the README's expectations, and keep the take honest (no edits to message text).
- Kin's name check ("Did you mean Glipizide?") depends on how the photo reads; the slip's time clash is checked in code and always appears, so it carries the "Kin asks" moment.
- After filming, set the judge demo back: `KIN_DEMO=true`, `TELEGRAM_ALLOW_ALL_USERS=true`, `docker compose up -d`, `make demo-reset`.
