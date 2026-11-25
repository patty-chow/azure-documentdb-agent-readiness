# Reference requirements: Next-best-action multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The system is written in Python and its agents and orchestrator are built with LangChain (LangChain Python), with the propensity agent, channel agent and timing agent each a separate agent that the orchestrator invokes.
- A propensity agent reads the customer's interaction history from Azure DocumentDB through a MongoDB-compatible Python driver (e.g. PyMongo) and scores the customer's likelihood of responding to each action type, returning a score per action type.
- A channel agent reads the customer's preference documents from Azure DocumentDB and selects the optimal contact channel for that customer.
- A timing agent determines the best send time for contacting the customer.
- An orchestrator runs the propensity, channel and timing agents for a given customer and combines their outputs into a single next-best-action recommendation (e.g. the highest-scoring action together with the selected channel and send time).
- The orchestrator writes the combined NBA recommendation for the customer to Azure DocumentDB.

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
