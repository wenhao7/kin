# Synthetic fixture

**Everything here is fictional.** The patient, family, clinicians, hospital, clinic, pharmacy and insurer are invented; identifiers are `DEMO-…` placeholders, phone numbers are `6xxx xxxx`, postal codes start with `000`, and every page is marked SYNTHETIC DEMO. No document purports to come from a real organisation. Family and timeline: [docs/06-synthetic-data.md](../docs/06-synthetic-data.md).

Demo day (Week 0) is Mon 26 Oct 2026, timezone Asia/Singapore.

## Layout

| Path | Content |
|---|---|
| `documents/<id>.json` | Ground truth for one document: `fields` as a correct transcription reads them (every value is printed verbatim, so they double as source spans), `excerpts` approved for other roles, `categories`, expected `views` per role, `render`-only details |
| `expected.json` | Expected outcomes: seed schedule, intake drafts and confirmations (conflict, supersession, low-confidence field, refill), recall, denied requests, the share flow, the minimum privacy tests, the public lookup |
| `templates/` | HTML/CSS per document type; `base.css` carries the watermark and footer |
| `fonts/` | Kalam (SIL Open Font License, `OFL.txt`) for the handwritten carer note |
| `renders/` | `make fixtures` output: `<id>.pdf` and `<id>-p<n>.png` (150 dpi), deterministic |
| `photos/` | Phone photos of the four photographed documents (below) |

`tests/test_fixtures.py` checks that every field and excerpt is printed, that only placeholder identifiers appear, that views follow `config/policy.yaml` (originals stay Admin-only) and that `expected.json` references real documents, excerpts and roster members.

## Documents

| ID | Type | Date | Categories | Photograph |
|---|---|---|---|---|
| `discharge-summary` | Discharge summary, 2 pages | 23 Oct 2026 | medical, medication, appointments | yes |
| `label-metformin` | Medication label | 23 Oct 2026 | medication | yes |
| `label-amoxiclav` | Medication label, faded dispensed date (low-confidence case) | 23 Oct 2026 | medication | |
| `label-losartan` | Medication label (refill case) | 28 Sep 2026 | medication | |
| `appointment-slip` | Appointment slip, 10:30 am (conflicts with the discharge summary's 9:30 am) | 23 Oct 2026 | appointments | yes |
| `clinic-memo` | Month −4 cardiology memo (recall source) | 26 Jun 2026 | medical, medication | |
| `insurance-letter` | Insurance claim letter (share-flow source) | 24 Oct 2026 | finance | |
| `carer-note` | Handwritten carer note | 25 Oct 2026 | observations | yes |

## Rendering

```bash
make setup-data   # WeasyPrint, Jinja2, pypdfium2 (needs the pango libs in KICKOFF.md)
make fixtures     # writes renders/
```

## Photos — **YOU**

Print the four marked documents at 100% (the label and slip print on their own small page sizes) and photograph each on a kitchen table with a phone: whole page in frame, natural light, slight angle, no flash. The carer note can instead be copied out by hand on lined paper — real handwriting is the better test. Save as `photos/<id>.jpg` (for example `photos/discharge-summary-p1.jpg`). Photos are what the intake demo sends; clean renders stay for tests.

Current photos: `discharge-summary-p1.jpg`, `discharge-summary-p2.jpg`, `label-metformin.jpg`, `appointment-slip.jpg`, `carer-note.jpg`: printed copies on a table, 646–1149 px on the long side, saved without metadata. MiniCPM-V 4.5 read 68 of 70 ground-truth values (the diagnoses come back with their list numbers) and misread "Glipizide" as "Glibpizide"/"Gliplzide" on both discharge pages, where an A4 page is under 900 px tall; label, slip and carer note were read in full. About 400–540 input tokens and 2–5 s per photo. Earlier photos of the renders on a monitor at 2000 px scored 70/70. Higher-resolution photos (Telegram keeps up to about 1280 px; sending as a file keeps the original) should close the gap; the misread is an `expected.json` intake case either way.
