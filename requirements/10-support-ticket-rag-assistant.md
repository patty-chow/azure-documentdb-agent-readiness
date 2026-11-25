# Reference requirements: Support ticket RAG assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Python agent built with LlamaIndex handles an incoming support ticket end to end: retrieval from Azure DocumentDB, context injection and generation of a suggested resolution.
- Past ticket resolutions and knowledge base articles are indexed into an Azure DocumentDB collection used as the LlamaIndex vector store, each stored as a document carrying its own embedding.
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field, with dimensions matching the embedding model that produced the embeddings.
- When a new ticket arrives, it is embedded and a vector search runs in Azure DocumentDB via $search / cosmosSearch (similarity COS, L2 or IP), returning the top 5 most similar past resolutions.
- The retrieved resolutions are injected as context into the prompt the agent sends to the language model.
- Context engineering keeps that prompt concise and focused on the current issue (e.g. only the ticket text plus the top 5 retrieved resolutions, trimmed to the relevant passages).
- The agent generates a suggested resolution for the ticket from the injected context and returns it to the support agent.

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
