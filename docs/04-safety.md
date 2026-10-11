# 04 · Safety

Target controls; every demonstration uses synthetic data.

## Organise confirmed instructions

| Kin does | Kin does not |
|---|---|
| Transcribe documents into draft fields with source excerpts | Diagnose or interpret symptoms or lab results |
| Remind from a confirmed, source-backed schedule | Recommend or infer doses, times, stopping or starting medication |
| Show a documented discrepancy between records and ask Admin to confirm | Infer drug interactions or resolve conflicting instructions itself |
| Provide a permitted clinic contact and record an observation | Judge urgency or say it is safe to wait |
| Compile sourced appointment questions | Answer clinical questions |
| Cite public scheme rules and clinic hours | Decide personal eligibility or financial outcomes |

Refusal: *"I can't advise on that — I keep the records and the schedule. From the discharge letter of 3 Oct, the clinic's number is 6xxx xxxx. Shall I note what you observed?"* A refusal never exposes a restricted contact or source.

## Confirmation and schedule state

Records move **extracted → confirmed → active → superseded**. Confirmation names the record version, details, source, times and timezone, assignee and end conditions. Ambiguity, unreadable text or conflicting instructions block activation; no model tier arbitrates a medical decision. Activation creates events; supersession cancels obsolete future events atomically; retries reuse event and delivery IDs. Refill estimates are labelled calculations from confirmed quantity, never dispensing advice. Translations keep the same confirmed values and sources.

## Grounding

Every personal claim comes from a permitted source or confirmed field; no source means "I don't know". Sources are validated after generation; the document date is cited; superseded instructions are distinguished from the current schedule.

## Audio and consent (optional, D6)

Explicit processing consent from the attendee is captured in chat before audio is processed, with a reminder about the clinician's consent. Audio drafts follow the same confirmation and visibility gates as photos. Deletion covers files, extracted text, derived records, indexes and history once that workflow exists; it is not claimed before then.

## Data flow

Records live on family-controlled storage; Telegram transports messages and media; approved context goes to Nebius for inference; Tavily receives validated public topics only. Self-hosting the store does not keep all information local. Health and financial data about an identifiable person is personal data under Singapore's PDPA; the demo is synthetic and any real use needs its own consent, retention and provider assessment.

## Minimum validation (before D5)

Advice and interaction requests refused; absent sources answered "I don't know"; fabricated citations rejected; unreadable fields and conflicts block activation; duplicate updates do not duplicate events; supersession and restart behave; cross-role, attachment and translation tests from 03-privacy-boundaries.md pass.

Video line: *"Kin organises confirmed records and reminders. It never diagnoses or changes doses, and every personal answer shows its permitted source."*
