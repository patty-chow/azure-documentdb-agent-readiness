# Reference requirements: Product Q&A chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Python and use LlamaIndex to build the RAG pipeline (imports and core pipeline construction must reference LlamaIndex).
- Ingest product data types (descriptions, specs, and reviews) and create Document objects with metadata indicating product_id and source_type (description/spec/review) before indexing.
- Persist the vector representations / index into Azure DocumentDB by writing vectors or index entries to the DocumentDB vector store (the code must connect to an Azure DocumentDB instance and write vector records).
- Chunk long product documents into smaller chunks during ingestion and store chunk-level metadata so each chunk is independently retrievable.
- Apply context engineering to keep prompts within token limits: implement logic that (a) enforces a configurable max context/token budget and (b) trims, summarizes, or prioritizes chunks to fit that budget before building the prompt.
- On each user question, perform a vector similarity retrieval from the DocumentDB vector store and return exactly the top 5 most relevant chunks (top_k=5 configurable but defaulted to 5).
- Inject the retrieved top-5 chunks as context into the LLM prompt assembled by LlamaIndex and call the LLM to generate the answer (the assembled prompt must visibly contain the retrieved chunk text).
- Ensure generated answers are grounded by including explicit citations or identifiers for the source chunks (e.g., product_id and chunk_id or source_type) alongside or within the response.
- Provide a single-agent runtime (Single-agent) implementation that handles both retrieval and generation in one process (no multi-agent orchestration code paths).
- Include an end-to-end example or automated test that indexes sample product descriptions/specs/reviews, queries with a sample shopper question, verifies retrieval returned 5 chunks, and asserts the LLM output contains grounded citations to those chunks.

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
