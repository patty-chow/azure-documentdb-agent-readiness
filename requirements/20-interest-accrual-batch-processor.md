# Reference requirements: Interest accrual batch processor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB (code calls mongoose.connect with a configurable Azure DocumentDB connection string).
- Implement a daily schedule that invokes the batch processor once per day (e.g., cron or timer) and is configurable for the run time.
- Query only active interest-bearing account documents from Azure DocumentDB and iterate them with a Mongoose cursor (cursor-based pagination) so documents are retrieved in cursor-paginated batches rather than loaded all at once.
- Process accounts in configurable batches (batch size parameter) so the processor works on bounded groups of documents per iteration.
- For each account compute one-day accrued interest using the account's rate and balance fields (explicit arithmetic using account.rate and account.balance) and produce a numeric accrual amount.
- For each computed accrual create a new immutable journal document in a separate journal collection/model (fields include accountId, amount, timestamp/accruedDate) and ensure journal entries are inserted only (no updates/overwrites of existing journal documents).
- Buffer journal documents and perform inserts using unordered bulk writes (Mongoose bulkWrite with ordered: false) to maximize throughput.
- Chunk bulkWrite operations into configurable maximum bulk sizes and include a configurable pause/backoff between bulk chunks to provide controlled throughput to Azure DocumentDB.
- Ensure the implementation uses streaming/pagination semantics so memory usage remains bounded (no accumulation of all account documents in memory before writing).

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
