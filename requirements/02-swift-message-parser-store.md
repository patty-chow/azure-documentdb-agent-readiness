# Reference requirements: SWIFT message parser & store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python using async functions and define persistence models using Beanie ODM (Beanie ODM must be used to model documents).
- Initialize Beanie against an Azure DocumentDB MongoDB-compatible endpoint (async Motor client + Beanie init), with connection configuration clearly visible in the code.
- Provide an async parser that accepts raw SWIFT MT messages and recognizes MT103 and MT202 message types (must detect message_type = "MT103" or "MT202").
- From MT103 and MT202 messages extract and map standard fields into the document model at minimum: transaction reference (field 20), value date/currency/amount (field 32A), ordering customer (field 50A/50K), beneficiary/customer (field 59), and instructing/receiving agents where present (e.g., 52/53/54); include the raw message and received_at metadata in each document.
- Define Beanie Document schemas with typed Pydantic fields for all parsed fields and enforce validation rules so that required fields (message_type, transaction reference (20), amount, currency, value date) are rejected if missing or invalid.
- Implement async batch collection and bulk-writes batches for throughput: accumulate parsed documents into configurable batches and perform async bulk insert operations (via Beanie insert_many or by calling the underlying Motor collection bulk/insert API) when batch size or flush interval is reached.
- Ensure bulk write operations target Azure DocumentDB collections and are performed as efficient bulk/unordered inserts (i.e., use insert_many/unordered bulk write options) so throughput behavior is testable.
- Surface parsing and validation failures and bulk-write errors: the code must return or log validation errors for individual messages and report which documents failed in bulk-write responses or logs.
- Expose an async aggregation endpoint that, when invoked, runs a MongoDB aggregation pipeline (via Beanie or the underlying Motor collection) and returns daily message volume and total value grouped by message type (grouped by ISO day and message_type, summing the numeric amount field).
- The aggregation result must include counts and summed amounts; if multiple currencies exist, the endpoint must return totals broken down by currency (i.e., group by date + message_type + currency) so totals are unambiguous.

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
