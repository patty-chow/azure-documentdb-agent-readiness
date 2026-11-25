# 1. Prompt review: 01-product-catalog-with-vector-search

**Verdict: sufficient_with_assumptions**

The prompt clearly defines a Flask product-catalog app with vector search, the embedding model, index type, /search endpoint and top-k behavior. The provided run-environment skill.md supplies the live cluster connection details and the target database. Many implementation details (Python version, Mongo driver and version, env var names for OpenAI, collection name, seed data size, idempotent seed script, tests, README, infra) are not specified and will be decided by the builder; these are not blocking but will be assumed by the builder.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Queries and indexes, AI components, App surface |
| Covered by a skill | 3: Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 3: Workflow type, Language and runtime, Data model |
| Missing: builder will guess | 6: Driver and version, Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. — model creds env var not specified by prompt or skill.md (skill.md supplies DOCUMENTDB_URI but not embedding credentials).
- A `.env.example` lists every setting with placeholder values. — prompt asks secrets not be written but does not say to include .env.example; skill.md mentions use but doesn't provide one.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. — prompt sets index kind/dimensions but not parameters or guidance; no skill covers this.
- One database client is created and reused across requests. — prompt doesn't specify connection reuse; no skill enforces it.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. — prompt asks creation and loading but does not require idempotence; no skill covers it.
- /search returns a clear error for an empty query and when the embedding call fails. — prompt requires endpoint behavior but not explicit error handling; no skill covers it.
- Search results include the similarity score. — prompt requires top-10 results but does not explicitly require returning similarity scores; no skill covers it.
- Dependencies are pinned in `requirements.txt`. — prompt doesn't require pinned dependencies; no skill covers it.
- Unit tests run without a live cluster. — prompt doesn't discuss tests or how to mock the cluster; no skill covers it.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. — prompt/skill.md indicate a live cluster is provided and do not request IaC; reference expects infra but neither prompt nor skill implements it.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. — prompt does not specify README contents; no skill provides one.

## Questions for the prompt author

- Should the sample rely on an agent/skill framework, or should it be a conventional Flask app? (The prompt references a 'DocumentDB skill' but none is installed.)
- Which environment variable name should be used for the embedding provider API key (e.g. OPENAI_API_KEY)?
- Do you require the embeddings to be stored as BSON binary vectors specifically, or as a numeric array field compatible with the cosmosSearch vector index? (This changes storage/indexing code.)
- Which Python version and MongoDB driver/version should the sample target (e.g. Python 3.10 and pymongo==4.3.3)?
- Should the repository include infrastructure-as-code to provision the cluster, or must it rely on the existing cluster only?

## Contradictions and missing references

