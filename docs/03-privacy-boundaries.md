# 03 · Privacy boundaries

Who sees what is data (`config/policy.yaml`, `config/members.yaml`) enforced in code. Kin's persona prompt never decides it.

## Where it is enforced

- **Identity** comes from the authenticated Telegram sender and chat, read by the Kin plugin from the gateway session. The model never supplies a principal. Forwarded messages, display names and unknown members carry no authority.
- **Retrieval** goes through one function, `retrieve(query, principal)`, which applies the matrix and field limits before any text reaches the model. An unknown category or qualifier fails closed.
- **Delivery.** Every model reply passes the reply check (`kin/answer.py`), which withholds it if it holds anything this chat may not see now, even something the model saw earlier in the session. Reminders and the weekly skill re-check their recipient when they fire.
- **The group** sees only what every member may see: per category, the lowest level among the roster's roles. It receives only admin-approved posts and short answers; restricted answers go to private chats.
- **Sharing** is per record and per person. **Yes** stands until `/revoke`; **Just this once** covers one answer. Every decision and delivery is audited and reported by `/who_saw`. A refusal never reveals whether a hidden record exists.
- **Documents.** Originals stay with the admin. Other roles see the confirmed fields and approved excerpts: the document's own printed lines, approved for the roles that may read those fields.
- **Hermes** has its memory, session search, skills, cron and file and terminal tools turned off, so nothing outside Kin carries data between people.
- **Lookups** send Tavily only the name of a scheme listed in the locale pack, limited to its allow-listed domains. The exact query is audited.
- **The kin API** is reachable only from the Hermes container and checks a shared token.

## Matrix

| Category | Admin | Family | Carer | Viewer |
|---|---|---|---|---|
| medical | all | summary, medicine plan, care instructions | medicine plan, care instructions | none |
| medication | all | read | schedule | schedule |
| appointments | all | read | read | none |
| tasks | all | read | assigned to them | assigned to them |
| observations | read | read | their own | their own |
| finance | all | none → share request | none | none |
| legal | all | none → share request | none | none |
| admin | all | read | emergency contacts | emergency contacts |
| notes | all | their own | their own | none |

The matrix sets each role's ceiling. `projections` in `config/policy.yaml` narrow it to named fields; for example, Family sees a medical record's summary and medication changes but never its clinical notes.

## Tested

`tests/` covers:
- a forged principal
- unknown senders in the group and in private chats
- family asking about finance (neutral reply, share request, denial)
- revoked and one-time grants
- a carer asking for an original
- restricted fields in a translation or a group post
- another role's data reaching an answer
- family data in a Tavily query

Live runs confirmed the same cases in Telegram.

## Not built

- grants bound to a record version
- viewer expiry
- deletion across every copy
- network isolation with OpenShell
