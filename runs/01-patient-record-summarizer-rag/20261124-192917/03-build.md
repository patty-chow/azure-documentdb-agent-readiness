# 3. Build report: 01-patient-record-summarizer-rag

**Status: partial**

Built a Python sample that ingests synthetic patient record chunks into an Azure DocumentDB collection, creates a cosmosSearch vector-HNSW index (dimensions 1536), and runs vector KNN queries pre-filtered by patientId. A FastAPI app and LlamaIndex are included as optional components, but the LlamaIndex-backed RAG engine was not executed in this run. Index creation required issuing a createIndexes runCommand via pymongo after a documentdb_create_index MCP tool call failed; the vector index was successfully created and verified.

## How to run

1) Create and activate a Python venv: python -m venv .venv && source .venv/bin/activate (Windows: .venv\Scripts\activate)
2) Install deps: pip install -r requirements.txt
3) Copy .env.example to .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if you want real embeddings).
4) Seed the sample data: python scripts/seed.py  # inserts ~60 chunk documents (10 patients x 6 chunks)
5) Create the vector index (the sample script attempts this via pymongo): python scripts/create_vector_index.py
   - This script also creates a scalar index on patientId.
6) Test a retrieval example (vector KNN prefiltered by patientId): python scripts/query.py --patient patient_001 --question "vitals summary"
7) Optional: run the FastAPI app: uvicorn src.app:app --reload --host 0.0.0.0 --port 8000 and POST to /search with JSON {"patientId":"patient_001","question":"..."}.
Notes: Do NOT put DOCUMENTDB_URI or API keys into source control. Use .env for local runs.

## Verified by running

- pip install -r requirements.txt: completed without error
- python scripts/seed.py: completed — inserted 60 documents into sample_healthcare_01.patient_chunks
- python scripts/create_vector_index.py: completed — createIndexes runCommand returned ok and scalar index on patientId created
- documentdb_list_indexes (MCP): returned 3 indexes including idx_embedding_hnsw with cosmosSearchOptions kind=vector-hnsw and dimensions=1536
- python scripts/query.py --patient patient_001 --question "vitals summary": completed — retrieved 5 hits with searchScore metadata

## Not verified

- Full LlamaIndex RAG agent end-to-end (Vector ingestion via LlamaIndex + VectorStoreIndex and query engine) — not executed. Reason: sample includes LlamaIndex in requirements and notes; the LlamaIndex-based flow is included in docs but was not run in this verification to keep testing focused on raw ingestion/index/query with pymongo and OpenAI fallback embedding. (model_default decision to include LlamaIndex but not execute.)
- documentdb_create_index MCP tool call: initial attempt to call functions.documentdb_create_index failed with a generic 'Function failed.' error; fallback to pymongo runCommand(createIndexes) was used instead. The MCP tool failure prevented verifying the MCP tool-based index creation path.
- Running the FastAPI server (uvicorn) and exercising /search endpoint was not executed (no long-running server started during verification).

## Open issues

- documentdb_create_index MCP tool returned an error when invoked; I fell back to issuing the createIndexes runCommand via pymongo which succeeded (see scripts/create_vector_index.py). Evidence: the documentdb_create_index call returned 'Error: Function failed.' during the run (logged via tool).
- LlamaIndex RAG flow is included in the repo (requirements and README) but was not executed or validated. If you want a demonstration that uses LlamaIndex's Azure DocumentDB vector store wrappers, run an interactive notebook or add a short script that calls LlamaIndex vector-store ingestion and query APIs against the created collection (ensure OPENAI_API_KEY is set).
- The sample uses OpenAI text-embedding-3-small (1536 dims) by default. If you change the embedding model or dims, you must recreate the vector index with matching dimensions. Recommendation: keep EMBEDDING_DIMS in .env consistent with the model you use.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `LICENSE`
- `src/db.py`
- `src/app.py`
- `scripts/seed.py`
- `scripts/query.py`
- `scripts/create_vector_index.py`

