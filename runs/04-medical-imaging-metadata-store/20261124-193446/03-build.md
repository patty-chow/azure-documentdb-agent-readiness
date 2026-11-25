# 3. Build report: 04-medical-imaging-metadata-store

**Status: completed**

Built a small Python FastAPI sample that stores medical imaging metadata and embeddings in an Azure DocumentDB collection, created a vector-ivf index, seeded 50 documents, and demonstrated semantic search against the live cluster. The sample stores embeddings as number[] (required for native DocumentDB vector indexes) and normalizes embeddings for cosine similarity. Where the environment lacked an OPENAI_API_KEY, the seed and query scripts used deterministic pseudo-embeddings so the demo can run without secrets. Index creation via the MCP tool initially failed, so the sample uses the MongoDB driver (pymongo) to create the vector index; the created index was confirmed with the documentdb MCP server's list-indexes call. Verification steps (install, seed, create index, and run a search) were executed and passed as listed below.

## How to run

1) Create and activate a venv (recommended): python -m venv .venv && source .venv/bin/activate
2) Install deps: pip install -r requirements.txt
3) Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY if you want real embeddings). Keep DB_NAME and COLLECTION_NAME defaults or set them.
4) Seed documents: python seed.py  # inserts ~50 records (uses real OpenAI embeddings if OPENAI_API_KEY is set; otherwise deterministic pseudo-embeddings)
5) Create the vector index (if you want to run it yourself): python create_index.py  # creates cosmosSearch vector-ivf index via pymongo
   - Note: create_index.py was used in verification because the MCP create-index call failed; both approaches are included in logs.
6) Run a demo search (no long-running server required): python run_search.py "pulmonary nodule"
7) To run the FastAPI server: uvicorn app.main:app --reload and then curl "http://127.0.0.1:8000/search?q=pulmonary%20nodule&k=5"

Notes: Do NOT check real secrets into source control. Use .env (local) or environment variables in CI. The sample stores embeddings as number[] so they can be indexed by DocumentDB native vector indexes. See README.md for more information.

## Verified by running

- pip install -r requirements.txt: success
- seed.py: inserted 50 documents into sample_healthcare_04.medical_images (ran locally, deterministic pseudo-embeddings used because OPENAI_API_KEY was not set)
- create_index.py (pymongo.create_index): created index 'medical_images_embedding_ivf' with cosmosSearchOptions {kind: 'vector-ivf', dimensions: 1536, similarity: 'COS', numLists: 100, lBuild: 50}
- documentdb_list_indexes (MCP): confirmed the vector index exists on sample_healthcare_04.medical_images
- run_search.py: executed an example semantic search for 'pulmonary nodule' returning ranked documents (printed id, modality, body_part, findings, score)

## Not verified

- documentdb_create_index via MCP server: attempt returned 'Error: Function failed.' so index creation via MCP tool could not be completed; create_index.py (pymongo) was used as a verified alternative. The MCP create_index failure could be a transient tool/server issue or a permissions limitation.
- OpenAI embeddings via real API: not executed because OPENAI_API_KEY was not present in the environment. The code paths for calling OpenAI are included and will run if OPENAI_API_KEY is provided. (Reason: missing credential).
- Running the FastAPI server under uvicorn and exercising the HTTP /search endpoint with external clients was not run here (the run harness avoids starting long-running servers). The internal aggregation and search were validated via run_search.py instead.

## Open issues

- Original prompt requested embedding storage as BSON Binary. Readiness report and DocumentDB vector-index docs require embeddings to be stored as number[] for native vector indexes. I changed the sample to store embeddings as number[] (decision logged). If you must store embeddings as BSON Binary for other reasons, native DocumentDB vector indexes cannot be used and an application-layer kNN fallback will be needed.
- documentdb_create_index (MCP) call failed with an opaque error; I used pymongo.create_index as a reliable workaround and confirmed index creation. If you need MCP-based create-index automation, inspect the MCP server logs or permissions and retry from the MCP server side.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `app/db.py`
- `app/main.py`
- `seed.py`
- `create_index.py`
- `compute_vector.py`
- `run_search.py`

