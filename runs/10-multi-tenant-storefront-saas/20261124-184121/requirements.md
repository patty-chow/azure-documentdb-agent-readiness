# Reference requirements: Multi-tenant storefront SaaS

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js application uses Mongoose as its ODM against Azure DocumentDB and stores merchant products, orders and inventory in collections shared by all merchants, one collection per resource (e.g. products, orders, inventory) holding every tenant's documents.
- The Mongoose schemas for products, orders and inventory each define a tenantId field, and every document written through the application carries a tenantId value.
- A compound index on (tenantId, sku), with tenantId as the leading key, is defined in application code (e.g. schema.index({ tenantId: 1, sku: 1 })) on the shared collection(s) that carry a sku field.
- A compound index on (tenantId, createdAt), with tenantId as the leading key, is defined in application code (e.g. schema.index({ tenantId: 1, createdAt: 1 })) on the shared collection(s) that carry a createdAt field.
- A repository layer sits between the rest of the application and the Mongoose models, and all reads and writes of products, orders and inventory go through it.
- Every repository read method includes tenantId as an equality condition in the query filter it passes to Mongoose.
- Every repository update and delete method includes tenantId in its filter alongside the document selector (e.g. { _id, tenantId }), so a write only touches documents of that tenant.
- Repository methods take the tenant identity from a tenant context supplied to the repository (e.g. a constructor argument or per-call parameter) and add the tenantId condition to the filter themselves.

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
