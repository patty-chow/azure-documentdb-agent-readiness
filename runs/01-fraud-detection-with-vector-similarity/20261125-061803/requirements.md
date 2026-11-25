# Reference requirements: Fraud detection with vector similarity

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python LangChain agent is the single entry point: it accepts a new transaction and runs the fraud check for it.
- The agent encodes a transaction's features into an embedding vector with an embedding model, and the same model is used for the stored fraud pattern vectors and for new transactions.
- Known fraud pattern vectors are stored as an embedding field on documents in an Azure DocumentDB collection, written through a MongoDB driver (e.g. PyMongo), with each document carrying the pattern information the explanation draws on.
- A cosmosSearch index of kind vector-ivf is created in code on that embedding field, with dimensions matching the embedding model's output (similarity e.g. COS).
- A LangChain tool performs the vector search against Azure DocumentDB with a $search / cosmosSearch query using the new transaction's embedding as the query vector, and returns the similar historical cases.
- On each new transaction the agent invokes that vector search tool and derives a fraud risk score from the returned similar cases (e.g. based on how closely they match).
- The agent's response contains both the numeric fraud risk score and a natural-language explanation that describes the matching fraud patterns.

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
