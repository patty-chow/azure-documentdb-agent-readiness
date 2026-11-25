# Reference requirements: Patient record summarizer (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python using LlamaIndex: provide a single-agent Python LlamaIndex RAG implementation that accepts a clinical question and a patient identifier and performs retrieval + summarization in one process.
- When ingesting patient records, split each record into searchable chunks, compute embeddings for each chunk, and store each chunk as a document in Azure DocumentDB with an embedding field and a patientId field.
- Create a cosmosSearch vector index (kind vector-hnsw, vector-ivf or vector-diskann) in Azure DocumentDB on the embedding field, with the index dimensions set to match the embedding vector length produced by the embedding model used by the app.
- Use a Mongo-compatible Python driver (e.g., pymongo) to insert chunk documents and to perform retrieval; run vector similarity queries against the cosmosSearch vector index using $search / cosmosSearch (similarity COS, L2 or IP) to return the top-k most similar chunks.
- Enforce access control by filtering retrieval queries by the patientId field so that only chunks whose patientId matches the requested patient identifier are returned.
- Apply context engineering: assemble the model prompt by combining a clinical-summary instruction template, the retrieved chunks ordered by relevance, and the original clinical question (the prompt must explicitly structure context and instructions for a clinical summary).
- Produce a grounded clinical summary that explicitly cites the source chunks/documents used as evidence (include references to the stored chunk documents such as chunk identifiers or other document reference + patientId alongside the summary so each claim can be traced to source documents).

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
