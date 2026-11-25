# Reference requirements: Medical imaging metadata store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implemented as a Python service that exposes an HTTP search endpoint which accepts a clinical query string and returns image metadata documents (including modality, body part and findings) ranked by semantic similarity.
- Use OpenAI to produce embeddings for findings when inserting documents and to produce an embedding for the clinical query at search time.
- Use PyMongo to store documents in Azure DocumentDB; each document contains modality, body part, findings and the embedding stored as a BSON binary vector (e.g., pymongo.binary.Binary holding the embedding bytes).
- Programmatically create a cosmosSearch index of kind vector-ivf on the embedding field by calling Azure DocumentDB createSearchIndexes; set the index's dimensions to match the length of the embedding vector returned by OpenAI.
- Implement search as a $search query using cosmosSearch that supplies the OpenAI query vector so the database performs a vector-ivf similarity search and returns matching documents ordered by similarity.
- The cosmosSearch vector query uses a supported similarity metric (e.g., COS, L2 or IP) and the query vector produced by OpenAI.
- The search endpoint returns each matched document's metadata and the similarity score from the database-side vector search.

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
