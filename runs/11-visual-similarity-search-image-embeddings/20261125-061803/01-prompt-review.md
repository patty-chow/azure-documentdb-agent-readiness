# 1. Prompt review: 11-visual-similarity-search-image-embeddings

**Verdict: sufficient_with_assumptions**

The prompt states the core goal: a Python app that encodes product images with CLIP into 512-d embeddings, stores them as BSON binary vectors subtype 0x09 in Azure DocumentDB, creates a vector-ivf index, and exposes a /visual-search endpoint that returns the top 8 similar products. Important implementation details (Python version, MongoDB driver, exact index parameters, HTTP framework, CLIP implementation, sample data and seed idempotency, tests, README and infra-as-code) are left to the builder and will be chosen by reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 1: Goal and scenario |
| Covered by a skill | 3: Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 7: Language and runtime, Data model, Queries and indexes, AI components, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 5: Workflow type, Driver and version, Sample data, Run and test instructions, Definition of done |
| Not applicable | 0: - |

## Reference requirements at risk

- Run the similarity search using a $search / cosmosSearch query over the vector-ivf index (the prompt doesn't explicitly require the $search API; builder might use a different mechanism).
- Seed script idempotency: seed script can be run twice without duplicating data (prompt asks to load sample data but doesn't require idempotency).
- Vector index parameters and README guidance: sample should choose index params appropriate for data size and document how to change them (prompt doesn't specify params or documentation).
- One database client created and reused across requests (not specified; typical builders may create a client per request unless instructed).
- /search returns a clear error for an empty query and when the embedding call fails (error handling behavior is not specified).
- Search results include the similarity score (prompt doesn't state whether to return scores; reference expects it).
- Dependencies pinned in requirements.txt (prompt doesn't require pinned deps).
- Unit tests that run without a live cluster (prompt doesn't mention test design; tests that mock DocumentDB are not guaranteed).
- Infrastructure-for-cluster as code using Azure DocumentDB resource type (prompt/skill.md prohibit provisioning; sample may not include infra as code).
- README coverage: instructions for prerequisites, setup, run, and clean-up (prompt doesn't specify README contents).

## Questions for the prompt author

- Which Python runtime should be targeted (exact version, e.g. 3.10 or 3.11)?
- Which HTTP framework do you prefer (FastAPI or Flask)?
- Which CLIP implementation and exact model identifier should be used (e.g. 'openai/clip-vit-base-patch32' via Hugging Face transformers, open_clip, or another provider)?
- Which MongoDB driver should be used and what version to pin (PyMongo version)?
- What collection name and primary document schema should be used (field names beyond `embedding`)?
- Should the seed script fetch real product images (and from where) or generate placeholders? Any license constraints?
- Do you require infra-as-code (Bicep/Terraform/azd) for the DocumentDB cluster, or explicitly forbid provisioning (skill.md suggests not provisioning)?

## Contradictions and missing references

- Starter prompt asks to use the 'DocumentDB skill' but the installed_skills list is empty — there is no installed agent skill named or matching 'DocumentDB'.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python app that encodes product images using the CLIP model ... returns the top 8 visually similar products. | - | - | - |
| Workflow type | missing | no | - | - | Single-process app (no agent orchestration). Developer-run sample with an HTTP server started locally. | Prompt asks to 'use the DocumentDB skill' but does not specify any agent workflow or framework. |
| Language and runtime | ambiguous | no | Python app | skill.md | Target Python 3.10 or 3.11; use a venv and pip for dependencies. | skill.md says `python` and `pip` resolve to a virtualenv but doesn't fix a concrete Python version. |
| Driver and version | missing | no | - | - | Use PyMongo (pymongo) pinned to a recent stable release compatible with MongoDB 7.0 (e.g. pymongo >=4.0, e.g. 4.3+). | The prompt doesn't name the MongoDB driver or version; reference requirements expect PyMongo but the prompt is silent. |
| Target service and tier | covered_by_skill | no | - | skill.md | - | skill.md provides the cluster details: vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF indexes) and DOCUMENTDB_URI env var. |
| Authentication and secrets | covered_by_skill | no | - | skill.md | - | skill.md instructs to read the cluster connection string from DOCUMENTDB_URI environment variable and not to write real secrets into the repo. |
| Data model | ambiguous | no | stores the resulting 512-dimensional embeddings as BSON binary vectors with subtype 0x09 in DocumentDB | skill.md | Create a collection named `products` in database `sample_retail_11`. Each document contains at least: `_id`, `name` (string), `image_url` or `image_path` (string), `embedding` (binary subtype 0x09 holding 512 floats), plus optional metadata fields. | Database name is in skill.md; collection name, exact field names and other document fields are not specified. |
| Sample data | missing | no | - | skill.md | Provide a small seed dataset (dozens–a few hundred product images) in a sample_data/ folder or downloaded by seed script from permissively licensed sources or generated placeholders. | Prompt/skill.md require loading sample data for verification but do not specify source, size, or license. |
| Queries and indexes | ambiguous | no | creates a vector-ivf index | skill.md | Create a vector-ivf index on field `embedding` with dimensions=512 (to match CLIP), metric 'cosine' (or inner product with normalized vectors), and reasonable IVF params (e.g. nlist=100) documented in README. | Index kind is specified but concrete dimensions and index parameters are implied by the 512-d embedding but not explicitly enumerated in the prompt. |
| AI components | ambiguous | no | encodes product images using the CLIP model ... 512-dimensional embeddings | - | Use an open CLIP model from Hugging Face or open_clip (e.g. ViT-B/32) that produces 512-d image embeddings, performed locally (no external paid API). | Prompt names CLIP and 512 dimensions, but not the exact model identifier, framework (transformers, open_clip), or whether embeddings are normalized; the builder must choose. |
| App surface | ambiguous | no | exposes a /visual-search endpoint that accepts an uploaded image ... returns the top 8 visually similar products | - | Implement HTTP API using FastAPI (or Flask). /visual-search accepts multipart/form-data with an `image` file field, returns JSON with up to 8 product documents and similarity scores. | HTTP framework, exact request/response schema, error responses and status codes are not specified. |
| Provisioning and deployment | covered_by_skill | no | - | skill.md | Do not provision a cluster; use the provided cluster reachable via DOCUMENTDB_URI. No infra provisioning needed during the build. | skill.md explicitly instructs to use the already-provisioned cluster and not to create another. |
| Run and test instructions | missing | no | - | skill.md | Provide README with commands: pip install -r requirements.txt, cp .env.example .env (fill values), python seed.py, uvicorn main:app --reload. Include sample curl or HTTPie calls for /visual-search. | skill.md asks to verify against the live cluster but doesn't supply step-by-step commands to run or test. |
| Definition of done | missing | no | - | - | Definition: seed script ran, vector-ivf index exists with dimensions=512, /visual-search returns JSON with 8 items and similarity scores for a sample image, and README documents how to reproduce. | Prompt implies acceptance criteria but does not state explicit pass/fail checks. |
| Constraints and non-goals | ambiguous | no | - | skill.md | Don't provision cloud infra; avoid including secrets in repo; keep sample small to limit cost. No production hardening or scaling required. | skill.md imposes some constraints (no provisioning, no writing secrets) but broader constraints (cost budget, non-goals) are not stated. |
| Repository conventions | ambiguous | no | - | skill.md | Use conventional layout: README.md, app/ (code), seed.py, requirements.txt, .env.example, tests/; pin deps in requirements.txt and provide .env.example with placeholders. | skill.md instructs using .env.example and not storing secrets; other conventions (tests, README sections) are not spelled out. |
