# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 8 |
| model_default | 7 |
| readiness_report | 4 |
| operator | 3 |
| tool_result | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:55:47+00:00

## D002 (build): I chose Python 3.11 runtime with a virtualenv for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.x
- **Because:** Python is the prompt's requested language for a LangChain agent and is best-supported for LangChain examples.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use a recent Python 3.x runtime (assume Python 3.11 or 3.10) and a virtualenv; tests and requirements will target that runtime.'
- **When:** 2026-11-25T05:56:05+00:00

## D003 (build): I chose the official synchronous pymongo driver (pymongo >= 4.4) and the singleton MongoClient pattern.

- **Instead of:** pymongo (synchronous) >=4.4; motor (async)
- **Because:** Synchronous pymongo is simple for a sample CLI app and aligns with DocumentDB driver guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official pymongo driver (pymongo >= 4.4) compatible with MongoDB 7.0; use synchronous pymongo client with singleton MongoClient pattern.'
- **When:** 2026-11-25T05:56:08+00:00

## D004 (build): I chose OpenAI via LangChain as the primary LLM integration, with a configurable mock fallback when OPENAI_API_KEY is not set (USE_MOCK_LLM env var).

- **Instead of:** Use OpenAI via LangChain; Use an on-prem/local LLM; Use a mock-only rule engine
- **Because:** OpenAI + LangChain is a common, well-supported configuration for samples; adding a mock fallback ensures verification can run without a paid API key.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Recommended LLM and embedding provider (and environment variable names) — builder must decide.'
- **When:** 2026-11-25T05:56:12+00:00

## D005 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:56:27+00:00

## D006 (build): I chose Python 3.11 (synchronous pymongo + LangChain).

- **Instead of:** Node.js (JavaScript); Python 3.11 (synchronous pymongo + LangChain); Go
- **Because:** Python has strong LangChain and pymongo ecosystem and aligns with the prompt asking for a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will use a recent Python 3.x runtime (assume Python 3.11 or 3.10) and a virtualenv; tests and requirements will target that runtime.' from the prompt review.
- **When:** 2026-11-25T05:56:40+00:00

## D007 (build): I chose the synchronous pymongo driver (pymongo >= 4.4) with a singleton MongoClient pattern.

- **Instead of:** Motor (async); pymongo >=4.4 synchronous client
- **Because:** Synchronous pymongo is simplest for a sample CLI app and the documentdb-driver skill recommends singleton pattern.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official pymongo driver (pymongo >= 4.4) compatible with MongoDB 7.0; use synchronous pymongo client with singleton MongoClient pattern.'
- **When:** 2026-11-25T05:56:43+00:00

## D008 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Read creds from code/config file (insecure); Read DATABASE connection string from DOCUMENTDB_URI env var
- **Because:** Security best practice and the sample guidance explicitly requires using DOCUMENTDB_URI.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read the DATABASE connection string from DOCUMENTDB_URI at runtime (do not hardcode)'.
- **When:** 2026-11-25T05:56:46+00:00

## D009 (build): I chose to make the LLM provider configurable via environment variables and default to OpenAI (OPENAI_API_KEY) and model name from ENV MODEL (default 'gpt-4').

- **Instead of:** Use Azure OpenAI provider bindings; Use OpenAI (openai.com) via LangChain by default
- **Because:** OpenAI is commonly available and LangChain supports it; making provider configurable keeps sample flexible.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Recommended LLM and embedding provider (and environment variable names) is missing; the builder must decide.'
- **When:** 2026-11-25T05:56:49+00:00

## D010 (build): I chose not to include vector search in this sample and instead implement aggregation-based demand metrics and simple indexed queries.

- **Instead of:** Create vector indexes and use vector search; Do not use vector search; use simple aggregations and indexed lookups
- **Because:** Keeps sample focused, simpler to run and verify, and meets prompt requirements for querying demand metrics, competitor prices, and margin rules.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'No explicit vector or full-text index is required unless the sample adds semantic search.'
- **When:** 2026-11-25T05:56:52+00:00

## D011 (build): I chose to implement a lightweight orchestration that exposes DocumentDB query functions as 'tools' and uses LangChain's ChatOpenAI for the LLM; the orchestration calls tools, builds a reasoning prompt that instructs step-by-step chain-of-thought, calls the LLM, extracts a numeric price, and writes it back atomically.

- **Instead of:** Use full LangChain agent initialization (risky due to LangChain API variability); Implement lightweight orchestration using LangChain LLM plus our own 'tools' wrappers for DB calls
- **Because:** This keeps the sample stable across LangChain versions while still demonstrating tools and step-by-step reasoning; it remains faithful to the prompt by exposing DocumentDB functions as callable tools used by the agent logic.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report noted 'LangChain tool-wrapper examples for DocumentDB' are missing and API surface varies; to avoid fragile agent API dependencies, a simple orchestrator is more robust.
- **When:** 2026-11-25T05:57:07+00:00

## D012 (build): I chose to call the OpenAI Python SDK directly (openai.ChatCompletion) instead of LangChain ChatOpenAI because the installed LangChain package does not include ChatOpenAI in the expected import path in this environment.

- **Instead of:** Fix LangChain import variants and pin a specific LangChain API; Switch to calling OpenAI SDK directly for stability
- **Because:** Direct OpenAI SDK calls are stable and keep the sample simple and robust across LangChain version differences; the sample still uses LangChain concepts (tools) but the LLM call will use openai directly.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError: cannot import name 'ChatOpenAI' from 'langchain.chat_models' (runtime error observed).
- **When:** 2026-11-25T05:58:45+00:00

## D013 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:00:40+00:00

