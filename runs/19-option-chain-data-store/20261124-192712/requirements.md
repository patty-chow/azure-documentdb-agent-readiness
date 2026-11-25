# Reference requirements: Option chain data store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The ingestion service is written in Python and accepts options chain snapshots (e.g. through an HTTP endpoint that receives a snapshot payload), storing each snapshot's option records as documents in an Azure DocumentDB collection.
- Each received snapshot is persisted with a bulk write through the Python MongoDB driver (e.g. pymongo's `bulk_write` given a list of write operations).
- The bulk write is issued with `ordered=False`.
- The code creates a compound index on the option documents collection with keys in the order underlying, expiry, strike (e.g. `create_index([("underlying", 1), ("expiry", 1), ("strike", 1)])`).
- The option documents carry the underlying, expiry and strike fields that the compound index is built on.
- The service exposes an endpoint that takes an underlying and an expiry date as inputs (e.g. path or query parameters).
- That endpoint queries Azure DocumentDB with equality filters on underlying and expiry, the leading prefix of the compound index, and returns the full set of matching option documents for that chain.

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
