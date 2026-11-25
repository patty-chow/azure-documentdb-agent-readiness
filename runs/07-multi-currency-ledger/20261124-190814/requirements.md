# Reference requirements: Multi-currency ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose as the application's runtime and ODM for all database models and operations.
- Define a Transaction Mongoose model that includes at minimum: amount, currency (string), accountId (or ledger identifier), a reference field to an exchange rate document (ObjectId ref to the exchange-rate collection), a timestamp, and an idempotencyKey field.
- Define an ExchangeRate Mongoose model (exchange rate documents) that includes baseCurrency, quoteCurrency, numeric rate, and timestamp fields.
- Create a unique index on the idempotencyKey field (DB-level uniqueness) to enforce idempotency for transaction postings.
- Expose an HTTP endpoint to post transactions (e.g., POST /transactions) that accepts payload fields including accountId, amount, currency, exchangeRateId (or other exchange rate reference), and idempotencyKey.
- The POST /transactions handler must check the idempotencyKey and avoid creating duplicate postings (returning the existing transaction or a suitable status) and must rely on the DB-level unique constraint as part of the protection.
- When posting a transaction, perform the write(s) that record the transaction and update any related balance or ledger documents inside a single DocumentDB transaction (using Mongoose sessions / session.withTransaction) so the create and balance updates are atomic.
- The transaction document stored must include the currency field and a reference to the exchange rate document (do not inline the rate as the only source of truth).
- Expose an HTTP endpoint to query balances in any base currency (e.g., GET /balances?baseCurrency=USD) that implements the conversion and aggregation using a Mongoose aggregation pipeline.
- The balance aggregation must use $lookup (or equivalent aggregation stages) to reference the ExchangeRate documents and convert transaction amounts to the requested base currency within the pipeline, then sum/group per account to produce balances.
- The application must be configured to connect to Azure DocumentDB (MongoDB-compatible service) for its database operations (connection code / configuration points to Azure DocumentDB).

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
