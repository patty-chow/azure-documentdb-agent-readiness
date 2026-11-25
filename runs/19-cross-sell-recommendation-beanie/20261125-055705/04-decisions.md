# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 4 |
| prompt | 3 |
| tool_result | 3 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:02:23+00:00

## D002 (build): I chose Python 3.x with FastAPI and Beanie ODM.

- **Instead of:** Node.js/TypeScript; Python async (FastAPI + Beanie); Go
- **Because:** The prompt explicitly requests Python and Beanie; this matches developer familiarity and ecosystem support for async MongoDB drivers.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build an async Python service using Beanie ODM'
- **When:** 2026-11-25T14:02:48+00:00

## D003 (build): I chose to pin package versions in requirements.txt: beanie>=1.19,<2.0, motor==3.1.1, pymongo==4.7.0, fastapi==0.100.0, uvicorn==0.22.0, openai==1.0.0, numpy==1.26.0.

- **Instead of:** Use latest Beanie without pinning; Pin specific Beanie and Motor versions
- **Because:** Pinning increases reproducibility while using version ranges for Beanie to allow small updates; selected versions are recent stable releases likely compatible.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Use Beanie latest stable compatible release with Motor/pymongo stable' and run environment has Python 3.x available.
- **When:** 2026-11-25T14:02:52+00:00

## D004 (build): I chose to read all secrets (DOCUMENTDB_URI, OPENAI_API_KEY) from environment variables and provide a .env.example with placeholders.

- **Instead of:** Read secrets from a config file; Read from environment variables
- **Because:** Environment variables avoid checking secrets into the repo and match the run-environment guidance.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'connection string is in the environment variable DOCUMENTDB_URI' and prompt review assumption about secrets.
- **When:** 2026-11-25T14:02:54+00:00

## D005 (build): I chose not to provision any Azure resources and to use the provided live cluster via DOCUMENTDB_URI.

- **Instead of:** Provision cluster in sample (Bicep/Terraform); Do not provision and use provided cluster
- **Because:** Provisioning Azure resources is disallowed by the run policy; sample should use the existing cluster and include IaC examples as files only.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy and skill_md: 'Do not provision another cluster unless run policy says Azure writes are allowed; the cluster above is the one to use.'
- **When:** 2026-11-25T14:02:57+00:00

## D006 (build): I chose to store both product embeddings (collection 'products') and product-pair embeddings (collection 'product_pairs').

- **Instead of:** Store only pair embeddings; Store product embeddings and pair embeddings
- **Because:** Storing product embeddings simplifies computing a basket embedding (average of product embeddings) and improves cross-sell scoring while still storing pair embeddings for direct similarity; it's straightforward in the seed script and keeps retrieval efficient.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions_from_prompt_review: 'Product-pair document shape ... embedding' and need to compute basket embedding to compare to pair embeddings.
- **When:** 2026-11-25T14:03:05+00:00

## D007 (build): I chose OpenAI 'text-embedding-3-small' with 1536 dimensions for embeddings.

- **Instead of:** text-embedding-3-small (1536 dims); text-embedding-3-large (3072 dims); openai-embedding-ada-002 (1536 dims)
- **Because:** This model is efficient, widely available, and 1536 dims are a good trade-off for a sample; document will note how to change model via env var.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information gap: 'OpenAI embedding model & dimensions' and common modern default.
- **When:** 2026-11-25T14:03:08+00:00

## D008 (build): I chose to recommend 'vector-diskann' for the sample index and document it; the sample will include index creation guidance but not execute cluster index changes automatically.

- **Instead of:** vector-diskann; vector-hnsw; vector-ivf
- **Because:** The cluster in the run environment is vector-capable and DiskANN is recommended for M30+; the sample must not change cluster configuration automatically per run policy, so index creation is documented and provided as JSON for manual application or via MCP tools.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Choose vector-diskann for M30+ or vector-hnsw/ivf based on sample scale'
- **When:** 2026-11-25T14:03:14+00:00

## D009 (build): I chose to use Motor as the MongoDB async driver because the prompt explicitly requires Beanie ODM, and current Beanie releases depend on Motor.

- **Instead of:** Use PyMongo AsyncMongoClient (recommended by documentdb-connection); Use Motor (required by Beanie ODM)
- **Because:** Beanie depends on Motor for async operations; to satisfy the prompt requirement and use Beanie, using Motor is necessary despite the connection skill recommendation; I will apply singleton client and pool best-practices from the driver/connection skills.
- **Reason came from:** `prompt`
- **Evidence:** documentdb-connection skill: 'Use PyMongo AsyncMongoClient... not Motor' vs prompt: 'Using the DocumentDB skill, build an async Python service using Beanie ODM'
- **When:** 2026-11-25T14:03:26+00:00

## D010 (build): I chose to relax the numpy requirement to 'numpy>=1.24.0' in requirements.txt because the environment Python version (3.13) prevented installing numpy==1.26.0.

- **Instead of:** Keep numpy==1.26.0; Relax numpy requirement to a compatible range
- **Because:** Relaxing the requirement to >=1.24.0 increases likelihood of finding a compatible wheel for the current Python runtime without changing code that uses basic numpy features.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: 'No matching distribution found for numpy==1.26.0' and environment Python 3.13 from readiness report.
- **When:** 2026-11-25T14:04:32+00:00

## D011 (build): I chose to relax pytest-mock to 'pytest-mock>=3.10' to allow installing a compatible wheel for the environment Python version (3.13).

- **Instead of:** Keep pytest-mock==3.11.2; Relax pytest-mock version constraint
- **Because:** Loosening the pin increases likelihood of a compatible package being found while maintaining testing support.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: 'No matching distribution found for pytest-mock==3.11.2'
- **When:** 2026-11-25T14:04:57+00:00

## D012 (build): I chose to make startup skip DB initialization when DOCUMENTDB_URI is not set (so unit tests that exercise request validation can run without a live DB).

- **Instead of:** Keep startup raising if DOCUMENTDB_URI missing; Make startup skip DB init when DOCUMENTDB_URI isn't set (safer for tests)
- **Because:** Skipping init when the env var is absent allows lightweight validation tests to run locally while still requiring DOCUMENTDB_URI for full integration. This is a pragmatic change for developer ergonomics in the sample code, and the README documents that a live cluster is needed for full functionality.
- **Reason came from:** `model_default`
- **Evidence:** Tests currently run in this workspace with no DOCUMENTDB_URI set; raising prevented tests from running.
- **When:** 2026-11-25T14:05:15+00:00

## D013 (build): I chose to modify the seed script to generate random normalized placeholder embeddings when OPENAI_API_KEY is not set so the sample can be run/verified against the live cluster without requiring an OpenAI key (documented as a dev-only shortcut).

- **Instead of:** Refuse to run seed without OPENAI_API_KEY; Modify seed to generate placeholder embeddings when OPENAI_API_KEY not present
- **Because:** The run environment lacks an OpenAI key; generating placeholder embeddings allows verifying DB writes and indexing flows without exposing secrets. The README documents that production runs should provide OPENAI_API_KEY to generate real embeddings.
- **Reason came from:** `tool_result`
- **Evidence:** OPENAI_API_KEY is not set in the environment (checked via python -c).
- **When:** 2026-11-25T14:06:04+00:00
