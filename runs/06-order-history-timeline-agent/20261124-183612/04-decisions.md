# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 9 |
| operator | 2 |
| model_default | 2 |
| tool_result | 2 |
| readiness_report | 2 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:26:06+00:00

## D002 (build): I chose Python (target CPython 3.10+/3.13) with pip for dependencies.

- **Instead of:** Node.js/TypeScript; Python 3.10+ (virtualenv); Go
- **Because:** LangChain has primary Python support; prompt requested a Python LangChain agent. Python 3.10+ is available on the run environment (Python 3.13).
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Target a modern Python 3.10+ runtime (virtualenv)'.
- **When:** 2026-11-25T05:26:22+00:00

## D003 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI (no secrets written to repo).

- **Instead of:** Embed secrets in files; Read connection from environment variable DOCUMENTDB_URI
- **Because:** Security and prompt requirement to not commit secrets. Also simplifies running on developer machine where env var is set.
- **Reason came from:** `prompt`
- **Evidence:** Skill MD: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into a file'.
- **When:** 2026-11-25T05:26:30+00:00

## D004 (build): I chose to use the existing, pre-provisioned Azure DocumentDB cluster and not create new cloud resources.

- **Instead of:** Provision new cluster via az/ARM/Bicep/Terraform; Use existing cluster (no provisioning)
- **Because:** Avoids creating cloud resources (not allowed by run policy) and uses the provided cluster for verification.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.'; Run policy forbids creating resources.
- **When:** 2026-11-25T05:26:32+00:00

## D005 (build): I chose a single-shard collection named 'orders' in the database 'sample_retail_06' (no sharding).

- **Instead of:** Shard collection with a hot-write shard key; No sharding, single-shard orders collection
- **Because:** Sample app is lightweight and the prompt's run environment implies a ready-to-use cluster; sharding is unnecessary for the demo and would complicate the sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review 'No sharding by default (single-shard cluster)'.
- **When:** 2026-11-25T05:26:34+00:00

## D006 (build): I chose pymongo and will implement a singleton MongoClient (per documentdb-driver guidance).

- **Instead of:** Use MongoDB driver only; Use pymongo with singleton MongoClient per documentdb-driver guidance
- **Because:** Pymongo is the standard Python MongoDB driver and the documentdb-driver skill recommends a singleton client for connection reuse.
- **Reason came from:** `skill`
- **Evidence:** readiness_report guidance: 'Use standard MongoDB drivers (pymongo) and a singleton MongoClient.'
- **When:** 2026-11-25T05:26:37+00:00

## D007 (build): I chose to create indexes using the documentdb MCP server's documentdb_create_index tool (and also include index-creation code in the seed script as idempotent fallback).

- **Instead of:** Create indexes via pymongo in seed script; Create indexes using documentdb MCP create_index tool for verification
- **Because:** Using MCP tool demonstrates verification via the provided data-plane tools; seed script fallback ensures idempotency when running standalone.
- **Reason came from:** `prompt`
- **Evidence:** readiness_report: 'the documentdb MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.'
- **When:** 2026-11-25T05:26:40+00:00

## D008 (build): I chose OpenAI for the sample (chat + embeddings) and will read API key from OPENAI_API_KEY environment variable. Use text-embedding-3-small for embeddings (1536 dims).

- **Instead of:** OpenAI (gpt-4o) + text-embedding-3-small; Anthropic or local models
- **Because:** OpenAI is commonly available and integrates easily with LangChain; embedding dims are documented for text-embedding-3-small and match vector index guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Default to OpenAI for models: Chat model via environment variable OPENAI_API_KEY ... and embeddings via OpenAI text-embedding-3-small (1536 dims).'
- **When:** 2026-11-25T05:26:43+00:00

## D009 (build): I chose to relax the pymongo pin to a compatible range pymongo>=4.5,<5 to allow pip to find a matching wheel in the environment.

