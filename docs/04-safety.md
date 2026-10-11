# 04 · Safety

Target controls; the scaffold does not implement intake, schedule activation or safety routing yet. Every demonstration uses synthetic data.

## Organise confirmed instructions

| Kin does | Kin does not |
|---|---|
| Transcribe documents into draft fields with source spans | Diagnose or interpret symptoms/lab results |
| Remind from an explicitly confirmed, source-supported schedule | Recommend or infer doses, times, stopping/starting medication |
| Show a documented discrepancy and ask the caregiver to confirm | Infer drug interactions or resolve conflicting instructions itself |
| Provide a permitted clinic contact and record an observation | Judge urgency or tell a family it is safe to wait |
| Compile sourced appointment questions | Answer clinical questions |
| Cite public scheme rules and clinic hours | Decide personal eligibility or financial outcomes |

For a clinical request, explain that Kin handles records and schedules, provide an authorized contact if available, and offer to record the observation. A refusal must not claim a diagnosis or expose a restricted contact/source.

## Schedule state and confirmation

Records progress **extracted → confirmed → active → superseded**; rejected drafts stay inactive. Confirmation names the exact record/version, prescription details, source, times/timezone, assignee and start/end conditions. Ambiguity, unreadable text or conflicting instructions blocks activation; never let a higher-tier model arbitrate a medical decision.

Create events only after explicit Admin confirmation. Superseding or correcting an active record cancels obsolete future events and creates the replacement atomically. Duplicate Telegram updates cannot duplicate records/events. Restart and retry preserve the event/delivery IDs and current authorization. Report ambiguous delivery truthfully.

Refill estimates are optional and require confirmed quantity/use assumptions; label the calculation rather than invent dispensing advice. A schedule summary and Mandarin translation retain the same confirmed values and sources.

## Grounding and sources

Every personal claim comes from a permitted source/confirmed field; no source means unknown. Validate source IDs and spans after generation. Cite the selected document date and distinguish an old superseded instruction from the current confirmed schedule. Source crops must pass the attachment boundary in [03-privacy-boundaries.md](03-privacy-boundaries.md).

Conflicts stay visible to authorized caregivers and block schedule changes. The minimum demo shows a discrepancy/confirmation, not an inferred interaction warning.

## Optional audio and consent

Capture explicit processing consent from the attendee and confirm relevant participants' recording consent before audio is processed. Store who consented, the recording ID and scope; do not infer consent from merely uploading a file. Audio drafts require the same confirmation and source/visibility gates as photos. Audio modality support is qualified separately at D6.

A deletion workflow must cover source files, extracted text, derived records, indexes, caches and retained history, with delivery/transport limitations stated. Do not claim one-command deletion until that workflow is implemented and tested.

## Data flow and operating claim

Kin-owned records live on family-controlled storage; Telegram transports messages/media, and approved content is sent to Nebius for inference. Tavily receives only validated public lookup topics. Self-hosting the store does not keep all information local or by itself establish privacy-law compliance. Dedicated endpoints may offer capacity isolation, but still process data at Nebius.

Keep demo institutions/people fictional, identifiers invalid-pattern, phone/address placeholders non-real and fixtures clearly marked synthetic. Do not use real personal data in this hackathon demonstration. Any future real-family use needs its own consent, access, retention and provider assessment beyond this synthetic pilot.

## Minimum validation

Test advice/interaction requests, absent sources, fabricated citations, unreadable fields, conflicting instructions, unchanged confirmation replay, duplicate events, supersession and restart. Cross-role/attachment/translation tests are mandatory before the minimum product gate; prompts supplement those controls and do not enforce permissions.

Video line: “Kin organises confirmed records and reminders. It never diagnoses or changes doses, and every personal answer shows its permitted source.”
