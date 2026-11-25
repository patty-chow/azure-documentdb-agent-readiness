# 1. Prompt review: 07-voice-of-customer-sentiment-hub

**Verdict: sufficient_with_assumptions**

The starter prompt is actionable: it clearly states the goal (single LangChain Python agent), the use of Beanie ODM, and the aggregation requirements. Several implementation details are left to the builder (Python version, exact embedding/chat models, API surface, index parameters, seed/data/test infra). Installed DocumentDB skills cover driver, connection and vector/indexing best practices, so the builder can sensibly proceed, but they will make defaults and assumptions for AI model choices, index dimensions, and repository scaffolding.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Data model |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Authentication and secrets, App surface, Definition of done |
| Missing: builder will guess | 6: Sample data, AI components, Provisioning and deployment, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — prompt/skills do not require or provide it; builder must add it.
- The vector index dimensions match the embedding model's output — embedding model is unspecified so dimensions are not defined.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — index parameter selection and README guidance are not requested explicitly.
- One database client is created and reused across requests — the documentdb-driver skill recommends singleton pattern (so this is likely but not explicitly required by the prompt).
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt does not ask for an idempotent seed script.
- /search returns a clear error for an empty query and when the embedding call fails — error-handling behavior not specified in the prompt.
- Search results include the similarity score — prompt asks for embeddings and storage but does not say to include score in search results.
- Dependencies are pinned in `requirements.txt` — prompt does not say to pin versions; common practice but at risk.
- Unit tests run without a live cluster — prompt doesn't demand offline-capable tests or mocking strategy.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt/skill.md assume an existing cluster; provisioning IaC is not requested.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a README, so completeness is at risk.
- Model credentials come from environment variables — DocumentDB URI is specified in DOCUMENTDB_URI in skill.md, but AI model credentials are not defined in the starter prompt or skill.md.

## Questions for the prompt author

- Which embedding and LLM models (provider and exact model names) should be used for extraction and embeddings? (This determines embedding dimension and vector-index shape.)
- Do you want an HTTP API (e.g., FastAPI) or a CLI/script interface for ingestion and aggregation demos?
- Which Python version should the sample target (3.10, 3.11)?
- Should the repository include infrastructure-as-code (Bicep/Terraform) to create the DocumentDB cluster, or rely on the provided cluster only?
- Do unit tests need to run without a live cluster (i.e., via mocks/fakes), and should tests be included in the sample?
- Given the documentdb-driver guidance, should the sample use Motor (traditional Beanie dependency) or PyMongo's AsyncMongoClient pattern (and adapt Beanie usage if possible)?
- What vector-index subtype and parameters do you prefer for the sample (DiskANN/HNSW/IVF) and what target scale should the README document be tuned for?

## Contradictions and missing references

