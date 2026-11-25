# Reference requirements: Chargeback dispute multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Node.js using LangChain Node.js to create a multi-agent architecture consisting of an orchestrator, an evidence-gathering agent, a policy-reasoning agent, and a decision agent.
- The orchestrator receives a chargeback claim input (e.g., a claim identifier or payload) and delegates processing sequentially: first invoking the evidence-gathering agent, then passing its result to the policy-reasoning agent, and finally invoking the decision agent with the policy output.
- The evidence-gathering agent queries Azure DocumentDB for related transaction and communication documents using the Node.js "mongodb" driver, retrieving all documents associated with the provided claim identifier (e.g., from collections for transactions and communications).
- The evidence-gathering agent returns the fetched transaction and communication documents as structured evidence (e.g., arrays of documents) to the orchestrator, and the orchestrator forwards that evidence to the policy-reasoning agent.
- The policy-reasoning agent accepts the evidence and interprets the dispute rules to produce a reasoning result or recommendation (an interpretation of which rules apply and a suggested accept/reject recommendation), and returns that result to the orchestrator/decision agent.
- The decision agent uses the policy-reasoning output to produce a final accept or reject outcome and writes that outcome back to Azure DocumentDB (using the Node.js "mongodb" driver), updating or inserting a document associated with the original claim to record the outcome.
- The orchestrator enforces the end-to-end flow so that the decision agent's stored accept/reject outcome is derived from the evidence retrieved by the evidence-gathering agent and the interpretation produced by the policy-reasoning agent (i.e., agents are invoked and data flows in the stated order).

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
