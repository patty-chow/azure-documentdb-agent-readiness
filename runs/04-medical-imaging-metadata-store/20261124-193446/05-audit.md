# 5. Best-practice audit: 04-medical-imaging-metadata-store

**Verdict: pass_with_findings** (10 followed, 3 violated, 2 not applicable)

The sample implements the core scenario: a Python FastAPI service, OpenAI-based embeddings, embeddings stored in documents as number[] (so DocumentDB native vector indexes work), a cosmosSearch vector-ivf index created in code, a /search endpoint that embeds queries and runs a $search/cosmosSearch vector search, and sample-seeding and verification scripts were executed against the live cluster. Major correctness items are met. Findings: (1) the builder intentionally diverged from the original starter-prompt request to store embeddings as BSON Binary because Azure DocumentDB requires number[] for its native vector indexes; this is documented in the repo but it means the sample does not follow the literal prompt. (2) Several “gallery hygiene” items are incomplete: the seed script is not idempotent, dependencies are not fully pinned, there are no offline unit tests, and no IaC is provided. (3) Some operational best-practices surfaced by installed skills (timeouts/retries/pool tuning, explicit retry/backoff) were not applied. See requirement_results and checks for details and the doc_gaps section for documentation items the product team should ship.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'blocked' | operator | sound | The decision documents the embedding-format conflict and requests author action; events show vector-index docs and the code followed the docs. Evidence: vector-search docs loaded and code stores number[] (seed.py). Decision is sound. |
| D002 | I chose Python 3.10 as the language/runtime for the sample. | prompt | sound | Choosing Python 3.10 is reasonable and consistent; recorded and used in README and testing steps. |
| D003 | I chose pymongo>=4.4,<5 for the MongoDB driver. | prompt | sound | Choosing PyMongo 4.x is supported and recorded; requirements.txt pins pymongo>=4.4,<5. |
| D004 | I chose to read secrets and connection strings from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_DIM). | prompt | sound | Secrets read from env; code reads DOCUMENTDB_URI and OPENAI_API_KEY (app/db.py line 7, app/main.py line 12). |
| D005 | I chose to store embeddings as a number[] (JSON array of numbers) in the 'embedding' field. | readiness_report | sound | Builder chose number[] instead of BSON Binary to enable DocumentDB native vector index. This follows public docs (vectors must be number[]) and is reflected in code (seed.py, create_index.py). |
| D006 | I chose OpenAI model text-embedding-3-small and EMBEDDING_DIM=1536. | skill | sound | Choosing text-embedding-3-small and EMBEDDING_DIM=1536 is internally consistent and matches the skill guidance used; the env defaults and README reflect the choice. |
| D007 | I chose to create a vector-ivf index (kind: 'vector-ivf'). | prompt | sound | Builder followed the prompt's vector-ivf request and skill guidance recommending IVF for small demo corpora; code creates vector-ivf (create_index.py). |
| D008 | I chose to use the existing pre-provisioned cluster and not provision any Azure resources. | skill | sound | Decision to use the existing pre-provisioned cluster is consistent with the run environment description and the events showing management tools were disabled. Recorded and followed. |
| D009 | I chose similarity 'COS' (cosine) for the index and query-time comparisons. | skill | sound | Choosing COS and normalizing embeddings is consistent with vector-search guidance; code normalizes embeddings (app/main.py, seed.py). |
| D010 | I chose lBuild=50 for the index build parameter. | skill | sound | Choosing lBuild=50 is supported by the vector-search skill guidance and was applied in create_index.py; evidence in events shows vector-create-diskann-index resource was read. |
| D011 | I chose to use pymongo.create_index from a local script (create_index.py) after the MCP documentdb_create_index call failed. | tool_result | sound | MCP create-index failed in the run (events show ToolExecutionException), and pymongo.create_index succeeded; using pymongo as a fallback is correct and the events show this path was executed. |

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
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 1 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 13 | Public and discoverable. |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Audit trail: pseudo-embedding decision | Record the decision to use deterministic pseudo-embeddings for demo mode (audit trail). | repo files (no public address recorded) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Pseudo-embeddings for demos | Use deterministic pseudo-embeddings when API keys are unavailable, but document this and ensure production uses real embeddings. | A short Learn page recommending deterministic pseudo-embeddings for demos and showing a canonical deterministic algorithm (seed by text hash) so agents can rely on it. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| One client reuse | Create and reuse a single MongoClient instance per process. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Client timeouts and pool tuning | Set client timeouts and tune connection-pool sizes (serverSelectionTimeoutMS, socketTimeoutMS, maxPoolSize). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| TLS enforcement | Always use TLS and enable driver certificate validation. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>.env.example |
| Store embeddings as number[] | Store embeddings as number[] in the document for native vector indexes (not BSON Binary). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Normalize embeddings for COS | Normalize embeddings at ingest time when using COS (store model name and dimension metadata). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Compute embeddings at ingest | Compute embeddings at write/ingest time and store them with the document (do not recompute on every query). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |
| Metadata indexes for filters | Create B-tree indexes on metadata fields used for filtering (modality, body_part) and prefer compound indexes. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Two-stage/hybrid retrieval | Use two-stage retrieval: vector KNN to get candidates, then re-rank/filter with metadata in-app. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |
| Choose index algorithm and params | Pick appropriate algorithm (IVF/HNSW/DiskANN) and explicit index params tuned to dataset size and dimension. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Limit result sizes / pagination | Limit results to small top-K and support pagination for larger result sets. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |
| Retries with backoff | Implement retries with exponential backoff for transient errors and make idempotent operations. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Log PHI-safety | Log query metadata and latencies but never log PHI or raw clinical findings. | [Store application secrets safely during development (and related monitoring guidance)](https://learn.microsoft.com/dotnet/architecture/microservices/secure-net-microservices-web-applications/developer-app-secrets-storage) |
| MCP vs driver index creation fallback | If MCP/create-index tooling fails, create the vector index via the driver and verify with listIndexes. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Set client timeouts and tune connection-pool sizes (serverSelectionTimeoutMS, socketTimeoutMS, maxPoolSize). | connection_handling | app/db.py creates MongoClient(MONGO_URI) without explicit timeout/pool options (line 18). | Set explicit MongoClient options from env (e.g., MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, socketTimeoutMS=45000, maxPoolSize=int(os.getenv('MAX_POOL_SIZE',100)))) | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Implement retries with exponential backoff for transient errors and make idempotent operations. | retries | No retry/backoff wrapper around network calls (OpenAI or DB) is implemented; MongoClient is created without custom retry logic (app/db.py). | Wrap network calls (embedding and DB operations) with retry/backoff (e.g., tenacity) and use upsert for idempotent DB writes; set driver's retryWrites where appropriate. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Record the decision to use deterministic pseudo-embeddings for demo mode (audit trail). | audit trail | seed.py implements deterministic pseudo-embeddings (seed.py lines 48-52) but there is no logged decision in decisions.jsonl recording that explicit choice. | Add a recorded decision entry or README note describing demo-mode embeddings and where that choice came from. | repo files (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create and reuse a single MongoClient instance per process. | connection_handling | app/db.py lines 10-19 | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always use TLS and enable driver certificate validation. | security | .env.example gives a connection string sample with ssl=true (app/.env.example line 2); code uses the URI passed in (app/db.py line 7). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>.env.example |
| Store embeddings as number[] in the document for native vector indexes (not BSON Binary). | vector_indexing | seed.py lines 39-47 and 60-61 produce and store embedding as a list (arr.tolist()); create_index.py creates cosmosSearchOptions index on 'embedding'. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Normalize embeddings at ingest time when using COS (store model name and dimension metadata). | vector_search | seed.py and app/main.py normalize vectors before storing/returning: seed.py lines 43-47; app/main.py lines 34-39. EMBEDDING_DIM and OPENAI_MODEL are stored/configured via env vars (.env.example lines 3-5). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Compute embeddings at write/ingest time and store them with the document (do not recompute on every query). | data_modeling | seed.py computes embeddings on insert (lines 39-47, 60) and run_search.py / app/main.py embed queries only on search (app/main.py lines 30-39). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |
| Pick appropriate algorithm (IVF/HNSW/DiskANN) and explicit index params tuned to dataset size and dimension. | vector_indexing | create_index.py uses kind 'vector-ivf', numLists=100, lBuild=50 and README explains demo-size assumptions; events show the builder used documentdb-vector-search guidance to pick IVF for small demo. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Limit results to small top-K and support pagination for larger result sets. | queries | API enforces default k param and Query accepts k (app/main.py line 49), run_search.py uses k=5 (run_search.py lines 26-29). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |
| Log query metadata and latencies but never log PHI or raw clinical findings. | monitoring | The sample contains no logging of PHI; seed and run scripts print findings for demo only; README warns 'Do not use as-is for PHI' (README.md line 29). | [Store application secrets safely during development (and related monitoring guidance)](https://learn.microsoft.com/dotnet/architecture/microservices/secure-net-microservices-web-applications/developer-app-secrets-storage) |
| Use deterministic pseudo-embeddings when API keys are unavailable, but document this and ensure production uses real embeddings. | seeding | seed.py and compute_vector.py implement deterministic pseudo-embeddings when OPENAI_API_KEY is not set (seed.py lines 48-52, compute_vector.py lines 8-11). | prior_knowledge_only (no public address recorded) |
| If MCP/create-index tooling fails, create the vector index via the driver and verify with listIndexes. | indexing | documentdb_create_index via MCP failed (events line 35/38) and create_index.py used pymongo.create_index successfully (create_index.py line 22; events show success). | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create B-tree indexes on metadata fields used for filtering (modality, body_part) and prefer compound indexes. | indexing | The sample does not issue metadata-only filtered queries; it uses vector-only queries. No metadata indexes are created in create_index.py or elsewhere. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use two-stage retrieval: vector KNN to get candidates, then re-rank/filter with metadata in-app. | queries | The sample performs a single-stage vector search and returns the results. No application-side re-ranking beyond returning searchScore is implemented. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search)<br>[Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search) |

