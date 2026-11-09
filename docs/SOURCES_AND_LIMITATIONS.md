# Official Sources, Provenance, Safety and Limitations

## What the knowledge base is intended to use

ArogyaGuard AI is designed to retrieve from an **allow-listed collection of official Indian government maternal-health documents**. A source appearing in this list does not guarantee successful download, readable OCR, complete local indexing or current legal/operational applicability.

| Programme / topic | Official resource | Purpose and important caveat |
|---|---|---|
| **ASHA training** | [ASHA Module 6, Simple Skills that Save Lives](https://nhm.gov.in/images/pdf/communitisation/asha/book-no-6.pdf) | Community maternal-health information, danger signs and appropriate professional referral; not an AI diagnosis protocol |
| **ASHA induction** | [NHM ASHA Induction Module](https://nhm.gov.in/images/pdf/communitisation/asha/ASHA_Induction_Module_English.pdf) | ASHA role and community linkage to services |
| **JSSK** | [NHM JSSK Guidelines PDF](https://nhm.gov.in/images/pdf/programmes/guidelines-for-jssk.pdf) · [NHM JSSK programme page](https://nhm.gov.in/index4.php?lang=1&level=0&lid=171&linkid=150) | Published free public-facility maternal services and specified transport provisions; **not** a promise of local availability or individual eligibility |
| **PMSMA** | [PMSMA Operational Framework](https://nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/PMSMA_Operational_Framework.pdf) | Antenatal programme services, high-risk identification and follow-up context |
| **Extended PMSMA** | [NHM high-risk tracking guidance](https://www.nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/Guidance_Note-Extended_PMSMA_for_tracking_HRPs.pdf) | Initial rollout and programme-specific follow-up considerations. Check **current** state rollout before making eligibility statements |
| **SUMAN** | [NHM SUMAN Guidelines](https://www.nhm.gov.in/New_Updates_2018/NHM_Components/RMNCHA/MH/Guidelines/SUMAN%20Guideline%202020%20Web%20Version.pdf) | Respectful maternity care and service-assurance context |
| **Programme overview** | [NHM Maternal Health](https://nhm.gov.in/images/pdf/guidelines/nrhm-guidelines/family-planning/index1.php?lang=1&level=2&lid=218&sublinkid=822) | Background on JSSK, PMSMA and other maternal-health programmes |

For the precise application registry and configured document metadata, inspect **`arogyaguard/catalog.py`** in the repository. Official government PDFs are **not included automatically** in the source-code package.

## Standards and ethics background

- [ITU-T Recommendation Y.3172](https://www.itu.int/ITU-T/recommendations/rec.aspx?id=13894): general ML architecture for future networks, adapted here as a conceptual mapping.
- [ITU AI Ready framework report](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework): readiness dimensions for examination, not a certification score.
- [World Health Organization: Ethics and governance of AI for health](https://www.who.int/publications/i/item/9789240029200): general ethical guidance informing human-oversight discussion.

## Source quality and provenance checklist

Before treating a retrieved document as authoritative for a particular response, confirm:

1. The document originates from an **approved official source** and the source link is correct.
2. The **title, publisher, publication/revision date, and page** are retained where possible.
3. The document's **programme, state/jurisdiction, rollout phase and time period** apply to the question.
4. OCR and extraction have not changed **numbers, negations, conditions or eligibility clauses**.
5. A response's citation supports the **specific statement** being made, rather than merely referring to a related page.
6. Missing evidence is described as uncertainty. An unverified amount, transport booking or local facility service is not invented.

**Source freshness:** The current prototype uses manually downloaded/indexed material. It does not continuously detect or apply official document updates. A future Knowledge Update Agent is proposed to monitor changes and support **verified, human-approved** re-indexing.

## Safety and deployment boundaries

**Clinical boundary:** This is a research/demo assistant, not a clinically validated diagnostic, treatment, emergency dispatch or triage tool. Severe headache with blurred vision during pregnancy warrants urgent qualified medical assessment. The system must not encourage waiting for its answer before seeking professional help.

**Human responsibility:** ASHA/ANM workers and qualified professionals make real-world decisions. A generated checklist does not mean a referral, visit, transport request or follow-up has been booked or confirmed.

**Privacy:** Only fictional demonstration cases should be entered. Live external LLM requests may transfer prompt content beyond the local machine. The sample application is not a complete authenticated patient-record system; basic input checks do not make it suitable for sensitive patient data.

**Connectivity:** The web application, SQLite and optional Qdrant can run locally, but **OpenRouter LLM inference currently requires internet access**. Initial PDF download, Python dependency installation, and embedding model download may also require internet.

**Regional-language performance:** The interface covers English, Hindi, Telugu and Kannada, but equivalent clinical/policy answer quality has **not** been established. Browser speech capabilities vary. Informal testing found English somewhat more consistent; matched multilingual validation is still required.

**Indexing:** Scanned PDFs may need Tesseract OCR and manual review. Qdrant only provides semantic search after successful vector building; until then retrieval may operate using SQLite FTS5 alone.

**Citations:** The code filters nonexistent model-generated evidence IDs, but does not fully validate every generated sentence against source passages. A valid source ID is not a guarantee of factual correctness.

**Licensing and redistribution:** A repository MIT license applies to the code released by its copyright holders. It does **not automatically relicense** government PDFs, external libraries, model weights or third-party content. Link to official documents rather than redistributing unreviewed copies.

**Future capability:** Document AutoSync, clinical validation, live local eligibility checks, authenticated patient workflow and fully offline edge inference are **not established current capabilities**.

## Related documentation

[MAP.md](MAP.md) · [USE_CASE_AND_REQUIREMENTS.md](USE_CASE_AND_REQUIREMENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [DEMO_AND_EVALUATION.md](DEMO_AND_EVALUATION.md) · [POLICY_AND_STANDARDS_GAPS.md](POLICY_AND_STANDARDS_GAPS.md)
