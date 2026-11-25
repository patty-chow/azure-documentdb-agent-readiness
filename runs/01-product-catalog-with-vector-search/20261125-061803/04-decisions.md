# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| model_default | 2 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:20:58+00:00

## D002 (build): I chose Python with Flask for a small single-process web app.

- **Instead of:** Node.js/Express; Python Flask; Go net/http
- **Because:** Python + Flask is concise, widely used for samples, and fits available runtimes and skills.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use a modern Python 3.x' and 'Implement as a normal single-process Flask web app'.
- **When:** 2026-11-25T14:21:16+00:00

## D003 (build): I chose the synchronous pymongo driver and will pin pymongo==4.3.3 in requirements.

- **Instead of:** motor (async) + async frameworks; pymongo (sync)
- **Because:** Synchronous pymongo is simple to use in a small Flask app and works with the available Python runtime.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the synchronous pymongo driver (pymongo>=4.0, pin to a specific minor version...)'.
- **When:** 2026-11-25T14:21:18+00:00

## D004 (build): I chose OPENAI_API_KEY as the env var to hold the embedding-provider credential.

- **Instead of:** OPENAI_API_KEY; AZURE_OPENAI_KEY; OTHER_ENV_VAR
- **Because:** text-embedding-ada-002 is an OpenAI model and the common env var name is OPENAI_API_KEY; using that keeps examples familiar to developers.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Embedding provider environment variable name and example' missing; prompt specified text-embedding-ada-002 (OpenAI model).
- **When:** 2026-11-25T14:21:20+00:00

## D005 (build): I chose to store embeddings as BSON Binary containing float32 bytes (BSON Binary), per the prompt request.

- **Instead of:** Store embeddings as numeric arrays (list of floats); Store embeddings as BSON Binary float32 bytes
- **Because:** The prompt explicitly requested BSON binary storage; we'll follow that and pack float32 bytes into bson.Binary when inserting.
- **Reason came from:** `prompt`
- **Evidence:** User prompt: 'store them as BSON binary vectors' and readiness guidance to decide and document storage format.
- **When:** 2026-11-25T14:21:21+00:00

## D006 (build): I chose to read the full connection string from DOCUMENTDB_URI and pass it directly to pymongo.MongoClient.

- **Instead of:** Parse DOCUMENTDB_URI and pass to MongoClient; Use separate user/pass env vars
- **Because:** Using the provided connection string avoids assumptions about auth scheme and aligns with run-environment guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Read the connection string from DOCUMENTDB_URI at runtime and derive authentication from that URI; do not hardcode ports or auth schemes in the sample.'
- **When:** 2026-11-25T14:21:24+00:00

## D007 (build): I chose to attempt a server-side vector index using a 'knnVector' createIndexes command (method 'ivf') and also include a client-side fallback ranking if the server-side index call fails.

- **Instead of:** Create a vector index using likely MongoDB 7 'knnVector' createIndexes syntax; Skip server-side vector index and rely on client-side ranking
- **Because:** Attempt server-side index with a plausible createIndexes body matching MongoDB 7 vector index ideas; if cluster rejects it, the seed script will still insert docs and the app will use local ranking to provide sample search functionality.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Authoritative index creation command text' is missing; but the target cluster supports IVF and the prompt requests a vector-ivf index. Also guidance: 'include a tested seed script that creates the vector index in the exact form accepted...'.
- **When:** 2026-11-25T14:21:26+00:00

## D008 (build): I chose to include a small precomputed-embeddings JSON and allow the seed script to run without OPENAI_API_KEY, while the /search endpoint requires the key to compute query embeddings.

- **Instead of:** Require OPENAI_API_KEY for seeding and searching; Provide precomputed embeddings for offline seeding and allow runtime without key
- **Because:** This lets reviewers seed the database and verify document insertion and index creation without requiring an OpenAI key; search endpoint will still show real embedding flow when key is set.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'OPENAI_API_KEY (env var) ... available: false' and 'workaround: provide a small precomputed embedding JSON file for offline testing when a key is not available.'
- **When:** 2026-11-25T14:21:28+00:00
