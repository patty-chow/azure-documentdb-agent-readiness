---
title: "Add `documentdb-framework-integrations` skill: route LangChain (Py/JS) and LlamaIndex (Py/TS) tasks to the official DocumentDB vector stores and Learn how-tos, plus a \"use the named framework\" rule"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 9
findings: 13
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add `documentdb-framework-integrations` skill: LangChain (Py/JS) and LlamaIndex (Py/TS) wired to `cosmosSearch`

## What happens today

The kit ships 17 skills and none of them mentions LangChain or LlamaIndex (`grep -ril 'langchain\|llamaindex\|llama-index\|llama_index'` over `skills/`, `knowledge-base/`, `docs/` and `AGENTS.md` returns nothing). The `vector-search` skill shows raw `$search` + `cosmosSearch` pipelines and the `driver` skill shows a singleton `MongoClient`, but nothing bridges either one to the two frameworks that AI-app starter prompts name most often.

Microsoft Learn already covers this ground: an "Integrations for AI apps" hub page, a LangChain RAG how-to, a LlamaIndex how-to and a TypeScript LangChain agent quickstart. Upstream packages now include classes under the Azure DocumentDB name. The kit does not point to any of it, so an agent that loads only kit skills never finds it. In the runs below, the builder did not reach those pages either.

Current integration surface (checked 2026-11-25; re-verify package names and versions before merging):

| Framework | Package | Class | Source |
|---|---|---|---|
| LangChain Python | `langchain-azure-cosmosdb` (newer) | `AzureDocumentDBVectorSearch` (`from langchain_azure_cosmosdb import AzureDocumentDBVectorSearch`) | reference.langchain.com |
| LangChain Python (what Learn shows today) | `langchain-azure-ai` | `AzureCosmosDBMongoVCoreVectorSearch` (`langchain_azure_ai.vectorstores.azure_cosmos_db`) | Learn `build-rag-applications` |
| LangChain JS/TS | `@langchain/azure-cosmosdb` | `AzureDocumentDBVectorStore`, `AzureDocumentDBSimilarityType` (old `AzureCosmosDBMongoDBVectorStore` name is legacy) | Learn `quickstart-agent-nodejs`, docs.langchain.com |
| LlamaIndex Python | `llama-index-vector-stores-azurecosmosmongo` | `AzureCosmosDBMongoDBVectorSearch` (still under the former name) | Learn `query-knowledge-base` |
| LlamaIndex TS | LlamaIndex TS ships an `AzureCosmosDBMongoDBVectorStore` class (former name), but the package name has to be checked. Learn's LlamaIndex page says the vector store integration is Python-only and tells TypeScript apps to use the `mongodb` driver with `$search` + `cosmosSearch`. | | developers.llamaindex.ai TS API reference; Learn `query-knowledge-base` |

## Why it matters

In a 100-sample readiness run (gpt-5-mini, this kit + the DocumentDB/Azure/Learn MCP servers), 13 findings across **9 distinct samples** hit this gap. The failure mode is the same every time:

1. The starter prompt explicitly requires LangChain or LlamaIndex.
2. Readiness lists "no LlamaIndex/LangChain + DocumentDB guidance found" as an information gap.
3. The builder records a `model_default` decision to **drop the framework** and ships a hand-rolled substitute:
   - sample 02 (Node, LlamaIndex): D004 "implement a lightweight agent-like flow ... instead of relying on LlamaIndex Node bindings" (availability "uncertain").
   - sample 10 (Python, LlamaIndex): D018 removed `llama-index` after guessing `llama-index==0.9.2`, which does not install on Python 3.13, then fell back to direct OpenAI calls.
   - sample 12 (Node, LangChain): D011 chose not to install `langchain` because a compatible version for Node 24 was uncertain. Learn's `quickstart-agent-nodejs` already shows a working LangChain JS stack (`langchain` `createAgent`/`tool`, `@langchain/openai`, `@langchain/azure-cosmosdb`).
   - sample 14 dynamic-pricing (Python, LangChain): D011 avoided `initialize_agent` after import errors "due to LangChain API variability" and hand-rolled the tool loop.
   - sample 06 (Python, LangChain multi-agent): implemented fetch->score->explain as plain functions.
4. The audit marks the framework requirement `not_met` / `partly_met` with cause `skill_silent`.

Net effect: published samples silently diverge from their own prompts. Each builder re-invents a different "LangChain-like" or "LlamaIndex-like" loop, so the gallery is inconsistent and shows none of the integrations that Microsoft documents.

## Proposed change

### 1. New rule-folder skill: `skills/framework-integrations/`

`SKILL.md` front matter:

