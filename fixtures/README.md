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

Current photos: `discharge-summary-p1.jpg`, `discharge-summary-p2.jpg`, `label-metformin.jpg`, `appointment-slip.jpg`, `carer-note.jpg`, taken with a phone of the renders on a monitor (screen moiré included), resized to 2000 px and saved without metadata. MiniCPM-V 4.5 read every ground-truth value on them verbatim (70/70; about 740 input tokens and 2–6 s per photo). Kitchen-table photos of printed copies can replace them for the video.
