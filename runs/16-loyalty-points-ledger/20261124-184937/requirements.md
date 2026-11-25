# Reference requirements: Loyalty points ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Builds the loyalty ledger in Node.js with Mongoose, storing every earn and redeem event as its own document in Azure DocumentDB.
- Provides a way to record an earn event and a redeem event (e.g. an HTTP endpoint or a service function) that appends a new event document each time.
- Treats event documents as immutable: the ledger changes only by appending new event documents, and an event document that has been written is never updated or deleted.
- Keeps a stored running balance (e.g. one balance document per member) that is updated each time an event is appended.
- Performs the event append and the running-balance update in one multi-document transaction on a Mongoose session (startSession with withTransaction, or start/commit/abort).
- Exposes a /balance endpoint that returns the current running balance.
- Exposes a /history endpoint that returns the recorded earn and redeem events (e.g. for one member, in chronological order).
- Includes an aggregation pipeline (Mongoose aggregate) run in Azure DocumentDB that sums lifetime points from the event documents and derives a tier status from that total (e.g. with $switch or $cond over tier thresholds).

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