## D014 (build): I chose Python 3.11 (using a virtualenv) for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.x; Go
- **Because:** Python is the requested language in the sample prompt and has strong LangChain and pymongo support; using a modern 3.x runtime ensures compatibility.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use a recent Python 3.x runtime (assume Python 3.11 or 3.10) and a virtualenv; tests and requirements will target that runtime.'
- **When:** 2026-11-25T06:01:02+00:00

## D015 (build): I chose the synchronous pymongo driver (pymongo >= 4.4) with a singleton MongoClient.

- **Instead of:** motor (async); pymongo sync client
- **Because:** Synchronous pymongo is simpler for the sample and aligns with DocumentDB driver best-practices guidance; singleton MongoClient avoids per-request creation overhead.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official pymongo driver (pymongo >= 4.4) compatible with MongoDB 7.0; use synchronous pymongo client with singleton MongoClient pattern.'
- **When:** 2026-11-25T06:01:09+00:00

## D016 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Embed secrets in files; Read connection string from env var DOCUMENTDB_URI
- **Because:** Do not write secrets into files; environment variable is standard and matches the provided run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read the DATABASE connection string from DOCUMENTDB_URI at runtime (do not hardcode)'.
- **When:** 2026-11-25T06:01:12+00:00

## D017 (build): I chose not to provision resources and to use the existing reachable Azure DocumentDB cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster (Bicep/Terraform/az); Use existing reachable cluster
- **Because:** The environment already provides a cluster to use and the run policy disallows creating new Azure resources; using the existing cluster keeps the sample safe and reproducible.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Also run_policy forbids Azure resource changes.
- **When:** 2026-11-25T06:01:14+00:00

## D018 (build): I chose the data model with collections: products, demand_metrics, competitor_prices, margin_rules and simple document shapes described in README.

- **Instead of:** Multiple collection names/sharding; Create collections: products, demand_metrics, competitor_prices, margin_rules
- **Because:** These collections directly map to the data the pricing agent needs and keep the schema small and readable for a sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will create collections: products, demand_metrics, competitor_prices, margin_rules. Products have fields: { _id, sku, price, cost, updated_at, ... }'.
- **When:** 2026-11-25T06:01:18+00:00

## D019 (build): I chose to create indexes: products.sku (unique), competitor_prices {sku:1, timestamp:-1}, demand_metrics {sku:1, timestamp:-1}, margin_rules {sku_or_category:1}.

- **Instead of:** No indexes; Create helpful indexes on sku and timestamp
- **Because:** Indexes speed queries the sample uses (recent competitor prices and metrics grouped by SKU) and reflect typical patterns; keep write costs low for a small sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'indexes will include an index on sku and timestamp for competitor_prices and a helpful index on products.sku.'
- **When:** 2026-11-25T06:01:20+00:00

## D020 (build): I chose OpenAI (set OPENAI_API_KEY and MODEL env vars) as the default LLM provider for the LangChain agent.

- **Instead of:** OpenAI (OPENAI_API_KEY); Azure OpenAI; Local LLM
- **Because:** OpenAI is commonly available with LangChain examples; the sample will accept MODEL env var for flexibility. Users can swap in Azure OpenAI by modifying the code/configs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'The builder must decide which model/embedding API; LangChain integrations exist but do not prescribe one.'
- **When:** 2026-11-25T06:01:24+00:00

## D021 (build): I chose not to use embeddings or vector search for this sample; the agent will use structured data queries and an LLM for reasoning only.

- **Instead of:** Use embeddings and vector search; No embeddings (lexical data only)
- **Because:** Keeping the sample focused on DocumentDB queries and the LangChain tool pattern reduces complexity; vector indexes are available but not necessary for the described pricing logic.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'No embeddings are strictly required for the pricing logic unless the sample includes vector search.'
- **When:** 2026-11-25T06:01:27+00:00

## D022 (build): I chose to perform an atomic find_one_and_update to write back the updated price without extra optimistic-concurrency filtering.

- **Instead of:** Use optimistic concurrency with expected price in filter; Use a single atomic find_one_and_update without optimistic concurrency
- **Because:** find_one_and_update performs the atomic update required for the sample; optimistic concurrency could be added but would complicate the demonstration.
- **Reason came from:** `prompt`
- **Evidence:** Prompt requirement: 'then write the updated price back to the product document atomically.'
- **When:** 2026-11-25T06:01:30+00:00

## D023 (build): I chose to use the documentdb MCP server tools (documentdb_list_databases, documentdb_sample_documents) to verify collections and sample documents programmatically.

- **Instead of:** Use mongosh manually; Use documentdb MCP server tools programmatically
- **Because:** Programmatic verification via the MCP server is reproducible in CI and avoids needing mongosh locally.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: mongosh is not on PATH; MCP server is available and recommended as a full workaround.
- **When:** 2026-11-25T06:02:36+00:00

## D024 (build): I chose to use a lightweight orchestration that calls the DocumentDB tools and prompts the LLM via the OpenAI SDK when OPENAI_API_KEY is present; otherwise fall back to deterministic pricing logic and still perform an atomic update. This avoids brittle LangChain API import issues in different versions.

- **Instead of:** Force using LangChain initialize_agent and attempt to resolve import issues; Use a lightweight orchestration (no initialize_agent) that still exposes tool functions and falls back to deterministic logic if no LLM key
- **Because:** Keeps the sample runnable in environments without a working LangChain agent initializer and still demonstrates the tools and atomic update behavior required by the prompt.
- **Reason came from:** `tool_result`
- **Evidence:** Import errors encountered when trying to import ChatOpenAI / langchain.llms in the current environment.
- **When:** 2026-11-25T06:04:14+00:00
