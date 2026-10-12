# 07 · Demo plan

Real Telegram chat, Kin responding live (phone over-the-shoulder for the kitchen scene; Telegram Desktop screen recording for the rest).

## Pre-conditions

- Demo family loaded through Week 0 ([06-synthetic-data.md](06-synthetic-data.md)).
- Group "Tan Family" with Mei Ling, Wei Jie, Bee Lian, Siti, Kin; privacy mode disabled.
- Languages: Bee Lian → zh; others → en.
- Skills pre-taught: Monday pill-organiser reminder; cardiology prep.
- Default policy matrix.
- Consult audio pre-recorded (synthetic); processing runs live.

## Video (≤ 3:00)

| Time | Scene | On screen | Voice-over |
|---|---|---|---|
| 0:00–0:20 | Kitchen table | Discharge letter and pill boxes; one photo sent to the group | One in four adults is a caregiver; Singapore is super-aged this year; this is the job: paper, pill boxes, a group chat |
| 0:20–1:10 | Intake | Kin posts: medication table before/after; "two of these may interact — worth asking the pharmacist"; "reminders set for Siti 8 am / 8 pm"; Mandarin version for Bee Lian; Siti's DM shows the reminder | A vision model on Nebius Token Factory reads the letter and labels; Nemotron files them with their source, builds the schedule, tells each person what they need in their language. Kin never diagnoses or doses |
| 1:10–1:35 | Grounded recall | Wei Jie: "What did Dr Tan change at the last visit?" → specific change + photo of the Month −4 clinic memo | The answer comes with the document it came from |
| 1:35–1:55 | Boundary | Wei Jie asks about the insurance claim in the group → "I've asked Mei Ling to share that" → Mei Ling's DM: Share? [Yes] [No] [Just this once] → Yes → Wei Jie gets the summary | Money is family-admin. Kin asks before sharing and enforces it where data is read, not by hoping the model behaves |
| 1:55–2:25 | Visit | Consent in chat; consult audio sent; summary, one medication record superseded, three action items, next appointment | With consent, the consult becomes records and tasks |
| 2:25–2:50 | Data map | OpenShell sandbox, Hermes runtime, Nemotron on Nebius, the family's data folder, the locale pack folder; `/who-saw` output | Ran on Nebius with open NVIDIA models; here is where the data lives, who saw what, and the folder you swap for another country |
| 2:50–3:00 | Close | Repo URL; "Built with NVIDIA Nemotron on Nebius · Hermes Agent · OpenShell" | — |

Production: replies short enough to read on screen; no copyrighted music; say "Token Factory" and "Nemotron" in the audio; state the safety line.

## Judge access

- Demo Telegram group via invite link, pre-loaded, Kin running; judges act as a Family member.
- README test script: five messages and expected results (intake photo supplied, recall question, finance question → share flow, `/skills`, `/who-saw`).
- Optional read-only data-map page (Serverless Endpoint): records by category, audit log.
- Reset script to restore the demo group between judges.

## Must work live

1. Photo intake → records + reminders + bilingual summary.
2. Grounded recall with source attachment.
3. Share-request flow end to end.
4. Audio debrief (pre-recorded audio, live processing).
5. `/who-saw`.
