# Reference requirements: Multi-currency ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js application that uses Mongoose as the ODM against Azure DocumentDB, with Mongoose models for ledger transactions and for exchange-rate documents, each kept in its own collection.
- The transaction model has a currency field and a reference to an exchange-rate document (e.g. a Mongoose `ref` holding that document's `_id`), and each posted transaction is stored with the reference to the rate document it was recorded against.
- Every transaction posting carries an idempotency key, and posting the same key a second time does not create another ledger entry (e.g. the key is persisted alongside the transaction and checked before the write).
- Posting a transaction performs its writes inside an Azure DocumentDB multi-document transaction using a Mongoose session (`session.withTransaction`, or `startTransaction` followed by `commitTransaction`/`abortTransaction`), and the model operations for the posting are passed that session.
- An HTTP endpoint for posting transactions (e.g. `POST /transactions`) that accepts the transaction to record (e.g. amount, currency, exchange-rate reference and idempotency key) and persists it through the Mongoose models.
- An HTTP endpoint for querying balances that takes the requested base currency as a request parameter (e.g. a `base=USD` query-string value) and returns the ledger balances expressed in that currency, for any currency that has an exchange-rate document.
- Balance conversion is a Mongoose aggregation pipeline executed by Azure DocumentDB: the pipeline joins transactions to their referenced exchange-rate documents (e.g. `$lookup`), converts each amount into the base currency (e.g. `$multiply`/`$divide`) and sums the converted amounts (e.g. `$group`), and the endpoint returns the pipeline's output.

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
