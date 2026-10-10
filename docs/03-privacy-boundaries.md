# 03 · Privacy boundaries

## Model

- Members have a **role**: admin, family, carer, viewer.
- Records have a **category**: medical, medication, appointments, tasks, observations, finance, legal, admin, notes.
- A **policy matrix** maps role × category → `read` / `summary` / `none`, plus `write` where relevant. Editable per family by the admin.
- A **share request** lets the admin grant access outside the matrix: Yes (standing grant), No, or Just this once (one-shot grant consumed by the next answer). All grants are logged.
- An **audit log** records every retrieval: principal, query, records shown, policy decision. Admin command `/who-saw <record>`; counts in the weekly admin digest.
- Per-item ACLs and time-bound grants are out of scope; the viewer role carries an `expires_at` field as the hook.

## Enforcement

Policy is applied **before retrieval**, not by prompt:

- The agent reads memory only through `retrieve(query, principal)`, which filters by the principal's role and active grants before any text enters model context.
- The store is partitioned by visibility class; a filtering bug fails closed.
- Skills run as a principal (normally the admin) through the same path.
- Outbound tool calls (Tavily) carry no record content.
- Secrets and network access are handled by the OpenShell/NemoClaw sandbox (credential proxying, allow-list).

## Policy matrix (default)

| Category ↓ · Role → | Admin | Family | Carer | Viewer |
|---|---|---|---|---|
| medical | read/write | summary | summary (what to watch for) | none |
| medication | read/write | read | read (schedule) | read (schedule) |
| appointments | read/write | read | read (if involved) | none |
| tasks | read/write | read | read/write (own) | read/write (own) |
| observations | read | read | read/write (own) | write (own) |
| finance | read/write | none → share request | none | none |
| legal | read/write | none → share request | none | none |
| admin (contacts, logistics) | read/write | read | read (emergency contacts) | read (emergency contacts) |
| notes | read/write | read (shared), own private | own private | none |

`summary` returns a generated, labelled summary of the category (e.g., "the claim is in progress"), not the records.

## Behaviour

- Group never receives detail that any group member cannot see; restricted answers go to DM.
- Unknown role or category → nothing shown, admin asked.
- Low-confidence category classification at intake → admin confirms in DM before filing.

## Data model fields

- Member: `telegram_id`, `name`, `role`, `language`, `expires_at?`
- Record: `id`, `category`, `visibility`, `fields`, `source_ref`, `created_by`, `created_at`, `supersedes?`
- Grant: `record_or_category`, `grantee`, `scope` (once | until), `granted_by`, `at`
- Audit: `principal`, `query`, `records_shown`, `decision`, `at`
