# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| model_default | 3 |
| prompt | 2 |
| operator | 1 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:36:04+00:00

## D002 (build): I chose Python 3.13 (use virtualenv) as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.x
- **Because:** Python is the common ecosystem for LlamaIndex, sentence-transformers, and pymongo; the run environment already has Python available.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption: 'Use a recent Python 3.x runtime (typical choice: Python 3.10 or 3.11) and a virtualenv; document in README and requirements.txt.' Readiness report: 'Python 3.13.13 on PATH'
- **When:** 2026-11-25T06:36:43+00:00

## D003 (build): I chose pymongo 4.x (pymongo==4.4) as the MongoDB driver version and will use a singleton MongoClient per process.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** pymongo 4.x is compatible with MongoDB 7.0 wire protocol and the documentdb-driver skill recommends singleton client usage.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use the official pymongo Python driver (pymongo 4.x compatible with MongoDB 7.0), instantiate a singleton MongoClient per process as recommended by documentdb-driver.'
- **When:** 2026-11-25T06:36:45+00:00

## D004 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime (do not write secrets into files).

- **Instead of:** Hardcode connection string; Read DOCUMENTDB_URI from env var
- **Because:** Security best practice and the run environment specifies DOCUMENTDB_URI contains the cluster connection string.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file...'
- **When:** 2026-11-25T06:36:47+00:00

## D005 (build): I chose to use sentence-transformers model 'all-MiniLM-L6-v2' producing 384-dimensional embeddings for the sample.

- **Instead of:** Use OpenAI embeddings (1536-dim); Use local sentence-transformers 'all-MiniLM-L6-v2' (384-dim)
- **Because:** Using a local embedding model avoids requiring user's cloud API keys and simplifies sample verification. 384 dims is common for miniLM and inexpensive to compute for the demo.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report 'information_gaps: Embedding model selection and output dimension' — no required model. Sentence-transformers is a lightweight open model that does not require API keys for sample runs.
- **When:** 2026-11-25T06:36:50+00:00

## D006 (build): I chose 'vector-diskann' as the vector index type for sample collection.

- **Instead of:** vector-hnsw; vector-diskann; vector-ivf
- **Because:** DiskANN is recommended for M30+ clusters and provides production-like behavior for the demo.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill: 'DiskANN is the recommended vector index in Azure DocumentDB for production-scale workloads' and the readiness report noted the cluster supports DiskANN.
- **When:** 2026-11-25T06:37:12+00:00

## D007 (build): I chose to create the vector index and the deduplication unique index using the documentdb MCP server functions (documentdb_create_index) rather than trying to rely on pymongo-specific syntactic variants.

- **Instead of:** Create index via application pymongo create_index; Create index using documentdb MCP server function documentdb_create_index
- **Because:** MCP server function exposes cluster-specific index creation shape (cosmosSearchOptions) reliably; avoids mismatch with pymongo's create_index parameter mapping.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'the documentdb MCP server's connection profile default is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.' Also DocumentDB-specific index options (cosmosSearchOptions) are best handled by the MCP helper.
- **When:** 2026-11-25T06:37:15+00:00

## D008 (build): I chose to include a small plaintext sample transcript (samples/earnings_call_sample.txt) in the repo and document how to provide real PDFs. The ingest script supports plain-text files and PDFs if provided by the user.

- **Instead of:** Store sample data as PDF in repo; Store sample text transcript in repo and accept PDFs from user
- **Because:** Including a small text transcript avoids bundling copyrighted/proprietary earnings-call PDFs but still lets the sample run end-to-end. The README documents how to use real PDFs.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will include a small placeholder PDF in samples/ or provide a script that accepts user-supplied PDFs.' Readiness report noted sample PDFs not provided and builder must supply or document.
- **When:** 2026-11-25T06:37:18+00:00

## D009 (build): I chose to use OpenAI (via OPENAI_API_KEY) for answer synthesis if the key is present; otherwise, the sample falls back to a deterministic context-aggregation summarizer that concatenates retrieved passages with citations.

- **Instead of:** Require OpenAI API for answer synthesis; Use OpenAI when available, else fallback to simple context-aggregation
- **Because:** This keeps the sample runnable without requiring an API key while showing how to integrate a real LLM via LlamaIndex/LLMPredictor when available.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'information_gaps: LLM model and provider choice' — no required model. Using OpenAI if present keeps the sample realistic; a fallback avoids failing when keys are missing.
- **When:** 2026-11-25T06:37:22+00:00

## D010 (build): I chose to use the existing DocumentDB cluster referenced by DOCUMENTDB_URI and not provision new Azure resources.

- **Instead of:** Provision a new DocumentDB cluster via az or Bicep; Use the existing cluster referenced by DOCUMENTDB_URI
- **Because:** No infra changes allowed; the environment already has a cluster to use for verification.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' Readiness report: 'A DocumentDB cluster is already provisioned and reachable; its connection string is in DOCUMENTDB_URI.'
- **When:** 2026-11-25T06:38:13+00:00

## D011 (build): I stopped retrying dependency installation after a pip failure and will use synthetic (random normalized) embeddings for verification inserts rather than running sentence-transformers locally.

- **Instead of:** Retry pip install until success; Stop retrying and use a workaround (synthetic embeddings)
- **Because:** Building heavy wheel dependencies is failing in this environment; for verifying vector index creation and KNN retrieval behavior we can insert random normalized vectors matching the embedding dimensions and still exercise vector index and retrieval logic.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed with 'ModuleNotFoundError: No module named distutils' while building numpy (see pip error).
- **When:** 2026-11-25T06:38:28+00:00
