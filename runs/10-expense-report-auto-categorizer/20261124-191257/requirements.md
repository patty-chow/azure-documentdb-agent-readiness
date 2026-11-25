# Reference requirements: Expense report auto-categorizer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python with LangChain as a single agent that, for each submitted expense report, reads the report, categorises its line items, flags policy violations and writes the enriched report back.
- Define Beanie ODM Document models for expense reports and use Beanie to read the submitted expense reports from Azure DocumentDB.
- Each line item in a report receives a category from the LLM (e.g. OpenAI through LangChain) through an engineered prompt that supplies the company policy and the line item's details.
- Flag policy violations: each line item that breaks the company policy is marked as a violation in the agent's output for the report.
- Write the enriched report back to Azure DocumentDB through Beanie, with the category and violation flag for each line item attached to the report document.
- Provide an agent memory component that lives for a session spanning multiple reports and records the categorisation decisions the agent makes.
- When categorising a line item, the agent consults the session memory and applies an earlier decision to a matching item, so the same kind of expense receives the same category across the reports processed in that session.

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
