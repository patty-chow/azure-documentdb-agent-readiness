# Reference requirements: Fraud detection with vector similarity

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution as a Python LangChain agent (single-agent) that orchestrates embedding, storage, search, scoring, and explanation steps in code.
- Provide code that encodes transaction features into embeddings in binary embedding format (i.e., binary embeddings) and exposes the embedding step as a callable function the agent uses.
- Create and configure an Azure DocumentDB vector-ivf index in code and verify the index exists before inserting vectors.
- Insert known fraud pattern vectors into Azure DocumentDB, storing each vector with an identifier and explanatory metadata fields (e.g., pattern name, description, timestamp) that can be used in explanations.
- Implement a LangChain tool that performs vector search against the Azure DocumentDB vector-ivf index (the "vector search tool" the agent invokes) and returns the top-k matching documents with similarity scores and metadata.
- Ensure the vector search and stored vectors use the binary embedding format and an appropriate binary similarity metric in the query parameters (e.g., binary similarity/distance configured for the vector-ivf index).
- For each new transaction, run the embedding function, call the vector search tool to retrieve similar historical cases, and expose the raw neighbor similarities/distances in the agent flow.
- Compute a reproducible fraud risk score in code from the retrieved neighbor similarities (for example an aggregate or distance-weighted score) and make the scoring algorithm and thresholds explicitly visible in the repository.
- Generate a natural-language explanation that references the retrieved matching patterns and their metadata (e.g., "matched pattern X with similarity Y because ...") and return that explanation alongside the numeric fraud risk score.
- Include a runnable example or test that loads a small set of known fraud patterns into Azure DocumentDB, sends a sample new transaction through the agent, and demonstrates retrieval, scoring, and the natural-language explanation in the output.

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
