# 01 · Problem

## Statement

Family caregiving is a multi-person, multi-year, medically demanding coordination job run out of a group chat and a shoebox of paper. The caregiver who holds it together has no memory aid, no admin support, and no way to share the load without sharing everything with everyone.

## Evidence

| Claim | Number | Source |
|---|---|---|
| Caregiving is mainstream | 63M US caregivers, ~1 in 4 adults, up ~50% since 2015; 29% sandwich generation | AARP / NAC, Caregiving in the US 2025 |
| Medical work without training | 55% perform medical/nursing tasks; 22% received training | AARP / NAC 2025 |
| Coordination is the pain | 1 in 3 find care coordination challenging; 64% communicate with providers; 70% monitor health | AARP / NAC 2025 |
| Singapore is super-aged | 1 in 5 residents aged 65+ in 2026 | LKYSPP; NBER |
| Load is rising | Family eldercare hours projected 29 → 41 per week | NBER w31958 |
| Burden is growing | 27.9% of informal caregivers report care burden (24.5% a decade earlier) | BMC Geriatrics 2026 (WiSE) |
| Work is disrupted | 55% of working caregivers left work for a doctor visit in the past 6 months; 68% took leave | Duke-NUS research brief |
| Who carries it | 66% adult children; 73% women; over half aged 60+ | Duke-NUS |

Treat figures above as research context, not measured Kin outcomes. Recheck each original source, publication date, population and denominator before putting statistics into Devpost/video; US caregiver findings and Singapore projections are not interchangeable.

## How the work happens

- Coordination in a WhatsApp/Telegram family group.
- Information arrives as paper: discharge summaries, clinic slips, pharmacy labels, MCs, insurance and grant letters.
- One sibling holds everything in their head; the sibling overseas is a day behind; the helper doing hands-on care is told last.
- Diagnoses, medication, finances and legal powers — the most sensitive data a family holds — sit in people's heads, consumer apps or general chatbots with no boundaries.

## Users

1. Primary caregiver (typically a working daughter, 40s–60s).
2. Siblings and remote family.
3. Domestic helpers and hired carers.
4. The parent, as the subject of care.

## Landscape

| Segment | Players | Gap |
|---|---|---|
| AI + human coordination (US) | Hera ($27M Series A, Jun 2026; nurses + AI; 1,000 families) | Service-heavy; US; health-system distribution |
| Employer care concierge | Cariloop ($40M), Wellthy ($35M) | Human coaches sold to HR |
| Paid family caregiving | Abby Care ($45M raised) | Medicaid-driven |
| Consumer coordination apps | Caring Village (AI "Julia"), ianacare, Carely, Lotsa Helping Hands, CaringBridge | Cloud coordination apps; Caring Village already has role permissions. Compare source-grounded chat memory and field/source sharing, not the mere existence of roles |
| Elder-facing devices | ElliQ, Sensi.ai | For the elder, not the family |
| Singapore | Homage, Jaga-Me; AIC caregiver resources | Supply of care, not coordination |
| Default | WhatsApp, Notes, ChatGPT | Fragmented context and documents; the intended cross-person permission/recall workflow needs explicit controls |

Kin targets a combined workflow rather than claiming unique role permissions: chat-based intake, confirmed schedules, durable source-grounded memory, reusable skills and auditable recipient-specific sharing. Validate competitor capabilities before using absolute novelty claims. [Caring Village member roles](https://help.caringvillage.com/hc/en-us/articles/218121268-What-do-the-member-roles-mean)

## Differentiation

1. Self-hosted domain records with explicit policy controls; Telegram carries messages and Nebius receives approved inference inputs. The deployed boundary must be tested.
2. Qualified photo intake from paper; audio debrief is optional.
3. Lives in the group chat the family already uses.
4. Memory across years, grounded to source documents.
5. Field/relationship boundaries enforced at retrieval, history/tools and delivery, with audit.
6. One durable reusable scheduled skill; arbitrary teach-by-chat is optional.
7. Confirmed scheduling in the minimum; appointment prep and audio debrief follow later.
8. Local context from allow-listed public sources.

Sources: [sources.md](sources.md).
