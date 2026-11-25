# 5. Best-practice audit: 01-fraud-detection-with-vector-similarity

**Verdict: pass_with_findings** (12 followed, 3 not assessable, 2 violated)

The repository is a compact, mostly-complete Python sample that demonstrates encoding transaction text to embeddings, storing them as documents, and running a $search/cosmosSearch vector query to compute a numeric fraud score plus a human-readable explanation. The builder implemented a singleton MongoClient, local sentence-transformers embeddings, an idempotent seed script (upserts), and a demo CLI script that computes risk and prints an explanation. Shortcomings: the prompt asked for a "Python LangChain agent" and a LangChain tool wrapper for vector search but the sample implements a standalone script (run_agent.py) and does not expose or register a LangChain Tool/Agent; index creation is not present in the code (the builder attempted MCP-managed index creation but the MCP write/management tools were disabled in this run); error handling around embedding failures is minimal; dependencies are not strictly pinned; no offline unit tests or IaC were included. Many of the expected DocumentDB best practices are present (env-driven connection string, client singleton, normalized vectors, embedding metadata saved with documents, $meta: 'searchScore' projection). The MCP verification attempts failed due to management/write tools being disabled in this run (events.jsonl shows ToolExecutionException with ENABLE_MANAGEMENT_TOOLS / ENABLE_WRITE_TOOLS opt-in errors).

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approving the build with readiness 'ready_with_gaps' is reasonable given the sample is functionally useful but had verification gaps and documentation omissions. The events and files support that the build is partial but deliverable. |
| D002 | I chose Python 3.10+ (use system Python 3.13 present) as the language/runtime for the sample. | readiness_report | sound | Choosing Python (system Python 3.13 available) is supported by the readiness report and the implementation is in Python. Events.jsonl shows the decision was logged (events entry at ~06:27:48). |
| D003 | I chose the Python pymongo driver (pymongo>=4.4,<5.0) for connecting to Azure DocumentDB. | model_default | sound | Choosing pymongo is appropriate for a Python MongoDB-compatible sample; the code uses pymongo and requirements.txt pins a compatible range. The decision was logged (events.jsonl). |
| D004 | I chose sentence-transformers/all-MiniLM-L6-v2 (local) with 384 dimensions for embeddings. | model_default | sound | Choosing sentence-transformers/all-MiniLM-L6-v2 (384 dims) for a local demo is consistent with the builder's intent to avoid cloud API keys. The choice is implemented (embeddings.py) and logged (events.jsonl). |
| D005 | I chose a vector-ivf index with dimensions=384 and numLists=1 for the sample fraud_patterns collection. | docs | sound | Choosing vector-ivf with dimensions=384 and numLists=1 is a defensible demo choice; events.jsonl shows the create_index attempt used those parameters. The index create failed because management tools were disabled in this run, not because the choice was incorrect. |
| D006 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | readiness_report | sound | Using DOCUMENTDB_URI from the environment is correct and implemented (docdb_client.py); the decision was logged and matches README/.env.example. |
| D007 | I chose deterministic, template-based explanations for the LangChain agent when an LLM key is not provided; if OPENAI_API_KEY is present the sample can optionally use OpenAI for richer explanations. | model_default | sound | Defaulting to deterministic, template-based explanations when an LLM API key is absent keeps the sample runnable without cloud LLM credentials. The code implements a template fallback in run_agent.py and the decision was logged. |
| D008 | I chose to use the documentdb MCP server tools to create the vector index and insert sample documents for verification rather than running the local seed script, because DOCUMENTDB_URI may not be set in this environment. | readiness_report | questionable | The builder chose to use the MCP server tools for data-plane verification because DOCUMENTDB_URI might be absent. Events.jsonl shows the MCP read tool (list_databases) worked, but management/write tools failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true' and 'Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true'. The decision statement that 'MCP tools are available' is partially true (read-only was available) but the write/management calls required opt-in and therefore the verification strategy was fragile. |

Documentation gaps: 7 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 1 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 15 | Public and discoverable. |

#### On the checklist, no public source found

