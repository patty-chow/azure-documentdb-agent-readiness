# Reference requirements: Insurance pre-auth multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the system in Node.js with LangChain Node.js as a multi-agent setup: an orchestrator that coordinates two LangChain agents, a medical-review agent and an insurer-comms agent, each backed by a language model.
- The orchestrator reads a pre-auth request document from Azure DocumentDB using a MongoDB driver (e.g. the MongoDB Node.js driver) and starts the workflow from that request.
- The orchestrator runs the agents in sequence: it hands the pre-auth request to the medical-review agent first, then hands the request together with the medical-review outcome to the insurer-comms agent.
- The medical-review agent reads clinical-necessity criteria stored in Azure DocumentDB and checks the pre-auth request against those criteria, returning the result of that check to the orchestrator.
- The insurer-comms agent drafts the submission letter to the insurer from the pre-auth request and the medical-review outcome, returning it as the final submission document.
- The orchestrator stores the final submission document and a status for the pre-auth request back in Azure DocumentDB.

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
