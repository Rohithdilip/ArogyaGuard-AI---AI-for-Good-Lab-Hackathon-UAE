# Use Case and Requirements

## The problem we address

In India, **Accredited Social Health Activists (ASHAs)** connect pregnant women and families with public healthcare services. A frontline worker may need guidance from separate documents to understand pregnancy danger signs, facility referral, JSSK transport provisions, missed antenatal care, high-risk pregnancy follow-up and respectful maternity care.

ArogyaGuard AI explores whether a multilingual, evidence-linked assistant can make that guidance easier to locate and understand. It is intended to **support healthcare workers, not replace qualified professionals**.

## A synthetic story: Lakshmi

Lakshmi is eight months pregnant in a village in Telangana. She reports **severe headache and blurred vision**, missed a scheduled antenatal visit, and her family is worried about transport costs. Her ASHA worker needs to understand three separate questions:

1. What requires **urgent professional assessment and referral**?
2. What does **official government guidance** say about transport support, and what must be confirmed locally?
3. Who should coordinate **missed-visit and high-risk follow-up** after the urgent needs are addressed?

Lakshmi is **entirely fictional**. The case demonstrates information coordination and AI limitations; it is not a clinical diagnosis or a claim that transport has been arranged.

## Primary users and responsibilities

| Role | Relationship to this prototype |
|---|---|
| **ASHA** | Community health worker asking questions, contacting care services and coordinating with supervisors |
| **ANM** | Auxiliary Nurse Midwife who may provide professional frontline support and referral coordination |
| **Qualified clinician / facility team** | Responsible for diagnosis, treatment and clinical decisions |
| **ASHA/ANM supervisor or local official** | Confirms uncertain local programme details and operational entitlements |
| **Prototype evaluator** | Uses synthetic scenarios, inspects routing and sources, records failure modes |

## Plain-language glossary

| Term | Meaning |
|---|---|
| **NHM** | National Health Mission, a framework for Indian public health programmes |
| **ANC** | Antenatal Care, health services and monitoring during pregnancy |
| **JSSK** | Janani Shishu Suraksha Karyakram, public maternal/newborn service entitlements, including specified transport |
| **PMSMA** | Pradhan Mantri Surakshit Matritva Abhiyan, focused antenatal services and identifying high-risk pregnancies |
| **Extended PMSMA** | Additional high-risk pregnancy follow-up guidance; rollout phase and state applicability must be verified |
| **SUMAN** | Surakshit Matritva Aashwasan, guidance supporting respectful and assured maternal/newborn care |
| **RAG** | Retrieval-augmented generation, using relevant retrieved documents when producing an answer |

## Functional and non-functional requirements

**Status meanings:** `Prototype` = functionality represented in the V3 implementation; `Partial / evaluate` = present or intended but not yet reliably validated; `Future` = not claimed as implemented.

| ID | Requirement | Acceptance / evaluation check | Status |
|---|---|---|---|
| R01 | Natural-language input | Accept written questions without requiring users to choose agents | Prototype |
| R02 | Four-language interaction | Test input and response in English, Hindi, Telugu and Kannada; confirm unclear speech transcripts | Partial / evaluate |
| R03 | Dynamic orchestration | Show which specialists were actually selected and why in the execution trace | Prototype; compound-intent gap |
| R04 | Guidance and referral | Find approved guidance on ANC and danger signs; prioritize urgent professional assessment | Prototype; clinical evaluation needed |
| R05 | Government benefits | Retrieve JSSK information with references; do not promise an unverified amount or vehicle | Prototype; local applicability verification needed |
| R06 | Follow-up continuity | Retrieve missed-ANC/high-risk follow-up guidance; make no claim that a task was completed | Prototype; routing coverage evaluation needed |
| R07 | Evidence and provenance | Provide real stored passage references/page attribution where available; abstain when evidence is insufficient | Prototype; claim-level checking pending |
| R08 | Safety and oversight | Surface conservative danger-sign caution; require qualified human decisions | Partial / evaluate |
| R09 | Source preparation | Extract/index approved PDFs; detect scan/OCR errors; show source/index status | Partial / evaluate |
| R10 | Minimal data exposure | Use synthetic cases; no identifying patient information; assess external model privacy requirements | Demo boundary; production controls future |
| R11 | Reproducible setup | Document Python, API key, dependencies, OCR and vector-build prerequisites | Documentation task |
| R12 | Evaluation transparency | Record expected versus actual agent selection, evidence, language and safety results | Evaluation protocol; larger test set future |

## Expected user journey

1. The frontline worker chooses a preferred language and enters a text or voice question.
2. The application can surface an **independent conservative safety warning** for possible danger signs.
3. The LLM planner decides whether the question is within the project scope and selects one or more specialist agents.
4. Each selected specialist retrieves relevant evidence from an approved official document collection.
5. Governance combines available findings into **one answer with citations, uncertainty and human-led next steps**.
6. The worker verifies the information and contacts qualified health services or local officials as appropriate.

A question about an ordinary ANC visit may need only Guidance and Governance. A question about transport may need Benefits and Governance. A synthetic combined case **should** engage Guidance, Benefits and Follow-up, but the full route must be checked rather than assumed.

## Scope boundaries

**In scope:** Indian maternal-health guidance; ANC visits; danger signs; referrals; ASHA/ANM responsibilities; JSSK entitlements; PMSMA follow-up; respectful maternity care; uncertainty about local implementation.

**Out of scope:** General knowledge questions unrelated to maternal health; actual treatment and diagnosis; medication prescription; guaranteed local eligibility, amounts or service availability; autonomous emergency dispatch or case-management action.

## Reuse beyond maternal healthcare

The reusable elements include natural-language intake, LLM planning, role-specific retrieval, evidence referencing, governance and a common interface. This offers a **starting point** for future education or agriculture applications, but each new domain will require its own reviewed official documents, domain-specific agent responsibilities, safeguards and evaluations. Replacing PDFs alone is insufficient.

See also [ARCHITECTURE.md](ARCHITECTURE.md), [MAP.md](MAP.md) and [POLICY_AND_STANDARDS_GAPS.md](POLICY_AND_STANDARDS_GAPS.md).
