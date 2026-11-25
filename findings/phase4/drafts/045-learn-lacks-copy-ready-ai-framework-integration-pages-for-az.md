---
title: "Learn's Azure DocumentDB AI Frameworks pages contradict each other on LangChain/LlamaIndex packages and Node support (and the vector-search page doesn't link to them)"
repo: learn-docs
type: learn-feedback
status: drop
priority: P1
sample_count: 12
findings: 13
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: premise_wrong
  maintainer: confirmed
---

# Make the Azure DocumentDB "AI tools and frameworks" pages consistent and discoverable

> **Status note:** The original theme said Learn has no AI framework integration pages for Azure DocumentDB. That is wrong. Learn already has an "AI tools and frameworks" section with framework-specific how-tos (see Verification). The original ask is therefore dropped. The body below is the corrected, narrower issue that is left over. It can be filed separately if the maintainers want it.

**Pages affected:**
- `https://learn.microsoft.com/azure/documentdb/ai-frameworks` (overview, "Language support at a glance" table)
- `https://learn.microsoft.com/azure/documentdb/build-rag-applications` (LangChain on Azure)
- `https://learn.microsoft.com/azure/documentdb/query-knowledge-base` (LlamaIndex)
- `https://learn.microsoft.com/azure/documentdb/persist-agent-state` (LangGraph)
- `https://learn.microsoft.com/azure/documentdb/vector-search` (section "Use large language model (LLM) orchestration tools")
- `https://learn.microsoft.com/azure/documentdb/mcp-toolkit`

## What happens today

Learn already documents the integrations:
- LangChain Python: `build-rag-applications`
- LlamaIndex Python: `query-knowledge-base`, with `llama-index-vector-stores-azurecosmosmongo` and `AzureCosmosDBMongoDBVectorSearch`
- LangGraph Python and TypeScript, with a `MongoDBSaver` checkpointer that persists across restarts: `persist-agent-state`
- A TypeScript LangChain agent that uses `@langchain/azure-cosmosdb` `AzureDocumentDBVectorStore`: `quickstart-agent-nodejs`
- The MCP Toolkit: `mcp-toolkit`

These pages disagree with each other, though, and the main vector page does not link to them:

1. **Two different LangChain Python packages, with no explanation.**
   - `vector-search` points to `AzureDocumentDBVectorSearch` in `langchain-azure-cosmosdb`. That package is currently 1.0.1 on PyPI, which describes it as covering "vector store, cache, chat history, and checkpoint".
   - `build-rag-applications` uses `AzureCosmosDBMongoVCoreVectorSearch` from `langchain-azure-ai`.
   - Neither page says which one is recommended, or that they target the same service.
2. **"Python-only" notes contradict the overview table and the Node quickstart.**
   - `build-rag-applications` says the vector store integration "is Python-only" and tells TypeScript users to use the raw `mongodb` driver.
   - The `ai-frameworks` table marks LangChain TypeScript/JavaScript as supported.
   - `quickstart-agent-nodejs` uses `@langchain/azure-cosmosdb` `AzureDocumentDBVectorStore` (1.2.0 on npm).
3. **LlamaIndex TypeScript support is unclear.**
   - The `ai-frameworks` table marks LlamaIndex TypeScript/JavaScript as supported.
   - `query-knowledge-base` says the vector store integration is Python-only.
   - The only LlamaIndex.TS package, `@llamaindex/azure`, is flagged on npm as "deprecated and no longer maintained" (0.2.1).
