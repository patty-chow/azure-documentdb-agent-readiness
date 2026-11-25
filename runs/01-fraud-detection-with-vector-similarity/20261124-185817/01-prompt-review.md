# 1. Prompt review: 01-fraud-detection-with-vector-similarity

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear goal (Python LangChain agent that embeds transactions, stores fraud-pattern vectors in a vector-ivf index, runs vector search, returns a numeric fraud risk score and an NL explanation) and the provided skill_md describes the live cluster to use. The installed DocumentDB skills (especially documentdb-vector-search, documentdb-driver, and connection/modeling skills) supply much of the technical guidance, but several concrete choices are left unspecified (Python version, embedding model & dimensions, binary-embedding format and metric, index tuning, app surface and run/test conventions). The builder can start, but will make defaults in those areas; the review lists the assumptions the builder will most likely make and which reference requirements are at risk.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 7: Language and runtime, Data model, Sample data, Queries and indexes, App surface, Run and test instructions, Repository conventions |
| Missing: builder will guess | 4: Driver and version, AI components, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Binary embedding format: The reference requires binary embedding format for storage and queries; the prompt does not mention binary and installed skills do not document a binary embedding workflow — builder will likely default to float embeddings.
- .env.example lists every setting: The prompt/skill_md mention DOCUMENTDB_URI but do not require a complete .env.example; the builder may omit some settings required by embeddings or external APIs.
- Vector index dimensions must match embedding model output: No embedding model or dimension is specified, so index dimensions may be chosen inconsistently with the model.
- Index parameters and README guidance: Specific IVF tuning parameters and instructions for scaling up are not specified; the builder will pick defaults for the sample and may not document how to change them for larger data.
- Idempotent seed script: The reference expects a seed script that can run twice without duplicating data; prompt asks to load patterns but does not require idempotence explicitly.
- Error handling for /search: The reference expects clear errors for empty queries and embedding failures; the prompt does not specify API surface or error behavior.
- Dependencies pinned in requirements.txt: The prompt does not require pinned versions; the builder may or may not pin dependencies.
- Unit tests that run without a live cluster: The reference requests offline unit tests; the prompt/skill_md focus on verifying against the live cluster and do not mandate mocked tests.
- Infrastructure-as-code to provision the cluster: The reference asks for IaC, but prompt and skill_md instruct using the existing live cluster and do not include IaC; this is likely missing.
- README completeness: The reference needs a README covering what the sample shows, prerequisites, setup, run, and clean-up; the prompt doesn't require a full README and the builder may provide a minimal one only.

## Questions for the prompt author

