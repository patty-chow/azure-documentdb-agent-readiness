# Reference requirements: ESG scoring pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Single-agent LangChain agent in Python that iterates company ESG documents stored in Azure DocumentDB and processes them one-by-one.
- Use prompt engineering inside the LangChain agent to instruct the LLM to return a numeric score (1–10) and a short reasoning/rationale for each pillar (E, S and G), and parse the LLM response into three numeric score fields and three corresponding rationale text fields.
- Use LangChain embeddings in Python to produce an embedding of the generated rationale text and attach that embedding to the company document before writing it back to Azure DocumentDB.
- Read and update documents in Azure DocumentDB from Python using a MongoDB driver (e.g. pymongo): the update must write the three numeric pillar scores, the three rationale strings, and the embedding vector into the same company document.
- Create a cosmosSearch vector index in Azure DocumentDB in code (using createSearchIndexes) on the stored embedding field (index kind vector-hnsw, vector-ivf or vector-diskann) with dimensionality equal to the embedding model’s output dimension (e.g. 1536) so the embedding field is queryable for semantic search.
- Store embeddings as an array of floats on the document (the embedding field), not as external files or references.
- Implement an Azure DocumentDB aggregation pipeline (using the driver’s aggregate) that computes a composite ESG score from the numeric E, S and G fields and returns companies ranked by that composite score (e.g., composite = average(E,S,G) as an example of aggregation).

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
