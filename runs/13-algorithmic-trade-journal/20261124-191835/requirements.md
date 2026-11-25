# Reference requirements: Algorithmic trade journal

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python service inserts each trading signal, each execution and each outcome as its own document into Azure DocumentDB using a MongoDB-compatible Python driver (e.g. PyMongo); every document carries a strategy identifier and a timestamp.
- Journal documents are immutable: the service has no code path that updates or deletes a stored signal, execution or outcome document.
- Win rate, average P&L and drawdown are computed by aggregation pipelines run in Azure DocumentDB (e.g. through the driver's aggregate call) that group on the strategy identifier, returning one result per strategy.
- The pipeline computes win rate per strategy from the outcome documents (e.g. winning outcomes divided by total outcomes).
- The pipeline computes average P&L per strategy from a numeric P&L value on the outcome documents.
- The pipeline computes drawdown per strategy from that strategy's outcomes ordered by timestamp (e.g. the largest peak-to-trough decline of cumulative P&L).
- A context engineering layer in Python takes the aggregated per-strategy stats and formats them into prompt-ready context for LLM-driven strategy review (e.g. a structured block of win rate, average P&L and drawdown with a short narrative).
- The service exposes operations (e.g. functions or endpoints) to record a signal, an execution or an outcome, and to produce the review context for a given strategy.

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
