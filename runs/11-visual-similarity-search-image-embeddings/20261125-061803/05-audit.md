# 5. Best-practice audit: 11-visual-similarity-search-image-embeddings

**Verdict: pass_with_findings** (5 violated, 10 followed, 1 not assessable)

The sample implements the requested functionality and is runnable for small, local demonstrations: CLIP-based encoder (with a deterministic fallback), BSON float32 packing/subclassing (subtype 0x09), a seed script that upserts 20 placeholder products into sample_retail_11.products, and a /visual-search FastAPI endpoint that attempts server-side vector search and falls back to client-side cosine similarity. Key risks and gaps remain: the builder could not verify or create the vector-ivf index because the cluster rejected the attempted index option names; ML packages (transformers/torch) were not installed during the build run so real CLIP encoding was not exercised; the code creates a new MongoClient on each get_client() call (not a single shared client); and a few gallery best-practices (pinned dependency versions, retries, batched bulk load, explicit index verification/listing and more README guidance) are missing or only partially provided. See requirement_results, checks and doc_gaps below for details and recommended minimal fixes.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval with readiness 'ready_with_gaps' is an operator decision (reason_source 'operator') and is recorded in decisions.jsonl. The build proceeded with known gaps; the events trace supports this. |
| D002 | I chose Python with FastAPI for the HTTP server. | prompt | sound | Choice of FastAPI is implemented in app/main.py and the events trace recorded the decision (events.jsonl entry 1). Evidence: app/main.py uses FastAPI (lines 11-13). |
| D003 | I chose pymongo >=4.3 (current 4.x series). | prompt | sound | Choosing pymongo >=4.3 is reflected in app/requirements.txt (line 3). The decision and its reason are recorded (events.jsonl). |
| D004 | I chose Hugging Face transformers with 'openai/clip-vit-base-patch32' as the default CLIP model. | model_default | sound | Choosing Hugging Face transformers and the model 'openai/clip-vit-base-patch32' is implemented in app/encoder.py (lines 19-20). The decision's reason_source is 'model_default' (see decisions.jsonl) — this is a reasonable default but not grounded in repository or external docs available to this run. |
| D005 | I chose to pack 512 float32 values little-endian into bytes and store as bson.binary.Binary(..., subtype=0x09). | docs | sound | Packing embeddings into BSON Binary subtype 0x09 is implemented (app/db.py lines 19-23) and matches the run environment requirement; the decision was logged and executed. |
| D006 | I chose to programmatically attempt to create a vector-ivf index with plausible options (vectorIndexType='ivf', dimensions=512, metric='cosine', indexOptions={'nlist':100}) and log any server errors if rejected. | prompt | sound | Attempting a plausible vector-ivf create_index and logging server errors is implemented (app/db.py ensure_vector_index). The events trace shows the server rejected the attempted options; the decision to best-effort and continue is justified and recorded. |
| D007 | I chose to read the cluster connection string at runtime from the DOCUMENTDB_URI environment variable (and support loading from a .env if present for local dev). | docs | sound | Reading DOCUMENTDB_URI from the environment is implemented in app/db.py lines 13-17 and is consistent with security guidance in README and .env.example. |
| D008 | I chose to generate a small set of placeholder product images programmatically in sample_data/ for the seed dataset. | model_default | sound | Decision to generate placeholder images programmatically is implemented in seed.py (make_placeholder_images) and recorded. Reason_source is 'model_default'; the approach is reasonable for demo samples and avoids licensing issues. |
| D009 | I chose to skip installing pytest in the builder run and instead run the test file via python -m to avoid network installs in this run. | tool_unavailable | sound | The environment lacked pytest (events.jsonl shows 'NOT INSTALLED'), the decision to avoid installing heavy test deps during this run is recorded and traces show an alternate pack/unpack check was executed. |
| D010 | I chose to install only pymongo for the build-time unit test to satisfy the missing 'bson' dependency while avoiding heavy ML package installs during the sample build run. | tool_result | sound | The decision to install only pymongo for the local unit check is reflected in events.jsonl where pip install pymongo was run and pack/unpack verification succeeded. |
| D011 | I chose to install Pillow only so seed.py can generate images and run; this avoids heavy ML installs. | tool_result | sound | Installing Pillow to run seed.py was necessary and recorded; events show pillow installed and seed.py executed. |
| D012 | I chose to install numpy to allow seed.py to run locally (fallback encoder uses numpy). | tool_result | sound | Installing numpy to support fallback encoder and seed operations was recorded and necessary for local verification; events show numpy installed and subsequent runs succeeded. |

