# 1. Prompt review: 11-correspondent-banking-risk-screener

**Verdict: sufficient_with_assumptions**

The prompt clearly states the goal (a Python LangChain agent that embeds correspondent profiles, stores vectors in Azure DocumentDB, searches sanctions/adverse-media, and returns a score, matches and a narrative). The provided skill.md supplies important run-time constraints (existing DocumentDB cluster, DB name, env var for connection string, index capabilities). Several implementation details are not specified (Python version, driver choice/version, embedding/chat model, exact data shapes, index parameters, API vs CLI, seed data). A builder can start, but will make several concrete assumptions (pymongo driver, OpenAI embeddings + chat models, FastAPI endpoint, typical embedding dimension such as 1536, collection names) unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Definition of done |
| Covered by a skill | 3: Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 6: Language and runtime, Data model, Queries and indexes, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 4: Driver and version, Sample data, AI components, Run and test instructions |
| Not applicable | 0: - |

## Reference requirements at risk

- Embed correspondent bank entity profiles with a LangChain embeddings integration and store each profile's vector on its document in Azure DocumentDB using a MongoDB-compatible Python driver — not fully specified: builder must choose embedding provider/model and the Python MongoDB driver/version.
- Create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field with dimensions matching the embedding model used — at risk: index kind/parameters and embedding dimensions are not specified.
- On each review cycle, run vector similarity search inside Azure DocumentDB with $search / cosmosSearch using each correspondent's embedding — at risk: prompt does not explicitly require using $search/cosmosSearch syntax; builder may instead perform client-side nearest-neighbour filtering.
- Derive a risk score for each correspondent from the similarity search results returned by Azure DocumentDB — at risk: method to derive the risk score (scaling/aggregation) is unspecified.
- The connection string and model credentials come from environment variables; none appear in the repository — at risk: skill.md mandates DOCUMENTDB_URI env var but model credentials (e.g. OPENAI_API_KEY) are not specified in prompt/skill.md.
- A .env.example lists every setting with placeholder values — at risk: skill.md asks to use .env.example but does not enumerate all required env vars.
- The vector index dimensions match the embedding model's output — at risk: embedding model not specified so dimensions cannot be assuredly matched.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — at risk: neither index parameters nor README guidance provided.
- One database client is created and reused across requests — at risk: connection pooling/reuse is not specified in prompt or skill.md.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — at risk: no seed files or idempotent seed script specified.
- /search returns a clear error for an empty query and when the embedding call fails — at risk: error handling requirements are not in the prompt or skill.md.
- Search results include the similarity score — at risk: prompt asks for matched entries but does not explicitly require including similarity scores in results.
- Dependencies are pinned in requirements.txt — at risk: pip environment is available but requirements pinning is not specified.
- Unit tests run without a live cluster — at risk: no test strategy or mocking is specified for unit tests.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — at risk: skill.md provides an existing cluster but no infra-as-code is included in prompt or skill.md.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — at risk: README content requirements are not included in the prompt or skill.md.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — at risk: naming convention is not enforced in the prompt or skill.md.

## Questions for the prompt author

- Which embedding model and provider should be used (name and expected embedding dimension)?
- Which chat / LLM model should generate the plain-language risk narrative (provider and model name)?
- Which MongoDB-compatible Python driver and version should the sample use (e.g., pymongo and version pin)?
- Should the sample expose an API (e.g., FastAPI /search endpoint), a CLI, or a simple script for the review cycle?
- Do you want real sanctions/adverse media sample data or synthetic dummy data in the repository? Any preferred format or size?

## Contradictions and missing references

