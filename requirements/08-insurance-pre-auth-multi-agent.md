# Reference requirements: Insurance pre-auth multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Node.js and use LangChain for Node.js to build a multi-agent architecture with an orchestrator component and two agents named exactly "medical-review agent" and "insurer-comms agent".
- The orchestrator must read a pre-auth request from Azure DocumentDB (a configurable collection/namespace) by connecting to Azure DocumentDB and querying for a queued or new pre-auth request document.
- The "medical-review agent" must retrieve clinical criteria stored in Azure DocumentDB (from a configurable collection) and run a deterministic clinical-necessity check that compares the pre-auth request data against those stored criteria.
- The "medical-review agent" must return a structured review object containing at minimum: a decision (e.g., pass/fail), the IDs of matched criteria, and a short rationale string explaining the decision.
- The orchestrator must pass the original pre-auth request and the structured review object from the "medical-review agent" to the "insurer-comms agent" via LangChain agent invocation/message passing (i.e., orchestrator calls the insurer-comms agent through LangChain APIs rather than by manual file edits).
- The "insurer-comms agent" must produce a submission document (single text or structured object) that includes the original request identifier, key request details, the clinical-review decision and cited criteria, and a human-readable submission/cover letter body.
- The orchestrator must store the final submission document and an explicit status field (for example, "submitted" plus timestamp and the review metadata) back into Azure DocumentDB, either by updating the original pre-auth request document or by creating a linked submission document that references the request ID.
- All Azure DocumentDB operations (reads and writes) must use a single configurable connection URI/connection string or environment-variable configuration and demonstrate authentication and connection setup before performing queries/updates.
- The medical-review check must be auditable in code: the implementation must expose the exact criteria matching logic (e.g., function or module) so a reviewer can inspect how criteria IDs map to decision outcomes.
- Include at least one end-to-end example or test script that inserts or uses a sample pre-auth request in Azure DocumentDB, runs the orchestrator, and verifies that the submission document and updated status are written back to Azure DocumentDB.

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
