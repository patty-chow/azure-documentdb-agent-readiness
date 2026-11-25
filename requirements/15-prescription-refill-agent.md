# Reference requirements: Prescription refill agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Node.js and build the conversational logic as a LangChain agent (exact phrasing "Node.js LangChain agent") that drives tool invocation and responses.
- Define persistent document models using Beanie ODM (exact phrasing "Beanie ODM") for at least two collections: prescriptions and refill requests, with prescription fields including medicationName, patientId, daysSupplyRemaining, refillCount, lastFilledDate, and status, and refill request fields including patientId, medicationName, requestedDate, createdBy, eligible (boolean) and status.
- Connect to Azure DocumentDB (the MongoDB-compatible service) and implement a LangChain tool that queries Azure DocumentDB to return a patient's active prescriptions (filter by patientId and status='active') and returns full prescription records to the agent.
- Implement a LangChain tool that checks refill eligibility for a given prescription by evaluating daysSupplyRemaining and refillCount and returns a deterministic result object {eligible: boolean, reason: string, daysSupplyRemaining, refillCount}.
- Implement a LangChain tool that creates and persists a refill request document into Azure DocumentDB using the Beanie ODM model, setting requestedDate, createdBy='agent', eligible per the eligibility tool, and initial status='pending'.
- Ensure the LangChain agent orchestrates the flow: when asked to refill, it calls the prescription lookup tool, then the eligibility checker tool, and—only if eligible—calls the refill request creation tool; the code path must be visible and testable in the agent’s tool call sequence.
- Implement agent memory (exact phrasing "agent memory") scoped per patient/session that stores the most recently referenced medicationName(s) and allows the agent to resolve user utterances like "refill my blood pressure medication" to a concrete prescription without the user re-specifying the drug name.
- If the user utterance is ambiguous (multiple active prescriptions match the remembered or queried description), the agent must ask a clarifying question listing the matched medicationName values and wait for the user to choose before creating a refill request.
- If the eligibility tool returns eligible=false, the agent must not create a refill request document and must return a clear message to the user explaining the reason (e.g., no refills remaining or daysSupplyRemaining too high); this behavior must be implemented in the agent flow.
- On successful creation of a refill request, the agent must return a confirmation message to the user including the created refill request ID (DocumentDB document _id), medicationName, requestedDate, and current status; the created document must be queryable directly from Azure DocumentDB to verify persistence.

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
