# Reference requirements: Cross-sell recommendation (Beanie)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python aggregation step, run through Beanie ODM's aggregation support over the order-history documents in Azure DocumentDB, derives co-purchase product pairs (products bought together in the same order) together with how often each pair was co-purchased (e.g. a count), and persists one document per pair back to Azure DocumentDB through Beanie.
- Each stored product pair is embedded by calling OpenAI's embeddings API, and the returned vector is saved on that pair's document in Azure DocumentDB.
- A cosmosSearch vector index of kind vector-ivf, vector-hnsw or vector-diskann is created in code on the pair documents' embedding field (e.g. createIndex with cosmosSearchOptions), with dimensions matching the output size of the OpenAI embedding model used and a similarity of COS, L2 or IP.
- The service exposes an HTTP endpoint at /cross-sell that accepts a basket of product IDs as its input.
- Handling a /cross-sell request embeds the basket with the same OpenAI embedding call used for the pairs and runs a $search / cosmosSearch aggregation against the vector index, so the similarity between the basket and the stored pair vectors is computed inside Azure DocumentDB.
- The endpoint returns exactly the top 5 cross-sell candidates, ordered from highest to lowest affinity score, with products already in the basket not offered as candidates; the affinity score is derived from the co-purchase pair data the search returns (e.g. the database similarity score, the co-purchase frequency, or a combination of the two).
- The service is asynchronous end to end: request handling, every Beanie ODM call to Azure DocumentDB (aggregation, writes, index creation and the $search query) and every OpenAI embedding call use Python async/await.

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
