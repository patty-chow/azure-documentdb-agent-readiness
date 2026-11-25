# Reference requirements: Interest accrual batch processor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The batch processor is a Node.js application that uses Mongoose as the ODM for every read and write against Azure DocumentDB, with the account and journal documents defined as Mongoose models.
- The processor runs as a scheduled job that executes once per day (e.g. a cron-style daily schedule).
- The processor queries all account documents that are active and interest-bearing, iterating them through a Mongoose query cursor and grouping the streamed documents into fixed-size batches.
- For each account document, the processor computes the accrued interest for the run from that account's rate and balance.
- Each computed accrual is written as a new, immutable journal document: one journal document per account per run, created by insert only (e.g. referencing the account and carrying the interest amount).
- Each batch's journal inserts are sent to Azure DocumentDB as exactly one unordered bulk write (bulkWrite with ordered: false on the Mongoose model), containing only that batch's operations.

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
