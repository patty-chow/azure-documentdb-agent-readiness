# Reference requirements: Cross-border payment audit trail

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB: the code must call mongoose.connect(...) using a MongoDB URI read from an environment variable that clearly indicates Azure DocumentDB (e.g., AZURE_DOCUMENTDB_URI).
- Define a Mongoose audit document schema and model named for the audit collection that includes at minimum: paymentReference (string), stage (enum containing exactly initiated, routed, FX converted, settled), timestamp or createdAt (Date with default Date.now), and a payload/object field for stage details.
- Create an index on paymentReference and a TTL index on the createdAt/timestamp field (using schema.index(..., { expireAfterSeconds: <env-configured value> })) so the TTL value is configurable via environment (e.g., AUDIT_TTL_SECONDS).
- Implement write-only behavior for lifecycle events: the service must insert a new audit document for each stage (initiated, routed, FX converted, settled) — either via dedicated endpoints or a single POST endpoint — and must not update existing audit documents when advancing stages.
- Implement application-layer guards that block any update or delete operations against audit documents: include Mongoose middleware or explicit checks that reject calls to updateOne, updateMany, findOneAndUpdate, findByIdAndUpdate, deleteOne, deleteMany, or remove with an error.
- Do not expose HTTP endpoints that perform updates or deletes of audit documents; API surface should only allow inserting new audit documents and reading aggregations (no PUT/PATCH/DELETE routes for audit records).
- Expose an HTTP aggregation endpoint that accepts a paymentReference and returns the full timeline reconstructed using a Mongoose aggregation pipeline (match by paymentReference, sort by timestamp ascending, and project stage, timestamp and payload); the endpoint must return the ordered array of stage entries in JSON.
- Validate stage values at the API and model level so that attempts to insert a document with a stage outside the enum (initiated, routed, FX converted, settled) are rejected with a 4xx error.
- Include a demonstrable sample or script in the repo that writes the four-stage lifecycle for a sample paymentReference to Azure DocumentDB and shows the aggregation endpoint returning the ordered timeline for that paymentReference.

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
