# Reference requirements: Correspondent banking risk screener

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Provide a Python LangChain agent that carries out the correspondent review: embedding profiles, searching the watchlist data and producing the per-correspondent result.
- Embed correspondent bank entity profiles with a LangChain embeddings integration and store each profile's vector on its document in Azure DocumentDB using a MongoDB-compatible Python driver (e.g. pymongo).
- Store sanctions list entries and adverse media entries as documents in Azure DocumentDB, each with its embedding on the document.
- Create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field in code, with dimensions matching the embedding model used.
- On each review cycle, run vector similarity search inside Azure DocumentDB with $search / cosmosSearch, using each correspondent's embedding as the query vector against the embedded sanctions list and adverse media entries.
- Derive a risk score for each correspondent from the similarity search results returned by Azure DocumentDB.
- Return, for each correspondent reviewed, the risk score, the matched sanctions list and adverse media entries, and a plain-language risk narrative written by the agent.

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
