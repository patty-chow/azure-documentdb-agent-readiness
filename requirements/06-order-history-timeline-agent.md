# Reference requirements: Order history & timeline agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python with LangChain as a single conversational agent that takes a customer service agent's question and chooses among its tools to answer it.
- Provide a tool that fetches a customer's order history from Azure DocumentDB through a MongoDB driver (e.g. PyMongo) and returns the matching order documents to the agent.
- Provide a tool that runs MongoDB aggregation pipelines against the orders in Azure DocumentDB to compute spend summaries (e.g. total spend over a period) and returns the results to the agent.
- Provide a tool that looks up an individual order in Azure DocumentDB and returns its status to the agent.
- Give the agent LangChain agent memory that carries conversation context (e.g. the customer under discussion and the period last asked about) from one turn to the next.
- Resolve follow-up questions such as "what about last month?" from that context, turning the relative reference into the concrete filter (e.g. a date range) used in the tool call.
- Reply in conversational language that summarises and reasons over the tool results for the customer service agent.

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
