# Reference requirements: Option chain data store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python.
- Expose an HTTP ingestion endpoint (for example POST /ingest) that accepts options chain snapshots as JSON and triggers storage of the snapshot documents.
- In the ingestion handler, perform bulk writes to Azure DocumentDB using ordered=False bulk writes (the bulk write call must include ordered=False).
- Chunk very large snapshots into bounded batches and send multiple unordered bulk write calls so the service can handle high-volume document ingestion without exceeding single-call limits.
- Create compound indexes on (underlying, expiry, strike) on the Azure DocumentDB collection at startup or via a migration script (index key order must be underlying, then expiry, then strike).
- Persist each option document with explicit underlying, expiry, and strike fields; expiry must be stored in a queryable date format (ISO 8601 string or native date type).
- Expose an HTTP query endpoint (for example GET /chains) that accepts underlying and expiry parameters and returns the full options chain as a JSON array.
- Implement the query to filter by equality on underlying and expiry and to sort results by strike (so the query uses the (underlying, expiry, strike) compound index to avoid full collection scans).
- Do not abort an entire ingestion batch on single-document failures: capture per-document errors returned from unordered bulk writes, log them, and return a summary indicating partial successes/failures.
- All read and write operations must target Azure DocumentDB (the managed MongoDB-compatible service) and include the connection/configuration code in the repository that points to an Azure DocumentDB collection/cluster.

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
