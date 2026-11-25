# Reference requirements: SWIFT message parser & store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The service is written in async Python and uses Beanie ODM to define Document models that store parsed MT103 and MT202 messages as structured documents in Azure DocumentDB, with each parsed SWIFT field held as its own typed document field (e.g. sender, receiver, amount, currency, value date).
- The service exposes an async ingestion entry point that accepts incoming SWIFT MT messages and runs them through the parse, validate and bulk-write flow (e.g. an HTTP endpoint or an async function that takes a batch of raw message text).
- A parser extracts the fields of MT103 and MT202 messages from the raw SWIFT MT text and maps each message type's fields onto the corresponding Beanie document, handling both message types.
- Each parsed message is checked for its required fields before it is stored, and a message missing a required field is not written (e.g. a missing amount, currency or value date).
- Parsed documents are collected into batches and each batch is written to Azure DocumentDB in a single asynchronous bulk-write call (e.g. Beanie's `insert_many`).
- An async aggregation endpoint runs an aggregation pipeline in Azure DocumentDB (e.g. a `$group` stage via Beanie's `aggregate` or the underlying async driver) that groups the stored messages by day and by message type.
- The aggregation result reports, for each day and message type, the number of messages and the total of their transaction values.

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
