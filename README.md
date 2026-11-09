# ArogyaGuard AI

**Connecting frontline maternal care with trusted government guidance**  
**Team RITAM | AI for Good Lab Hackathon, UAE 2026 | Country focus: India**

ArogyaGuard AI is a multilingual, multi-agent research prototype designed to help India's frontline healthcare workers find and interpret maternal-health information from official government sources. It combines document retrieval, LLM-driven agent orchestration, evidence references, and a human-led approach to referral and follow-up.

> [!IMPORTANT]
> **Research and demonstration prototype only.** ArogyaGuard AI is **not** a clinically validated medical device, diagnostic system, emergency service, or official government service. It must not replace professional medical assessment. Use **synthetic scenarios only**; do not enter identifiable patient information.

## The problem

Accredited Social Health Activists (**ASHAs**) and Auxiliary Nurse Midwives (**ANMs**) support families in accessing maternal healthcare. Relevant guidance is spread across government documents and programmes covering antenatal care, pregnancy danger signs, transport entitlements, high-risk follow-up, and respectful maternity care. Finding the right information quickly, including in a familiar language, can be difficult.

**ArogyaGuard AI aims to connect those sources in one understandable, source-aware response.** Its purpose is to support informed human action, not to automate clinical decisions or claim that a person is eligible for benefits without evidence.

## What the prototype provides

- **Natural-language questions** through a web interface, with text and browser-dependent voice features.
- **Four languages:** English, Hindi, Telugu, and Kannada.
- **LLM-first routing:** an orchestrator chooses relevant agents from the user's question instead of asking the user to select an agent manually.
- **Multi-agent synthesis:** guidance, benefits, and follow-up findings can be combined into one response, with a governance review stage.
- **Government-document retrieval:** local SQLite FTS5/BM25 search and optional semantic search with multilingual embeddings and Qdrant.
- **Evidence visibility:** document references, page attribution where PDF pages have been indexed, and agent activity or execution traces where available.
- **Safety-oriented behavior:** urgent maternal danger signs should prompt timely professional medical assessment rather than an AI-generated diagnosis.

Feature availability and quality depend on the local setup, indexed documents, language, browser, and model response. These capabilities are **not claims of clinical accuracy or deployment readiness**.

## Multi-agent architecture

| Agent | Responsibility |
| --- | --- |
| **Maternal Guidance & Referral** | Locate information about antenatal care, pregnancy warning signs, and appropriate human referral. |
| **Benefits** | Retrieve available government guidance on programmes such as JSSK, including transport support and eligibility caveats. |
| **Follow-up** | Address missed antenatal visits, high-risk pregnancy monitoring, and continuity-of-care responsibilities. |
| **Governance** | Bring findings together, check available evidence references and scope, and communicate uncertainty and safeguards. |

An **LLM-based orchestrator** determines which specialist agents are relevant. Not every question needs every specialist. The governance stage helps produce one consolidated response. A separate conservative warning mechanism may surface urgent danger-sign guidance, but agent selection is intended to be dynamic rather than based only on keyword matching.

```text
Question (text / voice)
        |
        v
   Safety awareness
        |
        v
 LLM scope + agent planning
        |
        +----> Maternal Guidance & Referral --+
        +----> Benefits -----------------------+--> Governance --> One response
        +----> Follow-up ----------------------+       |           + evidence
                                                   Retrieved      + agent trace
Official NHM documents --> SQLite FTS5/BM25 -------+ sources
                          + optional local embeddings
                            and Qdrant vector search
```

**Known routing limitation:** A specialist may respond correctly to an independent question but still be missed in a compound question. For example, a combined urgent referral, transport, and missed-appointment scenario has not consistently invoked the Follow-up Agent. This is an identified orchestration-evaluation gap, not a verified all-agent demonstration.

## Technology

