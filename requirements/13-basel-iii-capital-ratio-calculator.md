# Reference requirements: Basel III capital ratio calculator

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python as a single LangChain agent: one LLM-backed agent handles the whole request from question to commentary.
- Give the agent a DocumentDB aggregation tool: a LangChain tool whose implementation runs an aggregation pipeline against Azure DocumentDB through a MongoDB-compatible Python driver (e.g. pymongo) and returns the aggregated results to the agent.
- The aggregation pipeline itself produces the totals: it sums risk-weighted assets and the capital elements (e.g. CET1 capital, total capital) across the stored position documents (e.g. a `$group` stage with `$sum` accumulators).
- Compute the capital ratios from those aggregated totals (e.g. CET1 capital divided by risk-weighted assets, total capital divided by risk-weighted assets).
- Use prompt engineering for the LLM call: the prompt carries the computed ratios and instructs the LLM to interpret them against Basel III thresholds (e.g. the 4.5% CET1 and 8% total capital minimums).
- The agent's final output is an LLM-generated, board-ready capital adequacy commentary that states how each ratio stands against the Basel III thresholds, written for a board audience.

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
