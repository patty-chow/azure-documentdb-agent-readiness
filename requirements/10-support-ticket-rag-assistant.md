# Reference requirements: Support ticket RAG assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the assistant in Python (repository contains runnable Python code that implements the agent and exposes a callable entrypoint/function).
- Use LlamaIndex to build the retrieval and generation pipeline (create a LlamaIndex index from documents and use LlamaIndex query APIs to retrieve context and invoke the LLM).
- Persist and query vectors using an Azure DocumentDB vector store (code writes embeddings/vectors into Azure DocumentDB and performs vector similarity searches against that store).
- Load past ticket resolutions and knowledge base articles from Azure DocumentDB collections and convert them into LlamaIndex documents for indexing.
- Store and preserve document metadata (e.g., source id, title, timestamp, collection name) alongside each indexed document so retrieved items are inspectable and traceable.
- On ingest of a new ticket, perform a vector search that retrieves the top 5 most similar past resolutions (retrieval configured with k=5).
- Inject those top 5 retrieved documents as context into the prompt sent to the generator (the retrieved documents must be concatenated or passed via LlamaIndex context mechanisms before generation).
- Use a prompt template implementing context engineering that explicitly instructs the generator to be concise and focus on the current issue, and that limits or prioritizes included context to keep the prompt focused.
- Provide a single-agent RAG flow (Single-agent) function such as generate_suggested_resolution(ticket_text) that runs retrieval then generation in one process and returns the suggested resolution.
- Return both the generated suggested resolution and the 5 retrieved documents (or their IDs/metadata) in the agent response so reviewers can verify which contexts were used.

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