| Layer | Implementation |
| --- | --- |
| Web application | Python, FastAPI, HTML, CSS, JavaScript |
| AI orchestration and reasoning | OpenRouter with `openai/gpt-4o-mini` (configurable) |
| Document parsing | `pypdf`; optional Tesseract OCR for scanned PDFs |
| Lexical retrieval | SQLite FTS5 / BM25 |
| Semantic retrieval | `intfloat/multilingual-e5-small` embeddings |
| Vector storage | Qdrant in local persistent mode |
| Hybrid ranking | Reciprocal Rank Fusion (RRF) of lexical and semantic results |
| Voice | Browser speech recognition and speech synthesis, subject to browser support |

The application runs on a local computer, but **OpenRouter inference requires internet access**. Initial software installation, document download, and first embedding-model download may also need internet. It is **not a fully offline or edge-deployed system**.

## Run locally

These instructions describe the **Hybrid RAG V3 codebase**, including the V3.1 scope-handling patch when applied. If your repository contains a different application version, align the commands and feature descriptions with that version before publishing.

### Prerequisites

- Python **3.10+** and `pip`.
- An OpenRouter API key for LLM-based agent routing and response generation.
- Internet access for dependencies, the model API, and downloading official documents.
- Optional: Tesseract OCR for scanned government PDFs.
- A supported browser; Chrome or Edge is recommended for testing voice features.

### Windows (PowerShell)

Open a terminal in the folder containing `run.py`:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-hybrid.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your **own** key:

```dotenv
OPENROUTER_API_KEY=YOUR_OWN_OPENROUTER_KEY
OPENROUTER_MODEL=openai/gpt-4o-mini
AROGYA_VECTOR_ENABLED=true
```

Start the application:

```powershell
.venv\Scripts\python.exe run.py
```

Then open **http://127.0.0.1:8000**.

