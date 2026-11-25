# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| model_default | 2 |
| tool_result | 2 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:48:11+00:00

## D002 (build): I chose Python 3.11 as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.11; Go
- **Because:** Python is the user's requested language for a LangChain agent; 3.11 is the latest stable in that range and available in the run environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Python 3.10 or 3.11 (latest stable on developer machine).'
- **When:** 2026-11-25T10:48:38+00:00

## D003 (build): I chose PyMongo (pymongo>=4.0,<5.0) as the MongoDB driver and will implement a singleton MongoClient per documentdb-driver guidance.

- **Instead of:** pymongo>=3.12; pymongo>=4.0,<5.0; motor (async)
- **Because:** PyMongo 4.x is the current stable synchronous driver and aligns with the documentdb-driver skill guidance for singleton client patterns.
- **Reason came from:** `prompt`
- **Evidence:** Prompt review assumption: 'Use PyMongo (pymongo>=4.0,<5.0) and follow the documentdb-driver guidance to create a singleton MongoClient reused across requests.'
- **When:** 2026-11-25T10:48:48+00:00

## D004 (build): I chose OpenAI text-embedding-3-small as the embedding provider and set embedding dimension to 1536.

- **Instead of:** OpenAI text-embedding-3-large; OpenAI text-embedding-3-small; Hugging Face local model
- **Because:** OpenAI text-embedding-3-small is commonly available, cost-effective for samples, and maps to dimension 1536 used in many examples; this keeps the sample simple and reproducible. The .env.example will document OPENAI_API_KEY and EMBEDDING_DIM=1536.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Information gap: embedding model & dimension... builder must decide.' Prompt-review assumption used 1536 dims for text-embedding-3-small.
- **When:** 2026-11-25T10:48:50+00:00

## D005 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a config file; Read DOCUMENTDB_URI from environment variable; Prompt for connection string at runtime
- **Because:** Following the environment-driven secrets policy: never write secrets into files and follow the provided instruction in skill_md.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T10:48:53+00:00

## D006 (build): I chose to provide a small FastAPI HTTP API with a /screen endpoint and an additional CLI script for ad-hoc local testing.

- **Instead of:** Use FastAPI HTTP API only; Provide CLI only; Provide FastAPI + CLI for ad-hoc testing
- **Because:** FastAPI is lightweight and suitable for a simple agent surface; CLI aids demonstration without running a server. This matches the typical sample layout and developer expectations.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Provide a small HTTP API (FastAPI) with a /screen endpoint ... include a CLI script for ad-hoc local testing.'
- **When:** 2026-11-25T10:48:56+00:00

## D007 (build): I chose to create the DocumentDB vector index using the documentdb MCP server (documentdb_create_index) during verification rather than embedding it in seed.py.

- **Instead of:** Create vector index via PyMongo createIndexes command in seed script; Create vector index using the documentdb MCP server (documentdb_create_index); Skip creating a vector index
- **Because:** Using the MCP server ensures the index uses the correct DocumentDB-specific 'cosmosSearch' syntax and avoids risk of crafting an incorrect createIndexes payload in the sample seed script. The seed script will still create collection and sample documents and compute embeddings; the assistant will create the vector index during verification and document the steps in README.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Create vector indexes using DocumentDB's createIndexes/cosmosSearch JSON' and the MCP server is available for data-plane operations.
- **When:** 2026-11-25T10:49:00+00:00

## D008 (build): I chose vector weight 0.7 and regex weight 0.3 for combining signals, with thresholds: high >=0.8, medium >=0.5, else low.

- **Instead of:** Equal weights (0.5/0.5); Vector-heavy (0.8/0.2); Vector 0.7 / Regex 0.3
- **Because:** Vector similarity is the primary signal for semantic match; regex provides high-precision exact/fuzzy textual match. The 70/30 split gives preference to vector similarity but lets exact regex boost the score. Chosen thresholds are simple and suitable for a sample app; production systems should tune them on labeled data.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Information gaps: scoring function and thresholds... builder must decide and document.'
- **When:** 2026-11-25T10:49:58+00:00

## D009 (build): I chose to relax the openai requirement to openai>=1.0.0,<3.0 in requirements to pick a modern available client version.

- **Instead of:** openai==1.8.5 (pinned); openai>=1.0.0,<3.0; use azure-openai-package
- **Because:** A relaxed range avoids installation errors while still using the official OpenAI Python client. The sample code uses the standard openai.Embedding API which is stable across 1.x versions.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed: 'No matching distribution found for openai==1.8.5'
- **When:** 2026-11-25T10:50:06+00:00

## D010 (build): I chose to run the seed script (python -m src.seed) to populate the sample_banking_18.sanctions collection with synthetic documents and (if OPENAI_API_KEY set) compute embeddings.

- **Instead of:** Skip seeding; Run seed script locally to populate sample data
- **Because:** Seeding demonstrates the app end-to-end and is safe: it populates sample documents only in the designated database. Embeddings are computed only if OPENAI_API_KEY is present; the script is idempotent (replace_one upsert).
- **Reason came from:** `prompt`
- **Evidence:** Prompt skill_md: 'Use the database named sample_banking_18... seed script should create collection and index and load sample data idempotently.'
- **When:** 2026-11-25T10:50:42+00:00

## D011 (build): I chose to create the vector index via PyMongo db.command(createIndexes) because the documentdb_create_index MCP tool failed twice.

- **Instead of:** Retry documentdb_create_index MCP tool; Use PyMongo db.command(createIndexes) to create the index
- **Because:** Using PyMongo with the createIndexes command lets us send the DocumentDB-specific createIndexes payload directly to the server; this is a reliable fallback when the MCP helper tool fails.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index returned 'Error: Function failed.' on two attempts.
- **When:** 2026-11-25T10:51:33+00:00
