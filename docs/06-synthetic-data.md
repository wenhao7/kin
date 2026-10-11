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

Fictional institutions: Eastbrook General Hospital; Bedok Hill Family Clinic; Dr Tan Hui Min; Dr Rajan; Sunrise Pharmacy.

## Timeline

| When | Event | Documents |
|---|---|---|
| Month −6 | Routine follow-ups | Appointment slip; medication labels ×4; lab report |
| Month −4 | GP visit; BP medication adjusted | Clinic memo; updated label |
| Month −3 | Physio referral | Referral letter; exercise sheet |
| Month −1 | Admission (chest infection) | Admission note; discharge summary with medication review (one stopped, one dose changed, one antibiotic course); MC; invoice; insurance claim letter |
| Week 0 (demo day) | Post-discharge | Pill box photos ×5; follow-up slip |
| Week +1 | Cardiology follow-up | Consult recording (optional); next appointment |
| Week +3 | Siti on home leave | Respite carer (optional) |

## Minimum fixture (D1, 8 documents)

Discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter, handwritten carer note. All eight rendered; four photographed. Ground truth per document: fields, source spans, category, expected confirmation, supersession links, approved excerpts and expected Admin/Family/Carer views. Include cases for low-confidence extraction, a conflicting instruction between two documents, denied recall and a finance share request.

## Optional full set (≥ 20)

Discharge summary (2 pages); medication labels ×5; appointment slips ×3; lab reports ×2; clinic memos ×2; referral letter; exercise sheet; MC; invoice; insurance claim letter; LPA cover page; carer notes ×2; consult audio ×1 (scripted, two team members, mono 16 kHz).

## Generation

1. Content as structured JSON (ground truth and extraction test set).
2. HTML/CSS templates → PDF/PNG (WeasyPrint or Playwright) with realistic letterheads, tables, stamps, reference numbers; watermark "SYNTHETIC DEMO".
3. Print a subset and photograph on a kitchen table; the intake demo uses photos, clean renders stay for tests.
4. Identifiers obviously invalid (`DEMO-NOT-A-REAL-ID`), non-dialable phone placeholders, fictional addresses, dates relative to demo day.
5. Mandarin summaries checked by a fluent reviewer; live translation uses only confirmed fields.

## Locale pack (Singapore)

`locale/sg/locale.yaml`: languages `en`, `zh`; lookup allow-list (gov.sg scheme pages, demo clinic sites); document templates and label formats; local terms (polyclinic, MC, helper, CHAS, MediSave, Home Caregiving Grant, LPA). Swapping the locale replaces the folder.
