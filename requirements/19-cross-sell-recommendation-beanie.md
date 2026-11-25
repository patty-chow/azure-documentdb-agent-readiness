# Reference requirements: Cross-sell recommendation (Beanie)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service as an async Python application that uses Beanie ODM for all DocumentDB models and operations (use async/await and beanie imports in the code).
- Establish an async connection from Beanie to Azure DocumentDB (the code must show connection/initialization pointing at the Azure DocumentDB instance).
- Define a Beanie Order document model that stores order history with an order identifier, timestamp, and a list of product IDs.
- Define a Beanie ProductPair document model that stores an unordered product pair (product_a_id, product_b_id), a co_purchase_count integer, and an embedding field that holds the vector (list of floats).
- Provide an async aggregation routine that scans Order documents in Azure DocumentDB, generates unordered co-purchase pairs per order, and upserts ProductPair documents incrementing co_purchase_count for each observed pair.
- For each ProductPair, asynchronously call the OpenAI embeddings API to compute a vector for the product pair (the code must show the OpenAI embedding request) and persist that embedding into the ProductPair.embedding field in Azure DocumentDB.
- Persist embeddings in Azure DocumentDB as arrays of floats inside the ProductPair documents so they are retrievable for similarity calculations.
- Implement an async HTTP /cross-sell endpoint that accepts a JSON POST body with a "basket" field (array of product IDs) and returns a JSON list of candidate product IDs with affinity scores.
- In the /cross-sell handler, consider as candidates any product IDs that appear in ProductPair documents with at least one basket product and exclude products already in the submitted basket.
- Compute an affinity score for each candidate by aggregating across basket items: for each basket item, retrieve the ProductPair document for (basket_item, candidate), and combine the pair's co_purchase_count with the cosine similarity between that pair's stored embedding and the basket-item–candidate embedding(s); sum these per-basket-item contributions to produce a final affinity score that is then used to rank candidates.
- Perform all vector similarity (cosine similarity) calculations in the service code using the stored embeddings retrieved from Azure DocumentDB (do not rely on an external DB vector-search capability).
- Return the top 5 candidates sorted by the computed affinity score (include product ID and numeric affinity score in the JSON response).

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
