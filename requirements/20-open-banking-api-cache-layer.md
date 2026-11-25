# Reference requirements: Open banking API cache layer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js caching layer wraps or intercepts outgoing open banking API calls so that every call passes through the cache lookup before any request reaches the upstream API.
- The cache lookup queries Azure DocumentDB through the Mongoose ODM for a cached response document that matches the intercepted request (e.g. keyed on the request URL and parameters).
- A TTL index is created in code on a Date field of the cache documents (e.g. a Mongoose schema index with expireAfterSeconds) so Azure DocumentDB expires cached response documents automatically.
- A cached document's freshness is decided from a date stored on the document (e.g. the TTL date field compared against the current time), so a document can be stale while it still exists in the collection.
- When a matching cached document is fresh, the cached response is returned to the caller and the open banking API is not called.
- When no matching cached document exists, the response is fetched from the open banking API, stored in Azure DocumentDB as a new cache document through Mongoose, and returned to the caller.
- When a matching cached document is stale, the stale cached response is returned to the caller immediately and a background refresh fetches the open banking API and stores the refreshed response in Azure DocumentDB without delaying that response (stale-while-revalidate).

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
