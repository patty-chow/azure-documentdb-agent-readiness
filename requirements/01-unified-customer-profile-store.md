# Reference requirements: Unified customer profile store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js with the Mongoose ODM to implement the service (code must import and use Mongoose).
- Connect Mongoose to Azure DocumentDB using a MongoDB-compatible connection string so the canonical documents are stored in Azure DocumentDB.
- Define a Mongoose schema for the canonical customer profile that includes a top-level stable customerId field and create a unique index on customerId to drive identity resolution.
- Model nested sub-documents for each source system under distinct fields in the schema (at minimum fields named for CRM, e-commerce, and support) so each source’s attributes are stored under its own sub-document.
- Expose a handler that receives customer events from multiple source systems; events must include the source identifier (CRM, e-commerce, or support) and the stable customerId.
- For each incoming event, perform an upsert into Azure DocumentDB (e.g., using findOneAndUpdate or updateOne with upsert: true) targeting the document whose customerId matches the event’s stable customerId.
- When applying the update, merge the event’s attributes into the appropriate nested sub-document using the $set operator on the source-specific path (e.g., $set: { "crm.<field>": value } or "e-commerce.<field>": value) so unrelated fields are not overwritten.
- Only set the fields provided by the event (no document replacement); ensure existing data in other nested sub-documents and top-level fields is preserved after the upsert.
- Use atomic MongoDB update semantics (upsert + $set) to handle concurrent updates safely rather than replacing whole documents.

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
