# 06 · Synthetic data

All demo data is fictional. No real patient, family, clinician, clinic or hospital is depicted. Government scheme names are public information, looked up live with attribution; no document purports to be issued by a real agency.

## Family

| Person | Role | Notes |
|---|---|---|
| **Mdm Tan Siew Lan**, 78 | Care recipient | Lives with daughter's family. Hypertension, type 2 diabetes, mild osteoarthritis. Recent 5-day admission for a chest infection with medication review on discharge. Mandarin/Hokkien. |
| **Lim Mei Ling**, 52 | Admin | Daughter. Works full-time. Holds the LPA. |
| **Lim Wei Jie**, 48 | Family | Son. Lives in Melbourne. |
| **Tan Bee Lian**, 74 | Family | Mdm Tan's sister. Prefers Mandarin. |
| **Siti Rahmah**, 34 | Carer | Live-in helper. English and Malay. |
| Respite carer | Viewer (optional) | Covers Siti's home leave. |

Fictional institutions: Eastbrook General Hospital (Dr Tan Hui Min, cardiologist); Bedok Hill Family Clinic (Dr Rajan, GP); Sunrise Pharmacy; Orchidline Assurance (insurer).

## Timeline

Demo day (Week 0) is Mon 26 Oct 2026; documents carry absolute dates on that timeline.

| When | Event | Documents |
|---|---|---|
| Month −6 | Routine follow-ups | Appointment slip; medication labels ×4; lab report |
| Month −4 | Cardiology review with Dr Tan Hui Min; BP medication adjusted | Clinic memo; updated label |
| Month −3 | Physio referral | Referral letter; exercise sheet |
| Month −1 | Admission (chest infection) | Admission note; discharge summary with medication review (one stopped, one dose changed, one antibiotic course); MC; invoice; insurance claim letter |
| Week 0 (demo day) | Post-discharge | Pill box photos ×5; follow-up slip |
| Week +1 | Cardiology follow-up | After-visit summary (optional debrief); next appointment |
| Week +3 | Siti on home leave | Respite carer (optional) |

## Minimum fixture (D1, 8 documents)

Discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter, handwritten carer note. All eight rendered; four photographed. Ground truth per document: fields, source spans, category, expected confirmation, supersession links, approved excerpts and expected Admin/Family/Carer views. Include cases for low-confidence extraction, a conflicting instruction between two documents, denied recall and a finance share request.

Files: `fixtures/documents/<id>.json` (ground truth; field values are printed verbatim and double as source spans), `fixtures/expected.json` (expected outcomes), `fixtures/renders/` (`make fixtures`), `fixtures/photos/`. Cases: the discharge summary's 9:30 am follow-up conflicts with the slip's 10:30 am; it supersedes metformin 850 mg and stops glipizide in the seed schedule; the amoxicillin-clavulanate label's dispensed date is faded (low confidence); the losartan label drives a refill calculation; the Month −4 memo is the recall source; the insurance letter drives the share flow. See [fixtures/README.md](../fixtures/README.md).

## Optional full set (≥ 20)

Discharge summary (2 pages); medication labels ×5; appointment slips ×3; lab reports ×2; clinic memos ×2; referral letter; exercise sheet; MC; invoice; insurance claim letter; LPA cover page; carer notes ×2; after-visit summary ×1 (Week +1).

## Generation

1. Content as structured JSON (ground truth and extraction test set).
2. HTML/CSS templates → PDF/PNG (WeasyPrint and pypdfium2, `make fixtures`; deterministic) with realistic letterheads, tables, stamps, reference numbers; watermark "SYNTHETIC DEMO".
3. Print a subset and photograph on a kitchen table; the intake demo uses photos, clean renders stay for tests.
4. Identifiers obviously invalid (`DEMO-NOT-A-REAL-ID`), non-dialable phone placeholders, fictional addresses (postal codes `000xxx`), dates on the demo-day timeline.
5. Mandarin summaries checked by a fluent reviewer; live translation uses only confirmed fields.

## Locale pack (Singapore)

`locale/sg/locale.yaml`: languages `en`, `zh`; timezone; lookup allow-list (scheme pages on gov.sg, AIC, MOH, CPF, HealthHub, CHAS; the demo clinics are fictional, so lookups cover public schemes only) and the schemes Kin may look up (`lookup_topics`; the query is the scheme's name alone); document types and fields; local terms (polyclinic, MC, helper, CHAS, MediSave, Home Caregiving Grant, LPA). Swapping the locale replaces the folder.
