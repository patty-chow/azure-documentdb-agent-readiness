# Reference requirements: Subscription billing engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Node.js application built with the Mongoose ODM, with Mongoose schemas/models for subscription plans, customers, charge events and trial entitlement documents, stored in Azure DocumentDB.
- Subscription plan documents describe the recurring billing a customer subscribes to (e.g. price and billing interval), and a subscription status is stored for each subscription (e.g. on the customer document).
- A charge operation that records a charge by inserting a charge event document and updating the subscription status it belongs to.
- The charge event insert and the subscription-status update run atomically in one multi-document transaction on a Mongoose session (startSession with withTransaction, or startTransaction / commitTransaction / abortTransaction).
- The charge operation takes an idempotency key and checks it before recording; when a charge with that key has already been recorded, it does not insert a second charge event (e.g. the key stored on the charge event with a unique index, or a lookup inside the transaction).
- Trial entitlement documents have a Date-typed expiry field, and a TTL index (expireAfterSeconds on that single date field) is created in code through Mongoose so Azure DocumentDB deletes trial entitlements automatically once they expire.

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