```yaml
---
name: documentdb-framework-integrations
description: Wiring LangChain (Python, JS/TS) and LlamaIndex (Python; TS via driver fallback) to Azure DocumentDB vector search (cosmosSearch). Use when a task names LangChain, LangGraph, LlamaIndex, "agent", "RAG" or "tool" together with DocumentDB. Gives current package/class names (some still published under the former "Azure Cosmos DB for MongoDB vCore" name), links to the Learn how-tos, pinned interoperable versions, tool wrappers over the driver, and a mock-LLM smoke test.
license: MIT
---
```

The skill should be thin and link to Learn for the full walkthroughs: https://learn.microsoft.com/en-us/azure/documentdb/ai-frameworks, `build-rag-applications`, `query-knowledge-base`, `persist-agent-state` (LangGraph) and `quickstart-agent-nodejs`. Its own job is the agent-facing facts that those pages spread across several places.

Rule files (prefix `framework-`, same Incorrect/Correct template as the other rule folders):

- **`framework-name-mapping.md`**: the table above, plus the sentence agents need most. *"Azure DocumentDB is the service formerly called Azure Cosmos DB for MongoDB vCore. LangChain now has `AzureDocumentDB*` classes; LlamaIndex and some older LangChain classes still use `AzureCosmosDBMongo*` / `azurecosmosmongo`. Search for both names."*
- **`framework-langchain-python.md`**:
  - Correct: `AzureDocumentDBVectorSearch` from `langchain-azure-cosmosdb`, or `AzureCosmosDBMongoVCoreVectorSearch.from_connection_string(connection_string=..., namespace="db.coll", embedding=..., index_name=...)` from `langchain-azure-ai`, as on the Learn page.
  - Call `create_index(kind=CosmosDBVectorSearchType.VECTOR_DISKANN | VECTOR_HNSW | VECTOR_IVF, dimensions=..., similarity=CosmosDBSimilarityType.COS, ...)` once, then `as_retriever(...)`.
  - For agent use, add a `@tool` function that wraps a pymongo aggregation, and build the agent with LangChain 1.x `create_agent` (or LangGraph). Note in one paragraph that `initialize_agent` / `AgentExecutor` are legacy and that import paths moved to `langchain_openai` / `langchain_core`.
  - Incorrect: hand-rolled loop, `$vectorSearch` (Atlas), embeddings stored as BSON binary (not indexed; must be `number[]`).
- **`framework-langchain-js.md`**:
  - Correct: `AzureDocumentDBVectorStore` from `@langchain/azure-cosmosdb`, with `indexOptions` such as `{ kind: "vector-ivf" | "vector-hnsw" | "vector-diskann", dimensions, similarity: AzureDocumentDBSimilarityType.COS }` (follow the shape in `quickstart-agent-nodejs`).
  - Methods: `fromDocuments` / `similaritySearchVectorWithScore`.
  - Tools: `tool()` from `langchain` with a Zod schema, and `createAgent` from `langchain` (as in the Learn quickstart).
  - A tested `package.json` block for Node 22/24 (`langchain`, `@langchain/core`, `@langchain/openai`, `@langchain/azure-cosmosdb`, `mongodb`, `zod`) with exact versions verified in CI.
  - Link to the sample repo path `Azure-Samples/documentdb-samples` `ai/vector-search-agent-typescript`.
- **`framework-llamaindex-python.md`**:
  - Correct: `AzureCosmosDBMongoDBVectorSearch(mongodb_client=..., db_name=..., collection_name=..., index_name=..., embedding_key="embedding", text_key="text", cosmos_search_kwargs={"kind": "vector-diskann", "dimensions": 1536, "similarity": "COS"})`, then `StorageContext.from_defaults(vector_store=...)` and `VectorStoreIndex.from_documents`.
  - State the version-specific behaviour that Learn documents for 0.9.0:
    - the constructor issues `createIndexes` itself, so no separate `create_index` call is needed;
    - without `kind`, the index defaults to HNSW whatever `index_name` says;
    - `MetadataFilters` are not translated, so use `pre_filter` via `vector_store_kwargs` plus `create_filter_index("metadata.<field>")`.
  - Show the stored document shape: `embedding` as `number[]`, `metadata` sub-document, score surfaced on `source_nodes`.
  - Add `FunctionTool.from_defaults` for a driver-backed tool.
  - Pin `llama-index-core` + `llama-index-vector-stores-azurecosmosmongo` versions that install on Python 3.11, 3.12 **and** 3.13 (sample 10 failed on 3.13), or state the supported runtime explicitly.
- **`framework-llamaindex-ts.md`**: answers "does a Node LlamaIndex path exist?" honestly.
  - Learn says the vector store integration is Python-only, but LlamaIndex TS has an `AzureCosmosDBMongoDBVectorStore` class. The maintainer should verify the current package and either give a minimal tested `VectorStoreIndex.fromDocuments` + `asQueryEngine` example, or document the supported fallback: LlamaIndex TS for orchestration, plus a custom retriever/tool that runs `$search` + `cosmosSearch` through the `mongodb` driver.
  - Either way, the deviation must be stated in the sample README.

