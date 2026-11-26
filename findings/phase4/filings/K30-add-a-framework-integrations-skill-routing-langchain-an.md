---
id: K30
title: "Add a framework-integrations skill routing LangChain and LlamaIndex tasks to the official integrations"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P2
sample_count: 9
member_drafts:
  - 092-framework-integration-recipes-langchain-python-js-and-llamai.md
open_questions: 3
---

# Add a framework-integrations skill routing LangChain and LlamaIndex tasks to the official integrations

## What happens today

None of the kit's 17 skills mentions LangChain or LlamaIndex. A case-insensitive grep for `langchain|llamaindex|llama-index|llama_index` over `skills/`, `knowledge-base/`, `docs/` and `AGENTS.md` returns nothing. The `vector-search` skill shows raw `$search` + `cosmosSearch` pipelines, and the `driver` skill shows a singleton `MongoClient`. Neither connects to the two frameworks that AI-app prompts name most often.

Microsoft Learn already has this material: the AI frameworks hub (`ai-frameworks`), a LangChain Python RAG how-to (`build-rag-applications`), a LlamaIndex Python how-to (`query-knowledge-base`), a LangGraph state page (`persist-agent-state`) and a TypeScript LangChain agent quickstart (`quickstart-agent-nodejs`). The kit doesn't link to any of them, so an agent that loads only kit skills never finds them. Some integrations are published under the Azure DocumentDB name and some are still under the former "Azure Cosmos DB for MongoDB vCore" name. That split makes them hard to find by search, and Learn's own pages disagree with each other: `build-rag-applications` still teaches the deprecated `langchain-azure-ai` class through an import path that does not exist in the library, and `query-knowledge-base` says the LlamaIndex vector store is Python-only while the `ai-frameworks` table (correctly) ticks TypeScript.

## Why it matters

We ran an agent-readiness experiment: one run of 100 sample-app prompts, built by gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers. In that run, 9 distinct samples (13 findings) hit this gap. The counts come from that single run and may change on a re-run. Each time, the pattern was the same:

1. The prompt explicitly required LangChain or LlamaIndex.
2. The agent recorded "no LangChain/LlamaIndex + DocumentDB guidance" as a gap.
3. It made its own decision to **drop the framework** and hand-rolled a substitute:
   - It skipped LlamaIndex Node bindings as "uncertain".
   - It skipped LangChain JS because it couldn't tell which version works on Node 24.
   - It avoided `initialize_agent` after import errors.
   - It built a three-agent LangChain pipeline as plain functions.
4. The audit marked the framework requirement not met because the skill said nothing about it.

As a result, the samples silently diverge from their own prompts, each one invents a different "framework-like" loop, and none of them shows the integrations Microsoft documents.

## Proposed change

### 1. New rule-folder skill `skills/framework-integrations/`

`SKILL.md` front matter:

```yaml
---
name: documentdb-framework-integrations
description: Wiring LangChain (Python, JS/TS) and LlamaIndex (Python, TS) to Azure DocumentDB vector search (cosmosSearch). Use when a task names LangChain, LangGraph, LlamaIndex, "agent", "RAG" or "tool" together with DocumentDB. Gives current package/class names (some still published under the former "Azure Cosmos DB for MongoDB vCore" name), which ones are deprecated shims, links to the Learn how-tos, pinned interoperable versions, tool wrappers over the driver, and a mock-LLM smoke test.
license: MIT
---
```

Keep the body thin. It should link the five Learn pages above for full walkthroughs and carry only the facts an agent needs that are spread across them. Rule files use the `framework-` prefix and the kit's Incorrect/Correct template:

