# Reference requirements: Open banking API cache layer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB (the MongoDB-compatible endpoint) and perform all cache reads/writes through Mongoose models.
- Define a Mongoose schema/model for cached open banking responses that includes: a deterministic cache key, the response payload, a fetchedAt timestamp, and a Date field used for expiry; create a TTL index (TTL index) on the expiry Date field via the schema (e.g., schema.index(..., { expireAfterSeconds: 0 })).
- Implement deterministic cache key derivation from the incoming open banking API request (including HTTP method, URL/path, and relevant headers/body) and use that key to look up documents in Azure DocumentDB.
- On an incoming API request, check Azure DocumentDB (via Mongoose) for a cached document for the cache key and, if the document is within the configured freshness window, return the cached result immediately.
- If a cached document exists but is stale (outside the freshness window), immediately return the stale cached response to the client and trigger an asynchronous background refresh (stale-while-revalidate) that fetches a fresh response from the third-party open banking API.
- If no cached document exists for the key, synchronously fetch the response from the open banking API, store it in Azure DocumentDB (upsert via Mongoose), and return the live response to the client.
- Perform the background refresh as a non-blocking asynchronous task so the client response is not delayed; the background task must fetch the live API result and atomically upsert the cache document in Azure DocumentDB, updating fetchedAt and the expiry Date field.
- Prevent duplicate concurrent background refreshes for the same cache key (for example by using an atomic findOneAndUpdate flag or an in-memory/per-key lock) so only one refresh is in-flight per key.
- Ensure failed background refreshes do not overwrite existing cached data with error responses; on refresh failure keep the previous cached document unchanged and retry on a subsequent stale-while-revalidate trigger.
- Include observable indicators in logs or responses that let a reviewer verify whether each response was served as a cache hit (fresh), cache hit (stale-while-revalidate served), or cache miss (live fetch), so the stale-while-revalidate behavior can be validated.

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
