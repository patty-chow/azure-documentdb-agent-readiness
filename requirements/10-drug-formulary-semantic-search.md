# Reference requirements: Drug formulary semantic search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the service in Python with LlamaIndex, and use LlamaIndex to generate the embedding vectors for both the stored formulary entries and incoming clinical intent descriptions.
- Store each drug formulary entry as an Azure DocumentDB document, written through a Python MongoDB driver (e.g. pymongo), that carries the entry's name, indications, contraindications and dosing together with its embedding vector on the same document.
- Create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field in code, with dimensions matching the embedding model's output and a similarity option suited to ranking by vector similarity (e.g. COS).
- Expose an HTTP endpoint at /formulary-search that accepts a clinical intent description as free text.
- Embed the incoming clinical intent description with LlamaIndex and run the similarity search in Azure DocumentDB with a $search / cosmosSearch aggregation over the stored embedding field, issued through the same driver.
- Return the top 10 formulary matches from that search (e.g. k set to 10), ranked by vector similarity with the closest match first.

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
