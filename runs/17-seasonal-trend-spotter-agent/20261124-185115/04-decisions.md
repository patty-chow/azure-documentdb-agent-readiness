# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| prompt | 4 |
| readiness_report | 3 |
| operator | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:10:32+00:00

## D002 (build): I chose Python 3.11 (modern Python) as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11
- **Because:** The sample integrates with LangChain and pymongo; Python is commonly used for these libraries and the prompt asked for a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will target a modern Python 3.x runtime (assume Python 3.10 or 3.11) and create a venv; requirements.txt will target that."
- **When:** 2026-11-25T06:10:50+00:00

## D003 (build): I chose pymongo (official MongoDB Python driver) pinned to a recent 4.x release (pymongo>=4.4,<5).

- **Instead of:** motor (async); pymongo (sync)
- **Because:** pymongo is the recommended synchronous driver and easier for a small sample; it aligns with the documentdb-driver skill guidance to use a singleton MongoClient.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Use pymongo (the official Python MongoDB driver); pin a reasonably recent, MongoDB-7.0-compatible version (e.g., pymongo >=4.3 ...)."
- **When:** 2026-11-25T06:10:53+00:00

## D004 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI and use it with a singleton MongoClient.

- **Instead of:** Read connection string from env and use password auth; Use Microsoft Entra OIDC auth
- **Because:** Simpler for sample and matches environment setup described in the run environment (DOCUMENTDB_URI provided). Using OIDC increases complexity and requires additional setup not suitable for a sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "Read connection string from DOCUMENTDB_URI and create a single, reusable MongoClient"
- **When:** 2026-11-25T06:11:02+00:00

## D005 (build): I chose Bing Web Search (Azure Cognitive Services) as the web-search provider and to read credentials from BING_API_KEY and BING_ENDPOINT environment variables. If those aren't set the tool will return a small mocked set of trend signals.

- **Instead of:** Bing Web Search API (Azure Cognitive Services); SerpAPI; Google Custom Search
- **Because:** Bing Web Search is well-documented, commonly available to Azure users, and maps cleanly to an environment-variable credential pattern. Providing a mock fallback ensures the sample runs without external keys.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "Missing decision: Web search API choice"
- **When:** 2026-11-25T06:11:08+00:00

## D006 (build): I chose a compound index on { category: 1, sale_date: 1 } to support the aggregation grouping and range queries.

- **Instead of:** Compound index {category:1, sale_date:1}; Separate indexes on category and sale_date
- **Because:** Compound index aligns with ESR pattern (equality on category, range on sale_date) and will speed seasonal aggregation by category.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Builder will create at least indexes to support the aggregation: an index on { category: 1, sale_date: 1 }"
- **When:** 2026-11-25T06:11:13+00:00

## D007 (build): I chose OpenAI (public OpenAI API) for embeddings and the chat LLM, using environment variable OPENAI_API_KEY. I will use the embedding model 'text-embedding-3-small' and the chat model 'gpt-3.5-turbo'.

- **Instead of:** OpenAI embeddings and LLM; Azure OpenAI; Local LLM
- **Because:** OpenAI is commonly available, integrates with LangChain, and 'text-embedding-3-small' is a sensible embedding choice for sample-sized vector work. Using 'gpt-3.5-turbo' avoids requiring enterprise access to GPT-4 variants.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Builder will use environment variables for any model credentials (e.g., OPENAI_API_KEY) and choose a commonly used embedding model (e.g., OpenAI 'text-embedding-3-small')"
- **When:** 2026-11-25T06:11:21+00:00

## D008 (build): I chose not to create/use a vector index in this sample (vector search is out of scope); the sample will combine aggregation (sales velocity) and web signals using simple numeric scoring and optional embeddings for ranking if OPENAI_API_KEY is provided in the environment. If embeddings are used, they are computed client-side and not stored in the DB.

- **Instead of:** Create a full vector index and use embeddings; Skip vectors and use lexical signals
- **Because:** Keep sample simple and focused on combining DocumentDB aggregation with web signals; avoid creating persistent vector indexes on the production cluster in a sample.
- **Reason came from:** `model_default`
- **Evidence:** Prompt didn't strictly require vector search; readiness report noted vector capabilities but left choice open.
- **When:** 2026-11-25T06:11:24+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:14:25+00:00

## D010 (build): I chose Python 3.11 (targeting a modern Python 3.x runtime) and will create a virtualenv-based sample.

- **Instead of:** Node.js/TypeScript; Python 3.11; Go; C#
- **Because:** The starter prompt requests a Python LangChain agent; Python is the natural choice for LangChain and pymongo. Python 3.11 is modern and compatible with the libraries used.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: "Builder will target a modern Python 3.x runtime (assume Python 3.10 or 3.11)".
- **When:** 2026-11-25T06:14:44+00:00

## D011 (build): I chose pymongo >=4.4 as the MongoDB driver and will follow the documentdb-driver guidance to use a singleton MongoClient.

- **Instead of:** pymongo >=4.4; motor (async); mongoengine or other ODM
- **Because:** pymongo is the official driver, stable, and matches the DocumentDB MongoDB wire compatibility; using a singleton MongoClient follows the documentdb-driver skill best practices.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: "Use pymongo (the official Python MongoDB driver); pin a reasonably recent, MongoDB-7.0-compatible version (e.g., pymongo >=4.3...)" and readiness_report guidance about using a single MongoClient.
- **When:** 2026-11-25T06:14:48+00:00

## D012 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection from env DOCUMENTDB_URI; Use Azure AD OIDC auth with DefaultAzureCredential
- **Because:** This keeps secrets out of the repo and matches the provided environment in the run environment section.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "Read connection string from DOCUMENTDB_URI and create a single, reusable MongoClient".
- **When:** 2026-11-25T06:14:57+00:00

## D013 (build): I chose a pluggable approach: prefer Bing Web Search when BING_API_KEY is provided; otherwise fall back to deterministic mock signals so the sample is runnable without external keys.

- **Instead of:** Bing Web Search (Azure); SerpAPI; Google Custom Search; No external API (mock-only)
- **Because:** Bing is a sensible default for Microsoft/Azure-centric samples; providing a mock fallback ensures the example runs in environments without API keys (important for reproducible verification).
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "Web search API choice" information gap — no provider specified.
- **When:** 2026-11-25T06:15:52+00:00

## D014 (build): I chose to create the supporting index in the seed script (pymongo) and also record the index via the documentdb MCP server later for verification.

- **Instead of:** create index via pymongo in seed script only; create index via the documentdb MCP server create_index; both
- **Because:** Creating the index in the seed script makes the script idempotent and self-contained; calling the MCP server to create/list the index gives an independent verification path and uses available tools.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: "Builder will create at least indexes to support the aggregation: an index on { category: 1, sale_date: 1 }".
- **When:** 2026-11-25T06:15:59+00:00
