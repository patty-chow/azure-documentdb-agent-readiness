# Reference requirements: Subscription billing engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB (code calls mongoose.connect with an Azure DocumentDB/MongoDB URI and package.json lists mongoose).
- Define Mongoose schemas/models for subscription plans, customers, charge events, and entitlement documents (e.g., SubscriptionPlan, Customer, ChargeEvent, Entitlement) and export them for use by the billing engine.
- Implement and export an async processCharge function (or API route handler) that accepts at minimum customerId, planId, amount, and idempotencyKey parameters.
- Use a MongoDB session and DocumentDB transactions (multi-document transactions) inside processCharge: start a session, run the transactional logic with session/withTransaction, and commit/abort the session so the charge creation and subscription update are atomic.
- Inside the same DocumentDB transaction, create a ChargeEvent document and update the corresponding customer/subscription document (e.g., update billing status, lastChargedAt, billingCycle) so both changes are applied or rolled back together.
- Implement idempotency key checks: processCharge checks for an existing ChargeEvent with the same idempotencyKey and customerId and returns the existing event without creating a duplicate if found.
- Enforce idempotency at the database level by creating a unique (compound) index on the ChargeEvent collection for (customerId, idempotencyKey) to prevent race-condition double-billing.
- Define TTL indexes for entitlement documents (e.g., a Date field and schema.index(..., { expireAfterSeconds: 0 })) so trial entitlement documents inserted with an expiry timestamp are auto-expired by Azure DocumentDB.
- When creating a trial entitlement, set the expiry timestamp field used by the TTL index and associate the entitlement with the correct customer so it is auto-removed after the TTL.
- Ensure transactional error handling: on any error during the DocumentDB transaction the code aborts the transaction and does not persist a partial ChargeEvent or subscription update.
- Provide an automated check or example (script or test) that simulates concurrent/process calls using the same idempotencyKey and verifies only one ChargeEvent is persisted and the subscription update is applied once.

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
