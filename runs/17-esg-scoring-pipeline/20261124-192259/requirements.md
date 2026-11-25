# Reference requirements: ESG scoring pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single LangChain agent written in Python reads company ESG data documents from an Azure DocumentDB collection using a MongoDB driver (e.g. PyMongo).
- The agent's prompt instructs the LLM to score each ESG pillar (E, S and G) on a 1-10 scale and to give reasoning for each score.
- The agent embeds the LLM's rationale text with a LangChain embeddings integration.
- The agent writes the scored document back to Azure DocumentDB, so the company document carries the three pillar scores, their reasoning and the rationale embedding.
- A cosmosSearch vector index of kind vector-ivf, vector-hnsw or vector-diskann is created in code on the embedding field, with dimensions matching the embedding model's output and a similarity of COS, L2 or IP.
- Semantic search over the stored rationales is a $search / cosmosSearch aggregation query against that index, so the similarity is computed in Azure DocumentDB.
- An aggregation pipeline run through the driver computes a composite ESG score from the three pillar scores and returns the companies ranked by that composite score.

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
