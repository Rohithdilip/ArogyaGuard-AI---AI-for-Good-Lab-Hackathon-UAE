# ArogyaGuard AI — V3.1 scope + partial-answer fix
**Team RITAM | Target: existing V3 Hybrid RAG project**

## Why this patch exists
Three valid maternal-health questions were incorrectly classified as outside scope: SUMAN respectful maternity care, Extended PMSMA incentives in Telangana, and a JSSK amount/approval question. The original planner prompt was too narrow and a single LLM rejection immediately bypassed all retrieval and specialist agents.

## Changes
- `arogyaguard/prompts.py`: expanded in-scope taxonomy with positive/negative examples; prompts distinguish missing documentary evidence from out-of-scope questions, and partial information from unsupported exact payments.
- `arogyaguard/engine.py`: **independent LLM scope review** on proposed out-of-scope results, with observable `scope_review` trace entries, while retaining the clinical urgency safety notice.
- `arogyaguard/models.py`: adds two optional trace fields with defaults for backward compatibility (`scope_reviewed`, `initial_scope`).
- `arogyaguard/__init__.py`: reports version `3.1.0` in `/api/status`.

**No change** to SQLite FTS5, Qdrant collections, PDF storage, document hashes, `.env`, OpenRouter credentials, or the UI; no reindex is required for this patch.

## Apply to current VS Code V3 folder (Windows)
1. Stop the running app in VS Code using `Ctrl+C`.
2. **Back up your entire V3 project folder first**, particularly `.env` and `data/`.
3. Open the ZIP and copy its `arogyaguard/engine.py`, `arogyaguard/prompts.py`, `arogyaguard/models.py`, and `arogyaguard/__init__.py` **over the same four files** in the existing V3 project. Do not replace or delete anything under `data/` or `.env`.
4. Restart: `.venv\Scripts\python.exe run.py`
5. In browser refresh `http://127.0.0.1:8000` using `Ctrl+F5` if needed.
6. Check `/api/status` displays `version: 3.1.0`, then run the three questions below and inspect **Agent activity → View execution trace**. After a questionable initial rejection that gets corrected, the trace includes `scope_review` with `initial_scope=out_of_scope` and `review_result=in_scope`.

### Questions and correct behavior
| Input | Must not happen | Expected route and answer behavior |
| --- | --- | --- |
| What does SUMAN say about respectful maternity care? | Out-of-scope rejection | Guidance + Governance. Ground response in SUMAN evidence; if only summary exists disclose that. |
| Are Extended PMSMA incentives applicable in Telangana? | Out-of-scope rejection or unverified entitlement promise | Follow-up (+ Benefits as needed) + Governance. Distinguish historical first-phase state coverage from unverified current local rollout. |
| What is the exact JSSK payment amount and approval process? | Out-of-scope rejection or made-up amount | Benefits + Governance. Explain verified free/cashless services and that any exact amount/approver absent from sources cannot be confirmed. |
| Who is Virat Kohli? | General-knowledge biography | No specialists; remain out of scope after secondary check. |

## Test
Copy the two `tests/` files from the patch over the corresponding test locations (one replaces the older mock). In the V3 folder, with pytest available, run: `.venv\Scripts\python.exe -m pytest -q`.
The development copy passed **26 offline tests**, including four new simulated scope-regression tests. These tests use fake LLM responses and **do not verify the behavior of your live OpenRouter model**. Record actual responses and execution traces for quality evaluation.

## Important constraints
- This patch does **not** index the JSSK PDF or repair an OCR failure. Install OCR, index the official JSSK document, then rebuild vectors if needed.
- A correct scope decision does **not** guarantee correct policy evidence. Inspect retrieved PDFs and citation relevance. Additional programme documents may be needed for specific incentive figures or approvals.
- Independent review introduces one extra LLM request only when the initial planner wants to refuse a question. If OpenRouter times out, the application should show a service error rather than disguising it as out-of-scope.
- This remains a synthetic-case research prototype, not a clinically validated service. No real patient identifiers should be sent to external LLMs.
