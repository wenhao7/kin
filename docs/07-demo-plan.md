# 07 · Demo plan

Real Telegram chat, Kin responding live (phone over-the-shoulder for the kitchen scene; Telegram Desktop screen recording for the rest).

## Pre-conditions

- Demo family loaded through Week 0 ([06-synthetic-data.md](06-synthetic-data.md)).
- Group "Tan Family" with Kin; privacy mode disabled. Roster from `config/members.yaml`.
- Accounts: two Telegram accounts. Account A is Mei Ling (admin) throughout. Account B is Wei Jie (family) for the group scenes and is re-mapped to Siti (carer) for the reminder DM take (`KIN_MEMBER_IDS` in `.env`, display name changed between takes). Bee Lian is a roster-only member (no account): her `zh` preference makes Kin add the Mandarin version to group posts.
- Languages: Bee Lian → zh; others → en.
- Skills pre-taught in Kin's scheduler: Monday pill-organiser reminder; cardiology prep.
- Default policy matrix.
- After-visit summary printed and photographed (synthetic); processing runs live.

## Video (≤ 3:00)

| Time | Scene | On screen | Voice-over |
|---|---|---|---|
| 0:00–0:20 | Kitchen table | Discharge letter and pill boxes; one photo sent to the group | One in four adults is a caregiver; Singapore is super-aged this year; this is the job: paper, pill boxes, a group chat |
| 0:20–1:10 | Intake | Kin posts: medication table before/after; "two of these may interact — worth asking the pharmacist"; "reminders set for Siti 8 am / 8 pm"; Mandarin version for Bee Lian; Siti's DM shows the reminder | A vision model on Nebius Token Factory reads the letter and labels; Nemotron files them with their source, builds the schedule, tells each person what they need in their language. Kin never diagnoses or doses |
| 1:10–1:35 | Grounded recall | Wei Jie: "What did Dr Tan change at the last visit?" → specific change + photo of the Month −4 clinic memo | The answer comes with the document it came from |
| 1:35–1:55 | Boundary | Wei Jie asks about the insurance claim in the group → "I've asked Mei Ling to share that" → Mei Ling's DM: Share? [Yes] [No] [Just this once] → Yes → Wei Jie gets the summary | Money is family-admin. Kin asks before sharing and enforces it where data is read, not by hoping the model behaves |
| 1:55–2:25 | Visit | Mei Ling photographs the after-visit summary; Kin posts the dose change (before/after, superseding the old record), three action items with owners, the next appointment | After the visit, one photo becomes records and tasks |
| 2:25–2:50 | Data map | Self-hosted stack (OpenShell sandbox if D7 lands), Hermes runtime, Nemotron on Nebius, the family's data folder, the locale pack folder; `/who_saw` output | Ran on Nebius with open NVIDIA models; here is where the data lives, who saw what, and the folder you swap for another country |
| 2:50–3:00 | Close | Repo URL; "Built with NVIDIA Nemotron on Nebius · Hermes Agent" (+ "OpenShell" if D7 lands) | — |

Production: replies short enough to read on screen; no copyrighted music; say "Token Factory" and "Nemotron" in the audio; state the safety line.

## Judge access

- Demo Telegram group via invite link, pre-loaded, Kin running. A judge who joins is an unknown member and gets `default_role` (family, English) from `config/members.yaml`; Kin greets new members with the test script. Everything a judge tests happens in the group, so no DM or `/start` is needed.
- Share requests go to the admin DM (the operator's account). The judge sees the redirect ("I've asked Mei Ling to share that") immediately; the operator approves when available, and the video shows the full flow.
- README test script: five messages and expected results — the supplied intake photo, a recall question, a finance question (share redirect), a scheme lookup, a clinical-advice question (refusal). None needs an admin command.
- Optional read-only data-map page (Serverless Endpoint): records by category, audit log.
- `make demo-reset` restores Kin's store to Week 0 (nightly via host cron during 1–15 Dec, and on demand).

## Must work live

1. Photo intake → records + reminders + bilingual summary.
2. Grounded recall with source attachment.
3. Share-request flow end to end.
4. Visit debrief from the after-visit summary photo.
5. `/who_saw`.