Documentation gaps: 8 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 3 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 11 | Public and discoverable. |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Index creation idempotency | Check existing indexes with listIndexes before creating vector index (idempotent index creation). | app/db.py (no public address recorded) |
| Server feature detection | Detect server supported wire protocol and vector index algorithms (hello/buildInfo) and adapt index parameters accordingly. | app/db.py (no public address recorded) |
| Index presence verification | After index creation, verify that a vector-ivf index exists with expected parameters (use listIndexes). | app/db.py / seed.py |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Embedding metadata | Store per-document metadata for embedding dimensionality and dtype (e.g., embedding_dim=512). | A short doc page stating whether DocumentDB vector indexes require per-document metadata (embedding_dim, dtype) or whether the index defines/validates dims. |
| Retries/backoff | Wrap DB calls with exponential-backoff retries and make retry policy configurable. | A short 'retries' page describing recommended retry settings for DocumentDB and examples for pymongo. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | One client is created and reused for the life of the process. | app/db.py / app/main.py |
| Read connection string from env | Read the DocumentDB connection string from an environment variable (DOCUMENTDB_URI) and do not commit live credentials. | README.md / .env.example<br>README.md<br>.env.example |
| Pack binary embedding | Pack float32 embeddings into BSON Binary subtype 0x09 and unpack with matching little-endian reader. | app/db.py<br>app/db.py<br>tests/test_pack_unpack.py |
| L2 normalize embeddings | L2-normalize image embeddings in the encoder before storing and assume normalized vectors at query time. | app/encoder.py<br>app/encoder.py |
| Best-effort index creation | Attempt plausible create_index and catch/log server errors rather than failing startup (best-effort). | app/db.py<br>app/db.py |
| Prefer server-side vector search | Prefer server-side vector search when available and fall back to client-side computation when unsupported. | app/main.py / README.md<br>app/main.py<br>README.md |
| Seed upsert idempotency | Seed demo data into a dedicated database and collection and use upsert operations so repeated runs are safe. | seed.py / app/db.py<br>seed.py |
| Pack/unpack tests | Include unit tests that verify embedding pack/unpack round-trips. | tests/test_pack_unpack.py<br>tests/test_pack_unpack.py |
| Validate uploaded images | Validate uploaded images by trying to open them with PIL and return a 400 for invalid uploads. | app/main.py<br>app/main.py |
| Server-side knn aggregation | When attempting server-side vector search, use the vendor-supported aggregation stage and project only needed fields. | app/main.py<br>app/main.py |
| Fallback brute-force caution | Avoid transferring all embeddings to the client for production; use an ANN service if server lacks vector search. | app/main.py / seed.py<br>app/main.py<br>README.md |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| One client is created and reused for the life of the process. | connection | app/db.py lines 13-17 (get_client returns MongoClient(uri) per call); app/main.py line 40 calls get_client() inside request handler. | Create a single MongoClient at module import or app startup and return it from get_client(). | app/db.py / app/main.py |
| Check existing indexes with listIndexes before creating vector index (idempotent index creation). | indexing | app/db.py lines 40-50 call coll.create_index(...) with guessed options and catch exceptions; there is no list_indexes/listIndexes check or post-create verification. | Call coll.list_indexes() to inspect existing indexes and create only if absent; after create, verify the created index's parameters with list_indexes. | app/db.py (no public address recorded) |
| Wrap DB calls with exponential-backoff retries and make retry policy configurable. | retries | No retry/backoff wrappers or driver-level retryReads/retryWrites configuration found in app/db.py or seed.py. | Add a small retry decorator with jitter for transient errors and make retry parameters configurable; recommend enabling driver retry options where appropriate. | prior_knowledge (no public address recorded) |
| Detect server supported wire protocol and vector index algorithms (hello/buildInfo) and adapt index parameters accordingly. | indexing | app/db.py attempts create_index with guessed options rather than querying server buildInfo/hello to determine supported features (no buildInfo/hello usage found). | On startup, call client.admin.command('hello') or buildInfo and adapt index creation parameters or choose fallbacks based on supported algorithms. | app/db.py (no public address recorded) |
| After index creation, verify that a vector-ivf index exists with expected parameters (use listIndexes). | indexing | app/db.py currently only logs create_index exceptions and does not call list_indexes to confirm the index exists with expected parameters. | Call list_indexes after creation and log or error if the index is absent or has unexpected parameters. | app/db.py / seed.py |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Store per-document metadata for embedding dimensionality and dtype (e.g., embedding_dim=512). | data modeling | searched repository; external docs unavailable in this run | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read the DocumentDB connection string from an environment variable (DOCUMENTDB_URI) and do not commit live credentials. | authentication and secrets | app/db.py lines 13-17; app/.env.example lines 1-4; README.md lines 29-30. | README.md / .env.example<br>README.md<br>.env.example |
| Pack float32 embeddings into BSON Binary subtype 0x09 and unpack with matching little-endian reader. | data modeling | app/db.py lines 19-23 (pack_embedding) and 25-29 (unpack_embedding); tests/test_pack_unpack.py validates roundtrip. | app/db.py<br>app/db.py<br>tests/test_pack_unpack.py |
| L2-normalize image embeddings in the encoder before storing and assume normalized vectors at query time. | vector search | app/encoder.py lines 35-39 normalize the vector before returning; fallback also normalizes (lines 62-66). | app/encoder.py<br>app/encoder.py |
| Attempt plausible create_index and catch/log server errors rather than failing startup (best-effort). | indexing | app/db.py lines 32-55 show ensure_vector_index attempts create_index and catches exceptions; seed.py calls ensure_vector_index (line 41). events.jsonl shows a server rejection was logged. | app/db.py<br>app/db.py |
| Prefer server-side vector search when available and fall back to client-side computation when unsupported. | vector search | app/main.py lines 48-61 attempt a server-side aggregation pipeline then fall back to fetching all embeddings and computing cosine locally (lines 62-82). | app/main.py / README.md<br>app/main.py<br>README.md |
| Seed demo data into a dedicated database and collection and use upsert operations so repeated runs are safe. | provisioning | seed.py lines 54-59 use coll.update_one({'image_path': p}, {'$set': doc}, upsert=True). DB name set to sample_retail_11 in app/db.py line 10. | seed.py / app/db.py<br>seed.py |
| Include unit tests that verify embedding pack/unpack round-trips. | testing | tests/test_pack_unpack.py exists and was exercised successfully during build (events.jsonl shows the pack/unpack check returned OK). | tests/test_pack_unpack.py<br>tests/test_pack_unpack.py |
| Validate uploaded images by trying to open them with PIL and return a 400 for invalid uploads. | security | app/main.py lines 24-31 read the file and do Image.open(...).convert('RGB'), raising HTTPException(400) on failure. | app/main.py<br>app/main.py |
| When attempting server-side vector search, use the vendor-supported aggregation stage and project only needed fields. | queries | app/main.py lines 51-55 build a pipeline with $vectorSearch / knnBeta and then $project only name, image_path and score. | app/main.py<br>app/main.py |
| Avoid transferring all embeddings to the client for production; use an ANN service if server lacks vector search. | vector search | app/main.py falls back to fetching all embeddings and computing cosine similarity locally (lines 62-82). README notes this is suitable only for small datasets (README lines 21-22). | app/main.py / seed.py<br>app/main.py<br>README.md |

