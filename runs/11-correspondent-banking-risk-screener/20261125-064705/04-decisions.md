# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| readiness_report | 3 |
| tool_result | 3 |
| operator | 1 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:50:11+00:00

## D002 (build): I chose Python with FastAPI.

- **Instead of:** Use Node.js/TypeScript; Use Python with FastAPI
- **Because:** The prompt explicitly requested a Python LangChain agent and the run environment provides Python and pip; FastAPI is a lightweight HTTP API framework suitable for a small sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a modern Python 3.x runtime' and the sample requests a Python LangChain agent.
- **When:** 2026-11-25T14:50:34+00:00

## D003 (build): I chose pymongo>=4.3,<5.0.

- **Instead of:** pymongo latest (>=5.0); pymongo>=4.3,<5.0
- **Because:** MongoDB 7.x compatibility is safest with pymongo 4.x; pinning <5.0 avoids breaking changes.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use pymongo>=4.3,<5.0' for compatibility with MongoDB 7.0.
- **When:** 2026-11-25T14:50:37+00:00

## D004 (build): I chose to compute similarity client-side (numpy) for this sample.

- **Instead of:** Use server-side vector index (HNSW via createIndex); Compute similarity client-side with numpy
- **Because:** Client-side similarity is reliable for the small synthetic dataset, avoids undocumented createIndex parameters, and demonstrates the embedding + scoring flow while keeping the sample runnable against the provided cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Concrete createIndex syntax for managed cluster' is missing and the DocumentDB Agent Kit is not installed; creating a correct server-side vector index parameters may fail without docs.
- **When:** 2026-11-25T14:50:39+00:00

## D005 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); other embedding models
- **Because:** It's a compact widely used embedding model; readiness report identified embedding model & dims as a gap and recommended choosing one explicitly.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review suggested OpenAI text-embedding-3-small (1536 dims).
- **When:** 2026-11-25T14:50:42+00:00

## D006 (build): I chose gpt-4o-mini for generating plain-language narratives.

- **Instead of:** gpt-4o-mini; gpt-4o or other LLMs
- **Because:** gpt-4o-mini balances quality and cost; it's a reasonable default for sample narratives.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review suggested using a small/modern chat model for narratives (e.g., gpt-4o-mini).
- **When:** 2026-11-25T14:50:44+00:00

## D007 (build): I chose to read secrets from environment variables: DOCUMENTDB_URI and OPENAI_API_KEY.

- **Instead of:** Use environment variables for secrets; Hard-code connection strings or files
- **Because:** Security best practice and explicit instruction in the run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment guidance: 'Read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and never write the raw secret into files, logs, or repository artifacts.'
- **When:** 2026-11-25T14:50:52+00:00

## D008 (build): I chose to use the openai package directly for embeddings to avoid an extra dependency on langchain-community.

- **Instead of:** Use langchain OpenAIEmbeddings (requires langchain-community); Use openai package directly to compute embeddings
- **Because:** Using the openai client directly is straightforward for embedding calls and keeps dependencies smaller and tests simpler.
- **Reason came from:** `tool_result`
- **Evidence:** Pytest import error: ModuleNotFoundError: Module langchain_community.embeddings not found.
- **When:** 2026-11-25T14:52:14+00:00

## D009 (build): I chose to run scripts/seed.py to seed the live cluster with sample documents and embeddings.

- **Instead of:** Do not run seed (skip live cluster); Run seed.py to load sample data and embeddings into the provided DocumentDB cluster
- **Because:** The sample should be verified end-to-end against the provided vector-capable cluster; seeding is idempotent and required for the demo.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'Verify against the live cluster: create the collections and indexes, load the sample data, run the queries' and DOCUMENTDB_URI is available.
- **When:** 2026-11-25T14:52:28+00:00

## D010 (build): I chose to use deterministic synthetic embeddings when OPENAI_API_KEY is not set so seed can run against the live cluster without requiring a real key.

- **Instead of:** Abort seeding when OPENAI_API_KEY missing; Use deterministic synthetic embeddings when OPENAI_API_KEY missing
- **Because:** This keeps the sample runnable for demonstration and testing while avoiding embedding API calls when an API key is not present. The fallback uses deterministic hashing to produce reproducible vectors for similarity demos.
- **Reason came from:** `tool_result`
- **Evidence:** scripts/seed.py failed with RuntimeError: OPENAI_API_KEY environment variable is required to compute embeddings.
- **When:** 2026-11-25T14:52:45+00:00

## D011 (build): I chose to fallback to deterministic synthetic embeddings for querying when OPENAI_API_KEY is not set.

- **Instead of:** Require OPENAI_API_KEY for queries; Fallback to deterministic synthetic embedding when OPENAI_API_KEY missing
- **Because:** This keeps the sample runnable end-to-end for demonstration without requiring users to have an OpenAI key; synthetic embeddings are deterministic and consistent with seed fallback.
- **Reason came from:** `tool_result`
- **Evidence:** scripts/run_example.py failed because OPENAI_API_KEY was not set and embed_text raised RuntimeError.
- **When:** 2026-11-25T14:53:07+00:00
