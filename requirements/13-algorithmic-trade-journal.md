# Reference requirements: Algorithmic trade journal

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python and expose functions or HTTP endpoints that insert three distinct journal document types named "signal", "execution", and "outcome" into Azure DocumentDB; each insert path must create a new document (no updates) and be callable in the codebase.
- Each journal document inserted must include at minimum these fields: strategy_id (string), timestamp (stored in ISO 8601 / UTC), type (one of "signal", "execution", "outcome"), and for outcome documents a numeric pnl field; documents must also include a document-level version integer when applicable.
- Enforce immutability of journal entries in code by never issuing update operations for signal/execution/outcome events; implement document versioning by writing a new document with the same strategy_id and an incremented version field whenever a new version is created.
- Create a time-series-optimized storage layout for the journal in Azure DocumentDB by either configuring a time-series collection (if supported) or creating an index on (strategy_id, timestamp) to support efficient time-series aggregation queries.
- Provide MongoDB-style aggregation pipelines (an array of aggregation stages stored in code) against Azure DocumentDB that compute, per strategy_id, the win rate (wins / total outcomes), average P&L (mean of pnl), and total number of outcomes; the pipelines must be callable from the Python service.
- Implement an aggregation pipeline that computes max drawdown per strategy by calculating cumulative P&L ordered by timestamp and deriving the maximum peak-to-trough decline (using windowing like $setWindowFields or equivalent pipeline stages) and return max_drawdown as a numeric value.
- Package the aggregation pipelines as reusable functions that accept filtering parameters (at least strategy_id and an optional time range: start_timestamp, end_timestamp) and return structured numeric results for win rate, average P&L, total P&L, trade count, and max_drawdown.
- Add a context engineering layer in Python named/organized as such that accepts the aggregation output and formats a deterministic, LLM-ready text summary including strategy_id, analyzed period, trade count, win rate as percent, average P&L, total P&L, max drawdown, and top 3 trades (or a note when fewer than 3 trades exist).
- Include a Python data-seeding script that inserts representative signals, executions, and outcome documents for at least two different strategy_id values across a time range; the seeded dataset must be constructed so expected metric values (win rate, avg P&L, drawdown) are known and verifiable.
- Provide automated tests (unit or integration) that run the aggregation pipelines on the seeded data and assert the computed win rate, average P&L, and max drawdown match the expected values, and that the context engineering layer returns the expected formatted summary for a given aggregation result.

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
