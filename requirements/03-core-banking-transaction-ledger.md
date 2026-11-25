# Reference requirements: Core banking transaction ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The ledger is a Node.js application that uses Mongoose as its ODM: accounts and transactions are defined as Mongoose schemas and models, and every read and write of ledger data goes through them.
- Every debit and every credit is recorded as its own transaction document in Azure DocumentDB, inserted once and left unchanged afterwards (no code path updates or deletes a posted transaction document).
- Each account has a balance snapshot document that holds its current balance (e.g. an Account model with a balance field).
- Posting a transaction runs inside an Azure DocumentDB multi-document transaction: a Mongoose session (withTransaction, or start/commit/abort) wraps both the insert of the transaction document and the update of the account balance snapshot, so both are committed together or neither is.
- The balance snapshot is adjusted by the posted amount in the direction of the entry (a credit raises it, a debit lowers it).
- Every transaction document carries a transactionRef field supplied with the posting request.
- The transactionRef field has a unique index, declared in the Mongoose schema or created in code, so Azure DocumentDB enforces uniqueness.
- A second posting with an already-used transactionRef is rejected: the unique index makes the insert fail and the enclosing transaction aborts, so the balance snapshot is not changed by the duplicate.

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
