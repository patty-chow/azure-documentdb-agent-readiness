# Reference requirements: Financial advisor chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the application in Node.js and instantiate a LlamaIndex RAG agent (use the name "LlamaIndex" in the code) to handle user conversations.
- Create and populate an Azure DocumentDB vector index containing curated financial knowledge articles; include code that upserts documents with their vector embeddings into the Azure DocumentDB collection.
- Implement and demonstrate vector search against the Azure DocumentDB vector index: a function that submits a user query, performs similarity search, and returns the top-k relevant knowledge article snippets and metadata.
- Add a clear Azure DocumentDB connection/configuration mechanism (environment variables or config file) and use it in the code paths that upsert and query the DocumentDB vector index.
- Expose a tool function the agent can call to fetch a client's live portfolio data (structured JSON with holdings, allocations, and quantities); the agent must call this tool during query handling rather than reading a static file.
- Combine retrieved DocumentDB knowledge article snippets and the fetched portfolio tool output into the RAG retrieval context passed to the LlamaIndex agent so the generator sees both sources when creating answers.
- Implement and use "agent memory" to persist conversation history (user turns and assistant turns) and ensure the LlamaIndex agent consults this agent memory when resolving follow-up questions.
- Include an end-to-end conversation example (seed data and/or automated test) that demonstrates a follow-up question such as "how does that affect my bond allocation?" is answered using prior conversation context from agent memory plus the retrieved DocumentDB articles and the client’s live portfolio data.
- Ensure the agent’s final responses reference or cite the specific DocumentDB knowledge articles and the relevant portfolio values used in reasoning (e.g., include article titles/IDs and portfolio allocation numbers in the output or logs).
- Provide automated or manual tests that verify: (a) DocumentDB vector search returns expected articles for a sample query, (b) the portfolio tool returns structured client data, and (c) a follow-up conversational query produces a response that changes when agent memory or portfolio data are modified.

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