Each Correct section ends with a **mock-LLM smoke test**: LangChain `FakeListChatModel` / LlamaIndex `MockLLM` with deterministic synthetic embeddings, so an agent can prove the tool wiring without an API key. It also ends with a short **multi-agent skeleton** pointer (fetch -> score -> explain, each a tool with a JSON contract), which links to the planner/synthesizer pattern in `quickstart-agent-nodejs`, because sample 06's prompt pattern recurs in the gallery.

### 2. Routing rule (AGENTS.md, under "Route B — Text skills")

Add after step 3:

> **Named framework rule.** If the task names LangChain, LangGraph, LlamaIndex or another framework, load `documentdb-framework-integrations` and use that framework's DocumentDB integration, or the documented driver fallback where no integration exists. Do not substitute a hand-rolled "framework-like" loop. If the integration cannot be installed, record the exact install error and the pinned versions tried, state the deviation in the README, and prefer stopping to ask over silently changing the deliverable.

### 3. Catalog entries

- `AGENTS.md` "Skills in this kit" table: `| documentdb-framework-integrations | skills/framework-integrations/ | Wiring LangChain / LlamaIndex (Py, JS/TS) to cosmosSearch; package name mapping; pinned versions; tool wrappers; mock-LLM tests |`
- `docs/SKILLS.md` rule-folder table: `| framework-integrations/ | framework- | LangChain + LlamaIndex vector stores and tool wrappers over the driver; current vs former-name package mapping; Learn links |`
- A `CHANGELOG.md` entry. Add `metadata.json` if sibling folders have one.

### 4. Verification before merge

Add a small CI job (or extend `testing/`) that installs the pinned `requirements.txt` / `package.json` from each rule on Python 3.11–3.13 and Node 22/24. It should run the mock-LLM smoke tests against the local DocumentDB container from `documentdb-local-deployment`. Pins that no test exercises will go stale and bring back sample 10's failure.

## Evidence (run folders from the readiness experiment)

- `runs/02-ai-powered-product-recommendations/20261124-181835/doc-gaps.md` and `decisions.jsonl` (D004): Node + LlamaIndex dropped, "availability uncertain"
- `runs/10-support-ticket-rag-assistant/20261124-204529/decisions.jsonl` (D016, D018): guessed `llama-index==0.9.2`, failed on Python 3.13, removed
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/decisions.jsonl` (D011): LangChain JS not installed, version for Node 24 unknown
- `runs/14-dynamic-pricing-engine/20261124-184622/decisions.jsonl` (D011) and `doc-gaps.md`: `initialize_agent` import errors, hand-rolled orchestration
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/doc-gaps.md`: three-agent LangChain pipeline built as plain functions

Also affected: `runs/08-personalized-email-campaign-builder/20261124-183709`, `runs/09-crypto-wallet-activity-analyzer/20261124-191004`, `runs/14-telehealth-session-summarizer/20261124-195137`, `runs/15-financial-advisor-chatbot-rag/20261124-192021`.

## Verification

### 1. Already covered? partially_covered

- **agent-kit: not covered.** `grep -ril 'langchain\|llamaindex\|llama-index\|llama_index'` over the clone (`skills/`, `knowledge-base/`, `docs/`, `AGENTS.md`, everything) returns no matches. `skills/` has 17 folders (azure-deployment, connection, data-modeling, driver, full-text-search, high-availability, indexing, local-deployment, mcp-setup, monitoring, natural-language-querying, query-optimization, query-optimizer, security, sharding, storage, vector-search) and none covers frameworks.
- **documentdb-mcp: not covered.** The same grep over the clone returns nothing, which is expected because the MCP server does not do this.
- **Learn: substantially covered, but not where the agent looked.**
  - https://learn.microsoft.com/en-us/azure/documentdb/ai-frameworks: "Azure DocumentDB integrates with the leading large language model (LLM) orchestration frameworks". It lists LangChain, LangGraph, LlamaIndex, Haystack, Semantic Kernel and CosmosAIGraph, with a language table.
  - https://learn.microsoft.com/en-us/azure/documentdb/build-rag-applications: LangChain Python with `langchain-azure-ai` `AzureCosmosDBMongoVCoreVectorSearch`, `create_index` for `vector-ivf` / `vector-hnsw` / `vector-diskann`, and the retriever + chain.
  - https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base: LlamaIndex Python with `llama-index-vector-stores-azurecosmosmongo` `AzureCosmosDBMongoDBVectorSearch` and `cosmos_search_kwargs`. It notes that the integration is Python-only.
  - https://learn.microsoft.com/en-us/azure/documentdb/quickstart-agent-nodejs: a TypeScript LangChain planner/synthesizer agent using `AzureDocumentDBVectorStore` from `@langchain/azure-cosmosdb`, with `tool()` / `createAgent`.
