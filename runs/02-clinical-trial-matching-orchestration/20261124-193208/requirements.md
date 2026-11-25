# Reference requirements: Clinical trial matching orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Python LangChain orchestration pipeline that accepts a patient profile input and coordinates two agent components: an eligibility agent and a consent agent.
- Using the PyMongo driver, run a vector search against Azure DocumentDB by issuing a $search / cosmosSearch query on the trials collection to retrieve candidate trials ranked by similarity; the query must reference the embedding field stored on trial documents (e.g., an "embedding" field) and return the top candidates (e.g., top-N).
- In code, create a cosmosSearch vector index (kind vector-ivf, vector-hnsw, or vector-diskann) on the trial documents' embedding field via Azure DocumentDB’s search-index creation API; that index must specify the embedding dimensionality to match the embedding model used by the application.
- Ensure trial documents store embedding vectors on a document field (the seeding/upsert code writes embeddings into each trial document) so the vector index and $search operate over those stored embeddings.
- The orchestration passes retrieved candidate trials to an eligibility agent implemented with LangChain Python; that agent programmatically evaluates inclusion and exclusion criteria by inspecting trial criteria fields (e.g., age ranges, conditions, lab thresholds) against the patient profile and returns a structured eligibility decision (pass/fail) and rationale for each trial.
- After eligibility evaluation, the orchestrator hands eligible trials to a consent agent implemented with LangChain Python; the consent agent produces a plain-language, patient-facing trial summary for each trial that explains purpose, key procedures, and consent-relevant points tailored to the patient profile.
- Persist match results back into Azure DocumentDB using PyMongo so that each stored match record contains at least the trial identifier, the eligibility decision and rationale, and the consent-agent plain-language summary.
- Implement the pipeline sequencing so outputs flow through: vector search → eligibility agent → consent agent, with the orchestrator wiring each step’s outputs to the next within the LangChain Python orchestration.

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
