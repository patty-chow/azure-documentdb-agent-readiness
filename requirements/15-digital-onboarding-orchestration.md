# Reference requirements: Digital onboarding orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python Beanie ODM `Document` model represents an onboarding application as a state machine stored in Azure DocumentDB: the document holds the application's current state, and the model defines the states the onboarding journey moves through (e.g. one state per completed step).
- A Python LangChain orchestration pipeline acts as the orchestrator: it loads an onboarding application document through Beanie and drives that application through the journey.
- Three separate agents exist for the roles of ID verification, risk assessment and account opening, and the orchestrator delegates each step to the matching agent.
- The orchestrator invokes the agents in sequence, ID verification first, then risk assessment, then account opening, with each agent's run completing before the next one starts.
- After each agent step, the orchestrator updates the application document's state in Azure DocumentDB atomically: a single update to the one document, or, where more than one document is written, a session transaction (withTransaction, or start/commit/abort).
- Each state transition is logged (e.g. an entry naming the previous state, the new state and the agent that ran).

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
