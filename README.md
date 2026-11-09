# ArogyaGuard AI — Team RITAM · Hybrid RAG V3

**LLM-driven maternal-health multi-agent assistant for ASHA workers in India**  
**New in V3:** semantic embeddings + persistent local **Qdrant**, alongside **SQLite FTS5/BM25**. Retrieval results are combined using **reciprocal-rank fusion (RRF)**; extracted PDF pages retain source and page attribution. Original OpenRouter agent-planning and governance workflows remain in place.

> **Prototype only.** Synthetic patient scenarios only. This is not clinical advice, a clinical triage system or an official Government of India service. A human health professional must verify referral and medical decisions.

## A. Install and run from VS Code (Windows)

1. **Stop the old V2 app with Ctrl+C.** Extract this ZIP and in VS Code open the `ArogyaGuard_AI_RITAM_Hybrid_RAG_V3` folder.
2. Open **Terminal → New Terminal**. Run:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-hybrid.txt
Copy-Item .env.example .env
```

3. Open `.env` and enter your existing `OPENROUTER_API_KEY`. Keep `AROGYA_VECTOR_ENABLED=true`. Set `OPENROUTER_MODEL=openai/gpt-4o-mini` unless you already selected another compatible model.
4. Start:

```powershell
.venv\Scripts\python.exe run.py
```

5. Open <http://127.0.0.1:8000>. **No Docker, Qdrant cloud key, paid embedding API, Node.js or npm needed.** Qdrant runs in *persistent embedded local mode* in `data/qdrant/`.

**First embedding setup:** The `intfloat/multilingual-e5-small` model downloads from Hugging Face on first actual embedding operation. You need internet, sufficient disk space and CPU memory. The downloaded model runs locally after the download. The model is separate from the OpenRouter LLM. If installing `sentence-transformers` fails, check your Python version and PyTorch compatibility and install a supported version; the app can still run lexical search while semantic setup is unresolved.

## B. Keep your already indexed V2 PDFs — do not start over

The V2 database contains the indexed text/passages, page numbers and SQLite FTS5 keyword index. **Qdrant will not automatically contain them until you build vectors.** Do this while **both servers are stopped**:

```powershell
# Run from the new V3 folder (replace the example with the actual OLD project path)
.venv\Scripts\python.exe -m scripts.migrate_v2 --source "C:\Projects\ArogyaGuard_AI_RITAM_Agentic_V2" --replace
```

The script makes a backup before replacing a destination database, copies old `data/official_pdfs/` when present, **never copies `.env` or your API key**, and keeps the V2 database intact. If the V3 database doesn't exist yet, omit `--replace`. If you have already indexed some V3 PDFs, back up both databases and choose which one to preserve before replacing.

Or manually, with both servers stopped: copy **V2** `data/knowledge.sqlite3` → **V3** `data/knowledge.sqlite3` and copy the `data/official_pdfs` folder. Do not copy Python source files from the old version on top of V3.

**Check what migrated:** `http://127.0.0.1:8000/api/sources`. The PDF `indexed_chunks` values should reflect your prior indexed content. Documents showing 0 (e.g., JSSK in your screenshot) still require original PDF ingestion and possibly OCR.

## C. Build the new semantic index (essential new step)

After your PDFs are indexed/migrated, go to **Evidence Library → Build semantic index**. This will convert every actual indexed PDF passage in SQLite into a vector using the local multilingual model and store it in Qdrant.

Alternatively **stop the V3 server first** (Qdrant local mode locks its directory), then run this command from the V3 project folder:

```powershell
.venv\Scripts\python.exe -m scripts.build_vectors
```

You should see `passages_embedded` > 0 and a list of document IDs. Then visit <http://127.0.0.1:8000/api/status>. The `retrieval` object should contain:

```json
{
  "mode": "hybrid",
  "ready": true,
  "vector_count": 499,
  "embedding_model": "intfloat/multilingual-e5-small"
}
```

`499` is **an illustrative example**, NOT a precomputed count. The actual number depends on your documents. If `mode` is `lexical_only`, `not_indexed`, `needs_rebuild` or `unavailable`, semantic search is not working yet and only FTS5 is active. No vector counts are fabricated. The initial package contains **no pretrained weights, Qdrant collection, downloaded government PDFs or patient information**.

### JSSK document still at zero? Enable OCR

The original JSSK PDF failed because pypdf extracted no usable text. V3 integrates a **Tesseract OCR fallback** from the prior patch. Also install:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

Then install **Tesseract OCR for Windows** separately and add it to PATH, or set this in `.env` (adjust location if needed):

```dotenv
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
AROGYA_OCR_ENABLED=true
```

Restart the server. In **Evidence Library**, click **Index official PDF** on JSSK. It first downloads and extracts verified official PDF pages and then, if Qdrant has already been initialized, attempts to generate that document's embeddings. If text/OCR succeeds but semantic indexing fails, the app returns an explicit `semantic_warning`, and the valid SQLite passages remain usable. After any successful PDF index, you can click **Build semantic index** again to ensure new chunks are embedded.

## D. What runs where?

