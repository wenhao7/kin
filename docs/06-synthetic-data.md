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
| Respite carer | Viewer (14 days) | Covers Siti's home leave. |

Fictional institutions: Eastbrook General Hospital; Bedok Hill Family Clinic; Dr Tan Hui Min (physician); Dr Rajan (GP); Sunrise Pharmacy.

## Timeline

| When | Event | Documents |
|---|---|---|
| Month −6 | Routine follow-ups | Appointment slip; medication labels ×4; lab report |
| Month −4 | GP visit; BP medication adjusted | Clinic memo; updated label |
| Month −3 | Physio referral (knee) | Referral letter; exercise sheet |
| Month −1 | Hospital admission (chest infection) | Admission note; discharge summary with medication review (one stopped, one dose changed, one antibiotic course); MC for Mei Ling; invoice; insurance claim letter |
| Week 0 (demo day) | Post-discharge | Pill box photos ×5; follow-up appointment slip; family note on Home Caregiving Grant application |
| Week +1 | Cardiology follow-up | After-visit summary (printed by the clinic, photographed): one dose change, action items, next appointment |
| Week +3 | Siti on home leave | Respite carer onboarding; viewer role with expiry |

## Document set (≥ 20)

- Discharge summary (2 pages): diagnoses, course, medication table before/after, follow-up.
- Medication labels ×5 (pharmacy label format: name, strength, directions, quantity, date).
- Appointment slips ×3. Lab reports ×2. Clinic memo / GP note ×2.
- Referral letter; exercise sheet. MC; hospital invoice; insurance claim letter.
- LPA cover page (redacted-looking) — `legal`.
- Handwritten notes from Siti (photos) ×2 — `observations`.
- After-visit summary ×1 (Week +1 cardiology) — drives the debrief.

## Generation

1. Content for each document as structured JSON (ground truth; also the extraction test set).
2. HTML/CSS templates per document type → PDF/PNG (WeasyPrint or Playwright); realistic layout: letterhead, tables, stamps, reference numbers.
3. Print a subset and photograph on a kitchen table (angles, shadows). Intake demo uses photos; clean PDFs kept for tests.
4. Placeholders: NRIC `S0000000A`; phones `6xxx xxxx` / `9xxx xxxx`; fictional addresses; dates relative to demo day.
5. Mandarin summaries checked by a native speaker; live translation still performed by the model.

## Locale pack (Singapore)

- Languages: `en`, `zh`.
- Lookup allow-list: scheme pages on the domains in `locale/sg/locale.yaml` (gov.sg, AIC, MOH, CPF, HealthHub, CHAS). The demo clinics are fictional, so lookups cover public schemes only.
- Document templates and label formats.
- Local terms: polyclinic, MC, helper, CHAS, MediSave, Home Caregiving Grant, LPA.