- **Instead of:** Pin exact versions as before; Relax dependency pins to compatible ranges
- **Because:** Avoids hard failure from an unavailable exact version while keeping compatibility with DocumentDB driver guidance.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed for pymongo==4.5.1; list of available versions shows 4.5.0 and 4.6.0 etc.
- **When:** 2026-11-25T05:27:33+00:00

## D010 (build): I chose to relax the langchain pin to langchain>=0.0.331,<1 to avoid unavailable exact versions and allow pip to choose a compatible release.

- **Instead of:** Pin exact langchain version; Relax langchain to a compatible range
- **Because:** Reduce install failures and maintain compatibility with LangChain APIs; sample code uses basic LangChain constructs available in many recent releases.
- **Reason came from:** `tool_result`
- **Evidence:** pip install reported not finding langchain==0.0.418 but many earlier releases exist; relaxing lets resolver find a matching wheel.
- **When:** 2026-11-25T05:27:43+00:00

## D011 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:29:55+00:00

## D012 (build): I chose Python 3.10+ (CPython) with a virtualenv and pip for dependency management.

- **Instead of:** Node.js/TypeScript; Python (3.10+); Go
- **Because:** LangChain and pymongo samples are commonly distributed in Python; the prompt asked for a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Target a modern Python 3.10+ runtime (virtualenv), e.g., support CPython 3.10 or 3.11. Use pip for dependency installation.' from prompt review.
- **When:** 2026-11-25T05:30:15+00:00

## D013 (build): I chose OpenAI as the default LLM and embedding provider (OPENAI_API_KEY and text-embedding-3-small).

- **Instead of:** OpenAI (OpenAI API); Azure OpenAI; Anthropic/Other
- **Because:** OpenAI is a common default, and the prompt review left model choice unspecified; using OpenAI keeps the sample simple and widely usable.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Default to OpenAI for models: Chat model via environment variable OPENAI_API_KEY ... embeddings via OpenAI text-embedding-3-small (1536 dims).'.
- **When:** 2026-11-25T05:30:21+00:00

## D014 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use stored credentials in files; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** This prevents writing secrets into files and follows the provided environment convention.
- **Reason came from:** `prompt`
- **Evidence:** Skill MD: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time.'
- **When:** 2026-11-25T05:30:25+00:00

## D015 (build): I chose not to provision resources and to use the existing DocumentDB cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision resources via az/ARM/Bicep (create cluster); Use existing cluster and do not provision
- **Because:** Cluster already exists and policy forbids provisioning; sample must use it.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Also run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T05:30:29+00:00

## D016 (build): I chose single-shard collection (no sharding) for the sample orders collection.

- **Instead of:** Shard collection (pick shard key); Single-shard collection (no sharding)
- **Because:** Simpler for sample and consistent with prompt review assumption; avoids complexity of shard-key selection and cluster changes.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'No sharding by default (single-shard cluster)'; also sample is small synthetic dataset.
- **When:** 2026-11-25T05:30:32+00:00

## D017 (build): I chose to create indexes from the seed script using pymongo's create_index, and also verify indexes using the documentdb MCP server tools.

- **Instead of:** Create indexes using pymongo client in seed script; Create indexes using MCP documentdb_create_index tool; Both
- **Because:** Creating indexes via pymongo is straightforward and avoids extra permissions; verification via MCP tools strengthens the sample's verification step.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Use standard MongoDB drivers (pymongo) and a singleton MongoClient.' MCP server is available to inspect and verify indexes.
- **When:** 2026-11-25T05:30:34+00:00

## D018 (build): I chose to run verification tests against the live cluster (the environment provides a reachable cluster).

- **Instead of:** Run tests against live cluster; Mock the cluster so tests run offline
- **Because:** Live verification ensures indexes and queries behave as intended; the run environment supports this and policy allows it.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'A vector-capable Azure DocumentDB cluster ... is reachable from this machine.'
- **When:** 2026-11-25T05:30:36+00:00
