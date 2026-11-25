# Reference requirements: Open banking API cache layer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the caching layer in Node.js using the Mongoose ODM to read and write cache documents in Azure DocumentDB.
- Provide a function or middleware that intercepts outgoing open banking API calls, derives a cache key from the request (e.g., URL + query/body) and queries the cache collection in Azure DocumentDB via Mongoose for a matching document.
- Treat a cached document as fresh when a stored timestamp plus a freshness duration constant in code indicates it is still valid (e.g., compare a stored timestamp field such as cachedAt against now); if fresh, immediately return the cached response to the caller.
- If no cached document exists, synchronously fetch the response from the upstream open banking API, store the response and a timestamp in Azure DocumentDB via Mongoose, and return the fetched response.
- If a cached document exists but is stale (freshness check fails while the document still exists), immediately return the stale cached response to the caller and trigger an asynchronous background fetch of the open banking API that updates the stored document in Azure DocumentDB with the new response and a refreshed timestamp (the background refresh must not block the immediate response).
- Create a TTL index in code on a date field of the cache documents (using Mongoose schema index with expireAfterSeconds or an equivalent createIndex call) so Azure DocumentDB will automatically expire documents after the intended lifetime.
- Store the API response payload and the timestamp field used for freshness/TTL on each cache document (e.g., fields for response body and cachedAt/expiresAt) and update those fields when inserting or refreshing the document.

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
