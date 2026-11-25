# Reference requirements: Expense report auto-categorizer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python and include code entry points that run the agent-driven categorisation workflow.
- Use a LangChain agent as the agent framework to orchestrate LLM calls and control the per-report processing logic.
- Use Beanie ODM for all reads and writes to Azure DocumentDB; define Beanie Document models representing expense reports and their line items.
- Connect Beanie to an Azure DocumentDB (MongoDB API) cluster and query for expense report documents with a "submitted" status (or equivalent) to select reports to process.
- For each line item, invoke the LangChain agent with a prompt template that applies prompt engineering by embedding the company policy text and the line item fields, and request a category plus any policy-violation assessment.
- Augment each line item in the in-memory model with at least a "category" field and a "policy_violation" boolean plus a human-readable "violation_reason" when a violation is flagged.
- Persist the enriched report back to Azure DocumentDB via Beanie by updating the original expense report document (do not create duplicate submitted documents).
- Use LangChain agent memory (agent memory) during a session to store and retrieve prior categorisation decisions so the agent applies consistent categories across multiple reports processed in the same session.
- Demonstrate processing multiple reports in one agent session so that identical or similar line items encountered in later reports receive the same category according to the agent memory.
- Ensure the stored enriched report documents clearly reflect the agent’s outputs (categories and violation flags/reasons) so a reviewer can verify categorisation and flagged policy violations in Azure DocumentDB.

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
