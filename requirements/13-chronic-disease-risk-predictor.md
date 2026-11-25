# Reference requirements: Chronic disease risk predictor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python and use LlamaIndex as the agent framework (code imports and constructs a LlamaIndex agent).
- Create and persist an agent memory that stores high-risk patient profile embeddings in an Azure DocumentDB DocumentDB vector index (code shows upsert/insert of embeddings into the vector index).
- Connect to an Azure DocumentDB instance (resource type Microsoft.DocumentDB/mongoClusters) and target its vector index APIs/collection for storing and querying embeddings.
- Compute embeddings for stored high-risk cohort profiles and for each new patient’s structured clinical features using the same embedding procedure; the embedding step for both cohort profiles and new patients must be present in code.
- Execute a vector similarity search (vector search) against the DocumentDB vector index to retrieve the most similar high-risk profiles for a given new patient; the code must return the top-K matches and their similarity scores.
- Feed the retrieved high-risk profiles (and their similarity metadata) into the LlamaIndex agent so the agent can reason over the similarities when generating output.
- The LlamaIndex agent must generate a personalized risk narrative for the new patient that explicitly references retrieved similarities and provides recommended clinical interventions (output contains rationale tied to retrieved profiles).
- Persist agent memory in Azure DocumentDB so that stored high-risk profile embeddings are recoverable across runs (code demonstrates loading memory from and saving memory to the DocumentDB vector index).
- Provide an executable entry point (function, CLI command, or small API handler) that accepts structured clinical features for a new patient, runs embedding → retrieval → agent reasoning, and returns the personalized risk narrative and interventions.
- Include a small sample high-risk patient cohort preloaded into the DocumentDB vector index and at least one documented example new patient input that demonstrates the full embedding, retrieval, and narrative-generation flow.

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
