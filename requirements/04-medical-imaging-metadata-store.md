# Reference requirements: Medical imaging metadata store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python.
- Persist medical imaging metadata as DocumentDB documents in Azure DocumentDB, including at minimum the fields modality, body_part and findings (and an image identifier).
- Provide an ingestion pathway (API endpoint or function) that accepts modality, body_part, findings and image identifier and writes a DocumentDB document.
- Use OpenAI to compute an embedding for the findings text at ingestion and when processing a search query (i.e., call OpenAI embeddings for findings and for query strings).
- Store each embedding in the DocumentDB document as BSON binary vectors.
- Programmatically create a vector-ivf index on the embedding field in Azure DocumentDB, where the index dimension matches the embedding length returned by OpenAI and the index is created before running vector searches.
- Expose a search endpoint that accepts a clinical query string, computes its OpenAI embedding, performs an approximate nearest-neighbor search using the vector-ivf index over the BSON binary vectors, and returns matching image identifiers and their DocumentDB metadata.
- Return similarity scores or distances with search results and sort results by similarity.
- Use the Azure DocumentDB (MongoDB‑compatible) cluster API to create the index and run the vector search operations (i.e., index creation and vector query calls are visible in the code).

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
