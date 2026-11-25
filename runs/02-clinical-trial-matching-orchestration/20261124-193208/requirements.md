# Reference requirements: Clinical trial matching orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python pipeline built with LangChain acts as the orchestrator: it accepts a patient profile as input and runs the steps in order, vector search, then the eligibility agent, then the consent agent, passing each step's output to the next.
- In code, through a MongoDB driver (e.g. PyMongo), create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field of the trial-criteria documents in Azure DocumentDB, with dimensions matching the embedding model the pipeline uses.
- Embed the patient profile with an embedding model and find candidate trials by running a $search / cosmosSearch aggregation against the trial-criteria collection in Azure DocumentDB, so the database returns the trials whose stored criteria embeddings are most similar to the profile.
- An eligibility agent, built with LangChain, receives the candidate trials and applies each trial's inclusion and exclusion rules to the patient profile to decide which candidates the patient is eligible for.
- A consent agent, built with LangChain, receives the trials the eligibility agent accepted and generates a plain-language summary of each trial for the patient.
- Store the match results in Azure DocumentDB (e.g. the matched trial, the eligibility outcome and the plain-language summary for the patient).

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
