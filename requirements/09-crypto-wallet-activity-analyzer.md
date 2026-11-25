# Reference requirements: Crypto wallet activity analyzer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python LangChain agent (a single agent) that accepts a wallet address as its input and returns a plain-language summary as its output.
- A DocumentDB aggregation tool exposed to the LangChain agent as a tool; it runs an Azure DocumentDB aggregation pipeline over the wallet transaction documents through a MongoDB driver (e.g. PyMongo).
- The aggregation pipeline selects the given wallet's transactions and groups them by day, treating each transaction as a time-series document (e.g. a $match stage on the wallet followed by a $group stage keyed on the transaction's date).
- For each day, the pipeline computes volume and frequency metrics (e.g. summed amount and transaction count per day).
- The tool flags statistical outliers among the daily metrics (e.g. days whose volume or frequency deviates from the wallet's own norm by a z-score or similar threshold) and returns the flagged days alongside the per-day metrics.
- When given a wallet address, the agent invokes the aggregation tool through LangChain tool use and builds its answer from the tool's returned results.
- The agent's response is a plain-language summary that describes the wallet's activity patterns over time and names any anomalies the analysis detected.

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
