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
open_questions: 6
---

# Add a framework-integrations skill routing LangChain and LlamaIndex tasks to the official integrations

## What happens today

None of the kit's 17 skills mentions LangChain or LlamaIndex. A case-insensitive grep for `langchain|llamaindex|llama-index|llama_index` over `skills/`, `knowledge-base/`, `docs/` and `AGENTS.md` returns nothing. The `vector-search` skill shows raw `$search` + `cosmosSearch` pipelines, and the `driver` skill shows a singleton `MongoClient`. Neither connects to the two frameworks that AI-app prompts name most often.

Microsoft Learn already has this material: the AI frameworks hub (`ai-frameworks`), a LangChain Python RAG how-to (`build-rag-applications`), a LlamaIndex Python how-to (`query-knowledge-base`), a LangGraph state page (`persist-agent-state`) and a TypeScript LangChain agent quickstart (`quickstart-agent-nodejs`). The kit doesn't link to any of them, so an agent that loads only kit skills never finds them. Some integrations are published under the Azure DocumentDB name and some are still under the former "Azure Cosmos DB for MongoDB vCore" name. That split makes them hard to find by search.

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
description: Wiring LangChain (Python, JS/TS) and LlamaIndex (Python; TS via driver fallback) to Azure DocumentDB vector search (cosmosSearch). Use when a task names LangChain, LangGraph, LlamaIndex, "agent", "RAG" or "tool" together with DocumentDB. Gives current package/class names (some still published under the former "Azure Cosmos DB for MongoDB vCore" name), links to the Learn how-tos, pinned interoperable versions, tool wrappers over the driver, and a mock-LLM smoke test.
license: MIT
---
```

Keep the body thin. It should link the five Learn pages above for full walkthroughs and carry only the facts an agent needs that are spread across them. Rule files use the `framework-` prefix and the kit's Incorrect/Correct template:

- **`framework-name-mapping.md`**: the table below, plus this sentence: *"Azure DocumentDB is the service formerly called Azure Cosmos DB for MongoDB vCore. LangChain now has `AzureDocumentDB*` classes; LlamaIndex and some older LangChain classes still use `AzureCosmosDBMongo*` / `azurecosmosmongo`. Search for both names."*

  | Framework | Package | Class |
  |---|---|---|
  | LangChain Python (newer) | `langchain-azure-cosmosdb` | `AzureDocumentDBVectorSearch` |
  | LangChain Python (as on Learn today) | `langchain-azure-ai` | `AzureCosmosDBMongoVCoreVectorSearch` (`langchain_azure_ai.vectorstores.azure_cosmos_db`) |
  | LangChain JS/TS | `@langchain/azure-cosmosdb` | `AzureDocumentDBVectorStore`, `AzureDocumentDBSimilarityType` (`AzureCosmosDBMongoDBVectorStore` is legacy) |
  | LlamaIndex Python | `llama-index-vector-stores-azurecosmosmongo` | `AzureCosmosDBMongoDBVectorSearch` |
  | LlamaIndex TS | to be verified (see Open questions) | `AzureCosmosDBMongoDBVectorStore` in the LlamaIndex TS API reference |

- **`framework-langchain-python.md`**:
  - Correct: `AzureDocumentDBVectorSearch`, or the Learn form `AzureCosmosDBMongoVCoreVectorSearch.from_connection_string(connection_string=..., namespace="db.coll", embedding=..., index_name=...)`.
  - Call `create_index(kind=CosmosDBVectorSearchType.VECTOR_DISKANN | VECTOR_HNSW | VECTOR_IVF, dimensions=..., similarity=CosmosDBSimilarityType.COS)` once, then `as_retriever(...)`.
  - Add a `@tool` that wraps a pymongo aggregation, and build the agent with LangChain 1.x `create_agent` or LangGraph.
  - One paragraph: `initialize_agent` / `AgentExecutor` are legacy, and imports moved to `langchain_openai` / `langchain_core`.
  - Incorrect: a hand-rolled loop; `$vectorSearch` (Atlas syntax); embeddings stored as BSON binary. Vectors must be `number[]` to be indexed.
- **`framework-langchain-js.md`**:
  - Correct: `AzureDocumentDBVectorStore` with `indexOptions: { kind: "vector-ivf" | "vector-hnsw" | "vector-diskann", dimensions, similarity: AzureDocumentDBSimilarityType.COS }`, as in `quickstart-agent-nodejs`.
  - Methods: `fromDocuments` / `similaritySearchVectorWithScore`.
  - Tools: `tool()` with a Zod schema, plus `createAgent` from `langchain`.
  - A `package.json` block for Node 22/24 (`langchain`, `@langchain/core`, `@langchain/openai`, `@langchain/azure-cosmosdb`, `mongodb`, `zod`) with exact versions verified in CI.
  - Link `Azure-Samples/documentdb-samples` `ai/vector-search-agent-typescript`.
- **`framework-llamaindex-python.md`**:
  - Correct: `AzureCosmosDBMongoDBVectorSearch(mongodb_client=..., db_name=..., collection_name=..., index_name=..., embedding_key="embedding", text_key="text", cosmos_search_kwargs={"kind": "vector-diskann", "dimensions": 1536, "similarity": "COS"})`, then `StorageContext.from_defaults(vector_store=...)` and `VectorStoreIndex.from_documents`.
  - Behaviour Learn documents for 0.9.0:
    - the constructor issues `createIndexes` itself, so no separate `create_index` call is needed;
    - without `kind`, the index defaults to HNSW, whatever `index_name` says;
    - `MetadataFilters` are not translated, so use `pre_filter` via `vector_store_kwargs` plus `create_filter_index("metadata.<field>")`.
  - Show the stored document shape (`embedding` as `number[]`, a `metadata` sub-document, the score on `source_nodes`) and a `FunctionTool.from_defaults` driver-backed tool.
  - Pin `llama-index-core` + `llama-index-vector-stores-azurecosmosmongo` versions that install on Python 3.11–3.13, or state the supported runtime.
- **`framework-llamaindex-ts.md`**: say plainly whether a Node LlamaIndex path exists.
  - If it does: give a minimal tested `VectorStoreIndex.fromDocuments` + `asQueryEngine` example.
  - If not: document the fallback, which is LlamaIndex TS for orchestration plus a custom retriever/tool running `$search` + `cosmosSearch` through the `mongodb` driver. The deviation must be stated in the sample README.

Each Correct section ends with two things:

- A **mock-LLM smoke test** (`FakeListChatModel` / `MockLLM` with deterministic synthetic embeddings), so an agent can prove the wiring without an API key.
- A short **multi-agent skeleton** pointer (fetch -> score -> explain, each a tool with a JSON contract) that links the planner/synthesizer pattern in `quickstart-agent-nodejs`.

### 2. `AGENTS.md`, under "Route B — Text skills", after step 3

> **Named framework rule.** If the task names LangChain, LangGraph, LlamaIndex or another framework, load `documentdb-framework-integrations` and use that framework's DocumentDB integration, or the documented driver fallback where no integration exists. Do not substitute a hand-rolled "framework-like" loop. If the integration cannot be installed, record the exact install error and the pinned versions tried, state the deviation in the README, and prefer stopping to ask over silently changing the deliverable.

### 3. Catalog entries

- `AGENTS.md` "Skills in this kit": `| documentdb-framework-integrations | skills/framework-integrations/ | Wiring LangChain / LlamaIndex (Py, JS/TS) to cosmosSearch; package name mapping; pinned versions; tool wrappers; mock-LLM tests |`
- `docs/SKILLS.md` rule-folder table: `| framework-integrations/ | framework- | LangChain + LlamaIndex vector stores and tool wrappers over the driver; current vs former-name package mapping; Learn links |`
- A `CHANGELOG.md` entry, and `metadata.json` if sibling folders have one.

### 4. Verification (optional follow-up if too heavy for this PR)

Add a CI job that installs each rule's pinned dependencies on Python 3.11–3.13 and Node 22/24, then runs the mock-LLM smoke tests against the local DocumentDB container from `documentdb-local-deployment`. Pins that nothing exercises go stale.

## Evidence

- `runs/02-ai-powered-product-recommendations/20261124-181835/` (`decisions.jsonl` D004, `doc-gaps.md`): Node + LlamaIndex dropped
- `runs/10-support-ticket-rag-assistant/20261124-204529/` (`decisions.jsonl` D016, D018): guessed `llama-index==0.9.2`, failed to install on Python 3.13, removed. [needs SME confirmation] This install failure may be partly a build-environment artifact (see Open question 4)
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/` (`decisions.jsonl` D011): LangChain JS not installed
- `runs/14-dynamic-pricing-engine/20261124-184622/` (`decisions.jsonl` D011, `doc-gaps.md`): `initialize_agent` import errors, hand-rolled loop
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (`doc-gaps.md`): three-agent pipeline as plain functions

