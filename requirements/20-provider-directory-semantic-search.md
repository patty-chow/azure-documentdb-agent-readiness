# Reference requirements: Provider directory semantic search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the service in Python with LlamaIndex, and use LlamaIndex to produce the embedding vectors stored with the provider profiles.
- Model each provider profile as one Azure DocumentDB document that carries the provider's specialty, languages, accepted insurance and bio together with its embedding vector stored on the same document, written through the Python driver (e.g. PyMongo).
- Create in code a cosmosSearch vector index of kind vector-ivf, vector-hnsw or vector-diskann (e.g. vector-ivf) on the embedding field, with dimensions matching the embedding model used and a similarity of COS, L2 or IP.
- Expose an HTTP endpoint at /find-provider that accepts a plain-language patient request (e.g. 'Spanish-speaking cardiologist accepting Medicare').
- Embed the incoming request with LlamaIndex and run the similarity search inside Azure DocumentDB with a $search / cosmosSearch query against that index using the request embedding.
- Return the matching providers as a ranked list ordered by vector similarity.

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
