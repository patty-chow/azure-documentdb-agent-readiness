# Reference requirements: Digital onboarding orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the orchestration pipeline in Python using the LangChain framework and label the pipeline as an Orchestration implementation.
- Use Beanie ODM for all document modeling and database interactions against Azure DocumentDB.
- Define a Beanie document model that represents an onboarding application as a state machine document stored in Azure DocumentDB; the model must include a current_state field and an explicit set of states covering at least initiated → id_verified → risk_assessed → account_opened.
- Include a transition history/log array on the state machine document; each logged transition must contain the agent name, outcome/status, timestamp, and optional detail payload.
- Implement an orchestrator that delegates, in sequence, to an "ID-verification agent", then a "risk-assessment agent", then an "account-opening agent", waiting for each agent to complete before proceeding.
- After each agent completes, perform an atomic update to the onboarding document in Azure DocumentDB to set the new state and append the transition record; implement atomicity using a MongoDB-compatible single-document atomic update (e.g., find_one_and_update with $set/$push) or a Beanie/Motor session transaction.
- Persist a new onboarding state machine document to Azure DocumentDB when starting a new flow and retrieve/upsert that document for each subsequent orchestration step.
- If an agent returns a failure/non-success result, the orchestrator must update the state machine document to a failure/rejected state and append a failure transition record before halting or following a defined error path.
- Initialize Beanie with a Motor/Mongo client connected to Azure DocumentDB via a configurable MongoDB connection URI (i.e., repository contains connection configuration and Beanie.init usage).
- Ensure every state change and transition log entry is written to Azure DocumentDB (using Beanie methods or explicit atomic update operations) so the DocumentDB-hosted state machine is the single source of truth for the onboarding flow.

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
