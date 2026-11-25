# Reference requirements: Chargeback dispute multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the system in Node.js with LangChain as a multi-agent system with four distinct roles: an orchestrator, an evidence-gathering agent, a policy-reasoning agent and a decision agent.
- The orchestrator receives a chargeback claim as its input and drives the flow in order: it delegates to the evidence-gathering agent first, hands that agent's output to the policy-reasoning agent, then hands the policy-reasoning output to the decision agent.
- The evidence-gathering agent fetches the transaction documents and the communication documents related to the claim from Azure DocumentDB using a MongoDB-compatible Node.js driver (e.g. `mongodb`) and returns them as the evidence.
- The policy-reasoning agent receives the gathered evidence and interprets the dispute rules against it, producing a reasoning output that is passed on to the decision agent.
- The decision agent reaches an accept or reject outcome from the policy-reasoning output.
- The decision agent writes the accept/reject outcome back to Azure DocumentDB, associated with the original claim.

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
