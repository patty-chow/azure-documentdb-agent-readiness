# Reference requirements: Customer complaint classifier

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python LangChain single agent drives the whole pipeline: read unclassified complaints, classify them, embed the complaint text, and write the enriched documents back.
- The agent reads complaint documents that have not yet been classified from Azure DocumentDB through Beanie ODM (e.g. documents whose classification fields are absent).
- Prompt engineering: a LangChain prompt sent to the LLM assigns each complaint a product category, a root cause and an urgency tier.
- The complaint text is embedded with an embedding model and the resulting vector is stored as a field on the complaint document.
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field, with dimensions matching the embedding model used.
- Similarity search over complaints runs in Azure DocumentDB with a $search / cosmosSearch query against that index, returning the complaints nearest to a given embedding.
- The enriched complaint document (classification labels plus embedding) is written back to Azure DocumentDB through Beanie.
- An aggregation pipeline run against Azure DocumentDB groups complaints by category and returns per-category counts so that complaint hotspots stand out.

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