- The starter prompt says "Using the DocumentDB skill", but the installed_skills list is empty; however a run-environment skill.md was supplied. Clarify whether the DocumentDB skill is available to the builder as an installed skill.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "embeds correspondent bank entity profiles, stores the vectors in DocumentDB, and searches against embedded sanctions list and adverse media entries on each review cycle"; "return a risk score, matched entries, and a plain-language risk narrative" | - | - | Functional goal and expected outputs are clearly stated. |
| Workflow type | specified | no | "build a Python LangChain agent" | - | - | Single-agent using LangChain is explicit. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | Run environment (skill.md) | Use a modern Python 3.x runtime (assume Python 3.10 or 3.11) with a virtual environment; implement with pip/venv. | Language is given but no specific Python version is specified; skill.md only says python/pip resolve to a venv. |
| Driver and version | missing | no | - | - | Use the MongoDB-compatible Python driver pymongo, pinned to a current stable series compatible with MongoDB 7.0 (e.g. pymongo>=4.3,<5.0). | Prompt and skill.md do not name or pin a specific driver or version; builder will pick pymongo by convention. |
| Target service and tier | covered_by_skill | no | - | Run environment (skill.md) | - | skill.md supplies an existing vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF support) and DOCUMENTDB_URI env var. |
| Authentication and secrets | covered_by_skill | no | - | Run environment (skill.md) | - | skill.md instructs the connection string is in DOCUMENTDB_URI and must not be written into files; use .env.example placeholders. |
| Data model | ambiguous | no | "embeds correspondent bank entity profiles"; "sanctions list and adverse media entries" | Run environment (skill.md) (provides database name 'sample_banking_11') | Create collections named 'correspondents', 'sanctions', and 'adverse_media' in database 'sample_banking_11'. Documents include fields: _id, name/title, metadata, embedding (vector as list/array), source, date, and any provenance fields. | Database name is provided by skill.md, but collection names and document shapes are not specified; builder will pick reasonable names/fields. |
| Sample data | missing | no | - | Run environment (skill.md) (asks to load sample data during verification) | Include a small synthetic sample dataset (few correspondents, a few sanctions entries and adverse-media snippets) in repository (e.g. data/*.json) and provide a seed script to load it. | No data source, size, licence, nor concrete seed files are supplied; the builder must create synthetic samples. |
| Queries and indexes | ambiguous | no | "stores the vectors in DocumentDB, and searches against embedded sanctions list and adverse media entries" | Run environment (skill.md) (states cluster supports DiskANN, HNSW and IVF vector indexes and asks to create collections and indexes in verification) | Create a cosmosSearch vector index (choose vector-hnsw by default) on the embedding field named 'embedding' with dimensions matching the embedding model (assume 1536 dims if using OpenAI text-embedding-3-small). Use $search / cosmosSearch vector query from the database for similarity search. | Index kind/type support is provided by skill.md, but index parameters and exact field names/dimensions are not specified. |
| AI components | missing | no | "LangChain agent" and "embeds ... profiles" | - | Use OpenAI embeddings (text-embedding-3-small, 1536 dims) via LangChain's embeddings interface, and use an OpenAI chat model (e.g., gpt-4o-mini or gpt-4o) via LangChain to generate the plain-language risk narrative. API keys come from environment variables (e.g. OPENAI_API_KEY). | No embedding or chat model/provider is specified; this is a key implementation choice a builder will make. |
| App surface | ambiguous | no | "build a Python LangChain agent" (no UI/CLI specified) | - | Implement a small HTTP API (FastAPI) exposing a /search (or /review) endpoint that accepts a correspondent identifier or profile and returns JSON with risk_score, matches (with similarity scores), and risk_narrative. | Prompt does not specify CLI vs API vs UI; common sample pattern is an API route; reference requirements mention /search but the prompt did not. |
| Provisioning and deployment | covered_by_skill | no | - | Run environment (skill.md) | Do not provision new DocumentDB clusters; use the provided cluster. The sample will not include cluster creation steps unless run policy permits writes. | skill.md explicitly discourages provisioning another cluster and instructs using the provided cluster. |
| Run and test instructions | missing | no | - | Run environment (skill.md) (gives high-level verification steps but no concrete commands or unit test guidance) | Provide a README with commands: pip install -r requirements.txt; export env vars per .env.example; python scripts/seed.py; uvicorn main:app; tests use pytest with mocking for DB and embedding calls. | Detailed run commands and unit test setup are not provided. |
| Definition of done | specified | no | "The agent should return a risk score, matched entries, and a plain-language risk narrative for each correspondent reviewed." | - | - | Functional acceptance criteria are stated for the main feature. |
| Constraints and non-goals | ambiguous | no | - | Run environment (skill.md) (contains constraints like never write connection string, do not provision cluster) | Keep dataset small to avoid large index choices and costs; do not attempt to provide production HA or infra-as-code for the real cluster. | Some constraints are in skill.md (secrets, no provisioning), but other constraints (cost limits, non-goals) are not specified. |
| Repository conventions | ambiguous | no | - | Run environment (skill.md) (asks for .env.example and not to write real secrets; provides database name) | Repository layout: README.md, src/ package, scripts/seed.py, requirements.txt (pinned), .env.example, tests/ with pytest, and a sample data/ directory. | skill.md suggests some conventions (.env.example, DB name) but not full conventions like pinned deps or exact layout. |
