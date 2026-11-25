# Reference requirements: Product Q&A chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the chatbot in Python with LlamaIndex as a single RAG pipeline, using a LlamaIndex vector store backed by an Azure DocumentDB collection through a MongoDB-compatible Python driver (e.g. pymongo).
- Index product descriptions, specs, and reviews: split them into chunks with LlamaIndex, embed each chunk, and store the chunk text and its embedding together on each document in Azure DocumentDB.
- Create a cosmosSearch vector index in code (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field, with dimensions matching the embedding model used for the chunks.
- On each user question, embed the question and retrieve the top 5 most relevant chunks through the LlamaIndex retriever (e.g. similarity_top_k=5), which runs a $search / cosmosSearch similarity query (COS, L2 or IP) against the index in Azure DocumentDB.
- Inject the text of the retrieved chunks into the LLM prompt as context and generate the answer from that context (e.g. a LlamaIndex query engine or response synthesizer with a grounding instruction).
- Apply context engineering before the LLM call: measure the token size of the assembled prompt and, when long product docs would exceed the model's token limit, reduce the injected context (e.g. drop lower-ranked chunks or truncate chunk text) so the prompt fits within the limit.
- Accept user questions interactively and return the generated answer for each (e.g. a chat loop or chat endpoint).

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
