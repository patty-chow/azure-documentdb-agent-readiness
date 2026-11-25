# Reference requirements: Product catalog with vector search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The app is written in Python using the Flask framework.
- Product documents are stored in Azure DocumentDB through a Python MongoDB-compatible driver (e.g. pymongo); each product carries at least a title and a description.
- For each product, the title and description are embedded with text-embedding-ada-002 and the resulting vector is stored on the product document in a form the cosmosSearch index can index (e.g. a numeric array).
- A cosmosSearch index of kind vector-ivf is created in code on the embedding field, with dimensions matching text-embedding-ada-002 (1536).
- The app exposes a /search endpoint that accepts a natural-language query (e.g. as a query parameter or JSON body field).
- /search embeds the incoming query with text-embedding-ada-002 and runs the similarity search in Azure DocumentDB with a $search / cosmosSearch query over the vector-ivf index using that query vector.
- The cosmosSearch query requests the top 10 results (k = 10) and /search returns those 10 most semantically similar products in its response.

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
