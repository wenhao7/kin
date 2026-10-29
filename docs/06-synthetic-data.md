# 06 · Synthetic data

Everything in the demo is fictional: no real patient, family, clinician or institution. Government scheme names are public and are looked up live.

## The family

| Person | Role | Notes |
|---|---|---|
| Mdm Tan Siew Lan ("Ah Ma"), 78 | Care recipient | Hypertension, type 2 diabetes. Just home after a chest infection, with medication changes on discharge |
| Lim Mei Ling, 52 | Admin | Daughter; keeps the records |
| Lim Wei Jie, 48 | Family | Son; lives in Melbourne |
| Tan Bee Lian, 74 | Family | Ah Ma's sister; prefers Mandarin |
| Siti Rahmah, 34 | Carer | Live-in helper |

Fictional institutions: Eastbrook General Hospital (Dr Tan Hui Min, cardiologist), Bedok Hill Family Clinic, Sunrise Pharmacy, Orchidline Assurance.

## Timeline

The demo day (Week 0) is Mon 26 Oct 2026, and every document carries a date on that timeline.

| When | What happened | Document in the fixture |
|---|---|---|
| June (Month −4) | Cardiology review; Losartan started | Clinic memo |
| September | Losartan dispensed | Medication label |
| 18–23 Oct | Hospital stay; one medicine stopped, one dose reduced, one antibiotic course | Discharge summary (2 pages), medication labels, appointment slip |
| 24–25 Oct | Insurance claim under assessment; the helper's notes | Insurance letter, handwritten carer note |

## What the fixture tests

The fixture has eight documents. Their expected outcomes are in `fixtures/expected.json`:
- **A conflict:** the discharge summary's 9:30 am follow-up against the slip's 10:30 am.
- **Supersession:** the summary replaces Metformin 850 mg and stops Glipizide.
- **A doubtful field:** a faded dispensed date.
- **A refill calculation:** from the Losartan label.
- **Recall:** answering from the June memo.
- **Sharing:** the insurance letter drives the share flow.

Files and rendering: [fixtures/README.md](../fixtures/README.md).

## How it's made

1. **Content:** each document starts as structured JSON, which is both ground truth and the extraction test set.
2. **Rendering:** HTML templates are rendered to PDF and PNG (`make fixtures`). Every page is watermarked SYNTHETIC DEMO, with placeholder IDs (`DEMO-…`), non-dialable phone numbers and `000xxx` postal codes.
3. **Photos:** a subset was printed and photographed on a table. The demo sends the photos; the tests use the clean renders.

## Locale pack

`locale/sg/locale.yaml` holds:
- languages (`en`, `zh`) and the timezone
- the lookup allow-list (gov.sg, AIC, MOH, CPF, HealthHub, CHAS)
- the schemes Kin may look up

Another locale is a different folder.
