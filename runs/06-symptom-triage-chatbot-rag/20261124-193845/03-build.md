# 3. Build report: 06-symptom-triage-chatbot-rag

**Status: completed**

I built a small Python LangChain RAG sample that indexes synthetic clinical triage guideline sections into an Azure DocumentDB vector index and exposes a FastAPI /triage endpoint. The repo includes an idempotent seed script that creates a server-side DiskANN vector index (cosmosSearch, dimensions=1536) and upserts 20 synthetic guideline sections with normalized embeddings. The sample supports real OpenAI embeddings + LangChain LLMs when OPENAI_API_KEY is provided, and falls back to deterministic local embedding + deterministic LLM-like generation when API keys are absent so the sample is runnable and testable offline. I verified index creation and documents were inserted against the live cluster and ran automated tests (pytest) that exercise the triage endpoint using the fallback path.

## How to run

1. Copy .env.example to .env and set DOCUMENTDB_URI (mongodb+srv URI to the existing Azure DocumentDB cluster). Optionally set OPENAI_API_KEY to enable real embeddings and LLM outputs.
2. (Optional) Create and activate a virtualenv.
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate   # Windows
3. Install dependencies:
   pip install -r requirements.txt
4. Seed the data and create the vector index:
   python seed.py
5. Run the API server:
   uvicorn app:app --reload
6. POST to /triage with JSON {"symptoms": "<free-text symptom description>"} and receive a structured JSON response with urgency, advice and sources.
7. Run tests (integration-style):
   pytest -q
Notes:
- Never commit real secrets. Use .env for local testing; the repo includes .env.example.
- If OPENAI_API_KEY is not set, the sample uses deterministic local fallbacks so the seed, retrieval and API behaviors are testable without external calls.

## Verified by running

- pip install -r requirements.txt: succeeded
- python seed.py: succeeded, created/ensured vector index and upserted 20 documents into sample_healthcare_06.guidelines
- pytest -q: 1 passed (tests/test_app.py:test_triage_endpoint_basic) - this exercised the seed, vector retrieval via $search/cosmosSearch (fallback embeddings) and the /triage API endpoint in-process
- documentdb_list_indexes(sample_healthcare_06.guidelines): returned two indexes including 'guidelines_embedding_diskann' with cosmosSearchOptions: {kind: 'vector-diskann', dimensions: 1536, similarity: 'COS', maxDegree: 32, lBuild: 50}
- documentdb_sample_documents(sample_healthcare_06.guidelines, sample_size=5): returned sample documents with embedding, embeddingModel and embeddingDims fields

## Not verified

- Real OpenAI embedding calls (text-embedding-3-small) — not executed because OPENAI_API_KEY was not set in this run; the code path supports it but was tested with deterministic fallback embeddings.
- Real OpenAI / LangChain LLM responses (gpt-3.5-turbo via LangChain) — not executed because OPENAI_API_KEY was not set; the repo will call ChatOpenAI when OPENAI_API_KEY is present. I provided a deterministic fallback generator used during tests.
- Production tuning of DiskANN parameters on large corpora (maxDegree/lBuild/lSearch tradeoffs) — sample used moderate defaults suitable for demo sizes; tuning was not exercised on large datasets.
- End-to-end behavior with a paid OpenAI account (rate limits, cost, latency) — not verified here.

## Open issues

- If you want full production-quality LLM and embedding behavior, set OPENAI_API_KEY in your environment and re-run seed.py and the server. The sample will then generate real embeddings and use LangChain/OpenAI for the LLM step.
- The sample uses a synthetic dataset to avoid licensing/PHI concerns. Integrating real published clinical guidelines would require licensing and clinical oversight; do not use this sample for clinical decision-making.
- This repo includes a fallback deterministic embedding and LLM generator strictly for demo/test workflows; replace these with real models for production and ensure clinical review and safety testing.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `db.py`
- `sample_data.py`
- `utils.py`
- `seed.py`
- `app.py`
- `tests/test_app.py`

