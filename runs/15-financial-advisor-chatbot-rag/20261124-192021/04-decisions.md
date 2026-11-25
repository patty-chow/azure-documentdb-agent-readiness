# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 7 |
| prompt | 6 |
| readiness_report | 4 |
| operator | 3 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:16:37+00:00

## D002 (build): I chose a custom Node.js RAG implementation that emulates LlamaIndex behavior (retrieval + prompt composition) and uses client-side similarity over embeddings stored in DocumentDB, because LlamaIndex is primarily Python and there's no authoritative Node LlamaIndex library available in the environment.

- **Instead of:** Use Python LlamaIndex service called from Node; Use a Node-native RAG implementation with LangChain.js; Use a custom Node.js RAG implementation that emulates LlamaIndex behavior
- **Because:** Running a Python service adds complexity and cross-language wiring; a small custom RAG in Node demonstrates the same concepts (vector retrieval, agent memory, tool integration) and runs natively in the environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LlamaIndex is primarily a Python library; there is no authoritative Microsoft Learn page or installed skill that prescribes an official Node.js LlamaIndex package or integration approach.'
- **When:** 2026-11-25T07:17:03+00:00

## D003 (build): I chose the official mongodb Node.js driver (npm package 'mongodb') v5.x and will implement a singleton MongoClient pattern.

- **Instead of:** mongodb driver v4.x; mongodb driver v5.x; use Mongoose ODM
- **Because:** Official driver gives direct control over connections and matches DocumentDB quickstarts; Mongoose is unnecessary for this small sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the mongodb Node.js driver (npm package `mongodb`) v5.x, and implement the singleton MongoClient pattern (per documentdb-driver guidance).'
Also readiness guidance: 'Read the runtime connection string from DOCUMENTDB_URI and use the official mongodb Node.js driver (MongoClient).'
- **When:** 2026-11-25T07:17:07+00:00

## D004 (build): I chose to use deterministic mock embeddings (fixed-dimension pseudo-random vectors) in the seed data so the sample is runnable without external API keys; README documents how to swap in real embeddings from OpenAI.

- **Instead of:** Call OpenAI for real embeddings during seed; Use deterministic mock embeddings in seed to avoid external API dependencies
- **Because:** Keeps the sample self-contained and runnable; still models real usage and allows users with API keys to regenerate embeddings.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Information gaps: Embedding model & dimension choice' and 'No embedding helper for Node.js available.' Also the run environment may not include OPENAI_API_KEY, so using mock embeddings avoids failures at verification time.
- **When:** 2026-11-25T07:17:11+00:00

## D005 (build): I chose to support OpenAI (via OPENAI_API_KEY) for real LLM calls when available, and fall back to a deterministic local mock responder when the key is not set.

- **Instead of:** Use OpenAI as LLM provider (gpt-4o-mini); Use local mock LLM reply function
- **Because:** Allows the sample to run end-to-end without external keys while enabling real LLM behavior when the user provides credentials. README will explain env vars and how to enable real LLMs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM/chat provider and credentials names missing. The builder must choose.'
- **When:** 2026-11-25T07:17:22+00:00

## D006 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:19:20+00:00

## D007 (build): I chose Node.js with Express and the mongodb driver (singleton MongoClient pattern).

- **Instead of:** Python (LlamaIndex native); Node.js (Express + mongodb driver)
- **Because:** The user asked for a 'Node.js LlamaIndex RAG agent' and the environment provides Node.js; building in Node.js matches the prompt and available tooling.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use the mongodb Node.js driver (npm package `mongodb`) v5.x...' and run environment: 'Node.js 24 with npm and npx is available.'
- **When:** 2026-11-25T07:19:56+00:00

## D008 (build): I chose the mongodb Node.js driver v5.x (latest 5.x released).

