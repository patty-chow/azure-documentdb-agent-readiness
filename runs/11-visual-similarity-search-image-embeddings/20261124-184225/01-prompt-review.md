# 1. Prompt review: 11-visual-similarity-search-image-embeddings

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided skill.md and installed skills give enough to start and complete a working Python visual-similarity sample: CLIP → 512-dim vectors stored as BSON binary subtype 0x09, a vector-ivf index, and a /visual-search endpoint returning top-8 matches. Several implementation details are left to defaults (Python version, exact CLIP model and packaging, collection name, sample-data source/licence, index tuning, README/fixtures/tests). These will be decided by the builder unless the author specifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 7: Goal and scenario, Target service and tier, Authentication and secrets, Queries and indexes, AI components, App surface, Provisioning and deployment |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 3: Language and runtime, Data model, Sample data |
| Missing: builder will guess | 5: Workflow type, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not specified by the prompt or skill_md; builder must add this.
- Dependencies are pinned in `requirements.txt` — prompt doesn't require pinned versions; builder must create them.
- Unit tests run without a live cluster — prompt and skills don't provide guidance or mocks for offline tests; this may be omitted unless the builder adds them.
- Seed script loads sample data and is safe to run twice without duplicating data — prompt requires ingestion functionality but doesn't mandate idempotency.
- Search returns a clear error for an empty query and when the embedding call fails — prompt doesn't specify error semantics for edge cases.
- Search results include the similarity score — prompt requires ordering but not explicit scores; likely omitted unless the builder adds them.
- The README covers prerequisites, setup, run, and clean-up — not provided by prompt; builder must author it.
- Index parameter tuning and README guidance for scaling to larger datasets — prompt requires creating a vector-ivf index but not a discussion of parameters or how to change them for larger datasets.
- Infrastructure as code for the cluster using Azure DocumentDB resource type — skill_md forbids provisioning and prompt does not request IaC, so no cluster IaC will be produced unless the builder adds optional code.

## Questions for the prompt author