- **`framework-name-mapping.md`**: the table below, plus this sentence: *"Azure DocumentDB is the service formerly called Azure Cosmos DB for MongoDB vCore. LangChain now has `AzureDocumentDB*` classes; LlamaIndex still uses `AzureCosmosDBMongo*` / `azurecosmosmongo`, and LangChain's older `AzureCosmosDBMongo*` classes are deprecation shims. Search for both names, use the current one."*

  | Framework | Package | Class |
  |---|---|---|
  | LangChain Python (recommended) | `langchain-azure-cosmosdb` (1.0.1 on PyPI, 2026-09-24) | `AzureDocumentDBVectorSearch` (`from langchain_azure_cosmosdb import AzureDocumentDBVectorSearch`) |
  | LangChain Python (deprecated shim, do not recommend) | `langchain-azure-ai` | `AzureCosmosDBMongoVCoreVectorSearch` in `langchain_azure_ai.vectorstores.azure_cosmos_db_mongo_vcore`; emits `DeprecationWarning` and redirects to `langchain-azure-cosmosdb` since langchain-ai/langchain-azure#870 (merged 2026-07-28). The `langchain_azure_ai.vectorstores.azure_cosmos_db` path that Learn's `build-rag-applications` shows has never existed in the repository. |
  | LangChain JS/TS | `@langchain/azure-cosmosdb` | `AzureDocumentDBVectorStore`, `AzureDocumentDBSimilarityType` (`AzureCosmosDBMongoDBVectorStore` is legacy) |
  | LlamaIndex Python | `llama-index-vector-stores-azurecosmosmongo` (0.9.0, current) | `AzureCosmosDBMongoDBVectorSearch` |
  | LlamaIndex TS | `@llamaindex/azure` (0.2.1 on npm) | `AzureCosmosDBMongoDBVectorStore`, exported from `src/index.ts` of `run-llama/LlamaIndexTS` `packages/providers/storage/azure`; cite the GitHub source or the npm page, not the developers.llamaindex.ai API-reference URL, which returns 404 |

  Caveat to state next to the LangChain Python row: `langchain-azure-cosmosdb` 1.0.1 pulls `azure-cosmos`, `langgraph` and `langgraph-checkpoint` as hard dependencies.