- **Instead of:** mongodb driver v4.x; mongodb driver v5.x (recommended)
- **Because:** v5.x is the current major series with async support and aligns with the documentdb-driver skill guidance to use a singleton MongoClient.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the mongodb Node.js driver (npm package `mongodb`) v5.x, and implement the singleton MongoClient pattern'.
- **When:** 2026-11-25T07:19:59+00:00

## D009 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a file in repo; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Secrets must not be stored in the repo; environment variables are the standard pattern and match provided guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read the runtime connection string from DOCUMENTDB_URI and use the official mongodb Node.js driver (MongoClient). Use tls=true ...'
- **When:** 2026-11-25T07:20:04+00:00

## D010 (build): I chose to use the existing DocumentDB cluster and create the sample database, collection and indexes there via the documentdb MCP server and the MongoDB driver. I will not provision any new Azure resources.

- **Instead of:** Provision a new cluster via az / Bicep / Terraform; Use the existing cluster and create resources within it via the documentdb MCP server
- **Because:** Provisioning new Azure resources is disallowed; use the existing cluster as instructed and use MCP tools to inspect/manage data-plane objects.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T07:20:08+00:00

## D011 (build): I chose to store embeddings inline in each knowledge document under an 'embedding' numeric array field, with documents shaped { _id, title, content, embedding, metadata }.

- **Instead of:** Embed vs reference heavy (store embeddings separately); Store embeddings inside 'embedding' field in each knowledge doc
- **Because:** Storing embeddings inline is simple for sample apps, matches readiness assumptions and documentdb-vector-search guidance that vectors are stored in a field and indexed with cosmosSearch.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will create a `knowledge` collection with documents like { _id, title, content, embedding, metadata: {source, id, date} } and store embeddings in an `embedding` field'
- **When:** 2026-11-25T07:20:10+00:00

## D012 (build): I chose to implement the RAG agent in Node.js with a small LlamaIndex-like retrieval layer (embedding-based retriever + prompt composition + OpenAI chat completions) rather than attempting to call Python LlamaIndex.

- **Instead of:** Use official LlamaIndex (Python) via subprocess or microservice; Implement a LlamaIndex-like RAG flow in Node.js using OpenAI embeddings + retriever + chat completions (LangChain.js style)
- **Because:** Running an external Python LlamaIndex service would complicate the sample and the run environment; a small Node-side retriever plus OpenAI chat completions demonstrates RAG behavior while keeping the app purely Node.js.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LlamaIndex is primarily a Python library; there is no authoritative... The builder must choose: (a) implement RAG using a Node-compatible RAG library (LangChain.js / custom retrieval) or (b) call a Python LlamaIndex service from Node.'
- **When:** 2026-11-25T07:20:14+00:00

## D013 (build): I chose to implement agent memory as an in-memory per-session conversation history for this sample.

- **Instead of:** Use persisted agent memory (database); Use simple in-memory session memory for agent
- **Because:** In-memory memory is sufficient for a sample and keeps the code small and focused; the README will document persistence as a production improvement.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Maintain conversation history in agent memory...' and sample constraints: keep sample small and simple.
- **When:** 2026-11-25T07:20:16+00:00

## D014 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:23:49+00:00

## D015 (build): I chose to implement the RAG agent in Node.js using a LangChain.js-like retrieval approach (custom retrieval + prompt) rather than Python LlamaIndex.

- **Instead of:** Python LlamaIndex service called from Node; Use LangChain.js or custom RAG in Node
- **Because:** No authoritative Node LlamaIndex exists; implementing RAG directly in Node keeps the sample self-contained and runnable in the provided Node environment.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'LlamaIndex Node.js availability and recommended integration... The builder must choose: (a) implement RAG using a Node-compatible RAG library (LangChain.js / custom retrieval + prompt) or (b) call a Python LlamaIndex service from Node.'
- **When:** 2026-11-25T07:24:26+00:00

## D016 (build): I chose Node.js (v24) with Express as the app framework.

