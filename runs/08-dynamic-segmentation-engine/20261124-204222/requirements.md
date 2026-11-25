# Reference requirements: Dynamic segmentation engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The application is a Python LangChain agent, and one agent carries a customer through the whole flow: calling the aggregation tool, applying the segmentation rules, assigning the label and writing it back.
- The agent has a DocumentDB aggregation tool, registered as a LangChain tool, that runs an aggregation pipeline through the Python MongoDB driver (e.g. PyMongo) against the event data in Azure DocumentDB for the customer the agent is working on, when the agent calls it.
- The aggregation pipeline computes the behavioural metrics per customer on demand, at the time the tool is called: recency, frequency and category affinity, which the tool returns to the agent.
- The segmentation rules are injected into the agent's prompt through context engineering (e.g. as a rules section assembled into the system prompt), so the rules the agent applies are present in its prompt context.
- The agent assigns a segment label to the customer from the computed metrics and the injected segmentation rules.
- The agent writes the assigned segment label back to that customer's profile document in Azure DocumentDB (e.g. an update that sets a segment field on the profile).

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