You may also use `start_windows.bat` after configuring the environment. The supplied launcher simplifies startup, but you may still need to install the separate hybrid dependencies shown above.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-hybrid.txt
cp .env.example .env
# Edit .env and provide your own OPENROUTER_API_KEY.
.venv/bin/python run.py
```

Open **http://127.0.0.1:8000**. Do not commit `.env` or paste a real API key into the README, source code, screenshots, or logs.

### Set up the document knowledge base

1. Open the application's **Evidence Library**.
2. Download and index the available, approved official NHM documents. Indexing is required for page-based PDF evidence.
3. For scanned PDFs with no extractable text, install the dependencies from `requirements-ocr.txt` and the Tesseract executable, then re-index. OCR output requires verification.
4. Use **Build semantic index** to generate local embeddings and populate Qdrant. Semantic search is **not ready merely because PDF text has been indexed**.
5. Check **http://127.0.0.1:8000/api/status** for the actual model and retrieval status.

To build vectors with the app stopped:

```powershell
.venv\Scripts\python.exe -m scripts.build_vectors
```

If semantic retrieval is unavailable or not indexed, the application may operate with lexical search only. Do not claim that hybrid retrieval is active without confirming the status. The project should not commit downloaded PDFs, local SQLite data, Qdrant storage, or embedding-model caches.

### Run tests

```powershell
.venv\Scripts\python.exe -m pip install pytest
.venv\Scripts\python.exe -m pytest -q
```

Automated tests, including simulated LLM behavior, **do not prove** live-model reliability, clinical safety, or equal performance in different languages.

## Demonstration questions

Use synthetic examples and inspect the actual response and agent trace. The agent combinations below describe **intended behavior**, not guaranteed test outcomes.

| Scenario | Example question | Intended behavior |
| --- | --- | --- |
| Routine antenatal care | "What should an ASHA worker explain during a routine antenatal visit?" | Maternal Guidance and Governance |
| Urgent warning signs | "A woman who is eight months pregnant has a severe headache and blurred vision. What should I do?" | Prompt urgent human medical assessment; do not diagnose |
| Government support | "What transport support does JSSK provide for eligible pregnant women?" | Benefits and Governance, with source-based caveats |
| Missed follow-up | "A high-risk pregnant woman missed her antenatal follow-up. How should the ASHA worker coordinate continued care?" | Follow-up and Governance |
| Combined scenario | "Lakshmi is eight months pregnant, has a severe headache and blurred vision, missed a high-risk follow-up, and cannot afford transport. What urgent referral, verified transport information, and follow-up steps should the ASHA worker consider?" | Ideally Maternal Guidance, Benefits, Follow-up, and Governance; **check the real trace** |
| Out-of-scope control | "Who is Virat Kohli?" | A respectful out-of-scope response |

Severe headache with blurred vision during pregnancy is a potential warning sign. **Urgent assessment takes precedence over benefit lookups or routine follow-up planning.**

## Policy and standards gap analysis

The hackathon explores not only whether an AI prototype works, but also what is required for responsible public-sector deployment.

**Observed prototype challenges:**

- **Incorrect scope classification:** some legitimate SUMAN respectful-care and Extended PMSMA questions were initially rejected as out of scope; a V3.1 patch introduced a second LLM review of proposed rejections.
- **Incomplete policy evidence:** scanned or difficult-to-extract documents, including JSSK material, can leave the knowledge base incomplete.
- **Unverifiable entitlement details:** the application must not invent a payment amount, approval authority, or state-specific benefit when the indexed source does not establish it.
- **Agent-routing inconsistency:** compound questions can omit a relevant specialist even when it works independently.
- **Language consistency:** English has appeared more consistent in informal testing; four-language parity has not been established.

**Candidate policy and standards needs identified by the project:** machine-readable policy updates and state applicability; clear document provenance and versioning; standardized maternal-health topics; safe escalation and human oversight; transparent uncertainty; and structured multilingual evaluation. These are research findings and recommendations, **not a claim that every prototype bug represents a formal standards violation**.

The accompanying hackathon submission discusses these gaps through the ITU-T Y.3172 / AI Readiness 2.0 framing.

## Government information sources

The document catalogue is based on official **National Health Mission (NHM)** resources, including materials related to:

- ASHA maternal-health guidance.
- **JSSK:** Janani Shishu Suraksha Karyakram.
- **PMSMA:** Pradhan Mantri Surakshit Matritva Abhiyan and related high-risk pregnancy guidance.
- **SUMAN:** Surakshit Matritva Aashwasan, including respectful maternity care.

Start at the [National Health Mission website](https://nhm.gov.in/). The application must verify the actual official source, document version, relevant state, and effective conditions before relying on a specific entitlement. Linked government material is **not** automatically licensed for redistribution under this repository's code license.

## Limitations and safeguards

- Research prototype only; **no diagnosis, prescriptions, ambulance dispatch, or autonomous case decisions**.
- Human healthcare professionals and authorized services remain responsible for assessment, referral, eligibility decisions, and patient follow-up.
- A citation reference does not guarantee that a model's interpretation is correct. Check the actual source and its applicability.
- Policies and state-level programme implementation can change. This prototype does not automatically keep its entire knowledge base current.
- Voice recognition and speech output depend on browser, operating system, and language availability.
- Do not enter, upload, or transmit identifiable patient information. When OpenRouter is enabled, questions can be sent to an external model provider.
- Do not commit `.env`, credentials, downloaded patient records, private logs, local databases, or generated vector storage.

## Future directions

- **Knowledge Update Agent (proposed):** monitor official government sources, detect relevant policy changes, and support **human-verified** knowledge-base updates. **Not implemented as a fifth agent in the current prototype.**
- More systematic multi-agent routing tests, including compound questions.
- Better OCR/document completeness checks and source-version tracking.
- Comparative evaluation of response quality and safety in all four supported languages.
- Reuse of the core orchestration and retrieval framework for **education, agriculture, or other public-service domains**, with new documents, agent responsibilities, safeguards, and evaluations.

## Demo video

**YouTube demonstration:** Link will be added after the final demo is published.

## Team

**RITAM**  
**Rohith D** — Team Lead  
**Sanjana Daivanga** — Team Member

Developed for the **AI for Good Lab Hackathon, UAE 2026**.

## License

The source code is intended to be published under the **MIT License**. See [`LICENSE`](LICENSE) once it has been added to the repository. Third-party dependencies, model weights, and government publications retain their own terms.
