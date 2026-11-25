# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| readiness_report | 2 |
| model_default | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:44:53+00:00

## D002 (build): I chose Python targeting the system python available on the machine (Python 3.13) and to build a Python package for the sample.

- **Instead of:** Use Node.js/TypeScript; Use Python 3.10/3.11
- **Because:** The prompt requested a Python LangChain sample; the environment already has Python 3.13 available so using it avoids mismatches.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Python 3.13.13 on PATH (inventory).'
- **When:** 2026-11-25T13:45:25+00:00

## D003 (build): I chose pymongo (sync) pinned to a modern 4.x series (pymongo>=4.3,<5.0) and to implement a process-wide MongoClient singleton.

- **Instead of:** motor (async); pymongo (sync)
- **Because:** PyMongo 4.x is a standard, well-supported driver; the documentdb-driver skill emphasizes a singleton client pattern. Synchronous code keeps the sample simpler for readers.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Use PyMongo (pymongo) as the MongoDB driver for Python, pinned to a recent stable 4.x release (e.g., pymongo>=4.3,<5.0). Apply the documentdb-driver guidance: create a process-wide singleton MongoClient and reuse it.'
- **When:** 2026-11-25T13:45:28+00:00

## D004 (build): I chose to read the Azure DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime and never commit secrets into repo files.

- **Instead of:** Read connection string from a config file; Embed credentials in code
- **Because:** Security and the run environment both expect secrets to come from env vars; this follows the documented guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Read the connection string from DOCUMENTDB_URI at runtime and use pymongo.MongoClient ... Provide a .env.example placeholder and never commit real credentials.'
- **When:** 2026-11-25T13:45:32+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing DocumentDB cluster reachable from the machine.

- **Instead of:** Provision a new DocumentDB cluster in Azure; Use the existing cluster in the environment
- **Because:** Policy forbids resource creation; the environment already provides a cluster to use for verification.
- **Reason came from:** `prompt`
- **Evidence:** run_policy: 'Azure resource changes allowed: False' and skill_md: 'a DocumentDB cluster is already provisioned and reachable... DOCUMENTDB_URI.'
- **When:** 2026-11-25T13:45:34+00:00

## D006 (build): I chose to keep collections unsharded (single-shard demo) and create three collections in database sample_retail_09: sales_velocity, lead_times, purchase_orders, plus agent_memory for dedupe.

- **Instead of:** Shard collections with a shard key now; Keep single-shard demo collections (no shard key)
- **Because:** The sample is demo-sized and the readiness report indicates single-shard demo is acceptable; sharding adds complexity and provisioning requirements not permitted here.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Builder will create three collections in `sample_retail_09`: `sales_velocity`, `lead_times`, and `purchase_orders`... No shard key unless scaling is required (single-shard demo).'
- **When:** 2026-11-25T13:45:37+00:00

## D007 (build): I chose a small synthetic seed (dozens of SKUs, tens-to-low-hundreds of documents) inserted idempotently via upsert for demo and CI friendliness.

- **Instead of:** Use large seed (thousands); Use small demo seed (dozens)
- **Because:** Small dataset keeps runtime short and cost negligible while demonstrating functionality.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'The script also creates required indexes. The seed size will be a small demo dataset (dozens of SKUs) suitable for local runs and CI.'
- **When:** 2026-11-25T13:45:40+00:00

## D008 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings and to create vector index dimensions matching 1536 if vectors are used.

- **Instead of:** Use OpenAI text-embedding-3-small (1536 dims); Use another embedding provider/model
- **Because:** OpenAI embeddings are common in samples; 1536 dims is a practical default and matches the assumption. This decision fills the gap noted in the readiness report about choosing an embedding model.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'assume 1536 dims if using OpenAI text-embedding-3-small.'
- **When:** 2026-11-25T13:45:43+00:00

## D009 (build): I chose to implement shared agent memory persisted in a small `agent_memory` collection in the same database to prevent duplicate orders across agent runs.

- **Instead of:** Implement shared memory in-process only; Persist shared agent memory to DocumentDB
- **Because:** Persisting memory to the DB demonstrates durability and enables multiple orchestrator runs to see recent POs; it's simple to implement and aligns with the prompt requirement.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review and sample requirements: orchestrator should use shared agent memory to avoid duplicate orders.
- **When:** 2026-11-25T13:45:47+00:00
