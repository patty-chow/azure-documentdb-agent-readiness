# Reference requirements: Basel III capital ratio calculator

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution in Python and instantiate a LangChain agent named or clearly labeled as a "LangChain agent" that orchestrates the workflow from data retrieval to LLM invocation.
- Include a DocumentDB aggregation tool component, named or documented exactly as "DocumentDB aggregation tool", that connects to Azure DocumentDB and executes server-side aggregation pipelines (i.e., uses collection.aggregate) rather than performing client-side summation.
- The DocumentDB aggregation tool must read from the position documents and RWA documents (configurable collection names) in Azure DocumentDB and return aggregated totals in a single aggregation pipeline result.
- The aggregation pipelines must explicitly compute and return: total risk-weighted assets (RWA), total CET1 capital elements (sum of CET1 components from position documents), and total regulatory capital (sum of total capital elements), with the aggregation pipeline logic visible in the code (e.g., $group / $sum stages).
- The agent must compute CET1 ratio and total capital ratio using the aggregated sums with the formulas CET1 ratio = total CET1 / total RWA and total capital ratio = total capital / total RWA, and present both ratios as percentages (at least two decimal places) in the structured output.
- The LangChain agent must build an LLM prompt using explicit prompt engineering that (a) embeds Basel III thresholds (configurable values labelled as Basel III thresholds), (b) instructs the LLM to compare the computed CET1 and total capital ratios to those thresholds, and (c) asks for a board-ready capital adequacy commentary.
- The LLM invocation (labelled "LLM" in code/comments) must return a narrative commentary that includes: the computed ratios and raw aggregated totals, an interpretation of each ratio vs. the provided Basel III thresholds, and a concise board-ready executive summary/recommendation section.
- The LLM-generated commentary must include the LLM's reasoning or rationale (a short explanation of how the interpretation was reached, e.g., which thresholds were breached or met and by what margin) as part of the output.
- The agent must return a machine-readable result (e.g., JSON or dict) containing at minimum: aggregated totals (RWA, CET1, total capital), computed ratios (CET1 ratio, total capital ratio), the Basel III threshold values used, and the full LLM commentary.
- The code must detect and handle missing or zero total RWA in the aggregation result: if RWA is zero or absent, the agent must not perform division and must include an explicit warning or caveat in both the structured output and the LLM prompt/context so the commentary reflects the data limitation.

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
