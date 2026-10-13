# 04 · Safety

## Kin organises; it does not advise

| Kin does | Kin does not |
|---|---|
| Transcribe, structure and file what clinicians and pharmacists wrote | Diagnose, interpret symptoms, or suggest what is wrong |
| Keep the schedule the prescription defines; remind the right person | Recommend doses, changes, stopping or starting medication |
| Flag "worth asking the pharmacist" when records appear to interact or conflict | State that an interaction is dangerous or what to do about it |
| Say "this sounds like something to call the clinic about" and give the clinic number from records | Triage urgency or tell the family to wait |
| Prepare question lists for appointments from the family's records | Answer those questions itself |
| Look up public scheme rules from allow-listed sources, with attribution | Advise on eligibility outcomes or financial decisions |

Refusal pattern: *"I can't advise on that — I keep the records and the schedule. From the discharge letter of 3 Oct, the clinic's number is 6xxx xxxx. Do you want me to note what you observed?"*

## Grounding

- Every statement about the care recipient is attached to a source: document image/excerpt or message, with date.
- No source → Kin says it does not know.
- Conflicting records are surfaced to the admin, never resolved silently.
- `summary` renderings are labelled as summaries.

## Consent and recording

- Kin does not process audio: voice-note transcription is off and no audio-capable model is listed on Token Factory for our key. Kin replies that it can't listen yet and asks for text.
- If audio is added later, recording a consultation requires explicit consent in chat from the attendee first, and Kin reminds the attendee about the clinician's consent.

## Data protection

- Health and financial data about an identifiable person is personal data under Singapore's PDPA. Kin keeps it inside infrastructure the family (or a provider acting for them) controls. Design property, not legal advice.
- Demo data is synthetic only: fictional people and institutions; invalid-pattern NRIC placeholders (`S0000000A`); `6xxx xxxx` / `9xxx xxxx` phone placeholders; fictional addresses.

## Controls

- Kin's persona (`hermes/SOUL.md`) encodes the organise-not-advise rules; who-sees-what does not rely on prompts ([03-privacy-boundaries.md](03-privacy-boundaries.md#enforcement)).
- Clinical-advice requests route to the refusal pattern; tested with a small adversarial set before the demo.
- Outbound tools allow-listed; no record content in outbound queries.

## Stated in the video

*"Kin keeps the records and the schedule. It never diagnoses, never doses, and every answer shows its source."*