- Do you require the embeddings to be stored and queried in a binary embedding format (bit/byte-level binary) and use a binary similarity metric, or is a standard float-vector embedding (float32 arrays) acceptable? (This affects index type/params and how embeddings are serialized.)
- Which embedding provider/model should the sample use (e.g., a local sentence-transformers model such as all-MiniLM-L6-v2, or an external provider like OpenAI text-embedding-3-small)? Please specify model name and whether API keys are allowed in the environment.
- Which Python runtime should be targeted (e.g., 3.10 or 3.11)?
- Should the sample include infrastructure-as-code (Bicep/Terraform/az CLI) to provision the Azure DocumentDB cluster, or must it only use the existing cluster described in the skill_md? (skill_md suggests using the existing live cluster.)
- Do you require unit tests that run without a live cluster (mocked/memory) or is a live-cluster integration example sufficient?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent that encodes transaction features as embeddings, stores known fraud pattern vectors in a DocumentDB vector-ivf index ... return a fraud risk score and a natural language explanation" | - | - | Clear business problem and demonstration goals. |
| Workflow type | specified | no | "Python LangChain agent" | - | - | Single-agent LangChain is explicitly requested. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | documentdb-local-deployment | Use Python 3.10 (or 3.11) in a virtualenv as typical for current LangChain samples; pip/pip install works in that environment. | Prompt and skill_md imply Python is available but do not specify a version. |
| Driver and version | missing | no | - | documentdb-driver | Use the Python pymongo driver, pinned to a modern 4.x release compatible with MongoDB 7.0 (e.g., pymongo>=4.4,<5.0). Code will use a singleton MongoClient pattern per documentdb-driver guidance. | No explicit driver or version/range in prompt; driver best-practice skill gives pattern but not exact package/version to pin. |
| Target service and tier | specified | no | - | - | Use the existing live Azure DocumentDB cluster described in skill_md (compute tier M30, MongoDB 7.0 protocol, vector-capable). | skill_md explicitly describes the live, vector-capable cluster and forbids provisioning a new cluster. |
| Authentication and secrets | specified | no | - | - | Read the cluster connection string from env var DOCUMENTDB_URI and do not write secret values into files; follow skill_md instruction. | skill_md requires DOCUMENTDB_URI in environment and use of MCP profile for inspection. |
| Data model | ambiguous | no | "stores known fraud pattern vectors ... with explanatory metadata fields" | documentdb-data-modeling | Create a database sample_fintech_01 (per skill_md) with a collection named fraud_patterns containing documents: { _id: <id>, pattern_name: str, description: str, ts: ISO timestamp, vector: <binary blob>, model: <name>, dims: <int>, schemaVersion: 1 }. Optionally a transactions collection for logging; no sharding for the small sample. | Prompt requires metadata but not concrete field names, collection names, or shard key; the data-modeling skill gives principles but not exact schema. |
| Sample data | ambiguous | no | "stores known fraud pattern vectors" | documentdb-local-deployment | Use a small synthetic seed set (e.g., 5–20 fraud patterns) created by a seed script. No external dataset/license is required; the seed script inserts records with vectors computed from the chosen embedding model. | Prompt asks to store known patterns but does not specify source, size, or license. The developer will likely create synthetic examples and a small idempotent seed script. |
| Queries and indexes | ambiguous | no | "stores ... in a DocumentDB vector-ivf index" | documentdb-vector-search | Create a vector-ivf index via the DocumentDB API with dimensions matching the chosen embedding dim (e.g., 384 for a SentenceTransformer model or 1536 for OpenAI text-embedding-3-small). Use IVF parameters sized for small dataset (default nlist small), and use a float similarity metric (COS) unless binary embeddings are explicitly required. Verify index existence before insert using MCP or API. | documentdb-vector-search covers index types and how to create them, but the prompt leaves index parameters (dimensions, nlist, similarity) unspecified. The requirement for 'binary embedding format' in the reference is not addressed by the prompt or this skill. |
| AI components | missing | no | "encodes transaction features as embeddings" | - | Use a local/open-source embedding model such as sentence-transformers/all-MiniLM-L6-v2 (embedding dim 384) to avoid requiring cloud API keys; expose embedding as a callable function. Alternatively, the builder might default to OpenAI embeddings if an API key is provided, but the prompt gives no provider. | Prompt does not name an embedding model, dimensions, or where the model is called from; that materially affects index dimensions and storage format. |
| App surface | ambiguous | no | "LangChain agent" | - | Provide a CLI/demo script (e.g., run_agent.py or example.py) that demonstrates loading seed data and running a sample transaction through the LangChain agent, printing the fraud score and explanation to stdout. No web API required for the minimal sample. | Prompt requests an agent but does not specify whether to expose a CLI, REST API, or UI. |
| Provisioning and deployment | specified | no | - | - | Do not provision a new cluster; use the existing cluster described in skill_md. If IaC is added it's optional and must not create another live cluster by default. | skill_md explicitly instructs to use the existing live cluster and not to provision another unless allowed. |
| Run and test instructions | ambiguous | no | "The agent should return a fraud risk score and a natural language explanation" | documentdb-local-deployment | Include README with commands: pip install -r requirements.txt, copy .env.example to .env and fill DOCUMENTDB_URI, python seed.py, python run_agent.py. Tests: include a small integration example that runs against the live cluster; unit tests may be limited or mocked if offline support not requested. | Prompt asks for functionality but doesn't give precise CLI steps or test formats; skill_md instructs verification against the live cluster but not explicit commands. |
| Definition of done | missing | no | - | - | Builder will treat done as: code runs, seed script populates fraud_patterns into sample_fintech_01, agent encodes a sample transaction, vector search returns neighbors with similarity scores, a reproducible numeric fraud score is computed and printed with a human-readable explanation, and a README documents how to run the example. | No explicit acceptance criteria in the prompt; builder inferred the minimal visible outcomes. |
| Constraints and non-goals | missing | no | - | documentdb-security | No explicit cost constraints; follow skill_md restriction about not creating new clusters, do not store secrets in repository, and keep sample usage small to avoid cluster charges. | Prompt does not define cost, licensing, compliance or non-goals beyond secret handling guidance in skill_md. |
| Repository conventions | ambiguous | no | - | documentdb-local-deployment | Repository will include README.md, requirements.txt with pinned dependencies, .env.example with placeholders (DOCUMENTDB_URI, optionally EMBEDDING_MODEL or OPENAI_API_KEY), seed.py, agent code, and a tests/ directory containing at least an integration example. Use the name 'Azure DocumentDB' in README. | Prompt doesn't specify repository layout; skill_md implies env usage but not full conventions. |
