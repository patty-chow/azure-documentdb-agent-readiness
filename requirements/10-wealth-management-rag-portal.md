# Reference requirements: Wealth management RAG portal

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Python and include a runnable entrypoint that starts the LlamaIndex RAG agent for interactive queries.
- Use LlamaIndex as the agent framework to build a retrieval-augmented generation (RAG) agent and show the code that constructs the LlamaIndex index and query pipeline.
- Index a corpus of wealth management research documents into a DocumentDB vector store: ingestion code must create embeddings and persist the index/vectors into Azure DocumentDB (the "DocumentDB vector store") with per-document metadata (e.g., title, date, tags).
- Provide code that performs vector search against the Azure DocumentDB vector store and returns the top-K retrieved research documents for a free-text relationship manager query (top_k configurable in code).
- Implement "agent memory" in the LlamaIndex agent: persist conversation history / memory and demonstrate that the agent reuses prior interaction context when answering follow-up questions.
- Implement a tool used by the agent that, given a client identifier, fetches that client's portfolio document from Azure DocumentDB and returns structured portfolio fields (positions, allocations, risk profile) to the agent.
- Combine portfolio context with retrieved research via explicit context engineering: the agent must construct a combined context (portfolio fields + retrieved research snippets) before generation and use that combined context to produce answers about client positioning.
- The agent’s response routine must include explicit citations or references showing which retrieved research documents and which portfolio fields were used to form the answer (e.g., document IDs or metadata included in the response).
- Persist the LlamaIndex index and agent memory state back to Azure DocumentDB so that both the vector index and memory survive agent restarts and can be reloaded from Azure DocumentDB.
- Provide an example end-to-end scenario (test or script) that submits a relationship manager question plus a client id, triggers fetching the portfolio tool, performs vector retrieval from the Azure DocumentDB vector store, applies the context-engineered combine step, and returns a final answer about the client's positioning.

## What a gallery sample also needs (the starter prompt does not say these)

- The connection string and model credentials come from environment variables; none appear in the repository.
- A `.env.example` lists every setting with placeholder values.
- The vector index dimensions match the embedding model's output.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one.
- One database client is created and reused across requests.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data.
- `/search` returns a clear error for an empty query and when the embedding call fails.
- Search results include the similarity score.
- Dependencies are pinned in `requirements.txt`.
- Unit tests run without a live cluster.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name.
