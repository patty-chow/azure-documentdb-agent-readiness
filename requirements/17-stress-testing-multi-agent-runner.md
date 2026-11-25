# Reference requirements: Stress testing multi-agent runner

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implemented in Python using LangChain multi-agent architecture: repository contains an orchestrator component that invokes a scenario agent, an impact agent, and a reporting agent in sequence.
- The scenario agent produces structured macroeconomic shock parameters (e.g., interest_rate_shift, fx_rate_changes, credit_spread_shift) as a JSON/dict containing a unique scenario_id and timestamp.
- The impact agent accepts the scenario parameters and runs MongoDB-style aggregation pipelines against Azure DocumentDB position data (using collection.aggregate(...) or equivalent) to compute per-position and aggregate P&L impacts.
- Aggregation pipelines used by the impact agent include pipeline stages that perform filtering and arithmetic computations (e.g., $match, $project with $multiply/$subtract, $group and $sum) to derive stressed valuations and P&L deltas.
- The impact agent returns both per-position impact documents and aggregated statistics (total P&L, counts by asset class) that the reporting agent can consume.
- The reporting agent synthesises a structured stress test report (JSON/dict) that includes scenario metadata, aggregate P&L (total, mean, percentiles), per-asset-class breakdown, and a list of top-N worst positions, and returns that report programmatically.
- All scenario runs — including the scenario parameters, raw impact results, aggregated statistics, and the final report — are persisted as Azure DocumentDB documents in an audit collection (each stored document contains scenario_id, timestamp, agent outputs, and references/counts of affected positions).
- The codebase includes an executable example or test that runs the orchestrator end-to-end for at least one scenario, demonstrates the aggregation query against a positions collection, shows the generated report, and verifies that the corresponding audit document was inserted into Azure DocumentDB.

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
