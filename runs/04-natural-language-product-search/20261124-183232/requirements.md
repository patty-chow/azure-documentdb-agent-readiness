# Reference requirements: Natural language product search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Python agent built with LangChain that accepts a shopper's plain-English product query, calls a hybrid search tool, and replies with the best-matching products from the catalog.
- A prompt-engineering step that rewrites the shopper's raw query into a well-formed search intent before any search is issued; the hybrid search tool searches with that rewritten intent.
- The hybrid search tool runs a full-text search over the product catalog in Azure DocumentDB (what the prompt calls $text) using a search index created in code with createSearchIndexes and queried with the $search aggregation stage, through a Python MongoDB driver (e.g. PyMongo), and keeps the ranked results it returns.
- The same tool embeds the rewritten intent and runs a vector search against Azure DocumentDB with $search / cosmosSearch over the embedding field stored on each product document, so the similarity ranking is computed by the database, and keeps those ranked results.
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the product documents' embedding field, with dimensions matching the embedding model the app uses.
- The two ranked result lists are merged in the application into one ranking (e.g. reciprocal rank fusion), and the best matches from that merged ranking are what the tool returns to the agent.

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
