# 07 · Demo plan

Real Telegram DMs and group, Kin responding live; all data synthetic. Cuts for time are disclosed; no implied instant latency.

## Preconditions

- D0–D5 passed: chosen extractor, isolated contexts, confirmation and supersession, one persistent skill.
- Eight-document fixture and roster (`config/members.yaml`) loaded; every member with an account has opened a DM with the bot.
- Accounts: two Telegram accounts. Account A is Mei Ling (Admin) throughout. Account B is Wei Jie (Family) for the recall and sharing scenes and is re-mapped to Siti (Carer) for the reminder take (`KIN_MEMBER_IDS`, display name changed between takes). Bee Lian is a roster-only member (no account); her `zh` preference makes the group summary bilingual.
- Monday skill confirmed and shown surviving a restart.

## Video (target 2:50)

Full script, setup and narration: [10-video-script.md](10-video-script.md).

| Time | Scene | On screen / spoken |
|---|---|---|
| 0:00–0:15 | The task | Synthetic discharge letter, pill boxes, the family chat; one in four adults is a caregiver, Singapore is super-aged this year |
| 0:15–0:55 | Intake and confirmation | Admin sends the photo in DM; draft with source excerpt and one uncertain field; Admin confirms; schedule active. Name MiniCPM-V (the extractor), Nemotron and Token Factory |
| 0:55–1:15 | Reminder and summary | Siti's DM shows the reminder with its excerpt; the group gets the confirmed summary in English and Mandarin. Safety line |
| 1:15–1:40 | Recall | Wei Jie asks what changed at the last visit; answer with the Month −4 memo excerpt, not the whole document |
| 1:40–2:10 | Sharing | Finance question → neutral group reply → Mei Ling's DM: Yes / No / Just this once → Wei Jie's DM gets the answer; `/who_saw` glance |
| 2:10–2:30 | Personal AI | `/skills`, the Monday trigger, restart evidence |
| 2:30–2:50 | Try it and data flow | Public repo, judge instructions; records self-hosted, Telegram transport, Nebius inference, deployed isolation |

Readable fonts, no copyrighted music. Optional scenes (after-visit summary debrief, data map) replace a segment only after their gates pass.

## Judge access

- Disposable synthetic fixture with the bot running (`KIN_DEMO=true`, `kin/demo.py`); the judge joins the group via invite link and opens a DM with the bot. `/demo admin`, `/demo family` and `/demo carer` give their one account every member's seat and pick who they speak as, so one person completes both sides of sharing. Messages for a member they aren't playing arrive labelled ("For Mei Ling (Admin):"), and a tap on any of them answers for whoever was asked. A role switch starts fresh Hermes conversations.
- `/demo photos` sends the discharge-summary pages and the appointment slip to send back as Mei Ling. `/demo monday` runs Monday 08:00 on the demo day (reminders and the skill), since the clock-driven scheduler is off in the demo. `/demo reset` restores Week 0.
- Each new tester starts with a fresh Week 0 family. While a tester is active (within 10 minutes) nobody else can take the seats; a tester signed out after going quiet is told why. The intro and each role's message say who the family is, what Kin already remembers and what that role can see.
- Test script with expected results: README, "Try it (judges)". Bot and invite link go in Devpost's testing instructions, not the repo.
- `make demo-reset` (nightly by host cron during judging) restores the fixture, signs testers out and deletes Telegram conversations. Entrant-funded; no API key needed.
- Bot, endpoints and budget stay available through 16 Dec 2026, 04:00 SGT.

## Must work

1. Private photo intake → confirmation → reminder and bilingual summary.
2. Recall with an approved excerpt.
3. Sharing: neutral reply, Admin decision, private answer, audit.
4. Persistent memory and the Monday skill after restart.
5. Minimum privacy and safety tests; one public-only Tavily lookup.
