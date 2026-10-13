# 03 · Privacy boundaries

## Model

- Members have a **role**: admin, family, carer, viewer.
- Records have a **category**: medical, medication, appointments, tasks, observations, finance, legal, admin, notes.
- A **policy matrix** maps role × category → `write` / `read` / `summary` / `none` (`write` implies `read`), optionally qualified: `own` (records the principal created) or `emergency_contacts` (the emergency-contact records in `admin`). Data: `config/policy.yaml`. Editable per family by the admin.
- A **share request** lets the admin grant access outside the matrix: Yes (standing grant), No, or Just this once (one-shot grant consumed by the next answer). All grants are logged.
- An **audit log** records every retrieval: principal, query, records shown, policy decision. Admin command `/who_saw <record>`; counts in the weekly admin digest.
- Per-item ACLs and time-bound grants are out of scope; the viewer role carries an `expires_at` field as the hook.

## Enforcement

Policy is applied **before retrieval**, not by prompt:

- The agent reads the family's records only through Kin's tools, which call `retrieve(query, principal)`; it filters by the principal's role and active grants before any text enters model context.
- The principal is resolved from the sender's Telegram ID supplied by the gateway (Kin's Hermes plugin), never from model arguments; a message claiming to be someone else changes nothing.
- Hermes' own memory, user profile and session search are disabled: they are shared across every user and chat.
- The store is partitioned by visibility class; a filtering bug fails closed.
- Skills run in Kin's scheduler as their principal (the admin who taught them) through the same path.
- Outbound lookups (Tavily) are made by the kin service, which builds the query and rejects names and record content.
- Network allow-list and credential proxying: OpenShell/NemoClaw (planned, ROADMAP D7). Until then Hermes runs without host-reaching toolsets (`docs/05-architecture.md`, Deployment).

## Policy matrix (default)

| Category ↓ · Role → | Admin | Family | Carer | Viewer |
|---|---|---|---|---|
| medical | write | summary | summary | none |
| medication | write | read | read | read |
| appointments | write | read | read | none |
| tasks | write | read | write (own) | write (own) |
| observations | read | read | write (own) | write (own) |
| finance | write | none → share request | none | none |
| legal | write | none → share request | none | none |
| admin (contacts, logistics) | write | read | read (emergency contacts) | read (emergency contacts) |
| notes | write | write (own) | write (own) | none |

`summary` returns a generated, labelled summary of the category (e.g., "the claim is in progress"; for the carer, what to watch for), not the records. Notes are private to their author (and the admin); anything meant for everyone is posted in the group or filed under its category.

## Behaviour

- The group never receives detail that any group member cannot see. Per category, the group's level is the lowest level among its current members (`none` < `summary` < `read` < `write`); qualified levels (`own`, `emergency_contacts`) count as `none` for the group. With the default roster (admin, family, carer) the group gets medical summaries, medication and appointments, and never finance or legal. Restricted answers go to the asker's DM.
- Unknown role or category → nothing shown, admin asked.
- Low-confidence category classification at intake → admin confirms in DM before filing.

## Data model fields

- Member: `telegram_id`, `name`, `role`, `language`, `expires_at?`
- Record: `id`, `category`, `visibility`, `fields`, `source_ref`, `created_by`, `created_at`, `supersedes?`
- Grant: `record_or_category`, `grantee`, `scope` (once | standing), `granted_by`, `at`
- Audit: `principal`, `query`, `records_shown`, `decision`, `at`
