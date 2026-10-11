# 03 · Privacy boundaries

Required design and acceptance gates. `config/policy.yaml` currently describes a matrix, and `kin/policy.py` validates its shape. Neither implements the controls below. The present Hermes/Compose templates also do not establish isolation, authenticated MCP access or filtered history.

## Trusted identity and context

The trusted gateway verifies Telegram sender, family, enrolled chat and role. It creates a request identity bound to the current chat/destination and policy version. The Kin service derives the principal from that authenticated envelope; a model cannot choose a principal by tool argument. Reject forged IDs, forwarded-message identities, unknown/expired roles and cross-family requests.

Authenticate Kin MCP transport and bind its tools to that request. Keep it private to the gateway network or protected local access; public unauthenticated MCP is not acceptable. Model tools receive scoped capabilities, never general database/filesystem access to family records.

## Enforcement before context and before delivery

- `retrieve(query, principal)` is the internal read boundary; the principal is server-derived. Select allowed partitions, relationship filters and field projections before text enters model context. A partition name alone is not authorization.
- Apply the same rules to chat history, persistent notes, session search, compaction summaries, caches, skills, attachments and logs. Unknown categories/qualifiers fail closed.
- Hermes injects native memory and exposes session search. Disable unfiltered memory/user-profile injection and search/file/terminal tools over family stores, or demonstrate equivalent per-request isolation. Merely instructing Hermes to use Kin retrieval is insufficient. [Hermes memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
- Separate group and DM contexts. Prevent Admin tool results from entering another member's history or a shared bot memory. A policy or role change invalidates relevant cached projections and starts/rebuilds permitted context; previously disclosed messages cannot be retracted reliably.
- Reauthorize each destination immediately before delivery, including source excerpts, translations, reminders and digests. Skills' execution identity does not grant their recipients that identity's view.
- Log model-visible record/field references and accepted delivery outcomes. Audit access is itself restricted; raw queries and private excerpts must not become lower-role logs.

## Target role matrix and field constraints

| Category | Admin | Family | Carer | Viewer (optional) |
|---|---|---|---|---|
| medical | read/write | approved summary | approved care instructions | none |
| medication | read/write | read | confirmed schedule | confirmed schedule |
| appointments | read/write | read | involved appointments | none |
| tasks | read/write | read | read/write assigned | read/write assigned |
| observations | read | read | read/write own | read/write own |
| finance | read/write | none; scoped share request | none | none |
| legal | read/write | none; scoped share request | none | none |
| admin | read/write | contacts/logistics | emergency contacts | emergency contacts |
| notes | read/write | shared and own | own | none |

For tasks, `own` means assigned to the principal; for observations/notes it means authored by the principal. The current YAML level `write:own` implies reading one's own permitted records. Category-only `read` is still narrowed by the field rules above; implementing these projections and relationships is D2 work, not a claimed property of today's YAML.

`summary` is a defined projection: an Admin-confirmed overview, documented care instructions and permitted source spans, excluding omitted diagnoses, identifiers and raw text. Generate wording only from this allowed projection; labelling an unrestricted model summary does not make it safe.

## Documents and derived artifacts

A document can contain several categories. Its original file/extracted text inherits the most restrictive contained information and remains Admin-only in the minimum product. Each derived record references an approved crop/text span and its version. A permitted medication record never grants access to an unrestricted discharge letter.

Authorize attachment fetching separately. Validate referenced spans and generated output against the allowed fields; use a safe source card when a crop includes adjacent restricted text. Translation, thumbnails, search indexes and cached summaries inherit source restrictions. Low-confidence extraction/category/visibility stays quarantined until confirmed.

## Group delivery

Compute the permitted field intersection for the current verified roster, not only the asking member. Unknown members, stale roster state or an unsupported role block private group content. Restricted responses and sources go to DM. A Viewer joining can remove medical-summary access from the group; queue a neutral status or separate DMs instead. Do not claim that the bot can conceal a document a member already uploaded to the group.

## Sharing and revocation

A grant binds record/version, permitted fields/source spans, grantee, destination, scope and approving Admin. Yes is standing until revoked; Just this once reserves one bounded answer transactionally. Concurrent requests cannot consume it twice. Retries refer to the same answer/delivery ID; uncertain Telegram delivery stays reserved until reconciled, rather than permitting a fresh answer. Expiry/revocation is checked on retrieval and delivery. Record changes require renewed approval for the new version.

Category-wide grants and arbitrary ACL editing are outside minimum scope. Reject fabricated callbacks and approval tokens; recheck Admin authority. Share refusals and blocked retrievals must not reveal hidden titles, counts or record existence.

## Data fields

- Member: family ID, Telegram ID, role, language, DM readiness, optional expiry, policy version.
- Record: ID/version, category, status, permitted fields, creator/assignee relationships, approved source spans, timestamps, superseded version.
- Document: restricted storage reference, category set, approved derived spans and retention state.
- Grant: record/version, projection, grantee/destination, scope, approval, revocation/consumption and answer ID.
- Audit: request/principal, policy version, records/fields exposed to the model, decision, destination, delivery ID/outcome and time.

## Minimum adversarial acceptance tests

Use synthetic fixtures to verify forged principal/MCP calls, direct store access, shared Hermes memory/session recall, role changes and revoked grants, concurrent one-shot requests, mixed-source attachment leakage, unsafe translations, unknown/group membership and Admin-scheduled messages to lower roles. Also verify that secret/private query content cannot reach Tavily. Tests must exercise service/gateway behavior, not only matrix loading.
