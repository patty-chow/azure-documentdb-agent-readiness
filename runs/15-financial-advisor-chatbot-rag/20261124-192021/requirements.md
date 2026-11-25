# Reference requirements: Financial advisor chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js application built with LlamaIndex runs a single RAG agent that answers a retail investor's financial questions in conversation.
- Financial knowledge articles are stored as documents in Azure DocumentDB, each carrying its embedding vector on the document (e.g. written through the mongodb Node.js driver or a LlamaIndex vector store backed by it).
- A cosmosSearch vector index of kind vector-ivf, vector-hnsw or vector-diskann is created in code on the embedding field, with dimensions matching the embedding model the agent uses.
- Retrieval embeds the user's question and runs a $search / cosmosSearch query against Azure DocumentDB so the similarity ranking happens in the database and returns the most relevant knowledge articles.
- The agent has a tool that fetches the client's live portfolio data, and the agent calls it when a question needs the client's portfolio context.
- The retrieved knowledge articles and the portfolio data returned by the tool are both placed in the context the agent passes to the language model when generating its reply.
- Agent memory holds the conversation history across turns, so a follow-up such as "how does that affect my bond allocation?" is answered using the earlier exchange in that conversation.

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
