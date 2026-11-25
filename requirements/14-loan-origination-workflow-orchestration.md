# Reference requirements: Loan origination workflow orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Define a Beanie Document model (using Beanie) that represents a "state machine document" for a loan application persisted in Azure DocumentDB, including at minimum: unique id, current state (enum with values submitted, underwriting, compliance, approved, rejected), applicant payload, and a transitions log array/field.
- Configure and connect Beanie (in Python) to Azure DocumentDB (the MongoDB-compatible service) via a connection URI or client settings; the sample must show the connection code/variables used to open the Beanie/Motor session.
- Implement an orchestration pipeline in Python using LangChain that loads a loan application document and routes it to specialist agents based on the document's current state.
- Implement three specialist agents (as LangChain agents/components) named underwriting, compliance, and applicant communication; each agent must accept the document context and return a structured result (decision/outcome and notes) consumed by the orchestrator.
- Advance the application state only via an atomic update in Azure DocumentDB: perform a single atomic operation (e.g., find_one_and_update with a filter on the expected current state and $set/$push) or a multi-document transaction that simultaneously updates the state field and appends the transition log entry.
- For every state transition, append a transition log entry to the document that includes at least: previous state, new state, agent name (which specialist agent performed the step), decision/outcome, and an ISO8601 timestamp generated at the moment of transition.
- Enforce and validate the allowed state sequence in the orchestrator (submitted -> underwriting -> compliance -> approved/rejected) and fail/raise/log when an invalid transition is attempted.
- Ensure that state advancement is driven by the specialist agents' returned results: the orchestrator must interpret the agent output to decide the next state (e.g., underwriting decision -> move to compliance or rejected) and persist that decision via the atomic update.
- Provide a runnable end-to-end example (script or test) that creates a new loan application document in the submitted state in Azure DocumentDB, executes the LangChain orchestration through underwriting and compliance agents, and results in a terminal approved or rejected state with all transitions persisted.
- Use Beanie’s document read/write APIs for standard operations (and if a raw MongoDB atomic operation is required for the combined update, call it in code with an inline comment justifying why Beanie was not sufficient), so the sample demonstrates Beanie as the primary ODM interacting with Azure DocumentDB.

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
