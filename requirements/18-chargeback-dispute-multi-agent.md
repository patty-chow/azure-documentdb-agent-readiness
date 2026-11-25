# Reference requirements: Chargeback dispute multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Node.js using LangChain to build a Node.js LangChain multi-agent system with four distinct agents: an orchestrator, an evidence-gathering agent, a policy-reasoning agent, and a decision agent.
- Expose an HTTP endpoint (for example via Express) that the orchestrator uses to receive a chargeback claim (includes claim id) and that triggers the agent workflow end-to-end.
- The evidence-gathering agent must query Azure DocumentDB to fetch the related transaction documents and communication documents for the incoming claim id and return them as structured JSON; the code must demonstrate actual reads from Azure DocumentDB.
- When fetching evidence, the implementation must record and include the Azure DocumentDB collection names and document _id values in the evidence payload that is passed to downstream agents.
- The policy-reasoning agent must load dispute rules (from a JSON file or an Azure DocumentDB rules collection) and produce a human-readable rationale that maps which rules fired and why given the evidence; the agent’s output must include the rule ids and the specific evidence fields that triggered each rule.
- The decision agent must write an accept or reject outcome back to Azure DocumentDB by updating the original claim document or inserting a decision document; the written record must contain at minimum: claim id, decision (“accept” or “reject”), UTC timestamp, decisioning agent identifier, the rationale text, and references to the evidence document IDs.
- The orchestrator must perform explicit, sequential handoffs: invoke the evidence-gathering agent, wait for its structured response, pass that response to the policy-reasoning agent, wait for reasoning output, then pass the reasoning to the decision agent; each handoff must be implemented in code and observable in logs.
- All inter-agent messages and handoff payloads must be represented and logged as structured JSON so a reviewer can trace inputs and outputs between orchestrator → evidence → policy → decision.
- Provide a script or instructions (and sample JSON) to seed Azure DocumentDB with example transaction and communication documents plus a sample claim so the reviewer can exercise the full workflow against Azure DocumentDB.
- Include automated tests (unit or integration) that submit a sample chargeback claim to the orchestrator endpoint and assert that Azure DocumentDB contains the expected final decision document with the correct accept/reject value, timestamp, rationale, and evidence references.

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
