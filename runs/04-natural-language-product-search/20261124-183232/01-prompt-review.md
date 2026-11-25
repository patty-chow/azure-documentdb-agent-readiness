# 1. Prompt review: 04-natural-language-product-search

**Verdict: sufficient_with_assumptions**

The starter prompt is actionable: it clearly asks for a Python LangChain agent that rewrites queries and performs a hybrid lexical+vector search against Azure DocumentDB. Enough skills are installed to implement the core (vector + full-text guidance, driver/connection best practices, and local/run environment notes), but several concrete choices are left to the builder (Python version, driver version, embedding model and dims, exact index names and parameters, API surface/top-N defaults). These will be filled by skills where possible and by sensible defaults/assumptions for the rest.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Queries and indexes, Repository conventions |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Hybrid search using the community $text operator (reference requires sending a query document containing "$text"): documentdb-full-text-search skill indicates DocumentDB uses createSearchIndexes + $search; the starter prompt's $text requirement conflicts with the skill guidance and the live cluster's expected path.
- Embedding model & vector index dimension matching: the prompt doesn't specify an embedding model or dimension, so the builder must assume a model (affects index dimensions).
- Vector index parameters & README guidance: specific lBuild/lSearch/maxDegree and choosing DiskANN/HNSW/IVF depend on dataset size; the prompt doesn't provide dataset size or desired latency/recall tradeoffs.
- Top-N configurability: the starter prompt asks to 'return the best matches' but does not make N configurable; the reference requires configurable top-N.
- Returned product fields: prompt does not name required fields (product ID, title/name, description/snippet); builder must assume names and mapping to stored fields.
- Handling zero-results on one side: prompt does not explicitly require graceful handling if $text or vector returns zero results; reference requires this behavior.
- Seed script idempotency and existence: the prompt and skills mention loading sample data but do not supply or mandate an idempotent seed script; reference requires this.
- Error handling on /search (empty query and embedding failure): the starter prompt does not specify API surface or error-handling behavior expected by the reference.
- Search results must include similarity score: while the prompt asks for ranking, it does not explicitly require returning the numeric similarity score in results; reference requires it.
- Dependencies pinned in requirements.txt: the prompt doesn't require pinned dependency versions; reference requires pinned dependencies.
- Unit tests that run without a live cluster: not mentioned in prompt or skills; reference expects such tests.
- Infrastructure-as-code for the cluster: the prompt uses an existing cluster and doesn't ask for infra code; reference expects infra code (not covered).
- README completeness (what sample shows, prerequisites, setup, run, clean-up): the prompt does not require a README; reference expects it.
- Use the exact name 'Azure DocumentDB' throughout the sample: prompt doesn't mandate naming conventions; reference expects this wording.

## Questions for the prompt author

- Do you specifically require the MongoDB community '$text' operator, or do you allow using Azure DocumentDB's supported $search aggregation stage (createSearchIndexes + $search)? The two are different and the installed full-text skill prefers $search.
- Which embedding provider and model should the sample use (e.g., OpenAI text-embedding-3-small with 1536 dims)? This determines vector index dimensions and seed/index creation parameters.
- Do you want a web API (e.g., FastAPI POST /search) as the sample surface, or is a CLI/interactive notebook acceptable? Also, what should the default top-N be (e.g., top_n=10)?

## Contradictions and missing references

