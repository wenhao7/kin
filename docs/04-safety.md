# 04 · Safety

Kin organises confirmed records and reminders. It does not give medical advice.

| Kin does | Kin does not |
|---|---|
| Transcribe documents into drafts with source excerpts | Diagnose, or interpret symptoms or results |
| Remind from a confirmed schedule | Recommend doses, times, or starting and stopping a medicine |
| Show the admin where documents disagree, and ask | Infer drug interactions or settle a conflict itself |
| Cite public scheme rules | Decide eligibility or financial outcomes |

These rules are in Kin's persona (`hermes/SOUL.md`). Who sees what never depends on the persona.

## Controls in code

- **Confirmation.** Records move from draft to active to superseded. Kin asks the admin, rather than guessing, about:
  - an unreadable field
  - a medicine name that matches no record (the fixture photo reads Glipizide as "Glibpizide")
  - two documents that give the same appointment different times

  Nothing is scheduled until the admin confirms.
- **Reminders.** They come only from confirmed records. Superseding a record cancels its future reminders, and retries reuse event IDs so nothing is sent twice. Refill dates are labelled as calculations.
- **Grounding.** Every personal answer names its source document and date; no permitted source means "I don't know".
- **Fixed replies.** A request for an original document and a tap on an old button get fixed replies, not the model's.
- **Translation** keeps the confirmed values. Names are masked while translating, and a translation that loses a name or number is discarded.

## Data and consent

- **What leaves the host:** Telegram carries messages, Nebius receives the approved context for inference, and Tavily receives only scheme names.
- **Consent:** health and financial data about an identifiable person is personal data under Singapore's PDPA. The demo is synthetic; real use needs its own consent, retention and provider assessment.
- **Audio** is not processed. If it is ever added, consent would be captured in chat first.
