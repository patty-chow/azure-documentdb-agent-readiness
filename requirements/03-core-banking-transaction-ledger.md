# Reference requirements: Core banking transaction ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Uses Node.js and the Mongoose ODM in the codebase (e.g., package.json and require/imports show "mongoose").
- Connects to Azure DocumentDB (MongoDB API) via mongoose.connect (connection string or config in code points to an Azure DocumentDB cluster).
- Defines a transaction/event document schema that includes a transactionRef field and the debit/credit details (amount, account identifier, timestamp, type) and models transactions as append-only event-sourced documents.
- Creates a unique index on transactionRef (schema.index or DB index) so the Azure DocumentDB server enforces uniqueness to prevent double-posting.
- Marks transaction/event fields as immutable at the schema level or otherwise prevents updates to existing transaction documents (so transaction documents are not modified after insert).
- Implements posting logic that starts a Mongoose session and uses multi-document transactions (startSession + session.startTransaction / commitTransaction / abortTransaction) for the operation.
- Within the same multi-document transaction the code inserts the new transaction document and updates the account balance snapshot document so the append and balance change are atomic.
- Stores account balance as a separate snapshot document and updates that snapshot within the transaction to reflect the new balance after applying the inserted transaction.
- Handles duplicate-key (transactionRef) errors from Azure DocumentDB by treating the operation idempotently (e.g., returning the existing transaction or a clear idempotent response and not applying the balance update again).
- Supports both debit and credit operations in the posting logic and applies the correct sign/operation when computing the resulting account snapshot balance.
- Includes a demonstrable example or script in the sample showing a successful transaction commit and a retry with the same transactionRef that does not double-post (verifiable by inspecting the transaction and account snapshot documents).

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