### Reference requirements

7 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The /visual-search handler runs the similarity search in Azure DocumentDB with a $search / cosmosSearch query over the vector-ivf index, passing the encoded query embedding. | not_met | prompt_silent | app/main.py lines 51-55 attempt an aggregation using a $vectorSearch stage (pipeline = [{"$vectorSearch": {"knnBeta": { ... }}}]) rather than a $search/cosmosSearch $search stage. | Either: (A) change the starter prompt to explicitly require the $search/cosmosSearch API, or (B) update the code to attempt both the $vectorSearch aggregation and a $search/cosmosSearch form (catching server errors) so the sample demonstrates the recommended API when available. |
| One database client is created and reused across requests. | not_met | prompt_silent | app/db.py get_client() (lines 13-17) returns MongoClient(uri) on each call; app/main.py calls get_client() inside the /visual-search handler (line 40), creating a client per request. | Create a module-level client at import or during app startup and reuse it (e.g., create MongoClient once and return it from get_client() or expose a get_shared_client() wrapper). |
| Dependencies are pinned in requirements.txt. | not_met | prompt_silent | app/requirements.txt uses >= version expressions rather than exact pinned versions (lines 1-10). | Pin exact dependency versions for reproducible gallery builds (e.g., pymongo==4.x.y, fastapi==x.y.z) or add a separate requirements-lock.txt for CI. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files (Bicep/Terraform/ARM) present in the repository root or app/ directory (list_files and read_files show no infra code). | Add an optional IaC snippet (Bicep or Terraform) in docs showing the correct resource type and minimal parameters; mark it optional in README because the run environment forbids provisioning during the build. |
| Build the app in Python and encode each product image with the CLIP model into a 512-dimensional embedding. | partly_met | tool_unavailable | app/encoder.py lines 19-39 (CLIPModel.from_pretrained and encode_image_pil) and lines 42-66 (fallback encoder). | Ensure transformers and torch are available in the build/CI environment used to verify the sample, or provide a lightweight mock for CI; document the heavy ML deps and make them optional for demo runs. |
| In code, create a cosmosSearch index of kind vector-ivf on the embedding field, with dimensions set to 512. | partly_met | could_not_determine | app/db.py lines 40-48 attempts create_index with vectorIndexType='ivf' and dimensions=512; seed.py calls ensure_vector_index (line 41). The seed run logged a server error and no index was created (events.jsonl shows server rejection). | Make ensure_vector_index idempotent and adaptive: list the collection's indexes, attempt create only if absent, and try alternate vendor option keys or surface the server's accepted index syntax in logs (or ship an authoritative createIndex example in docs). |
| A .env.example lists every setting with placeholder values. | partly_met | prompt_silent | app/.env.example lines 1-4 list DOCUMENTDB_URI placeholder only. | Add placeholders for any optional settings the sample supports (e.g. CLIP_MODEL, OPTIONAL flags to force fallback, or timeouts) to .env.example. |
| The vector index dimensions match the embedding model's output. | partly_met | could_not_determine | app/db.py line 46 sets 'dimensions': 512 in attempted index options; encoder returns 512-d vectors (app/encoder.py uses 512-length). | Ensure index creation succeeds (see ensure_vector_index idempotency/adaptation fix above) so the server-side index actually records the dimensions. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | partly_met | prompt_silent | app/db.py indexOptions includes nlist=100 (line 48) and README notes nlist=100 and suggests consulting cluster docs (README lines 20-22). | Expand README with explicit, short guidance: why nlist=100 was chosen for ~20 items and how to tune nlist/nprobe/other params for larger datasets. |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | could_not_determine | seed.py uses coll.update_one(..., upsert=True) to avoid duplicates (seed.py lines 56-59), and seed.py calls ensure_vector_index(db) (line 41) which is best-effort but the attempted create_index may be rejected by the server (events show a server error). | Keep upsert for data (good). For index creation: make index creation idempotent by checking list_indexes and creating only if absent, and log explicit post-create verification. |
| /search returns a clear error for an empty query and when the embedding call fails. | partly_met | prompt_silent | app/main.py validates the uploaded file and raises HTTPException(400) if Image.open fails (lines 24-31). On encoding failure the app currently falls back to a deterministic encoder (lines 32-36) rather than returning an explicit error. | Decide sample behavior: either return 5xx/4xx on encoder failure or make fallback explicit and document it. To meet the requirement, return a clear 5xx/4xx when the real model attempt fails (or make fallback optional via config). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | README.md includes what the sample shows, prerequisites and setup/run steps (app/README.md lines 1-15) but does not include an explicit clean-up section or explicit instructions for verifying index creation. | Add a short 'clean-up' section and an explicit 'validate index' sub-section with commands (e.g., a pymongo snippet to list indexes and check vector index parameters). |
| Store each product as a document in Azure DocumentDB whose image embedding is saved as a BSON binary vector with subtype 0x09. | met | - | app/db.py lines 19-23 (pack_embedding returns Binary(..., subtype=0x09)); seed.py lines 54-59 (emb_bin = pack_embedding(vec); coll.update_one(..., upsert=True)). | - |
| Expose a /visual-search HTTP endpoint that accepts an uploaded image and encodes it with the same CLIP model into a 512-dimensional query embedding. | met | - | app/main.py lines 24-36 define POST /visual-search, read and validate the uploaded image, and lines 32-36 call encode_image_pil with fallback to encode_image_fallback. | - |
| The /visual-search endpoint returns the top 8 visually similar products from that query (k = 8). | met | - | app/main.py pipeline k:8 at line 52 and fallback sorting/results slicing at lines 81-82 ([:8]). | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example lines 1-4 show placeholder DOCUMENTDB_URI; app/db.py lines 13-17 read DOCUMENTDB_URI from the environment. | - |
| Search results include the similarity score. | met | - | Server-side pipeline projects score as $meta: 'searchScore' (app/main.py line 53). Fallback code app/main.py lines 75-81 computes 'score' and includes it in results. | - |
| Unit tests run without a live cluster. | met | - | tests/test_pack_unpack.py exists (app/tests/test_pack_unpack.py) and pack/unpack roundtrip was executed successfully without a cluster by installing pymongo locally in the build (events.jsonl run_command that printed OK). | - |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | README.md line 1 uses the phrasing 'Azure DocumentDB (MongoDB-wire-compatible)'. | - |

