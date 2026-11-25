# 5a. Best practices: prior knowledge against the public record: 11-visual-similarity-search-image-embeddings

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**19 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 6 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 4 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 5 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## Where public sources contradict the model

### P10: This sample's get_client() implementation reads DOCUMENTDB_URI and returns a new pymongo.MongoClient() on each call; the app creates a client inside request handlers rather than a single global client.

- **The model believed:** Create a single MongoClient (pymongo.MongoClient) at application startup and reuse it for all requests; close it on shutdown (do not create a new client per request). (knowledge of `mongodb`)
- **The source says:** This sample's get_client() implementation reads DOCUMENTDB_URI and returns a new pymongo.MongoClient() on each call; the app creates a client inside request handlers rather than a single global client.
- **Source:** app/db.py / app/main.py

### P12: The sample attempts create_index without first listing existing indexes (no idempotent listIndexes check); it relies on catching create_index exceptions instead of explicitly checking or adapting index creation parameters.

- **The model believed:** When creating a vector index do it idempotently: check existing indexes with list_indexes/listIndexes and only call create_index/createIndexes if the desired index is absent; catch and handle server rejections (bad option names) instead of failing startup. (knowledge of `mongodb`)
- **The source says:** The sample attempts create_index without first listing existing indexes (no idempotent listIndexes check); it relies on catching create_index exceptions instead of explicitly checking or adapting index creation parameters.
- **Source:** app/db.py

### P14: The sample does not query server buildInfo/hello to detect supported wire protocol or vector index algorithms; instead it attempts index creation with plausible options and logs failures rather than adaptively changing parameters based on server feature detection.

- **The model believed:** Detect and respect the server's supported wire protocol/features (MongoDB version, vector index types such as IVF/HNSW/DiskANN) at runtime—query server buildInfo or isMaster/hello—and adapt index creation parameters to that server's accepted syntax rather than assuming a single API format. (knowledge of `mongodb`)
- **The source says:** The sample does not query server buildInfo/hello to detect supported wire protocol or vector index algorithms; instead it attempts index creation with plausible options and logs failures rather than adaptively changing parameters based on server feature detection.
- **Source:** app/db.py / README.md

### P15: The /visual-search endpoint validates uploads by attempting to open with PIL and returning 400 on failure, but it does not explicitly validate content-type headers, does not enforce an upload size limit, and does not set explicit request timeouts in the sample.

- **The model believed:** Protect the /visual-search upload endpoint: validate content-type, limit upload size, enforce timeouts, and reject non-image files to avoid DoS and avoid decoding extremely large images in-memory; return clear 4xx errors for invalid input. (knowledge of `general`)
- **The source says:** The /visual-search endpoint validates uploads by attempting to open with PIL and returning 400 on failure, but it does not explicitly validate content-type headers, does not enforce an upload size limit, and does not set explicit request timeouts in the sample.
- **Source:** app/main.py

### P18: The sample does not call listIndexes/listIndexes to verify that a vector-ivf index exists and with expected parameters after creation; it only requests create_index and logs failures, so it does not explicitly verify index presence.

- **The model believed:** Use listIndexes/listIndexes on the collection to verify that the vector-ivf (or chosen algorithm) index actually exists and has the expected parameters after creation; if createIndex fails, capture the error and fall back or surface a clear admin message. (knowledge of `mongodb`)
- **The source says:** The sample does not call listIndexes/listIndexes to verify that a vector-ivf index exists and with expected parameters after creation; it only requests create_index and logs failures, so it does not explicitly verify index presence.
- **Source:** app/db.py / seed.py

### P19: For demonstration simplicity the sample falls back to fetching all embeddings and computing cosine similarity locally when server-side vector search is unavailable, rather than delegating to a dedicated ANN service.