- documentdb-driver skill recommends using PyMongo's AsyncMongoClient for new async Python code and explicitly notes Motor deprecation. The starter prompt requires Beanie ODM; Beanie historically depends on Motor. This creates a practical tension the builder must resolve (use Motor with Beanie despite deprecation, or adapt Beanie to PyMongo async if supported).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | ingests customer feedback from multiple channels, uses prompt engineering to extract sentiment, key topics, and a verbatim quote, embeds the text, and stores the enriched document in DocumentDB. Build aggregation pipelines that surface net sentiment trends by channel, topic, and time period. | - | - | Business problem and demonstration are clear. |
| Workflow type | specified | no | build a Python LangChain agent using Beanie ODM | - | - | Single-agent LangChain flow is explicitly requested. |
| Language and runtime | ambiguous | no | Python LangChain agent | - | Builder will target a modern Python 3.x (commonly 3.10 or 3.11) virtualenv; code and requirements will assume CPython 3.11-compatible dependencies. | Prompt and skill.md say `python`/`pip` exist in a virtual env, but no explicit Python version is given. |
| Driver and version | ambiguous | no | using Beanie ODM | documentdb-driver | Builder must choose Beanie-compatible async driver. Possible choices: Motor (traditional for Beanie) or PyMongo's new AsyncMongoClient if Beanie supports it; most builders will use Beanie + Motor despite deprecation guidance unless they rewrite Beanie init for PyMongo async. | documentdb-driver recommends singleton MongoClient and recommends PyMongo's AsyncMongoClient for new async Python code; this conflicts with Beanie's historical Motor dependency — see contradictions. |
| Target service and tier | specified | no | skill.md: A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable; connection string in DOCUMENTDB_URI. | - | - | Run environment already provides an M30 cluster; builder should use the database sample_customer_360_07 as specified in skill.md. |
| Authentication and secrets | ambiguous | no | skill.md: connection string is in the environment variable DOCUMENTDB_URI; do not write it into files or logs. | - | The builder will read DocumentDB connection URI from DOCUMENTDB_URI and will expect embedding/LLM credentials from standard env vars (e.g., OPENAI_API_KEY or AZURE_OPENAI_KEY and model names via EMBEDDING_MODEL / LLM_MODEL). | DocumentDB connection secret is specified in skill.md; AI model credentials are not specified in the starter prompt or skill.md. |
| Data model | specified | no | Define the enriched feedback document as a Beanie ODM model and persist it to Azure DocumentDB ... holding the original text, the source channel, when the feedback was received, the extracted sentiment, key topics and verbatim quote, and the embedding. | - | Collection will be single collection (e.g., `feedback` or `enriched_feedback`) in DB `sample_customer_360_07`. No shard key unless data scale forces sharding. | Fields required are explicitly listed; physical collection name and shard strategy are left to builder. |
| Sample data | missing | no | - | - | Builder will include a small synthetic seed dataset (a few dozen items) spanning multiple channels (email, chat, survey) and several topics; provide a seed script that inserts without duplicates. | Prompt asks to accept feedback from more than one channel but doesn't provide sample data or a seed script. |
| Queries and indexes | covered_by_skill | no | Build aggregation pipelines that surface net sentiment trends by channel, topic, and time period; store the embedding in the document. | documentdb-indexing / documentdb-vector-search | Builder will create a vector index (DiskANN recommended for M30 / production) with dimensions matching chosen embedding model; textSearch indices or `$search` will be used for text lookups. Exact index parameters (`lBuild`, `lSearch`, `maxDegree`) will follow documentdb-vector-search guidance and be documented in README. | Aggregation pipelines are requested; skills provide index-type guidance and vector-index tuning but prompt leaves the exact shapes and parameters to the builder. |
| AI components | missing | no | uses prompt engineering to extract sentiment, key topics, and a verbatim quote, embeds the text, ... | - | Builder will use LangChain for prompts and embeddings with a mainstream provider (e.g., OpenAI via OPENAI_API_KEY). They will put model names in env vars (EMBEDDING_MODEL, LLM_MODEL) and record the embedding dimension accordingly. Defaults often used: OpenAI embedding models via LangChain and a GPT-family chat model for prompt engineering. | Prompt requires extraction + embeddings, but does not name embedding/LLM models, nor dimensionality. |
| App surface | ambiguous | no | build a Python LangChain agent ... that ingests customer feedback ... and stores the enriched document | - | Builder will likely implement a small API (e.g., FastAPI) with endpoints like /ingest (POST single or batch), /seed (populate sample data), and /aggregations (return sentiment-by-channel/topic/time), plus a CLI script for local ingestion and a script to run the agent interactively. | Starter prompt does not mandate CLI vs HTTP vs UI; agent framework is LangChain but surface is unspecified. |
| Provisioning and deployment | missing | no | Using the DocumentDB skill, build ... (skill.md: a cluster is already provisioned and reachable). | documentdb-azure-deployment | Builder will not create new cloud resources (the run environment already provides a cluster). If IaC is needed, documentdb-azure-deployment skill exists and can be used later to add Bicep/Terraform. | Prompt / run environment pre-supplies a cluster; the starter prompt doesn't ask to include IaC in the repo. |
| Run and test instructions | missing | no | - | - | Builder will add a README with steps: pip install -r requirements.txt, copy .env.example to .env with DOCUMENTDB_URI and model keys, run seed script, start FastAPI server, and run sample aggregation queries. | No explicit run/test commands are in the starter prompt; skill.md includes runtime expectations which the builder should follow. |
| Definition of done | ambiguous | no | store the enriched document ... Build aggregation pipelines ... that surface net sentiment trends by channel, topic, and time period. | - | Accepting criteria will be: sample data is ingested and persisted with required fields, embeddings stored and indexed, aggregation pipelines run and return sensible net-sentiment outputs, and a short demo script shows these end-to-end. | Prompt implies high-level acceptance but does not enumerate testable checks. |
| Constraints and non-goals | missing | no | - | - | Builder will avoid provisioning new clusters and will not implement large-scale production features (no HA topology changes, limited sample sizes to keep cost low). | No cost / non-goals are specified; skill.md gives some operational constraints (do not write the DOCUMENTDB_URI to files). |
| Repository conventions | missing | no | - | - | Builder will follow common patterns: top-level README, src/ package, tests/ unit tests, requirements.txt, .env.example, and a seed/fixtures script. Dependencies will likely be pinned in requirements.txt but the prompt doesn't require it. | Starter prompt does not specify folder layout or naming conventions. |