- The starter prompt begins "Using the DocumentDB skill" but installed_skills is empty; no such skill is available to the builder.
- Prompt requests storing embeddings as "BSON binary vectors" while the reference requirements recommend storing the vector in a form the cosmosSearch index can index (e.g. numeric array). The prompt and reference disagree on storage form; the run environment does not settle which storage form must be used.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python Flask app with a product catalog stored in DocumentDB... expose a /search endpoint that takes a natural language query... returns the top 10 semantically similar products." | - | - | Business goal, user scenario and what the sample demonstrates are stated. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Implement as a normal single-process Flask web app (no agent framework); treat "DocumentDB skill" as an instruction to use the DocumentDB cluster rather than an installed agent. | Prompt references a 'skill' (suggesting an agent), but no agent framework or skill is installed to use; builder will likely produce a conventional app. |
| Language and runtime | ambiguous | no | "build a Python Flask app" | Run environment (skill.md) indicates python and pip are available on the developer machine | Use a modern Python 3.x; assume Python 3.10 (or 3.11) for packaging and compatibility. | Prompt specifies language and framework but not Python version; skill.md only says 'python' is present. |
| Driver and version | missing | no | - | - | Use the synchronous pymongo driver (pymongo>=4.0, pin to a specific minor version in requirements.txt, e.g. pymongo==4.3.3). | Prompt doesn't name the MongoDB-compatible Python driver or version; skill.md does not specify either. |
| Target service and tier | covered_by_skill | no | - | Run environment (skill.md) provides: vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes), and DOCUMENTDB_URI env var. | - | Cluster and database are present and described in skill.md; sample must use that live cluster and DB sample_retail_01. |
| Authentication and secrets | covered_by_skill | no | "Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." (skill.md) | Run environment (skill.md) specifies DOCUMENTDB_URI in env and rules about secrets | For embedding model credentials, assume an OpenAI API key provided via OPENAI_API_KEY in env and referenced in .env.example. | The DocumentDB connection secret is specified by skill.md; the prompt does not specify where the embedding/model credentials come from, so builder will assume standard OPENAI env var. |
| Data model | ambiguous | no | "Product titles and descriptions" stored in DocumentDB; embeddings stored on the product document | Run environment (skill.md) specifies database name sample_retail_01 | Create a collection named 'products' in database sample_retail_01; each document contains at least fields: _id, title (string), description (string), embedding (vector field or binary depending on strategy), and any metadata like price or category as optional. | Collection name, exact document schema, and whether additional fields exist are not specified. |
| Sample data | missing | no | - | - | Provide a small static seed dataset (e.g. 20–50 sample product JSON documents included in the repo) and a seed script to load them; license the data as MIT or public-domain-like placeholder. | Prompt doesn't indicate source, size or how data is loaded. |
| Queries and indexes | specified | no | "store them as BSON binary vectors, create a vector-ivf index" and "create a vector-ivf index, with dimensions matching text-embedding-ada-002 (1536)." | Run environment (skill.md) confirms cluster supports IVF vector indexes | Create the cosmosSearch / vector-ivf index on the embedding field with dimension 1536 and sensible IVF parameters for a small sample. | Prompt specifies the index kind and dimensions. (See contradictions: prompt requests storing embeddings as BSON binary vectors while the reference suggests numeric arrays; builder must choose an indexable storage form supported by the cluster.) |
| AI components | specified | no | "Embed product titles and descriptions using text-embedding-ada-002" and "/search embeds the incoming query with text-embedding-ada-002" | - | Use OpenAI's 'text-embedding-ada-002' via the openai Python package; the output dimension is 1536. | Model and dimensions are stated; the provider is implied by the model name but credentials/SDK usage are not specified. |
| App surface | specified | no | "build a Python Flask app" and "expose a /search endpoint that takes a natural language query... returns the top 10 semantically similar products." | - | Implement /search as a POST that accepts JSON {"q": "..."} and returns top 10 products including similarity score and product fields. | Framework and endpoint are specified; exact request/response shape is left to the builder. |
| Provisioning and deployment | covered_by_skill | no | - | Run environment (skill.md) forbids provisioning another cluster unless policy allows writes; instructs verifying against the live cluster rather than creating local gateway. | Do not create cloud infrastructure; use the provided cluster and supply no IaC for the cluster (no new resources will be provisioned). | Prompt does not request infra; skill.md constrains provisioning. |
| Run and test instructions | missing | no | - | Run environment (skill.md) says to verify against the live cluster and record what was executed | Add a README with commands to pip install -r requirements.txt, run seed.py to load data and create index, start Flask app with FLASK_APP=app.py flask run, and example curl to call /search. | Exact commands, success criteria and tests are not provided by the prompt. |
| Definition of done | missing | no | - | - | Define done as: seed script ran without error, index created, /search returns top-10 results for a sample query and includes similarity scores; README documents steps and env variables. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | missing | no | - | Run environment (skill.md) implies a constraint: do not provision another cluster unless allowed | Keep costs low by using existing cluster only; do not attempt to provision additional Azure resources. | No cost or non-goal guidance in the prompt beyond the run-environment restriction. |
| Repository conventions | missing | no | - | - | Follow common conventions: requirements.txt pinned, .env.example with placeholders (DOCUMENTDB_URI, OPENAI_API_KEY), seed/ scripts in /scripts or /tools, README.md with sections, use 'Azure DocumentDB' in docs. | Prompt does not prescribe repo layout or conventions; reference requirements list these as expectations. |
