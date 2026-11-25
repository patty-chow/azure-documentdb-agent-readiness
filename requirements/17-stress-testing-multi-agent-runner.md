# Reference requirements: Stress testing multi-agent runner

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The system is written in Python with LangChain and is organised as a multi-agent runner: an orchestrator coordinates three distinct agent roles (a scenario agent, an impact agent and a reporting agent) and runs them as one stress test, handing each agent's output to the next.
- The scenario agent uses the LLM to generate macroeconomic shock parameters for a stress scenario and returns them in a structured form (e.g. a dict of shock magnitudes per risk factor) that the impact agent can consume.
- The impact agent computes P&L impacts by running aggregation pipelines in Azure DocumentDB (e.g. PyMongo's `collection.aggregate` with `$match` and `$group` stages) over the stored position data to apply the scenario's shock parameters (e.g. inside the pipeline stages, or to the aggregated figures).
- The reporting agent synthesises the scenario parameters and the impact results into a structured stress test report (e.g. a dict or Pydantic model with scenario, aggregate P&L and breakdown sections), and the orchestrator returns that report as the result of the run.
- Every scenario run is stored as a document in Azure DocumentDB for audit (e.g. a document recording the generated shock parameters, the impact figures and the report).

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
