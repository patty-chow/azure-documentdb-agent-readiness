# Reference requirements: Cross-border payment audit trail

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js audit trail service built on the Mongoose ODM, with a Mongoose model for the audit documents it stores in Azure DocumentDB.
- Each stage of the cross-border payment lifecycle (initiated, routed, FX converted, settled) is recorded by inserting a new audit document, so a payment accumulates one document per stage.
- Each audit document carries the payment reference and the lifecycle stage it records, plus a field the timeline can be ordered by (e.g. a recorded-at timestamp).
- Application-layer guards reject attempts to update or replace an existing audit document (e.g. Mongoose pre-hooks on update and replace operations, or immutable schema fields).
- An aggregation endpoint accepts a payment reference and reconstructs that payment's full timeline with a Mongoose aggregation pipeline (e.g. a $match on the payment reference followed by a $sort on the ordering field), returning the stage documents in chronological order.

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