- **Instead of:** Use Python LlamaIndex and call from Node; Use Node.js and Express with LangChain.js-like approach
- **Because:** The prompt mandates Node.js and the environment provides Node.js v24; Express keeps the API minimal and familiar for JavaScript developers.
- **Reason came from:** `prompt`
- **Evidence:** sample prompt requires 'Node.js LlamaIndex RAG agent'; run environment includes Node.js v24 and npm.
- **When:** 2026-11-25T07:24:29+00:00

## D017 (build): I chose the mongodb Node.js driver v5.x and will implement the singleton MongoClient pattern.

- **Instead of:** mongodb npm driver v4.x; mongodb npm driver v5.x
- **Because:** Driver v5.x is current and the documentdb-driver skill recommends a singleton client for Azure DocumentDB.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Use the mongodb Node.js driver (npm package `mongodb`) v5.x, and implement the singleton MongoClient pattern (per documentdb-driver guidance).'
- **When:** 2026-11-25T07:24:34+00:00

## D018 (build): I chose to use OpenAI text-embedding-3-small as the recommended provider (1536 dims) but seed the sample with deterministic, local embeddings when OPENAI_API_KEY is not present.

- **Instead of:** Embed generation at build time via OpenAI only; Generate deterministic local embeddings for sample and optionally use OpenAI when API key present
- **Because:** This keeps the sample runnable without external API keys while documenting how to switch to OpenAI-based embeddings when the user supplies credentials.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information_gaps: 'Embedding model & dimension choice... builder must decide...'; assumptions_from_prompt_review suggested OpenAI text-embedding-3-small as an example.
- **When:** 2026-11-25T07:24:38+00:00

## D019 (build): I chose to create the collection and seed documents from the app (seed script) and to create the vector search index during verification using the documentdb MCP server tools (if available).

- **Instead of:** Create vector index inside app using driver commands; Create vector index using the documentdb MCP server during verification
- **Because:** Index creation via the MCP server is safer for cluster-specific commands and keeps the app code driver-simple; the app-level seed remains idempotent and independent of cluster-specific index APIs.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill recommends specific vector index settings (e.g., vector-diskann with dimensions and similarity) and the MCP server provides a create-index tool for the live cluster.
- **When:** 2026-11-25T07:24:41+00:00

## D020 (build): I chose to implement the portfolio tool as a mocked local function/endpoint returning deterministic JSON used by the demo and tests.

- **Instead of:** Use a real brokerage API for portfolio tool; Use a mocked local HTTP portfolio tool returning sample JSON
- **Because:** Avoids requiring third-party credentials and keeps the sample self-contained while demonstrating the agent-tool interaction.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'client portfolio can be a mocked JSON returned by the tool for the example conversation.'
- **When:** 2026-11-25T07:24:44+00:00

## D021 (build): I chose the data model: a 'knowledge' collection with documents { _id, title, content, embedding: number[], metadata: {source, id, date, model, dims} }.

- **Instead of:** Store embeddings as binary/byte arrays; Store embeddings as array of numbers in field 'embedding' and include model & dims in metadata
- **Because:** This model is simple, compatible with DocumentDB vector index expectations, and records the embedding provenance for reproducibility.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review and documentdb-vector-search skill recommending storing model and dimensions alongside vectors.
- **When:** 2026-11-25T07:24:48+00:00

## D022 (build): I chose to use mongodb@^5.0.0 in package.json because the requested mongodb@^5.12.0 failed to resolve from npm.

- **Instead of:** Keep mongodb@^5.12.0; Downgrade to mongodb@^5.0.0 available in registry
- **Because:** Select a broadly-available 5.x driver version constraint to proceed with installation and keep MongoDB driver major version 5 semantics.
- **Reason came from:** `tool_result`
- **Evidence:** npm install error: 'No matching version found for mongodb@^5.12.0.'
- **When:** 2026-11-25T07:25:54+00:00
