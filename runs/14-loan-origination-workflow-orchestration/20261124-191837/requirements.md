# Reference requirements: Loan origination workflow orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Beanie Document model in Python represents each loan application as a state-machine document in Azure DocumentDB, with a state field whose values are the workflow states (submitted, underwriting, compliance, approved/rejected).
- A Python LangChain orchestration pipeline loads an application's document, reads its current state and advances it step by step through submitted, underwriting and compliance to a final approved or rejected state, in that order, stopping once a final state is reached.
- Specialist LangChain agents exist for underwriting, compliance checking and applicant communication, and the orchestrator delegates each step of the flow to the matching specialist agent.
- Each specialist agent returns a result the orchestrator uses to choose the application's next state, including whether it finishes as approved or rejected.
- Each state advance writes the new value of the state field to the application document atomically through Beanie (e.g. a single find_one_and_update with $set, or a session transaction when several documents change together).
- Every transition is logged with a timestamp taken at transition time (e.g. an entry holding the previous state, the new state and a UTC datetime, appended to a transitions list on the application document or emitted through a logger).

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
