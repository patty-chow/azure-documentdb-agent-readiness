# Reference requirements: Wealth management RAG portal

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python application built with LlamaIndex that runs a single RAG agent answering relationship managers' questions about a client's positioning.
- Wealth management research documents are indexed into an Azure DocumentDB collection used as the LlamaIndex vector store, with each stored document carrying its embedding vector on the document itself.
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field, with dimensions matching the embedding model in use.
- Retrieval of research for a question runs a $search / cosmosSearch query against Azure DocumentDB so the similarity computation (COS, L2 or IP) happens in the database.
- The agent has a tool that fetches the client's portfolio document from Azure DocumentDB (e.g. looked up by a client identifier) and returns it to the agent as context.
- The agent assembles its model context by combining the fetched portfolio context with the retrieved research passages before generating the answer.
- The agent keeps agent memory of the conversation so that follow-up questions are answered with the earlier turns available to it.

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
