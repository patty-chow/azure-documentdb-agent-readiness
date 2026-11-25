# Reference requirements: Correspondent banking risk screener

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python and build it with the LangChain agent framework (imports and orchestration use LangChain classes to run embedding, search, scoring, and narrative steps).
- Use a LangChain Embeddings implementation to compute embeddings for correspondent bank entity profiles and for sanctions list / adverse media entries before storing or comparing them.
- Persist correspondent profiles, sanctions entries and adverse media documents in Azure DocumentDB using the MongoDB-compatible API via the pymongo driver; each stored document must include a metadata block and an "embedding" field containing the vector as an array of floats.
- Provide an upsert path for sanctions and adverse media entries that either accepts precomputed embeddings or computes embeddings via the LangChain embeddings component and stores them into Azure DocumentDB.
- On each review cycle, load sanctions list and adverse media documents (including their stored embeddings) from Azure DocumentDB and perform a vector similarity search in Python (e.g., cosine similarity) between the correspondent embedding and the stored embeddings, returning the top N matches per category.
- Derive a numeric risk score for each correspondent from the aggregated similarity results (e.g., weighted combination or max similarity across sanctions and adverse media), and normalize it to a defined numeric range (documented in code).
- For every matched entry include provenance metadata in the output (Azure DocumentDB document ID, source type: "sanctions" or "adverse_media", similarity score, and a short text excerpt or title from the matched document).
- Produce a plain-language risk narrative for each correspondent using the LangChain agent (LLM) that explains why the score was assigned and references the matched entries and their key indicators.
- Expose the review functionality as a callable Python function or method that accepts one or more correspondent profiles, runs embedding → store/upsert → search → score → narrative workflow, and returns structured results (e.g., dict/JSON) containing risk_score, matches, and narrative for each correspondent.
- Configure the code to connect to a real Azure DocumentDB instance (Microsoft.DocumentDB/mongoClusters) via connection string/URI (not a file-backed mock), and ensure collections for correspondents, sanctions, and adverse_media are read/written as part of automated review cycles.

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
