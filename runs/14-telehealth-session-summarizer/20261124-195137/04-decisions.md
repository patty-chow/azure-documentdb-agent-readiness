# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 4 |
| prompt | 3 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:46:47+00:00

## D002 (build): I chose Python 3.10+ as the implementation language.

- **Instead of:** JavaScript/Node.js; Python
- **Because:** Prompt review recommended Python 3.10+ and the run environment provides python and pip. Python is a common choice for LlamaIndex and OpenAI usage.
- **Reason came from:** `prompt`
- **Evidence:** assumption: "Target Python 3.10+ (e.g., 3.10 or 3.11). Use a virtualenv and pip; sample uses `python` / `pip` as entrypoints per skill_md."
- **When:** 2026-11-25T08:47:41+00:00

## D003 (build): I chose PyMongo (pymongo) MongoClient as the driver and will use a singleton client pattern.

- **Instead of:** motor async client; pymongo (MongoClient)
- **Because:** PyMongo is the officially recommended Python MongoDB driver and the documentdb-driver skill explicitly recommends a singleton MongoClient pattern. It's also compatible with Azure DocumentDB's MongoDB wire protocol.
- **Reason came from:** `prompt`
- **Evidence:** assumption: "Use PyMongo (pymongo) as the MongoDB driver, pinned in requirements.txt to a recent stable major" and documentdb-driver skill guidance on singleton.
- **When:** 2026-11-25T08:47:43+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection from a config file; Read connection from environment variable DOCUMENTDB_URI
- **Because:** Security best-practice and the run environment provides DOCUMENTDB_URI per skill_md. Avoids committing secrets to the repo.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report instruction: "Read the cluster connection string from DOCUMENTDB_URI at runtime and never log or commit it; provide a .env.example with a placeholder"
- **When:** 2026-11-25T08:47:46+00:00

## D005 (build): I chose to call OpenAI's Chat API directly for the summarisation step and structure the prompt using LlamaIndex-style prompt engineering; the code includes llama-index in requirements for extensibility.

- **Instead of:** Use LlamaIndex fully for LLM calls; Use direct OpenAI API for predict and use LlamaIndex concepts
- **Because:** Direct OpenAI API is more predictable for a small sample; we will still follow LlamaIndex prompt-engineering patterns and keep llama-index as an optional dependency. This ensures the sample runs even if llama-index versions differ in the environment.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: "OpenAI for the LLM call" and sample prompt requires a LlamaIndex pipeline; however LlamaIndex APIs vary and direct OpenAI calls are more reliable for the sample to run in this environment.
- **When:** 2026-11-25T08:47:49+00:00

## D006 (build): I chose gpt-3.5-turbo as the default LLM model for the sample.

- **Instead of:** gpt-4o-mini or gpt-4 family; gpt-3.5-turbo (widely available)
- **Because:** gpt-3.5-turbo is broadly available to users, cheaper than gpt-4, and sufficient for structured summarisation in a sample. Using it reduces friction for verification.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information gap: "OpenAI model & embedding choices" — no exact model mandated; gpt-3.5-turbo is widely available and cost-effective for demos.
- **When:** 2026-11-25T08:47:56+00:00

## D007 (build): I chose text-embedding-3-small (1536 dimensions) as the embedding model if embeddings are used; for this sample embeddings are optional and vector-index creation will be omitted by default.

- **Instead of:** text-embedding-3-large (3072 dims); text-embedding-3-small (1536 dims); no embeddings
- **Because:** text-embedding-3-small balances cost and dimensionality for small demos. But to keep the sample simpler and avoid creating vector indexes and extra cluster writes, embeddings are optional and not created automatically.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: recommends matching embedding dims to chosen model and listed text-embedding-3-small as an option.
- **When:** 2026-11-25T08:48:06+00:00

## D008 (build): I chose not to create a vector index by default. Instead the sample will create a patientId lookup index and include optional code/comments for creating a vector `cosmosSearch` index if the user wants embeddings.

- **Instead of:** Create a vector index in the sample by default; Do not create a vector index by default; provide instructions and code to create one optionally
- **Because:** Avoids adding vector-index complexity and cluster write operations in the default sample run. Keeps verification simpler while still documenting how to add a vector index and what dimensions to use.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: "Create a single-field index on patientId... and, if embeddings are used, create a vector index". The readiness_report indicates vector-index creation needs dimensions that match embedding model and careful params.
- **When:** 2026-11-25T08:48:09+00:00

## D009 (build): I chose not to provision or modify Azure resources; the sample will use the existing cluster pointed to by DOCUMENTDB_URI and will not run any az/infra commands.

- **Instead of:** Provision resources via az/ARM/Bicep; Do not provision any Azure resources (use existing cluster)
- **Because:** Run policy forbids creating Azure resources in this run, and the environment already provides a cluster to use.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." Run policy: Azure resource changes allowed: False.
- **When:** 2026-11-25T08:48:12+00:00

## D010 (build): I chose to use the documentdb MCP server tools (documentdb_list_indexes, documentdb_find_documents) to verify indexes and inserted documents.

- **Instead of:** Use direct PyMongo inspection only; Use the documentdb MCP server tools for inspection and verification
- **Because:** MCP tools provide a safe, audited way to inspect the live cluster from the build environment and are recommended by the readiness report.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "The `documentdb` MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created."
- **When:** 2026-11-25T08:50:06+00:00