- **Conclusion.** The recipes exist on Learn, but the kit neither carries nor links them. Several findings (for example F1418, F2570) claim that "no public guidance" exists. That is inaccurate for Learn but accurate for the kit. The draft was rewritten to link the Learn pages and keep the skill thin, instead of re-authoring full walkthroughs.

### 2. Is the premise true? confirmed (with corrections applied)

The core premise is true: the kit has no framework guidance, and builders dropped prompt-required frameworks with cause `skill_silent`. Supporting claims that were wrong or outdated have been corrected in the body:

- **Claim:** "neither framework's integration is discoverable under the name Azure DocumentDB". **Wrong for LangChain.** LangChain JS has `AzureDocumentDBVectorStore` in `@langchain/azure-cosmosdb` (docs.langchain.com azure_documentdb page; Learn quickstart-agent-nodejs). LangChain Python has `AzureDocumentDBVectorSearch` in `langchain_azure_cosmosdb` (reference.langchain.com). LlamaIndex still uses the former name.
- **Claim:** LangChain Python class is `AzureCosmosDBVectorSearch`. **Outdated.** Learn uses `langchain_azure_ai.vectorstores.azure_cosmos_db.AzureCosmosDBMongoVCoreVectorSearch`, and the newer class is `AzureDocumentDBVectorSearch`. The index kinds are passed as `CosmosDBVectorSearchType.VECTOR_DISKANN/HNSW/IVF` enums.
- **Claim:** LangChain JS class is `AzureCosmosDBMongoDBVectorStore` with `indexOptions: { indexType: "diskann" }`. **Outdated.** The current class is `AzureDocumentDBVectorStore`, and the Learn quickstart passes `kind: 'vector-diskann'` (or `vector-hnsw` / `vector-ivf`) with `dimensions` and `AzureDocumentDBSimilarityType`.
- **Claim:** LlamaIndex TS = `@llamaindex/azure` `AzureCosmosDBMongoDBVectorStore`, stated as definite. **Unverified, and it conflicts with Learn.** The LlamaIndex TS API reference documents an `AzureCosmosDBMongoDBVectorStore` class. Learn's query-knowledge-base page says "The vector store integration is Python-only", while the ai-frameworks table ticks TypeScript for LlamaIndex. The body now asks the maintainer to verify the package and provides a driver fallback.
- **Claim:** LlamaIndex Python recipe calls `create_index()`. **Corrected.** Per Learn (v0.9.0), the constructor issues `createIndexes` itself, `kind` defaults to HNSW, and filtering uses `pre_filter`, not `MetadataFilters`.
- **Correct as written:** `number[]` embeddings (BSON binary vectors are not indexed); `cosmosSearch` with `vector-ivf` / `vector-hnsw` / `vector-diskann`; the former service name; `initialize_agent` being legacy (LangChain 1.x uses `create_agent` / `createAgent`, as in the Learn quickstart).

### 3. Maintainer skeptic: confirmed

It names concrete files (`skills/framework-integrations/SKILL.md`, five rule files, the `AGENTS.md` routing rule, `docs/SKILLS.md`, `CHANGELOG.md`). It is specific to Azure DocumentDB: package/name mapping, `cosmosSearch` index options and `number[]` vectors. It follows the kit's existing rule-folder pattern. It belongs in Azure/documentdb-agent-kit, because Learn already has the content and the gap is the kit not routing to it. As maintainer I would accept it with the edits applied: keep the skill thin and link-heavy, and treat the multi-Python/Node CI matrix as optional follow-up if it is too heavy for one PR.

Sources: https://learn.microsoft.com/en-us/azure/documentdb/ai-frameworks ; https://learn.microsoft.com/en-us/azure/documentdb/build-rag-applications ; https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base ; https://learn.microsoft.com/en-us/azure/documentdb/quickstart-agent-nodejs ; https://docs.langchain.com/oss/javascript/integrations/vectorstores/azure_documentdb ; https://reference.langchain.com/python/langchain-azure-cosmosdb/_vectorstore_documentdb/AzureDocumentDBVectorSearch ; https://developers.llamaindex.ai/typescript/framework-api-reference/classes/azurecosmosdbmongodbvectorstore ; clone of Azure/documentdb-agent-kit (grep, no matches) ; clone of microsoft/documentdb-mcp (grep, no matches).

## Finding ids

- F0194
- F0209
- F0210
- F0902
- F1312
- F1320
- F1418
- F1701
- F1934
- F2373
- F2473
- F2570
- F2581