```text
Approved NHM PDFs only
    ↓ HTTP download → pypdf text extraction → Tesseract OCR if scanned
Page-preserving chunking (~1050 characters; 180 overlap)
    ↓
    SQLite passages + FTS5 / BM25  ←→ multilingual-e5-small (local embedding model)
                                          ↓
                                    Qdrant persistent vectors
    ↓                                   ↓
    Lexical top results              Semantic top results
                       ↘        ↙
                   RRF rank fusion
                         ↓
Question → OpenRouter LLM Planner (scope + which agents + retrieval queries)
             ↓
    Maternal Guidance / Benefits / Follow-up (parallel, selected by LLM)
             ↓
    OpenRouter LLM Governance (evidence ID checks, synthesis)
             ↓
    ONE answer + cited government excerpts + optional execution trace
```

OpenRouter is used for **routing, specialist reasoning and answer synthesis**, not document embedding or PDF OCR. The embedding model creates numeric vectors locally; Qdrant stores and searches them. RRF combines ranked lists; this is **not a trained cross-encoder reranker**. For Indian languages, the model supports multilingual retrieval but performs worse in some low-resource languages; run retrieval tests for Telugu and Kannada rather than claiming proven accuracy. LLM-generated English search queries may help when source PDFs are in English, but the index also supports multilingual queries.

### Components

| Component | Implementation |
|---|---|
| Professional app | FastAPI + HTML / CSS / JavaScript |
| Chat and language interface | English / Hindi / Telugu / Kannada; browser voice subject to browser support |
| AI agent planning | OpenRouter GPT-4o-mini, JSON schema validation |
| Specialist execution | Python asyncio, optional LangGraph adapter |
| Governance | LLM synthesis with verifiable citation ID filtering, NOT clinical fact validation |
| Approved source registry | `arogyaguard/catalog.py` |
| PDF extract + OCR | `arogyaguard/knowledge.py` |
| Lexical retrieval | SQLite FTS5 / BM25 |
| Semantic embedding | `intfloat/multilingual-e5-small`, local CPU with required `query:` / `passage:` prefixes |
| Vector DB | Qdrant embedded local mode, persistent in `data/qdrant/` |
| Rank fusion | RRF over lexical / semantic candidates in `arogyaguard/hybrid.py` |
| Vector migration and CLI | `scripts/migrate_v2.py`, `scripts/build_vectors.py` |

## E. Verify technically

- **App health:** `GET /api/status` — `retrieval.mode` and real Qdrant count.
- **Government source list:** `GET /api/sources` — per-document `indexed_chunks` (PDF text) vs `vector_chunks` (semantic).
- **Rebuild semantic index:** `POST /api/vectors/build` or `python -m scripts.build_vectors`.
- **Index one approved document:** `POST /api/sources/{document_id}/sync`.
- **Ask natural questions:** `POST /api/ask` or Care Assistant. The optional **Agent activity → View execution trace** shows LLM-selected agents, evidence count, retrieval mode and Governance.
- **Tests:** `.venv\Scripts\python.exe -m pytest -q` after installing `pytest`; local tests use fake LLMs or fake semantic retrievers, and do NOT prove live model quality.

Example questions:
- "What does an ASHA worker explain during routine antenatal visits?"
- "Under JSSK, can a pregnant woman get free transportation to a government hospital?"
- "Lakshmi has blurred vision and severe headache, missed follow-up and cannot afford transport. What should I do?"
- "Who is Virat Kohli?" (should be rejected as out of scope)

## F. Safety and deployment boundaries

- This hackathon version is **not an approved medical decision support tool**. LLM answers may be incomplete, wrongly retrieved or incorrect despite valid citation IDs; validation of each claim against sources remains important.
- A conservative, independent urgent symptom warning is shown before LLM calls; it does not provide definitive diagnosis/triage.
- Real identifiable patient information must not be sent to OpenRouter without proper authorization, privacy assessment and safeguards. The example app is for **synthetic cases only**.
- Indexed NHM documents are subject to their original copyright and government licensing terms; the ZIP does not redistribute them.
- OCR may misread numbers, eligibility details and negations; assess sample pages manually and prioritize quality checks before use.
- Changes in JSSK, PMSMA or state implementation may not be reflected in locally indexed versions. This is a local snapshot, not AutoSync. AutoSync remains future scope.
- Cross-domain agent reusability is a **design goal**, not a validated ability to solve any government domain by swapping PDFs alone.
- For larger deployments, migrate embedded Qdrant to its server mode. Do not run multiple local-mode app processes against one Qdrant directory.

## G. Troubleshooting

| Observation | Action |
|---|---|
| `model_ready: false` | Check `.env` and restart; OpenRouter key isn't detected |
| `retrieval.mode: not_indexed` or `needs_rebuild` | PDFs indexed in SQLite but no vectors built; run `python -m scripts.build_vectors` |
| `retrieval.mode: unavailable` | Read `retrieval.message`; install missing dependencies or fix Qdrant local folder access |
| JSSK PDF `0 indexed` | Install Tesseract and OCR requirements; re-index official PDF |
| `No indexed PDF passages found` | Index or migrate source PDFs first; curated summaries are not embedded by default |
| Embedding model cannot load | Check internet first download / Hugging Face access and memory |
| Qdrant path locked | Stop the other ArogyaGuard processes; use one server process |
| Answer has weak citations | Inspect source PDF page and test retrieval; vector search improves recall, not truthfulness by itself |

**Docs:** [Qdrant local mode](https://github.com/qdrant/qdrant-client#local-mode) · [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small) · [NHM government portal](https://nhm.gov.in/)
