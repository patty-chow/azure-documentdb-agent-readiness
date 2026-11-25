# Reference requirements: Lead scoring agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js LangChain agent scores one inbound lead per run: a single agent decides which tools to call, reasons over what they return and produces the result.
- The agent has a tool that fetches the lead's activity history from Azure DocumentDB (e.g. using the MongoDB Node.js driver).
- The agent has a tool that fetches the lead's company firmographic document from Azure DocumentDB.
- The agent has a tool that fetches the lead's engagement signals from Azure DocumentDB.
- The agent is given agent memory that retains context across its steps (e.g. the documents its tools returned earlier in the scoring run) so later reasoning can use it.
- The agent reasons over the fetched signals through an engineered prompt (e.g. a system prompt or prompt template that describes the scoring criteria) and assigns a score from 0 to 100 together with a one-paragraph rationale.
- The agent writes the score and the rationale back onto the lead's existing document in Azure DocumentDB (an update of that document, e.g. `updateOne` with `$set`).

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
