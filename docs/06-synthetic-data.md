# 06 · Synthetic data

All demo data is fictional. No real patient, family, clinician, clinic or hospital is depicted. Government scheme names are public information, looked up live with attribution; no document purports to be issued by a real agency.

## Family

| Person | Role | Notes |
|---|---|---|
| **Mdm Tan Siew Lan**, 78 | Care recipient | Lives with daughter's family. Hypertension, type 2 diabetes, mild osteoarthritis. Recent 5-day admission for a chest infection with medication review on discharge. Mandarin/Hokkien. |
| **Lim Mei Ling**, 52 | Admin | Daughter. Works full-time. Holds the LPA. Appointments, money, paperwork. |
| **Lim Wei Jie**, 48 | Family | Son. Lives in Melbourne. |
| **Tan Bee Lian**, 74 | Family | Mdm Tan's sister. Visits twice weekly. Prefers Mandarin. |
| **Siti Rahmah**, 34 | Carer | Live-in helper, three years with the family. English and Malay. |
| Respite carer | Viewer (14 days, optional) | Covers Siti's home leave. |

Fictional institutions: Eastbrook General Hospital; Bedok Hill Family Clinic; Dr Tan Hui Min (physician); Dr Rajan (GP); Sunrise Pharmacy.

## Timeline

| When | Event | Documents |
|---|---|---|
| Month −6 | Routine follow-ups | Appointment slip; medication labels ×4; lab report |
| Month −4 | GP visit; BP medication adjusted | Clinic memo; updated label |
| Month −3 | Physio referral (knee) | Referral letter; exercise sheet |
| Month −1 | Hospital admission (chest infection) | Admission note; discharge summary with medication review (one stopped, one dose changed, one antibiotic course); MC for Mei Ling; invoice; insurance claim letter |
| Week 0 (demo day) | Post-discharge | Pill box photos ×5; follow-up appointment slip; family note on Home Caregiving Grant application |
| Week +1 | Cardiology follow-up | Consult recording (~4 min, scripted); summary; next appointment |
| Week +3 | Siti on home leave | Respite carer onboarding; viewer role with expiry |

## Minimum fixture (8 documents)

D1 requires a discharge summary, three medication labels, appointment slip, Month −4 clinic memo, insurance claim letter and handwritten carer note. Four are photographed; clean renders and ground truth remain available for all eight. The larger timeline below is optional breadth.

Ground truth includes exact source spans, record/version/category, proposed fields, confirmed instructions and timezones, supersession links, approved field/source crops and expected Admin/Family/Carer/group views. A mixed discharge original stays Admin-only; lower roles receive approved excerpts. Finance/legal fields must not leak through a source attachment, translation, cache or previous chat.

Include deterministic cases for low-confidence extraction, conflicting medication instructions, pending confirmation, supersession, restart/retry, spoofed identity, unknown group member, revoked/one-shot grants and denied recall. The fixture must specify expected denials without exposing hidden record existence. No reminder activates directly from an unconfirmed extraction.

## Optional full document set (≥ 20)

- Discharge summary (2 pages): diagnoses, course, medication table before/after, follow-up.
- Medication labels ×5 (pharmacy label format: name, strength, directions, quantity, date).
- Appointment slips ×3. Lab reports ×2. Clinic memo / GP note ×2.
- Referral letter; exercise sheet. MC; hospital invoice; insurance claim letter.
- LPA cover page (redacted-looking) — `legal`.
- Handwritten notes from Siti (photos) ×2 — `observations`.
- Consult audio ×1 (scripted; two team members; mono 16 kHz).

## Generation

1. Content for each document as structured JSON (ground truth; also the extraction test set).
2. HTML/CSS templates per document type → PDF/PNG (WeasyPrint or Playwright); realistic layout: letterhead, tables, stamps, reference numbers.
3. Print a subset and photograph on a kitchen table (angles, shadows). Intake demo uses photos; clean PDFs kept for tests.
4. Use conspicuously invalid identifiers such as `DEMO-NOT-A-REAL-ID`, non-dialable phone placeholders, fictional addresses and dates fixed by the reset fixture. Watermark every document “SYNTHETIC DEMO”.
5. Mandarin summaries are checked by a fluent reviewer; live translation uses only the recipient-authorized fields and sources. Translation quality is a separate check from permission enforcement.

## Locale pack (Singapore)

- Languages: `en`, `zh`.
- Lookup allow-list: scheme pages on gov.sg domains; clinic/pharmacy sites used in the demo.
- Document templates and label formats.
- Local terms: polyclinic, MC, helper, CHAS, MediSave, Home Caregiving Grant, LPA.