### Reference requirements

12 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Unit tests run without a live cluster. | not_met | prompt_silent | No test files present in the repository. No mocking/in-memory tests for DB or OpenAI are included. | Add pytest unit tests that mock pymongo (e.g., use mongomock or monkeypatch get_collection) and mock OpenAI calls so tests run offline. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No ARM/Bicep/Terraform files in repository; only code that uses an existing cluster (app/db.py) and .env.example. | Add a Bicep or Terraform example that targets Microsoft.DocumentDB/mongoClusters (or an AzAPI wrapper), with parameters for tier, region and defaults for low-cost runs. |
| For each imaging record, the findings text is embedded with OpenAI and the resulting vector is stored on the same document as a BSON binary vector. | partly_met | builder_error | seed.py lines 39-47 (embed_text) and line 60 (embedding stored in document as list), app/main.py embed_text uses OpenAI (lines 30-39). However, embeddings are stored as a number[] list (seed.py line 61) not as BSON Binary. | If the intent is to follow the original prompt literally, change seed/main to pack embeddings into bson.Binary. If the intent is to use native DocumentDB vector indexes, update the starter prompt to say "store embeddings as number[] suitable for DocumentDB vector indexes". Prefer the latter (prompt change). |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | partly_met | prompt_silent | create_index.py sets numLists=100 and lBuild=50 (lines 17-18) and README notes that an index must be created (README.md line 29). README does not explain why these params were chosen nor document how to change them for larger corpora. | Add README text explaining: why vector-ivf was chosen for small (<10k) demos, and how to change kind/numLists/lBuild/lSearch for larger datasets (or expose these as env vars and describe them). |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | prompt_silent | seed.py inserts ~50 records using insert_many (lines 64-68) and create_index.py creates the index (create_index.py line 22). There is no idempotency guard: running seed.py twice will insert duplicate documents. | Make seed.py idempotent: add a deterministic document id or use replace_one(..., upsert=True) for each record or check for an existing marker document before inserting. |
| Dependencies are pinned in requirements.txt. | partly_met | prompt_silent | requirements.txt pins pymongo range (pymongo>=4.4,<5) but other packages (fastapi, openai, numpy) are unpinned (app/requirements.txt). | Pin dependency versions (e.g., fastapi==x.y.z, openai==x.y.z, numpy==x.y.z) or provide a constraints file. Prefer explicit pinned versions in requirements.txt for repeatable builds. |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | README.md includes what it shows, prerequisites and run steps (README.md lines 12-26) but does not provide explicit clean-up steps for the sample (e.g., how to delete the demo DB/collection), nor a short section on index tuning (see earlier). | Add a 'Clean up' section with commands to drop the sample database/collection and notes about removing created resources in Azure portal/CLI; add a short index-tuning subsection or link to the vector-search skill guidance. |
| The app is a Python service that stores medical imaging metadata documents (modality, body part, findings) in Azure DocumentDB through a Python MongoDB-compatible driver (e.g. pymongo). | met | - | seed.py lines 55-61 (make_doc returns {'modality','body_part','findings','embedding'}); app/db.py lines 13-19 uses pymongo.MongoClient to access DB/collection. | none |
| A cosmosSearch index of kind vector-ivf is created in code on the embedding field, with dimensions matching the OpenAI embedding model's output. | met | - | create_index.py lines 11-19 create cosmosSearchOptions kind:'vector-ivf' and dimensions from EMBEDDING_DIM; events/documentdb_list_indexes shows index 'medical_images_embedding_ivf' with dimensions 1536. | none |
| The service exposes a search endpoint that accepts a clinical query string (e.g. as a query parameter or JSON body field). | met | - | app/main.py lines 48-49 define GET /search with q: str query parameter. | none |
| The search endpoint embeds the clinical query string with OpenAI and runs the similarity search in Azure DocumentDB with a $search / cosmosSearch query over the vector-ivf index using that query vector (similarity e.g. COS). | met | - | app/main.py lines 30-39 (embed_text), lines 61-67 ($search cosmosSearch pipeline using path 'embedding' and vector qvec); create_index.py sets similarity 'COS' (line 16). | none |
| The search endpoint returns the imaging metadata documents matched by that vector search, ordered by semantic similarity to the query. | met | - | app/main.py pipeline projects 'score': {'$meta': 'searchScore'} (lines 71-76) and returns results ordered by the aggregation (lines 80-93). | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example lists DOCUMENTDB_URI and OPENAI_API_KEY (lines 2-3); app/db.py line 7 reads DOCUMENTDB_URI; app/main.py line 12 reads OPENAI_API_KEY. | none |
| A .env.example lists every setting with placeholder values. | met | - | .env.example lines 1-7 include DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_DIM, DB_NAME, COLLECTION_NAME. | none |
| The vector index dimensions match the embedding model's output. | met | - | .env.example and app/main.py default OPENAI_MODEL='text-embedding-3-small' and EMBEDDING_DIM=1536 (app/main.py lines 13-14); create_index.py uses EMBEDDING_DIM for dimensions (line 15). | none |
| One database client is created and reused across requests. | met | - | app/db.py lines 10-19 implement a module-level _client singleton and get_client(). | none |
| /search returns a clear error for an empty query and when the embedding call fails. | met | - | FastAPI Query(...) enforces min_length=1 on q (app/main.py line 49) so empty queries are rejected; embed_text exceptions are caught and returned as HTTPException with 'Embedding error' (app/main.py lines 51-54). | none |
| Search results include the similarity score. | met | - | Projection includes score: {'$meta': 'searchScore'} (app/main.py lines 71-76) and SearchResult includes score field (lines 22-27). | none |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md title and content use 'Azure DocumentDB' and the code/repo use 'DocumentDB' references (README.md line 1 and notes). | none |

