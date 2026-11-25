# Reference requirements: Interest rate scenario modeler

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build a Python LangChain single agent that exposes an Azure DocumentDB aggregation tool as a LangChain tool the agent can call.
- The aggregation tool runs an aggregation pipeline in Azure DocumentDB (through a MongoDB driver, e.g. PyMongo) over the stored position documents.
- The pipeline groups the positions by maturity bucket and separates fixed-rate from floating-rate positions within each bucket (e.g. a `$group` on a derived bucket key and the rate type), and the tool returns the grouped results to the agent.
- The agent's prompt instructs the LLM to reason through the net interest income (NII) impact of three interest rate scenarios: a parallel shift, a steepening and an inversion.
- At runtime the agent calls the aggregation tool and passes the grouped fixed/floating positions into the LLM prompt as the input for the scenario analysis.
- The agent returns a structured scenario analysis report that covers each of the three scenarios.

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
