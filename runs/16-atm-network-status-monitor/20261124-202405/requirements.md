# Reference requirements: ATM network status monitor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Receives status heartbeat documents from ATMs and writes each one to Azure DocumentDB through a Node.js Mongoose model.
- Opens a change stream on the heartbeat collection in Azure DocumentDB and processes change events as they arrive.
- Detects from the change-stream events when an ATM's status changes to online, offline or low cash (e.g. by comparing the incoming status with the ATM's last known status).
- Maintains a single live network summary document in Azure DocumentDB that the change-stream handler updates on each detected status change (e.g. counts of online, offline and low-cash ATMs).
- Computes a network availability metric (e.g. the share of ATMs currently online, kept on the summary document) and uses it for the alert check.
- Triggers an alert when the computed availability drops below the threshold (e.g. writes an alert document or logs an alert for the operations team).
- The availability threshold is configurable (e.g. via an environment variable), and the alert check uses the configured value.

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
