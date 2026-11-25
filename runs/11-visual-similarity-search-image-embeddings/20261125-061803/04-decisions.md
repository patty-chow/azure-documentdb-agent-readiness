# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| tool_result | 3 |
| model_default | 2 |
| docs | 2 |
| operator | 1 |
| tool_unavailable | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:21:33+00:00

## D002 (build): I chose Python with FastAPI for the HTTP server.

- **Instead of:** Node.js/Express; Python/Flask; Python/FastAPI
- **Because:** FastAPI is lightweight, async-friendly, widely used for Python samples and matches the prompt_review suggestion.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: 'Implement HTTP API using FastAPI (or Flask). /visual-search accepts multipart/form-data with an `image` file field.'
- **When:** 2026-11-25T14:21:51+00:00

## D003 (build): I chose pymongo >=4.3 (current 4.x series).

- **Instead of:** pymongo 3.x; pymongo 4.x (latest)
- **Because:** pymongo 4.x supports modern MongoDB features and is the recommended Python driver; it aligns with the readiness guidance.
- **Reason came from:** `prompt`
- **Evidence:** prompt_review assumption: 'Use PyMongo (pymongo) pinned to a recent stable release compatible with MongoDB 7.0 (e.g. pymongo >=4.0, e.g. 4.3+).'
- **When:** 2026-11-25T14:21:53+00:00

## D004 (build): I chose Hugging Face transformers with 'openai/clip-vit-base-patch32' as the default CLIP model.

- **Instead of:** open_clip (open-clip-torch); Hugging Face transformers CLIPModel
- **Because:** transformers is widely used and integrates CLIP models; it is straightforward for users to swap models. 'openai/clip-vit-base-patch32' is the canonical ViT-B/32 CLIP model producing 512-d embeddings.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt_review: 'Use an open CLIP model from Hugging Face or open_clip (e.g. ViT-B/32) that produces 512-d image embeddings.'
- **When:** 2026-11-25T14:21:55+00:00

## D005 (build): I chose to pack 512 float32 values little-endian into bytes and store as bson.binary.Binary(..., subtype=0x09).

- **Instead of:** Store embeddings as BSON array of floats; Store embeddings as BSON Binary subtype 0x09 containing float32 bytes
- **Because:** This matches the run_environment requirement and ensures interoperability with DocumentDB vector indexes.
- **Reason came from:** `docs`
- **Evidence:** readiness_report guidance: 'Store float32 512-dimensional embeddings as BSON Binary with subtype 0x09; pack floats into bytes consistently in seed and query code (e.g., struct.pack with little-endian float32) and wrap with bson.binary.Binary(..., subtype=0x09).'
- **When:** 2026-11-25T14:21:58+00:00

## D006 (build): I chose to programmatically attempt to create a vector-ivf index with plausible options (vectorIndexType='ivf', dimensions=512, metric='cosine', indexOptions={'nlist':100}) and log any server errors if rejected.

- **Instead of:** Create index using unknown exact server options without fallback; Attempt to create a vector-ivf index with reasonable option names and capture server errors
- **Because:** Exact option names for the DocumentDB vector index are not available locally; attempting with reasonable names plus error capture is the prudent approach while documenting unverifiable items.
- **Reason came from:** `prompt`
- **Evidence:** readiness_report: guidance to 'implement index creation via pymongo and programmatically capture and log any server errors when the createIndex call fails so you can refine the option names for IVF/HNSW/DiskANN.'
- **When:** 2026-11-25T14:22:01+00:00

## D007 (build): I chose to read the cluster connection string at runtime from the DOCUMENTDB_URI environment variable (and support loading from a .env if present for local dev).

- **Instead of:** Read connection string from a checked-in file; .env file and environment variable DOCUMENTDB_URI
- **Because:** This fulfills the security requirement not to store secrets in the repository and matches the run environment guidance.
- **Reason came from:** `docs`
- **Evidence:** readiness_report instruction: 'Read the cluster connection string only from the DOCUMENTDB_URI environment variable at runtime; do not embed or log its contents.'
- **When:** 2026-11-25T14:22:03+00:00

## D008 (build): I chose to generate a small set of placeholder product images programmatically in sample_data/ for the seed dataset.

- **Instead of:** Use real product images downloaded from the web; Generate small set of placeholder sample images programmatically
- **Because:** Generating placeholder images avoids licensing issues, keeps the sample self-contained and small, and ensures quick testing without network downloads.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt_review: 'Provide a small seed dataset ... or generated placeholders.'
- **When:** 2026-11-25T14:22:05+00:00

## D009 (build): I chose to skip installing pytest in the builder run and instead run the test file via python -m to avoid network installs in this run.

- **Instead of:** Install pytest via pip then run tests; Skip running pytest because pytest not installed
- **Because:** The environment does not have pytest on PATH and installing packages now may be slow/heavy; running the simple test module via python -m pytest would still need pytest. Instead run a minimal test script using python to exercise pack/unpack without pytest.
- **Reason came from:** `tool_unavailable`
- **Evidence:** run_command output: "NOT INSTALLED: 'pytest' was not found on PATH."
- **When:** 2026-11-25T14:22:47+00:00

## D010 (build): I chose to install only pymongo for the build-time unit test to satisfy the missing 'bson' dependency while avoiding heavy ML package installs during the sample build run.

- **Instead of:** Install full requirements.txt (heavy); Install only pymongo to run small unit test
- **Because:** Installing only pymongo is faster and sufficient to run the pack/unpack unit check; full requirements can be installed by users as needed per README.
- **Reason came from:** `tool_result`
- **Evidence:** Error: ModuleNotFoundError: No module named 'bson' when running quick python test; bson provided by pymongo.
- **When:** 2026-11-25T14:22:57+00:00

## D011 (build): I chose to install Pillow only so seed.py can generate images and run; this avoids heavy ML installs.

- **Instead of:** Install full requirements; Install Pillow only to run seed
- **Because:** Pillow is lightweight and required for image generation; ML packages remain optional.
- **Reason came from:** `tool_result`
- **Evidence:** Seed run error: ModuleNotFoundError: No module named 'PIL'
- **When:** 2026-11-25T14:23:07+00:00

## D012 (build): I chose to install numpy to allow seed.py to run locally (fallback encoder uses numpy).

- **Instead of:** Install numpy and proceed; Skip seeding because numpy missing
- **Because:** numpy is lightweight relative to ML packages and is required by encoder fallback and data handling.
- **Reason came from:** `tool_result`
- **Evidence:** Seed run error: ModuleNotFoundError: No module named 'numpy'
- **When:** 2026-11-25T14:23:14+00:00
