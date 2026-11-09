# Policy and Standards Gap Analysis

**Purpose:** Identify practical policy, data and AI-governance questions exposed by the ArogyaGuard AI prototype. This analysis is the main research contribution for the hackathon, not a claim of clinical or standards certification.

## How to interpret the evidence

We distinguish three types of statement:

- **Observed prototype behavior:** an issue reported or seen during local tests.
- **Risk or test scenario:** an important failure mode to evaluate, even if it has not been observed as a completed failure.
- **Candidate policy/standards gap:** a broader question raised by the behavior. This is a proposal for further study, **not proof that Indian government policy or an ITU standard is deficient**.

ITU-T Y.3172 is used as an **architectural mapping tool**. The relevant AI Readiness discussion supplies evaluation lenses; it does not issue a readiness grade for this prototype. See [MAP.md](MAP.md).

## Evidence-to-gap analysis

| ID | Observed issue / risk | Why it matters | Candidate gap to investigate | Proposed improvement | Y.3172 node(s) |
|---|---|---|---|---|---|
| **G01** | **Observed:** some valid SUMAN and PMSMA questions were classified as outside scope | A relevant public programme may become unreachable to a worker | Common topic labels and explainable programme-level routing | Build a reviewed maternal-health taxonomy and synonym set; evaluate in-scope false rejections across languages | M, D |
| **G02** | **Observed:** Follow-up worked with a focused question but was omitted from at least one combined urgent referral/transport/missed-visit request | A multi-need scenario may not cover continuity of care | Compound-intent completeness in agent orchestration | Compare actual `agents_used` against labeled expected specialist sets; improve planner instructions without forcing every agent on every query | M, D |
| **G03** | **Observed:** a JSSK PDF did not yield useful searchable content without further OCR work | Correct guidance can be unavailable even when the PDF exists | Machine-readable public policy, extraction quality and provenance | Human-reviewed OCR, page-by-page checks, structured fields and source-version metadata | SRC, C, PP |
| **G04** | **Observed limitation:** the available evidence did not justify a precise JSSK amount or some local entitlement detail | An unsupported amount or service guarantee could mislead | Jurisdiction, eligibility and programme-phase metadata | Explicitly record state/phase/eligibility; distinguish published entitlement from live local implementation; abstain when unverifiable | SRC, P |
| **G05** | **Risk:** a generated citation refers to a retrieved passage but the passage supports only part of a claim | Provenance is not the same as correctness | Claim-level evidence traceability and accountability | Evaluate each consequential claim against supporting text; escalate uncertain or conflicting evidence | P, D |
| **G06** | **Risk:** severe headache/blurred vision are buried inside a long question or negated in translation | Urgent assistance could be delayed or a warning misfired | Safety evaluation and escalation thresholds across languages | Clinically reviewed danger-sign tests, negation tests and prompt human assessment; urgent message must not wait for benefit lookup | PP, M, P, SINK |
| **G07** | **Informal observation:** English answers have been somewhat more consistent; regional-language parity is unmeasured | A working language toggle does not establish comparable safety or comprehension | Multilingual readiness and user-centered accessibility | Matched English/Hindi/Telugu/Kannada questions, citation checks, referral clarity scoring and speech-transcript review | PP, M, SINK |
| **G08** | **Architecture limitation:** remote LLM inference requires connectivity, even with a local app and local document store | Offline or low-connectivity users may not receive the intended experience | Infrastructure readiness for frontline settings | State network requirements transparently; test connectivity failure; evaluate offline-safe alternatives in later phases | C, M, SINK |

### Specific findings: observed vs not yet demonstrated

**Observed or reported in development:** SUMAN/PMSMA scope misclassification; JSSK retrieval/OCR difficulties; lack of evidence for certain exact benefit claims; Follow-up routing missing from a combined question; informal language-quality differences.

**Not established by those observations:** clinical safety effectiveness, multilingual equivalence, nationwide lack of policy standards, actual local transport availability, proof that the application reliably invokes all relevant agents, or any official ITU compliance result.

## Recommendations and priority

| Priority | Recommendation | Evidence of completion to collect |
|---|---|---|
| **P0: Safety** | Preserve immediate warnings for possible danger signs; never defer urgent clinical assessment for policy retrieval | Synthetic tests covering positive, negated, ambiguous and multilingual symptom statements; clinician-reviewed expectations |
| **P0: Trust** | Avoid invented amounts, eligibility and vehicle availability; distinguish uncertainty from verified entitlements | Manual claim-to-source review for high-impact responses |
| **P1: Routing** | Improve multi-intent planning and in-scope coverage without mandatory all-agent dispatch | Agent-set precision/recall on a labeled set of routine and compound questions |
| **P1: Evidence** | Validate OCR, PDF version, programme jurisdiction, publication scope and page attribution | Source inventory and sampled extraction audit |
| **P1: Inclusion** | Evaluate all four supported languages with the same clinical and policy meanings | Matched multilingual outcome and transcription results |
| **P2: Operations** | Version and review official documents before changing the knowledge base | Human-approved source-update workflow and change history |

Priorities are **Team RITAM's engineering proposals**, not legal requirements or official recommendations from the ITU or NHM.

## Open questions for policy owners and standardization

1. Can government programmes publish **machine-readable, versioned policy records** alongside PDFs, with effective dates, geography, eligibility conditions and issuing authority?
2. What minimum **evidence provenance** should a public-service AI response carry for a worker to verify it?
3. What review and accountability process should govern **state-specific entitlement answers**, especially when a national document is not sufficient?
4. How should multi-agent applications disclose **why an agent was or was not invoked**, without exposing private reasoning or sensitive records?
5. What **multilingual and urgent-safety benchmarks** should be required before a frontline decision-support application is considered suitable for field use?
6. Which steps must remain **explicitly human-controlled** when the application mentions referral, transport or high-risk follow-up?

## Why the prototype matters for the hackathon

ArogyaGuard AI is not presented as a finished national healthcare service. It offers a concrete, reproducible use case to test whether official evidence can be found and routed reliably. The most important output is a defensible set of **data, interoperability, inclusion, governance and human-oversight questions** that can inform future public-service AI requirements.

## Reference framework

- [ITU-T Y.3172](https://www.itu.int/ITU-T/recommendations/rec.aspx?id=13894)
- [ITU: AI Ready report](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework)
- [NHM maternal health programmes](https://nhm.gov.in/images/pdf/guidelines/nrhm-guidelines/family-planning/index1.php?lang=1&level=2&lid=218&sublinkid=822)
- [NHM JSSK](https://nhm.gov.in/index4.php?lang=1&level=0&lid=171&linkid=150)
- [SOURCES_AND_LIMITATIONS.md](SOURCES_AND_LIMITATIONS.md)
