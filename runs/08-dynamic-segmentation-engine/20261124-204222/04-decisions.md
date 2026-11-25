# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 4 |
| readiness_report | 3 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:32:32+00:00

## D002 (build): I chose to target the Python runtime already on PATH (Python 3.13) for the sample and pin package versions in requirements.txt.

- **Instead of:** Use Python 3.11/3.12 pinned in requirements; Use the Python already on PATH (3.13)
- **Because:** Using the available Python avoids introducing venv setup steps that may differ across environments and ensures the sample runs with the existing interpreter.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report inventory: "Python 3.13.13 on PATH (inventory)"
- **When:** 2026-11-25T11:33:00+00:00

## D003 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read credentials from a local config file; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Security best-practice and the prompt explicitly instructs to read DOCUMENTDB_URI from the environment and never write secrets to files.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time."
- **When:** 2026-11-25T11:33:03+00:00

## D004 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new DocumentDB cluster as part of the sample (Bicep/Terraform/az); Do not provision and use the existing cluster provided via DOCUMENTDB_URI
- **Because:** The environment already provides a reachable cluster and the run policy forbids provisioning Azure resources in this run.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: "a cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI." and run_policy forbids Azure resource changes.
- **When:** 2026-11-25T11:33:06+00:00

## D005 (build): I chose to implement a LangChain-compatible agent that will use OpenAI (if OPENAI_API_KEY is provided) and fall back to a deterministic rule-based assigner when no API key is available.

- **Instead of:** Use an LLM-only agent for segmentation (OpenAI); Use deterministic rule-based segmentation without external AI
- **Because:** This keeps the sample faithful to the prompt (LangChain agent) while allowing the demo to run in environments without an LLM key. Secrets are read from env and not stored in files.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions and readiness report discuss using an embedding/chat provider (commonly OpenAI) but embedding/model selection is ambiguous.
- **When:** 2026-11-25T11:33:10+00:00

## D006 (build): I chose to provide both a minimal CLI for one-shot demos and a small FastAPI HTTP endpoint (POST /segment) to demonstrate how the agent can be called from an API.

- **Instead of:** Create only a CLI interface; Create a CLI and a small FastAPI HTTP endpoint
- **Because:** Provides both an easy-to-run demo (CLI) and a realistic integration point (HTTP API) for users.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from the prompt review suggested both a CLI and a FastAPI endpoint.
- **When:** 2026-11-25T11:33:16+00:00

## D007 (build): I chose to create the collections and indexes using pymongo in the seed script (idempotent operations), and then verify them with the documentdb MCP server tools.

- **Instead of:** Create indexes using the documentdb MCP server tools; Create indexes using pymongo in the seed script
- **Because:** Creating indexes from the language SDK is a common developer workflow; MCP will be used for verification only (read-only).
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: pymongo and documentdb MCP server available; creating resources via pymongo is straightforward and aligns with driver best practices.
- **When:** 2026-11-25T11:33:22+00:00

## D008 (build): I chose not to use vector indexes or embeddings for this sample because the segmentation logic is based on behavioural aggregates (recency, frequency, category affinity) and does not require semantic vectors.

- **Instead of:** Use vector indexes and embeddings in the sample; Do not use vector indexes; use aggregation only
- **Because:** Keeps the sample focused, simpler to run, and avoids needing to choose an embedding model and dimension.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: "If the sample does not require semantic vectors, no vector index will be used."
- **When:** 2026-11-25T11:33:28+00:00
