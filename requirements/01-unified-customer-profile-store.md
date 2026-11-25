# Reference requirements: Unified customer profile store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The service is written in Node.js and uses the Mongoose ODM, with a Mongoose schema and model for the canonical customer profile document stored in Azure DocumentDB.
- The canonical profile schema carries a stable `customerId` field and one nested sub-document per source system (CRM, e-commerce and support) holding that system's attributes (e.g. top-level fields `crm`, `ecommerce`, `support`).
- The service exposes an entry point that receives a customer event carrying its originating source system, the customer's `customerId` and that system's attributes (e.g. an HTTP endpoint or an exported handler function).
- Identity resolution matches an incoming event to its profile on the stable `customerId` alone: the update's filter selects the document by `customerId`.
- Each event is applied through a Mongoose upsert (e.g. `findOneAndUpdate` or `updateOne` with `upsert: true`), creating the canonical profile document when none exists for that `customerId` and updating the existing one otherwise.
- The update merges the event's attributes with the `$set` operator on dotted paths inside the originating source system's sub-document (e.g. `crm.email`), writing only the fields present in the event.

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
