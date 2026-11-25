# Reference requirements: Mortgage application multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Node.js using the LangChain framework as a multi-agent application with a distinct orchestrator plus underwriting, compliance, and comms agents (i.e., a "Node.js LangChain multi-agent" setup).
- The orchestrator must read the mortgage application document from Azure DocumentDB (by document id or a query) at the start of processing and load its full application fields into the pipeline.
- The orchestrator must pass the same application data sequentially to the underwriting agent, then to the compliance agent, and finally to the comms agent, enforcing that execution order in code.
- The underwriting agent must perform an affordability assessment and return a structured result containing at minimum: an affordability decision (approve/decline/conditional), numeric metrics (e.g., income, monthly debt, calculated DTI or equivalent), and a human-readable rationale explaining the assessment.
- The compliance agent must evaluate regulatory requirements against the application fields and return a structured compliance report that includes a pass/fail outcome plus a list of any flagged compliance issues or required remediation steps.
- The comms agent must generate a decision letter text (string) that incorporates the final decision, the key reasons from underwriting and compliance, and clear next steps for the applicant; the letter must be returned as part of the structured agent output.
- The orchestrator must combine the original application id, underwriting assessment, compliance report, comms decision letter, a final pipeline decision/status, agent identifiers, and timestamps into a single outcome object.
- The orchestrator must write (create or update) that outcome object back to Azure DocumentDB and persist the final status and decision fields on the same application document (or a clearly linked outcome document) so the result can be retrieved later.
- If any agent produces an error or a failing outcome, the orchestrator must set and persist an appropriate final decision/status (e.g., declined, needs-follow-up) and include error or failure details in the stored outcome.
- Each agent implementation and the orchestrator must expose or record the agent inputs and outputs (structured data) so a reviewer can inspect the prompt/response exchange in the Node.js LangChain multi-agent logs or the saved outcome object.

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