Also affected: samples 08, 09, 14-telehealth and 15.

## Open questions

1. [needs SME confirmation] Package and class names in the mapping table (checked 2026-11-25). Which LangChain Python package should the kit recommend: `langchain-azure-cosmosdb` (newer) or `langchain-azure-ai` (what Learn shows)?
2. [needs SME confirmation] Is there a LlamaIndex TypeScript vector store for DocumentDB, and in which package? Learn's `query-knowledge-base` page says the integration is Python-only, while the `ai-frameworks` table ticks TypeScript for LlamaIndex. If no supported path exists, should the driver fallback be the official answer?
3. [needs SME confirmation] Does the documented LlamaIndex 0.9.0 behaviour still hold in current versions? That behaviour is: the constructor creates the index, the default kind is HNSW, and `MetadataFilters` are ignored in favour of `pre_filter`.
4. [needs SME confirmation] What are the exact, tested version pins for Python 3.11–3.13 and Node 22/24? Sample 10's Python 3.13 install failure may be partly an artifact of the experiment's build environment (tracked separately), so it should not be read as proof that the packages are broken.
5. [needs SME confirmation] Is the CI matrix in section 4 acceptable for this repo, or should it be a separate PR?
6. [needs SME confirmation] Sample counts come from one run and include samples where the build environment also interfered. Please confirm the count before it is quoted outside this issue.

## Source drafts

- 092-framework-integration-recipes-langchain-python-js-and-llamai.md
