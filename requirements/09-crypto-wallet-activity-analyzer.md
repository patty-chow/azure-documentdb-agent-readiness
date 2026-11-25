# Reference requirements: Crypto wallet activity analyzer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the project in Python and expose a runnable Single-agent LangChain agent (use the term "LangChain agent") as the entrypoint that accepts a wallet address string input.
- Register and use a LangChain Tool named exactly "DocumentDB aggregation tool" that the agent calls to perform the database analysis.
- The "DocumentDB aggregation tool" must connect to Azure DocumentDB and execute a MongoDB-style aggregation pipeline against the transactions time-series collection for the provided wallet address.
- The aggregation pipeline executed by the tool must include a $match stage filtering on the provided wallet address and a grouping-by-day stage (e.g., $dateTrunc or equivalent) that computes per-day volume (sum of amount) and frequency (count of transactions).
- The aggregation pipeline must perform the volume and frequency metric computations server-side (in the pipeline) and return daily documents containing at minimum: date, daily_volume, daily_count.
- The tool must return the raw aggregation results to the agent (not only a formatted summary) so the agent can perform statistical analysis client-side.
- The LangChain agent must compute and flag statistical outliers from the returned daily metrics using a documented, reproducible method (for example, z-score thresholding or IQR) and mark which days are anomalous in the results.
- The agent must produce and return a plain-language text summary that describes activity patterns (overall trend, average daily volume and frequency, notable changes) and enumerates any anomalies with date, which metric is anomalous, and why it was flagged.
- The agent code must invoke the "DocumentDB aggregation tool" programmatically when given a wallet address (e.g., provide a function analyze_wallet(address: str) -> str or an agent.run(...) call) and return the plain-language summary as its output.
- The code must explicitly target Azure DocumentDB in its connection/configuration and use MongoDB aggregation pipeline semantics when calling the database aggregate operation.

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
