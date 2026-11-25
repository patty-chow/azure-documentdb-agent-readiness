# Reference requirements: Hyper-personalized content engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js application built with LlamaIndex in which a single agent carries out the whole flow for one customer: fetching that customer's documents, retrieving content pieces via vector search and generating the final output.
- Fetch the customer's profile, segment and recent interaction documents from Azure DocumentDB (e.g. with the MongoDB Node.js driver, looked up by a customer identifier) and supply them to the agent as context.
- Content pieces are stored in Azure DocumentDB with an embedding on each document, and a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field with dimensions matching the embedding model.
- Retrieve the content pieces semantically relevant to the customer with a $search / cosmosSearch query against that index (similarity COS, L2 or IP).
- The LlamaIndex agent is given agent memory that retains earlier turns of the interaction and is drawn on when generating the current recommendation.
- Context engineering: the fetched profile, segment and recent interactions and the retrieved content pieces are assembled into a deliberately structured context for the model (e.g. clearly delimited sections per source) before generation.
- The agent's output for a customer contains a personalised content-selection rationale explaining why the content suits that customer and a ranked list of the retrieved content pieces.

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
