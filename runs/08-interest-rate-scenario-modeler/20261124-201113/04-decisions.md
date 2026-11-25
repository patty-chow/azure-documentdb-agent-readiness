# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| readiness_report | 3 |
| operator | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:50:43+00:00

## D002 (build): I chose Python 3.x as the language and runtime, using pymongo as the MongoDB driver and LangChain/OpenAI for the agent.

- **Instead of:** Node.js/TypeScript; Python 3.x (3.10+); Go
- **Because:** Python is standard for LangChain, the environment already has Python and pip, and the prompt asked for a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a modern Python 3.x runtime' and readiness_report notes Python available.
- **When:** 2026-11-25T09:50:59+00:00

## D003 (build): I chose env var DOCUMENTDB_URI for the connection string.

- **Instead of:** Azure AD/OIDC; Env var connection string
- **Because:** Matches environment and avoids committing secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Read the connection string from DOCUMENTDB_URI and instantiate a single, process-wide pymongo.MongoClient'.
- **When:** 2026-11-25T09:51:12+00:00

## D004 (build): I chose OpenAI as the LLM provider and gpt-4 as the model for the LangChain agent.

- **Instead of:** OpenAI (hosted); Azure OpenAI; local LLM
- **Because:** OpenAI is widely available, supported by LangChain, and simple to configure via OPENAI_API_KEY for a sample repository.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM provider and model choice' is an information gap; the sample must pick a provider and document it.
- **When:** 2026-11-25T09:51:17+00:00

## D005 (build): I chose to NOT use embeddings or vector search in this sample; the agent will pass aggregate numeric results to the LLM for scenario reasoning.

- **Instead of:** Use vector indexes + embeddings; Do not use embeddings / only use aggregation results
- **Because:** Keeps the sample small, avoids needing to align embedding dims and vector index config, and still demonstrates scenario analysis with LLM reasoning on aggregated data.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report notes an information gap around embedding model/dimensions and recommends decisions be documented.
- **When:** 2026-11-25T09:51:21+00:00

## D006 (build): I chose maturity buckets: 0-1y, 1-3y, 3-5y, 5-10y, >10y.

- **Instead of:** Buckets: 0-6mo,6-12mo,1-2y,2-5y,>5y; Buckets: 0-1y,1-3y,3-5y,5-10y,>10y
- **Because:** These are common banking maturity buckets and keep the aggregation readable in a sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Maturity buckets will be derived ... e.g., 0-1y,1-3y,3-5y,5-10y,>10y.'
- **When:** 2026-11-25T09:51:27+00:00

## D007 (build): I chose to create an index on {maturity_date: 1, rate_type: 1} for the positions collection to support the aggregation pipeline.

- **Instead of:** Create indexes programmatically and via MCP; Do not create any indexes (rely on cluster defaults)
- **Because:** Simple, conservative index that supports grouping and common filters; inexpensive for a sample dataset.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'create an index on { maturity_date: 1, rate_type: 1 }'.
- **When:** 2026-11-25T09:51:30+00:00

## D008 (build): I chose not to provision resources; the sample will use the preprovisioned cluster (DOCUMENTDB_URI) and will not modify Azure infra.

- **Instead of:** Provision resources via az / Bicep; Use preprovisioned cluster and do not change infra
- **Because:** Avoids making control-plane changes and matches the environment described in the prompt.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and skill_md indicating a cluster is already provisioned.
- **When:** 2026-11-25T09:51:33+00:00

## D009 (build): I chose to run the seed script to insert idempotent sample data into the reachable DocumentDB cluster.

- **Instead of:** Do not run seed (avoid modifying live cluster); Run seed script to insert sample data into live cluster
- **Because:** The seed script is idempotent and the sample must demonstrate aggregation against real data; readiness_report allowed data-plane operations.
- **Reason came from:** `readiness_report`
- **Evidence:** Skill_md: 'A vector-capable Azure DocumentDB cluster is reachable... connection string in DOCUMENTDB_URI' and prompt asks to verify against live cluster.
- **When:** 2026-11-25T09:53:14+00:00

## D010 (build): I attempted to use the documentdb_create_index MCP tool but it failed, so I used pymongo.create_index from the aggregation code to create the index programmatically.

- **Instead of:** Use documentdb_create_index MCP tool; Create index programmatically via pymongo create_index
- **Because:** MCP tool failed in this environment; programmatic create_index is idempotent, simple, and works with the live cluster for sample setup.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index call returned 'Error: Function failed.'; aggregation_tool._ensure_index calls coll.create_index and succeeded during aggregation.
- **When:** 2026-11-25T09:54:00+00:00