- **The model believed:** Avoid transferring all embeddings to the client for search in production; if the server lacks vector search, provision a small dedicated ANN service (FAISS/Annoy/HNSWlib) or do batched approximate operations rather than naive full-table brute-force queries. (knowledge of `general`)
- **The source says:** For demonstration simplicity the sample falls back to fetching all embeddings and computing cosine similarity locally when server-side vector search is unavailable, rather than delegating to a dedicated ANN service.
- **Source:** app/main.py / seed.py

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P11 | I found no guidance in the repository or reachable documentation that stores per-document metadata fields for embedding dimensionality or dtype (e.g., embedding_dim=512 or embedding_dtype='float32'); the sample omits such metadata fields. | general | azure documentdb embedding metadata best practices; documentdb embedding dimensions dtype |
| P13 | I found no repository guidance or sample code that implements exponential-backoff retries with jitter or config-driven retry policies for DocumentDB operations; the sample does not wrap DB calls with custom retry/backoff logic. | mongodb | azure documentdb retry best practices; pymongo retryWrites retryReads azure documentdb |
| P16 | I found no guidance in the repository about scheduling index builds during maintenance windows or using server-specified background/online index build options; the sample performs a best-effort create_index during seeding without such scheduling guidance. | amazon_documentdb | azure documentdb index build best practices; vector index build maintenance windows |
| P17 | I found no instrumentation or Azure Monitor integration for vector-search-specific metrics in the sample (no index-size, ANN memory/IO or query-latency metrics are emitted by the demo code). | azure_cosmos_db | azure monitor documentdb vector metrics; documentdb monitoring vector index |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string from an environment variable (DOCUMENTDB_URI) and do not commit live credentials or connection strings into the repository or logs. | authentication and secrets | prior_knowledge_confirmed | README.md / .env.example (local_file) | **none** | README.md | yes |
| P02 | When creating a vector index, attempt a plausible create_index call and catch and log server errors rather than failing startup, so the app can continue (best-effort index creation). | indexing | found_in_public_source | app/db.py (local_file) | **none** | app/db.py | yes |
| P03 | Store 512-d embeddings as little-endian float32 packed into a BSON Binary with subtype 0x09 (use struct or equivalent and pymongo.binary.Binary), and unpack with a matching little-endian float32 reader. | data modeling | prior_knowledge_confirmed | app/db.py (local_file) | **none** | app/db.py | yes |
| P04 | L2-normalize image embeddings (unit length) in the encoder before storing and assume normalized vectors when computing cosine similarity on query time. | vector search | prior_knowledge_confirmed | app/encoder.py (local_file) | **none** | app/encoder.py | yes |
| P05 | Seed demo data into a dedicated database and collection (sample_retail_11.products) and use upsert operations when inserting sample/demo documents so repeated runs are safe. | provisioning | prior_knowledge_confirmed | seed.py / app/db.py (local_file) | **none** | seed.py | yes |
| P06 | Prefer server-side vector search when available: attempt a server-side knn pipeline (best-effort) and fall back to fetching embeddings and computing similarity client-side only if server-side vector search is unsupported. | vector search | prior_knowledge_confirmed | app/main.py / README.md (local_file) | **none** | app/main.py | yes |
| P07 | Include unit tests that verify embedding pack/unpack round-trips (and test packing dtype/byte-order) to prevent storage/serialization regressions. | testing | found_in_public_source | tests/test_pack_unpack.py (local_file) | **none** | tests/test_pack_unpack.py | yes |
| P08 | Validate uploaded images by trying to open them with an image library (PIL) and return a 400 error for invalid image uploads rather than accepting arbitrary files. | security | found_in_public_source | app/main.py (local_file) | **none** | app/main.py | yes |
| P09 | When attempting server-side vector search, use the vendor-supported aggregation stage (this sample tries $vectorSearch / knnBeta) and project only the fields needed (name, image_path, and score) to reduce transfer. | queries | found_in_public_source | app/main.py (local_file) | **none** | app/main.py | yes |
| P10 | This sample's get_client() implementation reads DOCUMENTDB_URI and returns a new pymongo.MongoClient() on each call; the app creates a client inside request handlers rather than a single global client. | connection handling | prior_knowledge_contradicted | app/db.py / app/main.py (local_file) | **none** | app/db.py | yes |
| P11 | I found no guidance in the repository or reachable documentation that stores per-document metadata fields for embedding dimensionality or dtype (e.g., embedding_dim=512 or embedding_dtype='float32'); the sample omits such metadata fields. | data modeling | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb embedding metadata best practices; documentdb embedding dimensions dtype | yes |
| P12 | The sample attempts create_index without first listing existing indexes (no idempotent listIndexes check); it relies on catching create_index exceptions instead of explicitly checking or adapting index creation parameters. | indexing | prior_knowledge_contradicted | app/db.py (local_file) | **none** | app/db.py | yes |
| P13 | I found no repository guidance or sample code that implements exponential-backoff retries with jitter or config-driven retry policies for DocumentDB operations; the sample does not wrap DB calls with custom retry/backoff logic. | retries | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb retry best practices; pymongo retryWrites retryReads azure documentdb | yes |
| P14 | The sample does not query server buildInfo/hello to detect supported wire protocol or vector index algorithms; instead it attempts index creation with plausible options and logs failures rather than adaptively changing parameters based on server feature detection. | indexing | prior_knowledge_contradicted | app/db.py / README.md (local_file) | **none** | app/db.py | yes |
| P15 | The /visual-search endpoint validates uploads by attempting to open with PIL and returning 400 on failure, but it does not explicitly validate content-type headers, does not enforce an upload size limit, and does not set explicit request timeouts in the sample. | security | prior_knowledge_contradicted | app/main.py (local_file) | **none** | app/main.py | yes |
| P16 | I found no guidance in the repository about scheduling index builds during maintenance windows or using server-specified background/online index build options; the sample performs a best-effort create_index during seeding without such scheduling guidance. | provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb index build best practices; vector index build maintenance windows | yes |
| P17 | I found no instrumentation or Azure Monitor integration for vector-search-specific metrics in the sample (no index-size, ANN memory/IO or query-latency metrics are emitted by the demo code). | monitoring | prior_knowledge_only | - (prior_knowledge) | **none** | azure monitor documentdb vector metrics; documentdb monitoring vector index | yes |
| P18 | The sample does not call listIndexes/listIndexes to verify that a vector-ivf index exists and with expected parameters after creation; it only requests create_index and logs failures, so it does not explicitly verify index presence. | indexing | prior_knowledge_contradicted | app/db.py / seed.py (local_file) | **none** | app/db.py | yes |
| P19 | For demonstration simplicity the sample falls back to fetching all embeddings and computing cosine similarity locally when server-side vector search is unavailable, rather than delegating to a dedicated ANN service. | vector search | prior_knowledge_contradicted | app/main.py / seed.py (local_file) | **none** | app/main.py | yes |

## Searches that returned nothing useful

- Azure DocumentDB vector index best practices
- Azure DocumentDB embedding binary subtype 0x09
- Azure DocumentDB store embedding dtype embedding_dim
- Azure DocumentDB retry policy best practices
- Azure DocumentDB monitoring vector index metrics

## Notes

Discovery was performed against the sample app and its README in the local workspace; external documentation search was not available in this run. Practices were recorded from the sample code and README (source_kind local_file). Each prior belief (K01..K20) was matched to the sample code: when the sample implements the belief it is marked prior_knowledge_confirmed and the belief fields are filled in the matching practice entry; when the sample implements a different approach the belief is marked prior_knowledge_contradicted and the repo file that shows the differing behavior is given as the source; where no repository or reachable documentation supported or contradicted a belief it is marked prior_knowledge_only and lists example queries that were attempted.

Prior beliefs the discovery step did not classify: K08, K09, K10, K12, K16. See 05a-prior-beliefs.json.

