# 02 · Product

## Scope

- **In:**
  - one family and care recipient, with verified admin, family and carer accounts
  - private photo intake with the admin's confirmation
  - reminders
  - bilingual group posts
  - role-scoped answers with sources
  - sharing with an audit trail
  - one weekly skill
  - a public-scheme lookup
- **Out:**
  - audio (voice notes get a fixed reply)
  - several care recipients
  - WhatsApp
  - clinic or pharmacy integrations
  - payments
  - clinical advice

## Roles

| Role | Demo member | Sees | Does |
|---|---|---|---|
| Admin | Mei Ling (daughter) | Everything | Files documents, approves posts and shares |
| Family | Wei Jie (son, overseas), Bee Lian (aunt) | Medical summary, medicines, appointments, their own notes | Asks, adds notes, requests shares |
| Carer | Siti (helper) | Schedule, assigned tasks, care instructions, emergency contacts | Confirms assigned tasks |
| Viewer | Respite carer (not in the demo) | Schedule and assigned tasks | Confirms assigned tasks |

Roles and languages come from `config/members.yaml`, bound to Telegram IDs in `.env`. A member without Telegram can stay on the roster: Bee Lian's Mandarin still shapes group posts. Every member must open a private chat with the bot first, because bots can't start one.

## Flows

- **Intake.** Documents go to Kin in the admin's private chat; a photo sent anywhere else is not filed. Kin drafts the records and asks about doubtful fields one at a time. Nothing is filed or scheduled until the admin confirms.
- **Reminders.** Times and assignees come from the confirmed record; Kin never infers a dose or time. A superseded medicine's reminders stop. Restarts never send a reminder twice.
- **Group post.** After confirming, the admin approves one update, posted in English and Mandarin, holding only what every member may see.
- **Answers.** Answers come from the records the asker may see, with the quoted source. No permitted source means "I don't know", without hinting whether a hidden record exists.
- **Sharing.** A finance or legal question gets a neutral reply. The admin chooses **Yes** (standing), **No** or **Just this once**, and the answer goes to the asker's private chat.
- **Weekly skill.** "Every Monday 08:00, remind Siti to refill the pill organiser and tell Mei Ling when done." It survives restarts; `/skills` shows it to those who may see it.
- **Lookup.** Public scheme rules (Home Caregiving Grant, CHAS…) from government sites, with the link. Kin never decides eligibility.

## Chat conventions

- **In the group:** Kin answers only when addressed, by "Kin", an @mention or a reply to one of its messages, and keeps posts short. Detail and anything restricted go to private chats.
- **Sources:** every personal answer quotes its dated source.
- **Mandarin:** it uses the same confirmed fields. Medicine and people's names stay as written, and a translation missing any name or number isn't posted.
- **Admin commands** (in the admin's private chat): `/roles`, `/reminders`, `/who_saw`, `/revoke`. The last two offer documents or shares as buttons. Everyone has `/skills` and `/help`, and each chat's "/" menu lists only what works there.
- **Group Privacy** must be off for the bot (or the bot must be a group admin) so Kin sees group messages. Identity and policy apply to every message regardless.