- Prompt asks explicitly to query DocumentDB using the community '$text' operator, but documentdb-full-text-search skill states that Azure DocumentDB's supported path is createSearchIndexes + $search (BM25) and that the community $text operator is not the DocumentDB search path. Builder must choose which to implement; this choice will change index/query implementation.
- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB skill' — multiple documentdb-* skills are installed (full-text, vector-search, driver, etc.).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python LangChain agent with a hybrid search tool that queries DocumentDB using both $text and vector search, merges the ranked results, and returns the best matches | - | - | The business problem (natural-language product search) and what the sample demonstrates are stated. |
| Workflow type | specified | no | build a Python LangChain agent ... Include a prompt engineering step ... the agent must invoke this rewrite step programmatically | - | - | Single LangChain agent (no multi-agent orchestration) is requested explicitly. |
| Language and runtime | ambiguous | no | Python LangChain agent | - | Use Python 3.10 (or 3.11) as the runtime for the sample and test environment; virtualenv-based pip install as in skill_md. | Prompt says Python but does not fix a minor version; builder will pick a common supported version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the latest stable PyMongo compatible with MongoDB 7.x (e.g., pymongo >=4.3 or 4.5+), with a singleton MongoClient per process as recommended by the documentdb-driver skill. | documentdb-driver covers client patterns but does not specify an exact driver version to pin in requirements.txt. |
| Target service and tier | specified | no | skill_md: A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable; connection string in DOCUMENTDB_URI | skill_md (run environment provided with the starter prompt) | - | The run environment / live cluster (M30, MongoDB 7.0) is specified in the shared skill_md block. |
| Authentication and secrets | specified | no | Read connection string from environment variable DOCUMENTDB_URI; never write it into files or logs; use a config file or .env.example with a placeholder | skill_md | - | Credentials come from env vars; skill_md instructs how to manage them. |
| Data model | ambiguous | no | - | documentdb-data-modeling | Builder will create a 'products' collection in database sample_retail_04 with documents containing _id (or product_id), title/name, description (text), and a vector field named 'embedding' (float array). Add schemaVersion and small metadata fields. This is the simplest model to satisfy search and presentation needs. | The prompt asks for product search but does not define collection or field names. data-modeling skill provides patterns but no concrete sample schema. |
| Sample data | missing | no | - | - | Include a small synthetic sample dataset (JSON) bundled with the repo (e.g., 100–1k product docs) and a seed script to insert/update those docs; dataset will be MIT or public-domain-like synthetic data. | Prompt/skills mention 'load the sample data' in the run guidance but do not provide the dataset source, size, or license. |
| Queries and indexes | covered_by_skill | no | prompt requests queries using both $text and vector search | documentdb-full-text-search, documentdb-vector-search | Builder will create a search index (via createSearchIndexes) mapping title and description for BM25 search and a vector index (e.g., vector-diskann or vector-hnsw) on an 'embedding' field. Index names and exact parameters will be chosen based on sample size (DiskANN for larger sample; HNSW for small datasets). | Full-text skill indicates DocumentDB uses createSearchIndexes + $search (BM25) rather than community $text. Vector skill covers cosmosSearch/cosmos vector index creation and KNN querying. |
| AI components | missing | no | - | documentdb-vector-search (covers vector index best practices but not embedding provider) | Use OpenAI embeddings via LangChain (model text-embedding-3-small) and normalize embeddings to cosine similarity; assume embedding dimension 1536 and declare that in .env.example and README. The code will be written so the model can be swapped. | The prompt requires embedding-based vector search but does not name an embedding model or dims; that choice affects index creation parameters. |
| App surface | ambiguous | no | build a Python LangChain agent with a hybrid search tool ... returns the best matches | - | Provide a simple FastAPI HTTP endpoint (POST /search) that accepts the raw user query and optional top_n parameter; also include a minimal CLI example calling the agent. | Prompt does not require a web API or CLI; reference requirements expect an endpoint like /search, so the builder will likely add one. |
| Provisioning and deployment | specified | no | skill_md: cluster already provisioned and reachable; do not provision another cluster unless run policy allows Azure writes | skill_md | - | The sample is to verify against an existing live cluster rather than provisioning resources. |
| Run and test instructions | missing | no | - | - | README will include: create virtualenv, pip install -r requirements.txt, copy .env.example to .env and set DOCUMENTDB_URI and embedding API key, run 'uvicorn app.main:app --reload' and run the seed script. Basic smoke test: POST /search returns results. | No explicit run/test commands are provided in the prompt. |
| Definition of done | missing | no | - | - | Definition of done will match the reference checklist: LangChain agent calls rewrite step, performs real $text (or $search) + vector queries against DocumentDB, merges/ranks results, returns top-N with product id/title/description and scores, and includes seed script and README. | Prompt does not include explicit acceptance criteria; builder will use the natural reading of the starter prompt plus gallery expectations. |
| Constraints and non-goals | missing | no | - | - | Sample is educational only: not production-ready, no autoscaling or CMK, keeps costs small by using a small dataset and not provisioning new cloud resources. | No cost or scope constraints are given. |
| Repository conventions | covered_by_skill | no | skill_md: Never write connection string into files; use a .env.example with a placeholder; python + pip available | documentdb-local-deployment, skill_md | Repo will include .env.example, requirements.txt, README, src/ or app/ layout, seed script, and tests/ directory following gallery conventions. | Skill_md includes guidance about env handling; other repository conventions are not fully specified but common defaults will be used. |