- **`framework-langchain-python.md`**:
  - Correct: `pip install langchain-azure-cosmosdb`, then `AzureDocumentDBVectorSearch.from_connection_string(connection_string=..., namespace="db.coll", embedding=..., index_name=...)`.
  - Call `create_index(kind=CosmosDBVectorSearchType.VECTOR_DISKANN | VECTOR_HNSW | VECTOR_IVF, dimensions=..., similarity=CosmosDBSimilarityType.COS)` once, then `as_retriever(...)`.
  - Add a `@tool` that wraps a pymongo aggregation, and build the agent with LangChain 1.x `create_agent` or LangGraph.
  - One paragraph: `initialize_agent` / `AgentExecutor` are legacy, and imports moved to `langchain_openai` / `langchain_core`.
  - Incorrect: `pip install langchain-azure-ai` with `AzureCosmosDBMongoVCoreVectorSearch` (a deprecation shim that warns and points to `langchain-azure-cosmosdb`; Learn's `build-rag-applications` page is stale on this and its import path does not exist); a hand-rolled loop; `$vectorSearch` (Atlas syntax); embeddings stored as BSON binary. Learn requires an array of numbers: a document whose vector is BSON binary (subtype 9 included) is stored but not indexed and is silently absent from results, and a binary query vector is rejected ("expected an array type field"). The rule file should name BSON binary explicitly rather than only saying "must be `number[]`".
- **`framework-langchain-js.md`**:
  - Correct: `AzureDocumentDBVectorStore` with `indexOptions: { kind: "vector-ivf" | "vector-hnsw" | "vector-diskann", dimensions, similarity: AzureDocumentDBSimilarityType.COS }`, as in `quickstart-agent-nodejs`.
  - Methods: `fromDocuments` / `similaritySearchVectorWithScore`.
  - Tools: `tool()` with a Zod schema, plus `createAgent` from `langchain`.
  - A `package.json` block for Node 22/24 (`langchain`, `@langchain/core`, `@langchain/openai`, `@langchain/azure-cosmosdb`, `mongodb`, `zod`) with exact versions verified in CI. Pin `mongodb` to the 7.x line: MongoDB's compatibility table marks driver 7.0 to 7.9 as compatible with Node.js 24 and leaves the Node 24 cell blank for 6.11 to 6.21 (untested), and 7.x requires Node >= 20.19.0; Microsoft's own `ai/vector-search-agent-typescript` sample pins `mongodb ^7.1.0`.
  - Link `Azure-Samples/documentdb-samples` `ai/vector-search-agent-typescript`.
- **`framework-llamaindex-python.md`**:
  - Correct: `AzureCosmosDBMongoDBVectorSearch(mongodb_client=..., db_name=..., collection_name=..., index_name=..., embedding_key="embedding", text_key="text", cosmos_search_kwargs={"kind": "vector-diskann", "dimensions": 1536, "similarity": "COS"})`, then `StorageContext.from_defaults(vector_store=...)` and `VectorStoreIndex.from_documents`.
  - Behaviour of 0.9.0, which is the current release (PyPI latest; `pyproject.toml` on main says 0.9.0) and is confirmed in the integration's `base.py` as well as on Learn's `query-knowledge-base`:
    - the constructor ends with `_create_vector_search_index()`, which issues `createIndexes` immediately, so no separate `create_index` call is needed and the index exists before any document is ingested. It re-sends `createIndexes` on every construction and does not catch the error: on the service a repeat is a no-op only when the name and the options document are identical, key order and defaults included; another vector index on the path (for example from a seed script) fails with 85 `IndexOptionsConflict`, and the same name with other options or another key order with 86 `IndexKeySpecsConflict` (managed test, 2026-11-25, raw `createIndexes`; the store itself was not run), so construction would fail. Create the index through the store only, or have the seed script send exactly the options document the store builds (the same keys in the same order, with the store's own defaults; read them from the store's source for the installed version, since they were not re-checked here);
    - without `kind`, the index defaults to `vector-hnsw`, whatever `index_name` says; HNSW (and DiskANN) need an M30 or higher tier, so on M10/M20/M25 and the free tier pass `kind: "vector-ivf"` explicitly or the constructor fails;
    - `_query()` reads only `pre_filter` from the kwargs and the file never references `query.filters` or `MetadataFilters`, so LlamaIndex `MetadataFilters` are ignored: use `pre_filter` via `vector_store_kwargs` plus `create_filter_index("metadata.<field>")`.
  - Show the stored document shape (`embedding` as `number[]`, a `metadata` sub-document, the score on `source_nodes`) and a `FunctionTool.from_defaults` driver-backed tool.
  - Pin `llama-index-core` + `llama-index-vector-stores-azurecosmosmongo` versions that install on Python 3.11–3.13, or state the supported runtime. Known constraints: 0.9.0 declares `llama-index-core>=0.13.0,<0.15` and `pymongo>=4.6.1,<5`; the current PyMongo line (4.19/4.20) requires Python >= 3.11; Learn's install command is unpinned and Microsoft publishes no tested versions for this integration (see Open question 1).
- **`framework-llamaindex-ts.md`**: a Node LlamaIndex path exists, so say so and show it.
  - Correct: `npm install @llamaindex/azure`, then `AzureCosmosDBMongoDBVectorStore` (its `createIndex()` issues `createIndexes` with `cosmosSearchOptions.kind` of `vector-hnsw` | `vector-diskann` | `vector-ivf`, and the docstring says the index is created automatically by default), wired into a minimal tested `VectorStoreIndex.fromDocuments` + `asQueryEngine` example. The same package also ships `AzureCosmosMongovCore` DocumentStore, IndexStore, KVStore and ChatStore.
  - Note for agents: Learn's `query-knowledge-base` note "The vector store integration is Python-only. If you're building a TypeScript app, use the mongodb driver" is stale; the `ai-frameworks` table's TypeScript tick for LlamaIndex is the correct statement. No Learn how-to covers the TS store yet, so cite the LlamaIndexTS GitHub source or the npm page.
  - Incorrect: dropping LlamaIndex for a hand-rolled retriever because "no Node bindings exist". A custom retriever/tool over the `mongodb` driver is only a fallback when the package cannot be installed, and the deviation must then be stated in the sample README.

Each Correct section ends with two things:

- A **mock-LLM smoke test** (`FakeListChatModel` / `MockLLM` with deterministic synthetic embeddings), so an agent can prove the wiring without an API key.
- A short **multi-agent skeleton** pointer (fetch -> score -> explain, each a tool with a JSON contract) that links the planner/synthesizer pattern in `quickstart-agent-nodejs`.

### 2. `AGENTS.md`, under "Route B — Text skills", after step 3

> **Named framework rule.** If the task names LangChain, LangGraph, LlamaIndex or another framework, load `documentdb-framework-integrations` and use that framework's DocumentDB integration, or the documented driver fallback where no integration exists. Do not substitute a hand-rolled "framework-like" loop. If the integration cannot be installed, record the exact install error and the pinned versions tried, state the deviation in the README, and prefer stopping to ask over silently changing the deliverable.

### 3. Catalog entries

- `AGENTS.md` "Skills in this kit": `| documentdb-framework-integrations | skills/framework-integrations/ | Wiring LangChain / LlamaIndex (Py, JS/TS) to cosmosSearch; package name mapping; pinned versions; tool wrappers; mock-LLM tests |`
- `docs/SKILLS.md` rule-folder table: `| framework-integrations/ | framework- | LangChain + LlamaIndex vector stores and tool wrappers over the driver; current vs former-name package mapping; Learn links |`
- A `CHANGELOG.md` entry, and `metadata.json` if sibling folders have one.
- Source hygiene for the PR: cite `https://github.com/run-llama/LlamaIndexTS/blob/main/packages/providers/storage/azure/src/vectorStore/AzureCosmosDBMongoVectorStore.ts` or `https://www.npmjs.com/package/@llamaindex/azure` for the TS store; the `developers.llamaindex.ai` API-reference URL in the source draft returns 404. Cite `https://pypi.org/project/langchain-azure-cosmosdb/` and `https://github.com/langchain-ai/langchain-azure/pull/870` for the LangChain Python package and its deprecation shim.

### 4. Verification (optional follow-up if too heavy for this PR)

Add a CI job that installs each rule's pinned dependencies on Python 3.11–3.13 and Node 22/24, then runs the mock-LLM smoke tests against the local DocumentDB container from `documentdb-local-deployment`. Pins that nothing exercises go stale.

## Evidence

- `runs/02-ai-powered-product-recommendations/20261124-181835/` (`decisions.jsonl` D004, `doc-gaps.md`): Node + LlamaIndex dropped
- `runs/10-support-ticket-rag-assistant/20261124-204529/` (`decisions.jsonl` D016, D018): guessed `llama-index==0.9.2`, failed to install on Python 3.13, removed. [needs SME confirmation] This install failure may be partly a build-environment artifact (see Open question 1)
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/` (`decisions.jsonl` D011): LangChain JS not installed
- `runs/14-dynamic-pricing-engine/20261124-184622/` (`decisions.jsonl` D011, `doc-gaps.md`): `initialize_agent` import errors, hand-rolled loop
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (`doc-gaps.md`): three-agent pipeline as plain functions

Also affected: samples 08, 09, 14-telehealth and 15.

## Resolved

- Vector-index facts: settled 2026-11-25 from the Learn vector-search, half-precision, product-quantization and limitations pages and engine issue documentdb/documentdb#109, see findings/phase4/DECISIONS.md.
  - BSON binary vectors are stored and returned intact but not indexed, so they are silently absent from vector results, and a binary query vector is rejected with "expected an array type field"; the `framework-*` rule files name BSON binary explicitly as the Incorrect form. Settled by the vector-search page (DiskANN field table and IVF Important box) and documentdb/documentdb#109.
- Framework-integration facts: settled 2026-11-25 from library source, PyPI/npm and Learn (DECISIONS.md, SME topic 13 and topic 4).
  - LangChain Python package for the kit: recommend `langchain-azure-cosmosdb` with `AzureDocumentDBVectorSearch`; `langchain-azure-ai`'s `AzureCosmosDBMongoVCoreVectorSearch` has been a deprecation shim since langchain-ai/langchain-azure#870 (merged 2026-07-28; still a shim in langchain-azure-ai 1.4.0 of 2026-11-17), and Learn's `ai-frameworks` page already links the `langchain-azure-cosmosdb` reference while `build-rag-applications` is the stale page. Which package Learn itself standardises on is a Learn question that stays open for Microsoft (topic 13, open item 5) and does not block the kit. Sources: https://github.com/langchain-ai/langchain-azure/pull/870; https://github.com/langchain-ai/langchain-azure/blob/main/libs/azure-ai/langchain_azure_ai/vectorstores/azure_cosmos_db_mongo_vcore.py; https://pypi.org/project/langchain-azure-cosmosdb/ (1.0.1); https://pypi.org/project/langchain-azure-ai/ (1.4.0); https://learn.microsoft.com/en-us/azure/documentdb/ai-frameworks; https://learn.microsoft.com/en-us/azure/documentdb/build-rag-applications.
  - LlamaIndex TypeScript store: it exists; `@llamaindex/azure` (npm 0.2.1) exports `AzureCosmosDBMongoDBVectorStore`, whose `createIndex()` issues `createIndexes` with kind `vector-hnsw` | `vector-diskann` | `vector-ivf`, so the driver fallback is not the official answer and Learn's `query-knowledge-base` "Python-only" note is wrong while the `ai-frameworks` TypeScript tick is right. Sources: https://github.com/run-llama/LlamaIndexTS/blob/main/packages/providers/storage/azure/src/vectorStore/AzureCosmosDBMongoVectorStore.ts; https://github.com/run-llama/LlamaIndexTS/blob/main/packages/providers/storage/azure/src/index.ts; https://www.npmjs.com/package/@llamaindex/azure; https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base; https://learn.microsoft.com/en-us/azure/documentdb/ai-frameworks.
  - LlamaIndex 0.9.0 behaviour: still holds and 0.9.0 is the current release (PyPI latest; `pyproject.toml` on main); `base.py` ends `__init__` with `_create_vector_search_index()`, defaults `kind` to `vector-hnsw` (which needs M30 or higher) and reads only `pre_filter`, never `MetadataFilters`. Sources: https://pypi.org/project/llama-index-vector-stores-azurecosmosmongo/ (0.9.0); https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/vector_stores/llama-index-vector-stores-azurecosmosmongo/llama_index/vector_stores/azurecosmosmongo/base.py (lines 118-146, 295-315); https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base; https://learn.microsoft.com/en-us/azure/documentdb/limitations.

## Open questions

1. [needs SME confirmation] Which exact versions has Microsoft tested for the LlamaIndex integration and for Node 24 (DECISIONS.md topic 4, items 4.9-open and 4.10-open)? Learn's `query-knowledge-base` install command is unpinned and publishes no tested versions; the declared ranges are known (`llama-index-vector-stores-azurecosmosmongo` 0.9.0 needs `llama-index-core>=0.13.0,<0.15` and `pymongo>=4.6.1,<5`; PyMongo 4.19+ needs Python >= 3.11; MongoDB marks only `mongodb` 7.x as compatible with Node 24), so this PR will pin the exact versions resolved at filing time for Python 3.11–3.13 and Node 22/24 and asks the page owners to confirm or replace them. Sample 10's Python 3.13 install failure may be partly an artifact of the experiment's build environment (tracked separately), so it should not be read as proof that the packages are broken.
2. Maintainer decision: is the CI matrix in section 4 acceptable for this repo, or should it be a separate PR?
3. [needs SME confirmation] Sample counts come from one run and include samples where the build environment also interfered. Please confirm the count before it is quoted outside this issue.

## Source drafts

- 092-framework-integration-recipes-langchain-python-js-and-llamai.md
