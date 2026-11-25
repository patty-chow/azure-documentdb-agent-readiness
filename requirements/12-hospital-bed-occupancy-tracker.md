# Reference requirements: Hospital bed occupancy tracker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js service uses Mongoose to store bed status documents in Azure DocumentDB; each bed document belongs to a ward and carries a status that is one of occupied, available or cleaning.
- The service opens a change stream on the bed status collection and keeps consuming its events while running, so that bed status changes are picked up as they are written.
- From the change stream events the service detects status transitions between occupied, available and cleaning (e.g. by comparing the bed's previous status with the new one) and acts only on events where the status changed.
- A live occupancy summary document is maintained per ward (e.g. holding counts of beds per status), and it is updated from the change stream handler on every detected transition.
- Each summary update is a single atomic update operation (e.g. one updateOne with $inc adjusting the affected counts).
- A TTL index is created in code on a Date field of the bed status documents, with its expireAfterSeconds (or the Date value it expires on) derived from a configurable cleaning timeout.
- Cleaning-state documents, and only those, are expired by the TTL index once the timeout has passed (e.g. the indexed Date field is set when a bed enters cleaning and unset when it leaves, or the index carries a partial filter on the cleaning status).

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
