# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| readiness_report | 2 |
| operator | 1 |
| skill | 1 |
| model_default | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:18:02+00:00

## D002 (build): I chose Python 3.x with FastAPI for the HTTP API and a small CLI seed script.

- **Instead of:** Node.js/Express; Python/FastAPI; Go/Fiber
- **Because:** Python has rich ecosystem for LangChain, pymongo and quick HTTP prototyping; matches prompt expectations for a Python LangChain RAG chatbot.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will target a modern Python 3.x runtime (e.g., 3.10 or 3.11). Use virtualenv and 'python' / 'pip' from the run environment.'
- **When:** 2026-11-25T08:18:44+00:00

## D003 (build): I chose pymongo >=4.x (synchronous MongoClient) and will implement a singleton MongoClient.

- **Instead of:** pymongo 3.x; pymongo >=4.x; motor (async)
- **Because:** pymongo is the standard driver and the documentdb-driver skill recommends a singleton MongoClient; synchronous code is simpler with FastAPI for this sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use the Python MongoDB driver (PyMongo) and a current stable release compatible with chosen Python (e.g., pymongo >=4.x). Follow the documentdb-driver guidance to create a single process-wide MongoClient.'
- **When:** 2026-11-25T08:18:49+00:00

## D004 (build): I chose OpenAI text-embedding-3-small (1536 dims) as the primary embedding model, with a deterministic local fallback when OPENAI_API_KEY is not set.

- **Instead of:** OpenAI text-embedding-3-small (1536); OpenAI text-embedding-3-large (3072); HuggingFace local embedder
- **Because:** text-embedding-3-small is a common choice with 1536 dims and matches vector-search examples; fallback ensures the sample can run without API keys for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Builder must pick an embedding model and dimensions' and vector-create-diskann-index.md examples using 1536 dimensions.
- **When:** 2026-11-25T08:18:52+00:00

## D005 (build): I chose OpenAI gpt-3.5-turbo via LangChain with an in-process deterministic fallback when OPENAI_API_KEY is not set.

- **Instead of:** OpenAI gpt-3.5-turbo via LangChain; OpenAI gpt-4 via LangChain; local LLM/none
- **Because:** gpt-3.5-turbo is widely available, cost-effective and integrates with LangChain; fallback enables offline testing without calling external APIs.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption from prompt review: "Builder will pick a commonly available embedding provider and LLM (for example OpenAI embeddings such as text-embedding-3-small and an OpenAI chat model via LangChain)."
- **When:** 2026-11-25T08:19:09+00:00

## D006 (build): I chose to create a server-side vector index (vector-diskann) on the 'guidelines' collection using cosmosSearchOptions (dimensions=1536, similarity=COS, maxDegree=32, lBuild=50).

- **Instead of:** create server-side vector index; store vectors and do client-side ANN
- **Because:** Server-side vector index yields faster and more accurate ANN queries and demonstrates DocumentDB vector-search features required by the sample.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill and vector-create-diskann-index.md examples showing createIndex with cosmosSearchOptions kind 'vector-diskann' and dimensions matching embedding model.
- **When:** 2026-11-25T08:19:18+00:00

## D007 (build): I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime and use it directly (do not store any secrets in files).

- **Instead of:** Use SCRAM auth from connection string; Use MONGODB-OIDC via Entra ID; Use connection string from env (DOCUMENTDB_URI)
- **Because:** Respect security constraints and the run environment; using DOCUMENTDB_URI ensures connectivity without embedding secrets in repo.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file'.
- **When:** 2026-11-25T08:19:21+00:00

## D008 (build): I chose to include a small synthetic, hand-crafted corpus of guideline sections (20 items) created for the sample and provided via an idempotent seed script.

- **Instead of:** Synthetic hand-crafted sample data; Use public clinical guideline corpora automatically; Small subset of licensed guidelines
- **Because:** Using synthetic content avoids licensing and PHI issues, keeps sample self-contained and safe for demonstration/testing.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: include a small synthetic/hand-curated corpus for the sample.
- **When:** 2026-11-25T08:19:28+00:00
