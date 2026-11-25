# Reference requirements: Real-time event stream ingestion

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The service is implemented in Node.js and exposes an entry point that receives customer behavioural events (page views, clicks, purchases) for ingestion.
- Received events are grouped into batches and written to Azure DocumentDB through a MongoDB-compatible Node.js driver (e.g. the mongodb package) as unordered bulk operations (e.g. bulkWrite or insertMany with ordered: false).
- A composite unique index on (customerId, eventId) is created in code on the collection that holds the events (e.g. createIndex({ customerId: 1, eventId: 1 }, { unique: true })) and is the mechanism used for deduplication.
- A change stream is opened in code against Azure DocumentDB (e.g. with the driver's watch() on the events collection or its database).
- Each change reported by the change stream triggers a downstream profile update job (e.g. invoking or enqueuing a profile-update function with the customer identified in the change event).

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