| Topic | Searched | Description |
|---|---|---|
| .env completeness | Searched repository for .env.* and sample env templates; searched docs for recommended sample env variables (embedding model name, index knobs). Found no canonical .env.example for this sample. | .env.example lists every required setting with placeholder values.<br>**What would help:** A public example .env template listing connection, model, index and optional LLM keys so an agent can confirm all required settings. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Schema versioning | Use an explicit, consistent document schema for fraud/transaction data and include schemaVersion for migrations. | A short public page showing recommended schema fields for transaction+embedding documents (transaction_id, account_id, timestamp, features, embedding, model, dims, schemaVersion). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Instantiate and reuse a single MongoClient per process (module-level singleton) instead of creating a client per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS on connection | Always connect with TLS enabled and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Connection tuning | Tune client connection-pool and timeout options to match workload. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Env secrets | Keep the cluster connection string and any credentials out of source control and read DOCUMENTDB_URI from environment variables or a secrets store. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Document size | Keep documents small and move very large raw payloads to an external blob store. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Create vector index | Create a cosmosSearch vector index on the vector field and declare algorithm-specific options (kind, dimensions, similarity, algorithm params). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index) |
| Vector query projection | Use $meta:'searchScore' and returnStoredSource:true to obtain searchScore and matched document for explanations. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search) |
| Normalize embeddings for COS | Ensure all embeddings in a collection use the same dimension and, when using COS, normalize vectors to unit length at ingestion and store model name + dimensions. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Index tuning for sample size | Tune search-time ANN parameters and keep lSearch >= k; choose conservative topK and adjust ef/probe for recall vs latency. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Idempotent seed upserts | Make seeding scripts idempotent by using upsert/replaceOne with upsert:true. | [Manage a document in Azure Cosmos DB for MongoDB using JavaScript](https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-javascript-manage-documents#update-a-document) |
| Avoid logging sensitive data | Do not log raw embeddings, transaction PII, or DB credentials in application logs. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Store embedding metadata | Store embedding-model metadata (model name, version, dims) with each inserted vector. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Limit candidate set | Limit the candidate set (topK) used to compute scores; compute fraud risk from a small set of nearest neighbors (e.g., top 5–10). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Cluster tier sizing | Provision cluster compute/tier to match expected search and ingestion load (choose an appropriate tier such as M30+ for production vector workloads). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Vector value type | Vectors must be a number[] in documents to be indexed by a cosmosSearch vector index. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| .env.example lists every required setting with placeholder values. | authentication | app/.env.example: only DOCUMENTDB_URI and OPENAI_API_KEY are present; no MODEL_NAME, MODEL_DIMS, INDEX parameters or toggles are listed. | Add MODEL_NAME, EMBEDDING_DIMS (or MODEL_DIMS), INDEX_KIND, INDEX_NUMLISTS and optional toggles to .env.example. | checklist only (no public address recorded) |
| Create a cosmosSearch vector index on the vector field and declare algorithm-specific options (kind, dimensions, similarity, algorithm params). | indexing | No createIndexes call in repo; events.jsonl shows attempted documentdb_create_index calls that failed with 'Management tools are disabled by default' (events.jsonl: entry at 06:28:57 and 06:29:05). | Add idempotent createIndexes JSON via pymongo's database.command() or a create_index helper in seed.py using cosmosSearchOptions (kind:'vector-ivf', dimensions=len(vec), similarity:'COS', numLists:1). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Tune client connection-pool and timeout options to match workload. | connection_handling | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Tune search-time ANN parameters and keep lSearch >= k; choose conservative topK and adjust ef/probe for recall vs latency. | vector_search | - | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Provision cluster compute/tier to match expected search and ingestion load (choose an appropriate tier such as M30+ for production vector workloads). | provisioning | - | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Instantiate and reuse a single MongoClient per process (module-level singleton) instead of creating a client per request. | connection_handling | docdb_client.py:4-15 implements a module-level _client and get_client() singleton. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always connect with TLS enabled and do not disable certificate validation in production. | connection_handling | .env.example:2 suggests tls=true and docdb_client.py relies on the connection string (docdb_client.py:10-14). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Keep the cluster connection string and any credentials out of source control and read DOCUMENTDB_URI from environment variables or a secrets store. | authentication | docdb_client.py:10 reads DOCUMENTDB_URI from the environment; .env.example contains a placeholder (app/.env.example:1-4). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Use an explicit, consistent document schema for fraud/transaction data and include schemaVersion for migrations. | data_modeling | seed.py:44-52 includes model, dims and schemaVersion fields in each inserted document. | prior_knowledge_only (no public address recorded) |
| Keep documents small and move very large raw payloads to an external blob store. | data_modeling | seed.py creates compact pattern docs with small metadata and vector; no large raw payloads are embedded (seed.py:44-52). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Use $meta:'searchScore' and returnStoredSource:true to obtain searchScore and matched document for explanations. | queries | run_agent.py pipeline uses {'$search': {'cosmosSearch': {...}, 'returnStoredSource': True}} and projects similarityScore via {$meta: 'searchScore'} (run_agent.py:21-24). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search) |
| Ensure all embeddings in a collection use the same dimension and, when using COS, normalize vectors to unit length at ingestion and store model name + dimensions. | vector_search | embeddings.embed_text normalizes embeddings via model.encode(..., normalize_embeddings=True) (embeddings.py:16); seed.py stores 'model' and 'dims' with each doc (seed.py:48-51). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Make seeding scripts idempotent by using upsert/replaceOne with upsert:true. | seeding | seed.py:53 uses coll.replace_one({'pattern_name': ...}, doc, upsert=True) to avoid duplicates. | [Manage a document in Azure Cosmos DB for MongoDB using JavaScript](https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-javascript-manage-documents#update-a-document) |
| Do not log raw embeddings, transaction PII, or DB credentials in application logs. | security | Source files do not write embeddings or credentials to logs or print them; seed.py prints only 'Upserted pattern' and run_agent.py prints risk and explanation but not raw embedding vectors (seed.py:55; run_agent.py:65-66). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Store embedding-model metadata (model name, version, dims) with each inserted vector. | data_modeling | seed.py:48-51 includes 'model' and 'dims' fields in each document. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Limit the candidate set (topK) used to compute scores; compute fraud risk from a small set of nearest neighbors (e.g., top 5–10). | vector_search | run_agent.py uses k=5 in vector_search() and compute_risk computes score from top similarity (run_agent.py:18-27, 30-38). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Vectors must be a number[] in documents to be indexed by a cosmosSearch vector index. | vector_search | seed.py stores Python float lists (seed.py:48); embeddings.embed_text returns float list via vec.tolist() (embeddings.py:16-18). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index) |

