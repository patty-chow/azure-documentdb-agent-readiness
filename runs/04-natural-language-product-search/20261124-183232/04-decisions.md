# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| operator | 1 |
| readiness_report | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:16:55+00:00

## D002 (build): I chose Python 3.11 as the sample language/runtime.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11
- **Because:** Python is the common choice for LangChain and fast to develop; the run environment has Python 3.13 but 3.11 is compatible. Using Python meets the prompt assumptions.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.10 (or 3.11) as the runtime".
- **When:** 2026-11-25T05:17:20+00:00

## D003 (build): I chose pymongo >=4.5 as the driver version and will follow singleton MongoClient patterns.

- **Instead of:** pymongo 3.x; pymongo >=4.3 (MongoDB 7.x compatible)
- **Because:** PyMongo 4.x is compatible with MongoDB 7.x wire protocol; using a recent 4.5+ ensures compatibility with DocumentDB features and supports modern connection options.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use the latest stable PyMongo compatible with MongoDB 7.x (e.g., pymongo >=4.3 or 4.5+)" and documentdb-driver skill guidance.
- **When:** 2026-11-25T05:17:23+00:00

## D004 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions as the default embedding model/dimension for the sample.

- **Instead of:** OpenAI text-embedding-3-small (1536d); other embedding (smaller dims)
- **Because:** This is a commonly used embedding model in LangChain examples and gives realistic dimension size for vector-index configuration; making it explicit avoids ambiguity for index creation and seed scripts.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use OpenAI embeddings via LangChain (model text-embedding-3-small) and normalize embeddings to cosine similarity; assume embedding dimension 1536".
- **When:** 2026-11-25T05:17:27+00:00

## D005 (build): I chose to include index JSON templates and README instructions for creating 'createSearchIndexes' and vector indexes, but not to create complex search/vector indexes programmatically from the sample because the MCP create-index API shape for createSearchIndexes is uncertain.

- **Instead of:** Create real indexes programmatically via MCP; Provide index JSON and instructions but not create them automatically
- **Because:** Avoid accidental mis-creation or failing API calls for complex search index definitions; provide safe templates and instructions so users can apply them with mongosh or portal. Seed data insertion (documents) is safe and will be automated via MCP insertion for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Use createSearchIndexes + $search (BM25) ... and create vector indexes using createIndexes with cosmosSearchOptions" but the MCP tool semantics may differ and could fail if wrong.
- **When:** 2026-11-25T05:17:31+00:00

## D006 (build): I chose to run the local seed script (seed/seed.py --skip-embed) to insert sample documents because the MCP documentdb_insert_documents call failed with an unspecified error.

- **Instead of:** use documentdb_insert_documents MCP tool; run local seed script using PyMongo and DOCUMENTDB_URI env var
- **Because:** Using the seed script connects via DOCUMENTDB_URI and is a reliable way to upsert seed data; it also matches the sample's documented workflow for users.
- **Reason came from:** `tool_result`
- **Evidence:** Attempt to call documentdb_insert_documents returned: "Error: Function failed."
- **When:** 2026-11-25T05:19:22+00:00