- Which exact CLIP model checkpoint and package should be used (e.g., Hugging Face `openai/clip-vit-base-patch32` via transformers + torch, or the `clip` package)? This determines dependency pins and preprocessing code.
- Which Python major/minor runtime should be targeted (3.10, 3.11)?
- Should sample images be included in the repo, or referenced by URL? If included, what license/source is acceptable?
- Do you require returning similarity scores in the API response, and do you prefer cosine similarity labeling? (Prompt asks for ordering but not scores.)
- Do you want idempotent seed behavior enforced (no duplicates on repeated runs) and unit tests that run without a live cluster?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python app that encodes product images using the CLIP model ... exposes a /visual-search endpoint ... returns the top 8 visually similar products." | - | - | Business goal and user-facing scenario are clearly stated in the prompt. |
| Workflow type | missing | no | - | - | Builder will implement a single-agent, single-process web service (e.g., Flask/FastAPI) serving /visual-search; no multi-agent/orchestration framework will be used. | Prompt doesn't say whether to use serverless, a background worker for ingestion, or an agent framework. A simple single-process API is the obvious default. |
| Language and runtime | ambiguous | no | "build a Python app" | - | Use Python 3.10 or 3.11 (current stable supported runtimes). The code will use standard virtualenv / pip workflow. | Python is specified but not a precise version; builders will pick a recent 3.x and document it. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use the official PyMongo driver (pymongo 4.x) and apply the singleton MongoClient pattern described in the documentdb-driver skill. | The documentdb-driver skill provides the pattern (singleton client) and best practices; the prompt doesn't pin an exact driver version, so the builder will choose a recent PyMongo compatible with MongoDB 7.0 (e.g., pymongo>=4.6). |
| Target service and tier | specified | no | "Using the DocumentDB skill" and skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ... connection string in DOCUMENTDB_URI" | - | - | Environment notes (cluster exists, M30, MongoDB 7.0, connection in env var) are supplied in the skill_md run environment. |
| Authentication and secrets | specified | no | - | - | The app will read the connection string from DOCUMENTDB_URI at runtime and will not log or commit it; other secrets (if any) come from environment variables. | skill_md explicitly instructs using DOCUMENTDB_URI and not writing actual secrets to files. |
| Data model | ambiguous | no | "stores the resulting 512-dimensional embeddings ... in DocumentDB" and "writes a product document ... containing a product identifier, display metadata (e.g., name or image URL), and the embedding." | documentdb-data-modeling | Builder will create a collection named `products` in database `sample_retail_11` (per skill_md), with documents like: { _id: <id>, name: <string>, image_url: <string>, embedding: <BSON binary subtype 0x09>, schemaVersion: 1 }. | Prompt requires identifier + display metadata + embedding but doesn't fix field names or collection name; skill_md fixes DB name; document shape and schemaVersion are reasonable defaults. |
| Sample data | ambiguous | no | - | documentdb-local-deployment | Builder will include a small seed/ingest script with ~20 example products (images from permissive sources such as CC0/Unsplash) and an idempotent ingestion routine; images will be referenced by URL rather than committed to the repo. | The prompt asks for functionality to write product docs but does not specify source, size, or license of sample images. The run-environment notes say 'load the sample data' but don't give specifics. |
| Queries and indexes | specified | no | "stores ... embeddings as BSON binary vectors with subtype 0x09 ... creates a vector-ivf index" | documentdb-vector-search | The sample will create a `cosmosSearch` vector index of sub-type `vector-ivf` on the embedding field with dimensions=512 and reasonable IVF parameters (defaults tuned for small sample size as suggested by documentdb-vector-search). | Prompt explicitly requires storing embeddings as subtype 0x09 and creating a vector-ivf index; vector-search skill guides index parameter choices (IVF recommended for small collections). |
| AI components | specified | no | "encodes product images using the CLIP model ... 512-dimensional embeddings" | - | Builder will use a standard CLIP implementation (e.g., Hugging Face `openai/clip-vit-base-patch32` via transformers/torch or the `clip` package) that produces 512-dim image embeddings. | CLIP and 512-dim embedding requirement are explicit. The prompt doesn't name the exact package or model checkpoint; builder will pick a common CLIP model that outputs 512 dims. |
| App surface | specified | no | "exposes a /visual-search endpoint that accepts an uploaded image, encodes it, and returns the top 8 visually similar products." | - | Implement as an HTTP API endpoint (e.g., FastAPI or Flask) accepting multipart/form-data image upload and returning JSON with top-8 results. | Route, input type, and expected behavior are specified; implementation framework is left to the builder. |
| Provisioning and deployment | specified | no | - | - | No new cluster will be provisioned; use the live vector-capable cluster referenced in skill_md. If any IaC is included, it will be optional and use documentdb-azure-deployment patterns. | skill_md mandates using the existing cluster and forbids provisioning another unless allowed by policies. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Builder will add a README with pip install, env setup (DOCUMENTDB_URI), seed/ingest script usage, and how to call /visual-search. Tests will be manual verification steps; no pre-existing automated tests are required by the prompt. | Prompt and skill_md ask to verify against the live cluster but do not provide exact commands. The builder must author run instructions and tests. |
| Definition of done | missing | no | - | - | The sample will be considered done when: (1) product docs with 512-dim subtype 0x09 embeddings exist in `sample_retail_11`, (2) a vector-ivf index is created on the embedding field, (3) /visual-search returns ordered top-8 results for a supplied image, and (4) a seed script and README allow a reviewer to reproduce these steps. | No explicit acceptance criteria in the prompt; the above is the reasonable checklist the builder will adopt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep costs low by using the existing cluster; do not implement full production HA, CMK, or private endpoints in the sample. Security best practices (TLS, env secrets) will be followed. | Prompt doesn't state cost or compliance constraints; builder will avoid provisioning additional cloud resources. |
| Repository conventions | missing | no | - | - | Use a conventional layout: README.md, app/ (source), scripts/seed.py, requirements.txt, .env.example, and tests/ with at least one unit test scaffold. Use the name 'Azure DocumentDB' in docs. | No explicit repo layout or naming conventions supplied; builder will use common sample conventions. |
