# Reference requirements: Real-time event stream ingestion

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Node.js and connect to Azure DocumentDB using the MongoDB Node.js driver.
- Expose an HTTP endpoint (e.g., POST /events) that accepts customer behavioural events containing at minimum customerId, eventId, type (pageView|click|purchase), and timestamp, and returns an immediate 2xx on receipt.
- Buffer incoming events into batches and flush them with unordered bulk operations using collection.bulkWrite(operations, { ordered: false }) to maximize throughput; batch size and flush interval must be configurable.
- Create a composite unique index on (customerId, eventId) with unique: true on the Azure DocumentDB collection at service startup (createIndex or equivalent) to provide deduplication.
- Handle duplicate-key errors (E11000) returned from bulkWrite by ignoring/recording them and not failing the overall ingestion flow; successfully inserted documents must still be persisted.
- Open a change stream on the same collection (collection.watch()) and listen for insert events.
- On each insert change event, invoke an asynchronous profile update job handler (e.g., call a profileUpdateHandler function or enqueue a job) passing the event's customerId and payload; do not perform long synchronous work inside the change stream handler.
- Provide a simple simulation or load-test script that emits high-throughput events (including duplicates) to the ingestion endpoint and verifies that unordered bulkWrite is used and duplicates are deduplicated by the composite unique index.
- Ensure the service creates the target collection (or verifies it exists) before performing bulk writes or opening the change stream.
- Expose configuration for the Azure DocumentDB connection string, collection name, batch size and flush interval in code or config constants so reviewers can run the service against an Azure DocumentDB instance.

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
