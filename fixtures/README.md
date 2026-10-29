# Synthetic fixture

**Everything here is fictional.**
- **People and organisations:** the patient, family, clinicians, hospital, clinic, pharmacy and insurer are invented.
- **Identifiers:** IDs are `DEMO-…`, phone numbers are `6xxx xxxx`, and postal codes start with `000`.
- **Watermark:** every page is marked SYNTHETIC DEMO.

The family and timeline are in [docs/06-synthetic-data.md](../docs/06-synthetic-data.md). The demo day is Mon 26 Oct 2026 (Asia/Singapore).

| Path | Content |
|---|---|
| `documents/<id>.json` | Ground truth for one document: fields exactly as printed (so they double as source spans), approved excerpts, categories, the expected view per role |
| `expected.json` | Expected outcomes: the seed schedule and weekly skill, intake drafts and checks, recall, denials, the share flow, privacy cases, the lookup |
| `templates/`, `fonts/` | HTML/CSS per document type; Kalam (SIL OFL) for the handwritten note |
| `renders/` | `make fixtures` output: `<id>.pdf` and `<id>-p<n>.png` at 150 dpi |
| `photos/` | Phone photos of printed copies, used by the intake demo |

`tests/test_fixtures.py` checks four things:
- every field and excerpt is actually printed
- only placeholder identifiers appear
- the views follow `config/policy.yaml`
- `expected.json` points at real documents and members

## Documents

| ID | Type | Date | Case | Photo |
|---|---|---|---|---|
| `discharge-summary` | Discharge summary, 2 pages | 23 Oct 2026 | Supersession; 9:30 am follow-up | yes |
| `appointment-slip` | Appointment slip | 23 Oct 2026 | 10:30 am, which clashes with the summary | yes |
| `label-metformin` | Medication label | 23 Oct 2026 | — | yes |
| `label-amoxiclav` | Medication label | 23 Oct 2026 | Faded dispensed date | |
| `label-losartan` | Medication label | 28 Sep 2026 | Refill calculation | |
| `clinic-memo` | Cardiology memo | 26 Jun 2026 | Recall source | |
| `insurance-letter` | Insurance claim letter | 24 Oct 2026 | Share flow | |
| `carer-note` | Handwritten carer note | 25 Oct 2026 | Observations | yes |

## Rendering

```bash
make setup-data   # WeasyPrint, Jinja2, pypdfium2; needs libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
make fixtures     # writes renders/
```

MiniCPM-V 4.5 reads 68 of the 70 ground-truth values from the photos. It misreads Glipizide as "Glibpizide" on the low-resolution discharge pages (under 900 px tall), and the intake tests expect Kin to ask about it.