### Reference requirements

8 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| A Python LangChain agent is the single entry point: it accepts a new transaction and runs the fraud check for it. | not_met | builder_error | run_agent.py:1-11, run_agent.py does not import or instantiate LangChain agent APIs, it is a CLI script (main) that calls embed_text and vector_search directly. | Wrap the existing vector_search/compute_risk/explain functions in a LangChain Tool and provide a minimal LangChain Agent instantiation in run_agent.py (or add a separate agent.py that registers the tool and exposes the same CLI). |
| A cosmosSearch index of kind vector-ivf is created in code on that embedding field, with dimensions matching the embedding model's output (similarity e.g. COS). | not_met | builder_error | No createIndexes / createSearchIndexes call in repository files; events.jsonl shows attempted documentdb_create_index calls that failed (ToolExecutionException: Management tools are disabled) (events.jsonl entries at timestamps ~06:28:57 and 06:29:05). | Add idempotent index-creation code (e.g., a create_index() in seed.py that issues the createIndexes command with cosmosSearchOptions including kind:'vector-ivf' and dimensions=len(vec)) so the sample can create/verify the index from code. |
| A LangChain tool performs the vector search against Azure DocumentDB with a $search / cosmosSearch query using the new transaction's embedding as the query vector, and returns the similar historical cases. | not_met | builder_error | run_agent.py:18-27 implements vector_search using pymongo.aggregate with $search/cosmosSearch but it is not exposed as a LangChain Tool (no langchain imports or Tool wrapper). | Wrap vector_search as a LangChain Tool (or Retriever) and register it in the sample agent; add an example of calling the tool from a LangChain Agent in the CLI. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No tests found in repository; no mocking or offline test harness present. | Add pytest-based unit tests that mock pymongo (e.g., with mongomock or monkeypatching) to validate compute_risk, explain, and embed logic without a live cluster. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/Terraform) files present in the repository; readiness findings described how to use Microsoft.DocumentDB/mongoClusters but no template is included. | Add a minimal IaC example (Bicep or Terraform) that creates an Azure DocumentDB mongoClusters resource (Microsoft.DocumentDB/mongoClusters) with cost-saving defaults, and reference it from the README. |
| On each new transaction the agent invokes that vector search tool and derives a fraud risk score from the returned similar cases (e.g. based on how closely they match). | partly_met | builder_error | run_agent.py:59-63 (the CLI script calls embed_text(), vector_search(), compute_risk() to derive a numeric score). The flow exists but it is not performed via a LangChain agent/tool. | Have the LangChain Agent call the registered LangChain Tool that performs the vector search, or document that the CLI is a minimal agent implementation; prefer adding the LangChain Tool wrapper so the sample matches the starter prompt. |
| .env.example lists every setting with placeholder values. | partly_met | prompt_silent | app/.env.example:1-4 includes DOCUMENTDB_URI and OPENAI_API_KEY but does not list MODEL_NAME, EMBEDDING_DIMS or index parameters used by the sample. | Add placeholders to .env.example for MODEL_NAME, EMBEDDING_DIMS (or MODEL_DIMS), INDEX_KIND, INDEX_NUM_LISTS and any other toggles (e.g., USE_LOCAL_EMBEDDINGS, ENABLE_LLM_EXPLANATIONS). |
| The vector index dimensions match the embedding model's output. | partly_met | tool_unavailable | embeddings.py uses all-MiniLM-L6-v2 (384 dims) (embeddings.py:7-11, 14-18). The builder recorded a decision to create an IVF index with dimensions=384 (decisions.jsonl / events.jsonl D005), and events show attempted index creation with dimensions=384 (events.jsonl). However, index creation did not succeed in this run and there is no createIndexes call in the repo. | Create the index from code in seed.py (use len(vec) for dimensions) and document the match; if you keep MCP-based verification, add a fallback createIndexes path in code. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | partly_met | prompt_silent | decisions.jsonl D005 documents use numLists=1 for a demo and README.md:41-44 and builder_report.open_issues mention numLists=1 and advise changing for production. README notes index tuning but does not provide ranges or explicit step-by-step for larger datasets. | Add a short README section with recommended index types and parameter ranges (small demo vs medium vs large) and show the exact JSON to change in the createIndexes call. |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | builder_error | seed.py:53 uses coll.replace_one(..., upsert=True) (idempotent upserts). However seed.py does not create the vector index; index creation was attempted via MCP tools and failed in this run (events.jsonl shows management/write tools disabled). | Add idempotent index creation (createIndexes) to seed.py before upserts so seed.py fully prepares the collection and can be re-run safely. |
| /search returns a clear error for an empty query and when the embedding call fails. | partly_met | prompt_silent | run_agent.py:54-57 checks for missing CLI argument and prints usage. There is no try/except around embed_text() or vector_search() to produce a clear error on embedding failures or runtime exceptions. | Wrap embedding and vector_search calls with explicit exception handling and return/print distinct errors for empty input and embedding failures (catch exceptions from sentence_transformers and pymongo and provide helpful messages). |
| Dependencies are pinned in requirements.txt. | partly_met | prompt_silent | app/requirements.txt:1-4 pins ranges (pymongo>=4.4,<5.0, sentence-transformers>=2.2.2, langchain>=0.0.300, python-dotenv>=1.0.0) but not exact pinned versions (==). | Pin exact compatible versions (==) or include a constraints file (pip-constraints.txt) with exact hashes to make CI reproducible. |
| The agent encodes a transaction's features into an embedding vector with an embedding model, and the same model is used for the stored fraud pattern vectors and for new transactions. | met | - | embeddings.py:14-18 (embed_text uses model.encode(normalize_embeddings=True)); seed.py:39-41 (embed_many used to compute vectors for patterns); run_agent.py:59 (embed_text used for new transaction). | - |
| Known fraud pattern vectors are stored as an embedding field on documents in an Azure DocumentDB collection, written through a MongoDB driver (e.g. PyMongo), with each document carrying the pattern information the explanation draws on. | met | - | seed.py:42-54 creates documents with fields pattern_name, description, ts, vector, model, dims, schemaVersion and uses coll.replace_one(..., upsert=True); docdb_client.get_db() uses pymongo (docdb_client.py:7-15). | - |
| The agent's response contains both the numeric fraud risk score and a natural-language explanation that describes the matching fraud patterns. | met | - | run_agent.py:61-66 prints the computed risk and explanation; explain() builds a readable explanation with pattern names and similarity scores (run_agent.py:41-51). | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example:1-4 contains DOCUMENTDB_URI and OPENAI_API_KEY placeholders; docdb_client.py:10 reads DOCUMENTDB_URI from the environment and raises if absent. | - |
| One database client is created and reused across requests. | met | - | docdb_client.py:4-15 implements a module-level MongoClient singleton (_client) and get_client() returns the shared client. | - |
| Search results include the similarity score. | met | - | run_agent.py:21-24 uses pipeline projecting {'similarityScore': {'$meta': 'searchScore'}, 'document': '$$ROOT'} and explain() prints sim values (run_agent.py:22-24, 45-50). | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | README.md includes sample description, prerequisites, quickstart steps, seeding, run instructions and cleanup guidance (README.md:1-40, 48-49). | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md title and text consistently call it 'Azure DocumentDB' (README.md:1-8, 21-23); .env.example and code reference cluster endpoints but do not use older product names. | - |

