# Reference requirements: Rare disease literature search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python with LlamaIndex, including an ingestion step that fetches PubMed abstracts for rare diseases (e.g. through the PubMed E-utilities API) and keeps each abstract's text, PubMed ID and publication year.
- Split each ingested abstract into text chunks with LlamaIndex and carry the source abstract's PubMed ID and year on every chunk as metadata.
- Generate an embedding for each chunk with LlamaIndex's embedding integration and store the chunks with their embedding vectors as fields on documents in Azure DocumentDB (through LlamaIndex's Azure DocumentDB vector store integration or a MongoDB-compatible Python driver such as PyMongo).
- Create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field in code, with dimensions matching the embedding model's output and a similarity of COS, L2 or IP.
- Answer a researcher question by embedding it and running the vector similarity search inside Azure DocumentDB with $search / cosmosSearch, ordering the retrieved chunks by the database's similarity score (semantic relevance).
- Expose a RAG agent built with LlamaIndex in Python that takes a researcher question, retrieves the semantically ranked chunks from Azure DocumentDB and generates an answer conditioned on those chunks.
- Include a citation for each retrieved abstract the answer draws on, and give the PubMed ID and abstract year in every citation.

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