4. **`vector-search` does not link to the framework section.** The "Use LLM orchestration tools" section at the end of `vector-search` lists only Semantic Kernel, the LangChain vector store and the LangChain semantic cache. It has no link to `ai-frameworks`, LlamaIndex, LangGraph or the TypeScript path. Agents that land on `vector-search`, the most-cited page, never reach the framework how-tos.
5. **`persist-agent-state` recommends retrievers that may need Atlas Search.** It recommends "MongoDB LangChain retrievers (full-text, vector, hybrid, parent-document)" and links to MongoDB Atlas docs. Those retrievers are built on Atlas Search / `$vectorSearch`. Azure DocumentDB runs vector search through `$search` + `cosmosSearch`, and full-text search through its own text indexes, not Atlas Search. The page should say which retrievers work, or point to the DocumentDB vector store classes instead.
6. **No recipe for using the MCP server as agent tools.** `mcp-toolkit` covers only IDE and CLI hosts (Copilot CLI, Claude Code, VS Code). It has no example of loading the server's tools (`find_documents`, `aggregate`, `find_and_modify`, ...) into an agent framework, for example through LangChain MCP adapters.

## Why it matters

The experiment had 100 samples, run with gpt-5-mini, the DocumentDB Agent Kit and the DocumentDB/Azure/Learn MCP servers. In 12 of the samples (13 findings), the prompt asked for a LangChain or LlamaIndex agent and the builder logged "no maintained adapter / no Learn guidance". The pages exist, so the problem is discoverability and contradictions, not missing content. What happened in the built apps:
- `10-support-ticket-rag-assistant`: LlamaIndex was removed entirely.
- `15-financial-advisor-chatbot-rag` (Node): the builder concluded there is no Node LlamaIndex path and shipped client-side cosine similarity instead of a `cosmosSearch` query. The Learn pages contradict each other on exactly this point (items 2 and 3).
- `13-chronic-disease-risk-predictor`: a hand-rolled pymongo retriever.
- `05-appointment-scheduling-assistant` and others: the builder defaulted to in-process `BufferMemory`, even though `persist-agent-state` shows restart-safe persistence. The agent never reached that page from `vector-search` (item 4).
- `14-dynamic-pricing-engine`, `01-fraud-detection-with-vector-similarity`: each built its own wrapper for running documentdb-mcp tools from an agent (item 6).

## Proposed change

1. In `ai-frameworks`, add a short "Packages and classes" table with framework, language, package, class and status. For example:
   - `langchain-azure-cosmosdb` → `AzureDocumentDBVectorSearch`
   - `langchain-azure-ai` → `AzureCosmosDBMongoVCoreVectorSearch`
   - `@langchain/azure-cosmosdb` → `AzureDocumentDBVectorStore`
   - `llama-index-vector-stores-azurecosmosmongo` → `AzureCosmosDBMongoDBVectorSearch`
   - `@llamaindex/azure`: deprecated

   State which LangChain Python package is recommended. Add the note "formerly Azure Cosmos DB for MongoDB vCore" so the page is found under the old class and package names.
2. Fix the contradictions:
   - Replace the "Python-only" note in `build-rag-applications` with a pointer to `@langchain/azure-cosmosdb` and `quickstart-agent-nodejs`.
   - Correct the LlamaIndex TypeScript cell in the `ai-frameworks` table, or document a supported option, given that `@llamaindex/azure` is deprecated.
3. In `vector-search`, add a link to `ai-frameworks` at the top of the "Use LLM orchestration tools" section, and list LlamaIndex and LangGraph there.
4. In `persist-agent-state`, either qualify the "MongoDB LangChain retrievers" bullet (Atlas Search-based retrievers are not supported) or replace it with the DocumentDB vector store classes from item 1. Optionally, mention the chat-history class in `langchain-azure-cosmosdb` as a lighter alternative to the checkpointer. Verify the class name before publishing.
5. In `mcp-toolkit`, add a short "Use from an agent framework" subsection. It should show a LangChain or LangGraph agent loading the server's tools (`find_documents`, `aggregate`, `find_and_modify`) over stdio or streamable HTTP. Note that vector queries go through `aggregate` with a `$search`/`cosmosSearch` stage, and that embeddings must be stored as `number[]`.

Dropped from the original draft:
- A brand-new `integrations-ai-frameworks` article. It already exists as `ai-frameworks`.
- A generic multi-agent "step log" collection pattern. That is general engineering guidance with no DocumentDB-specific angle.

