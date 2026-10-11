# 03 · Privacy boundaries

`config/policy.yaml` holds the matrix and `kin/policy.py` validates its shape; enforcement is implemented at D2. The compose and Hermes templates do not establish isolation by themselves.

## Minimum boundary (D2)

- **Identity** comes from the gateway's authenticated Telegram sender, chat and roster. The model never supplies a principal. Forwarded messages, display names and unknown or expired members carry no authority.
- **Retrieval** goes through one function, `retrieve(query, principal)`, which applies the matrix and field projection before any text reaches the model. Unknown category or qualifier fails closed.
- **Hermes isolation**: native memory injection, session search and file/terminal tools are disabled over family data; group and DM contexts are built separately. Instructing Hermes to "use Kin retrieval" is not isolation.
- **Delivery**: restricted answers go to the requester's DM; the group receives only Admin-confirmed summaries. Destination permission is re-checked immediately before sending, including excerpts and translations.
- **Sharing**: a grant is per record and per grantee. Yes = standing until revoked; Just this once = one answer. Decisions and deliveries are audited; `/who-saw` is Admin-only. Refusals do not reveal whether a hidden record exists.
- **Documents**: a mixed original stays Admin-only; derived records reference approved excerpts; an excerpt that includes adjacent restricted text is replaced by a source card.
- **Kin MCP** is reachable only from the Hermes container on the compose network.

## Matrix and field constraints

| Category | Admin | Family | Carer | Viewer (optional) |
|---|---|---|---|---|
| medical | read/write | confirmed summary | care instructions | none |
| medication | read/write | read | confirmed schedule | confirmed schedule |
| appointments | read/write | read | involved appointments | none |
| tasks | read/write | read | assigned | assigned |
| observations | read | read | own | own |
| finance | read/write | none → share request | none | none |
| legal | read/write | none → share request | none | none |
| admin | read/write | contacts and logistics | emergency contacts | emergency contacts |
| notes | read/write | shared and own | own | none |

`own` = assigned to (tasks) or authored by (observations, notes) the principal. `summary` is the Admin-confirmed overview plus care instructions and permitted excerpts, not a model paraphrase of the whole record. The YAML level sets the ceiling; field projections narrow it.

## Data fields

- Member: family ID, Telegram ID, role, language, DM opened, optional expiry.
- Record: ID and version, category, status (extracted → confirmed → active → superseded), permitted fields, creator/assignee, approved excerpt, timestamps, superseded-by.
- Document: restricted storage reference, categories, approved excerpts.
- Event: stable ID, record version, assignee, due time and timezone, status.
- Grant: record and version, grantee, scope (once | standing), approver, consumed/revoked.
- Audit: principal, chat, records and fields exposed, decision, destination, delivery outcome, time.

## Minimum tests (D2, through the real gateway path)

Forged principal in a tool call; direct store access from a model tool; Hermes memory or session recall of another role's data; unknown sender in group and DM; Family asking for finance (neutral reply, share flow, denial); revoked grant; mixed original requested by Carer; translation of a restricted field; family data in a Tavily query.

## Hardening (D7, optional)

Grants bound to record version, projection and destination; transactional one-shot consumption under concurrency; roster-intersection check for group posts; cache and context invalidation on policy change; delivery reconciliation for uncertain Telegram sends; viewer expiry at retrieval and delivery; deletion across files, extracted text, records, indexes and history; OpenShell network and credential isolation.
