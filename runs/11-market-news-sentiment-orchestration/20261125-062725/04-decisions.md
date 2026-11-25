# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| model_default | 4 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:30:14+00:00

## D002 (build): I chose Node.js (JavaScript/TypeScript not used) for the sample.

- **Instead of:** Python, Node.js
- **Because:** Prompt explicitly requested Node.js and LangChain JS; aligns with available Node 24 runtime.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T14:30:21+00:00

## D003 (build): I chose 'mongodb' ^5.7.0 as the driver dependency.

- **Instead of:** mongodb driver ^4.x; mongodb driver ^5.7.0; mongodb driver latest
- **Because:** Recent driver that supports MongoDB 7.0 wire protocol and provides reproducible dependency resolution.
- **Reason came from:** `prompt`
- **Evidence:** Prompt review assumption: "Use the official 'mongodb' npm package (Node driver) and pin a recent stable major that supports MongoDB 7.0 wire protocol, e.g. 'mongodb' ^5.7.0."
- **When:** 2026-11-25T14:30:27+00:00

## D004 (build): I chose to read the Azure DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Connection string env var DOCUMENTDB_URI; Use managed identity / Entra ID
- **Because:** DOCUMENTDB_URI is declared authoritative in the run-environment; simpler for a sample and avoids requiring Entra setup.
- **Reason came from:** `model_default`
- **Evidence:** Run environment guidance: 'Read the DocumentDB connection string from DOCUMENTDB_URI at runtime and never hardcode'
- **When:** 2026-11-25T14:30:30+00:00

## D005 (build): I chose OpenAI as the LLM/embedding provider and to read credentials from OPENAI_API_KEY (and OPENAI_API_BASE optionally).

- **Instead of:** OpenAI (OPENAI_API_KEY); Azure OpenAI (AZURE_OPENAI_KEY); Local LLM or mock
- **Because:** OpenAI is widely available, well-supported by LangChain JS and examples; using OPENAI_API_KEY keeps the sample simple. Code will allow environment configuration so users can substitute Azure if desired.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM & embedding credentials (e.g. OPENAI_API_KEY or AZURE_OPENAI_KEY) not present; builder must decide'
- **When:** 2026-11-25T14:30:33+00:00

## D006 (build): I chose 'text-embedding-3-small' with embedding dimension 1536 for embeddings.

- **Instead of:** text-embedding-3-small (1536); text-embedding-3-large (3072); openai-embedding-ada-002 (1536?)
- **Because:** Provides reasonable quality and small size for a sample; 1536 dims are a common small model size and allow creating a vector index placeholder.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review suggesting text-embedding-3-small and 1536 dims.
- **When:** 2026-11-25T14:30:35+00:00

## D007 (build): I chose console notifications with an optional webhook POST (WEBHOOK_URL) for demo notifications.

- **Instead of:** Console-only notifications; Console + Webhook POST (WEBHOOK_URL); Email/SMTP/Slack integration
- **Because:** Console output is simple and safe for samples; optional webhook allows demonstration of external notification without shipping secrets or complex integrations.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Notification transport for alerts' is unspecified; builder must choose.
- **When:** 2026-11-25T14:30:37+00:00

## D008 (build): I chose to create a text index on headline and an index on tickers; for vector index I'll include code that attempts to create one but will not rely on it and will document that vector index creation could require manual steps.

- **Instead of:** Create text + ticker indexes only; Also create vector index using driver createIndex with vector options (may fail); Skip index creation and leave to user
- **Because:** Ensures queries and alerts work reliably; provides vector index attempt while being robust if unsupported in this environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Do not rely on hybrid vector+filter queries until you verify the exact vector-index API... implement alert logic that can fall back to filtering by tickers ($in) and then run a vector search in a second step if needed.'
- **When:** 2026-11-25T14:30:40+00:00

## D009 (build): I chose both a CLI and a minimal Express HTTP endpoint.

- **Instead of:** CLI only; Express endpoint only; Both CLI and Express endpoint
- **Because:** Provides scriptable and web-based trigger options.
- **Reason came from:** `prompt`
- **Evidence:** Prompt review recommended CLI and Express endpoint.
- **When:** 2026-11-25T14:30:47+00:00

## D010 (build): I chose a simple document schema for 'articles' with fields: _id, headline, sentiment (number), tickers (array), timestamp (ISO), embedding (array of numbers) optional.

- **Instead of:** Complex normalized schema; Simple document schema with fields (_id, headline, sentiment, tickers, timestamp, embeddings)
- **Because:** Simple schema is readable and aligns with sample goals.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review that sample articles include these fields.
- **When:** 2026-11-25T14:30:52+00:00
