# Reference requirements: Product catalog with vector search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Python using the Flask framework (i.e., a Python Flask app) with a runnable server exposing HTTP endpoints.
- Persist the product catalog as documents in Azure DocumentDB (store product documents in the database/collection used by the app).
- For each product, compute a single embedding over the product title and description using the text-embedding-ada-002 model (code must call that model to produce embeddings).
- Store each product embedding in its DocumentDB document as a BSON binary vector (e.g., bson.Binary containing the raw float32 bytes).
- Create a DocumentDB vector-ivf index on the embedding field (index creation shown in code/config, referencing the same embedding field stored as BSON binary).
- Ensure the vector-ivf index is created with a dimension parameter that matches the embedding length returned by text-embedding-ada-002 (dimension value set programmatically or in the index creation code).
- Provide a Flask /search endpoint that accepts a natural language query (e.g., query parameter or JSON body) and returns results in JSON.
- When /search is called, embed the incoming natural language query using text-embedding-ada-002 and convert that embedding to the same BSON binary vector format used for stored product vectors.
- Use Azure DocumentDB's vector search (server-side, using the vector-ivf index) to query with the query-vector and retrieve the top 10 semantically similar products (the code must perform the vector search query, not client-side nearest-neighbor computation).
- Return up to 10 products from /search, sorted by similarity, and include each product's identifier and key fields such as title and description in the JSON response.
- Include a seeding or ingestion routine (script or endpoint) that adds product documents to Azure DocumentDB by computing embeddings with text-embedding-ada-002 and storing them as BSON binary vectors and ensuring the vector-ivf index exists before searches.

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
