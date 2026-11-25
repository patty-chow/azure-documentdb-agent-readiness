# Reference requirements: Subscription billing engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js with the Mongoose ODM to define and persist subscription plans, customer records, charge events, and entitlement documents in Azure DocumentDB.
- Implement a charge operation that uses a Mongoose session and session.withTransaction (startSession + withTransaction) to atomically insert a charge event document and update the corresponding customer's subscription status in Azure DocumentDB.
- Ensure the transaction spans multiple collections (at least the charge events collection and the subscriptions/customers collection) so the insert of the charge event and the subscription-status update occur together.
- Add idempotency-key enforcement by creating a unique index in code on the charge events collection for an idempotency key (e.g., an "idempotencyKey" field) so duplicate keys are rejected by Azure DocumentDB.
- Inside the same transaction, query for an existing charge event with the same idempotency key and, if found, do not create a new charge event but return/reuse the existing event (prevent double-billing).
- Model trial entitlement documents with an expiry date field and programmatically create a TTL index (MongoDB-style expireAfterSeconds on that date field) so trial entitlement documents auto-expire in Azure DocumentDB.
- Create the required indexes (the charge-events unique idempotency index and the entitlement TTL index) in code via the Mongoose/driver APIs against Azure DocumentDB (e.g., at startup or migration time).

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
