# Hybrid RAG architecture, safety and verification

This addendum replaces V2's statement that retrieval uses only FTS5. All other V2 descriptions of LLM-first dynamic agent routing and Governance generally remain valid.

## Indexing vs reasoning

- **Indexing**: Official NHM PDF → extract `pypdf` and optional OCR → chunk text with page numbers → SQLite FTS5 index → E5 sentence embeddings → Qdrant. **No OpenRouter LLM calls are made for document ingestion or embedding.**
- **At question time**: OpenRouter plans relevant agents and search queries. Each specialist retrieves from SQLite FTS5 and Qdrant. Ranked candidates are fused via reciprocal-rank fusion (`k=60`). Then OpenRouter synthesizes specialist findings; Governance returns a single answer.
- **Failure transparency**: If Qdrant or embeddings cannot load, requests use *only* SQLite FTS5. `GET /api/status` exposes this; `GET /api/sources` exposes counts. The system must not claim hybrid retrieval with an empty vector index.
- **Source integrity**: Only passages of `kind='indexed-pdf'` are embedded by default. Curated notes remain explicitly labelled if lexical retrieval uses them. Document IDs, PDF pages and citation IDs derive from stored SQLite rows; model-generated IDs are filtered.
- **Quality controls missing from this prototype**: Expert review of extracted OCR, automated claim-level factual entailment checks, state applicability verification against live government rollout, clinical expert validation, independent multilingual retrieval benchmarks.

## Migration

V2 `data/knowledge.sqlite3` can be migrated as-is. Ingested text remains in that SQLite file, but Qdrant is a **new independent store** and requires a one-time embedding build. The `scripts/build_vectors.py` command loads all existing `indexed-pdf` passages. The user's OpenRouter key and patient data are never migrated automatically.

## Operational notes

Use one process with Qdrant local mode. Separate V3 folder from V2. Avoid copying any old `arogyaguard/` Python files over the V3 implementation. Stop the server before migrating SQLite. The first E5 model load downloads model weights once and may consume significant disk space and CPU time. `AROGYA_EMBEDDING_MODEL` changes require new compatible vector collections; do not claim they can be swapped into an existing collection without reindexing. Additional state and eligibility validation are necessary before production use.
