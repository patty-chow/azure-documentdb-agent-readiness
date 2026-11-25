# Reference requirements: Hospital bed occupancy tracker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB via a MongoDB-compatible connection string taken from configuration/environment variables and establish the Mongoose connection at service startup.
- Define a Mongoose model for bed status documents that includes at minimum: bedId, wardId, status (enum: "occupied" | "available" | "cleaning"), lastUpdated (Date), and a date field used for TTL expiration (e.g., cleaningExpiresAt).
- Define a Mongoose model/collection for a single occupancy summary document per ward (unique by wardId) that stores integer counts for occupied, available, cleaning, a configured capacity value, an alert flag (or threshold state), and a lastUpdated timestamp.
- On startup create a TTL index (using Mongoose/collection.createIndex) on the cleaningExpiresAt field with expireAfterSeconds set from a configurable TTL timeout; create the index as a partial index that only applies to documents where status == "cleaning" so only cleaning-state documents expire.
- When a bed status is set to "cleaning", set its cleaningExpiresAt timestamp to now + configured timeout so the TTL index will expire it automatically.
- Open a DocumentDB change streams watch on the bed status collection using Mongoose (model.watch or underlying collection.watch) configured to provide the needed document images (e.g., fullDocument and pre-image/fullDocumentBeforeChange as supported) so the handler can determine status transitions.
- In the change stream handler detect status transitions (inserts, updates/replaces where status changed, and deletes from TTL expiration) and compute the previous and new status for each event so you know which counters to decrement and increment.
- Update the per-ward occupancy summary using a single atomic update (e.g., updateOne with $inc, $set and upsert: true) so the counters for occupied, available and cleaning are adjusted in one atomic operation for each transition.
- When updating the occupancy summary, set or clear the ward-level capacity alert atomically (e.g., based on occupied >= capacity) and update lastUpdated; ensure this logic runs on every transition including deletions caused by TTL expiry.
- Ensure deletion events originating from TTL index expiration are handled by the change stream handler and cause the occupancy summary cleaning count to decrement so the live summary stays correct.

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