**Follow-up for Azure/documentdb-agent-kit (separate issue):** `skills/` and `knowledge-base/` contain no mention of LangChain, LlamaIndex or LangGraph, and no link to the Learn AI-frameworks pages. Add one line to the vector-search skill that points to `https://learn.microsoft.com/azure/documentdb/ai-frameworks`, and tell agents not to hand-roll retrievers or memory.

## Verification

### 1. Already covered? — partially_covered
Most of what the original draft asked for is already on Learn under "Search and AI > AI tools and frameworks". The TOC (`https://learn.microsoft.com/en-us/azure/documentdb/toc.json`) lists Overview `ai-frameworks`, LangChain on Azure `build-rag-applications`, LangGraph `persist-agent-state`, LlamaIndex `query-knowledge-base`, Haystack `build-rag-pipelines`, Semantic Kernel, and MCP Toolkit `mcp-toolkit`.
- `ai-frameworks` (ms.date 2026-05-06) has a framework table and a "Language support at a glance" table.
- `query-knowledge-base` names "`llama-index-vector-stores-azurecosmosmongo`" and "`AzureCosmosDBMongoDBVectorSearch`". It has a full Python example with `cosmos_search_kwargs` set to `kind: vector-diskann`.
- `persist-agent-state` gives Python and TypeScript `MongoDBSaver` examples. It states that "State persists across process restarts."
- `quickstart-agent-nodejs` uses `AzureDocumentDBVectorStore` from `@langchain/azure-cosmosdb` inside a LangChain `createAgent` tool-calling agent.

Not covered:
- consistency between these pages (items 1–3)
- a link from `vector-search` (item 4)
- a recipe for using the MCP server as agent tools (item 6)

The agent kit has no framework coverage at all: grepping for langchain, llamaindex, llama-index, langgraph and ai-frameworks in `documentdb-agent-kit/skills` and `documentdb-agent-kit/knowledge-base` returned nothing.

### 2. Premise true? — premise_wrong
The draft's central claims are false:
- "Learn has no page that names the shipped LangChain / LlamaIndex adapters"
- "the only mention is three paragraphs at the bottom of vector-search"
- "a search for 'Azure DocumentDB LlamaIndex' returns nothing"
- "no Node path"
- no restart-safe memory pattern

The pages cited in check 1 cover all of these. One page is literally titled "Use LlamaIndex with Azure DocumentDB".

Corrected statement: the pages exist but contradict each other, and the most-visited vector page does not link to them.

Other claims checked and corrected in the body:
- `langchain-azure-cosmosdb` 1.0.1: confirmed on PyPI.
- `@langchain/azure-cosmosdb` → `AzureDocumentDBVectorStore`: confirmed, npm 1.2.0, and used in `quickstart-agent-nodejs`.
- `@llamaindex/azure` deprecated: confirmed. The npm "deprecated" field says "This package is deprecated and no longer maintained."
- `llama-index-vector-stores-azurecosmosmongo`: confirmed, version 0.9.0, which matches `query-knowledge-base`.
- MCP tool names: the draft said `find`/`findAndModify`. The real names are `find_documents`, `aggregate` and `find_and_modify`, per `mcp-toolkit` and the `name:` registrations in `documentdb-mcp/src`.
- The LlamaIndex default `embedding_key` (`content_vector`) could not be confirmed from Learn, which sets `embedding_key="embedding"` explicitly. The claim was removed.
- "number[] required; double[] not indexed": confirmed on `vector-search`, which says "Vectors must be a `number[]` to be indexed".

### 3. Maintainer skeptic — confirmed
I would accept the narrowed issue. It names specific pages, contradicting sentences, and concrete edits. The Atlas-retriever bullet in item 5 needs the maintainers to confirm it. The original ask (a brand-new page) would be closed as a duplicate of `ai-frameworks`.

## Finding ids
- F0054
- F0190
- F0191
- F0672
- F0709
- F1116
- F1498
- F1637
- F1693
- F2201
- F2368
- F2402
- F2563
