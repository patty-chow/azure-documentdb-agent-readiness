# Reference requirements: ATM network status monitor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Node.js service that accepts ATM heartbeat JSON documents over an HTTP endpoint and writes them to Azure DocumentDB using Mongoose.
- Define a Mongoose schema/model for heartbeat documents that includes atmId, timestamp, and a status field constrained to the values "online", "offline", and "low cash".
- Connect to Azure DocumentDB with a MongoDB-compatible connection string provided via configuration or environment variable and use that connection for all Mongoose operations.
- Open a change stream (change streams) on the heartbeats collection using Mongoose's Model.watch() or collection.watch() and listen for inserts and updates that affect ATM status.
- Detect status changes (online, offline, low cash) from the change stream events and handle them in the change-stream event handler.
- Maintain a single live network summary document in Azure DocumentDB (e.g., a known _id) that tracks total ATMs, online count, offline count, low cash count, and a lastUpdated timestamp.
- Update the live network summary document atomically (e.g., using $inc and $set or a transaction) from change-stream handlers to avoid race conditions on concurrent events.
- Compute availability as the percentage of ATMs currently "online" (online / total) and read the availability threshold from a configurable source (environment variable or config file).
- When computed availability falls below the configurable threshold, create an alert record in Azure DocumentDB's alerts collection that includes timestamp, availability, threshold, and the summary snapshot; optionally also emit a configurable webhook or log for external alerting.
- Implement resume/reconnect logic for the change stream (using resumeToken or automatic re-establishment) so the long-running watcher recovers from transient errors without losing events.
- Provide a simple heartbeat sender or example script that posts sample heartbeats (including status transitions) to the service so a reviewer can reproduce status changes and verify summary updates and alerts.

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
