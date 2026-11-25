# Reference requirements: Multi-tenant storefront SaaS

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the backend in Node.js and use the Mongoose ODM for all schema and DB interactions.
- Connect Mongoose to Azure DocumentDB using a configurable connection string (e.g., environment variable) so the app runs against an Azure DocumentDB MongoDB-compatible endpoint.
- Define Mongoose models/schemas for Product, Order, and Inventory that are stored in shared Azure DocumentDB collections (one collection per entity that contains documents for all tenants).
- Require a tenantId field on every document (Product, Order, Inventory) at the schema level (tenantId must be present and non-null).
- Include sku on the Product and Inventory schemas and include createdAt timestamps on schemas so createdAt is present on documents.
- Declare Mongoose compound indexes index({ tenantId: 1, sku: 1 }) on the Product and Inventory schemas.
- Declare Mongoose compound indexes index({ tenantId: 1, createdAt: 1 }) on the Product, Inventory, and Order schemas.
- Implement a repository layer (repository classes or modules) that wraps all Mongoose access and requires a tenantId argument for every query/update/delete/aggregate operation; repository methods must inject tenantId into the Mongo filter and throw an error if tenantId is omitted.
- Prevent direct model usage from business logic by exposing only the repository API; include at least one automated test or runtime check that attempts a query without tenantId and asserts the repository rejects it.
- Provide repository methods that demonstrate tenant-scoped query patterns (e.g., find product by sku + tenantId, list orders for a tenant sorted by createdAt) and ensure those methods use the tenantId + sku and tenantId + createdAt compound index patterns so queries can use the tenant-scoped indexes.
- Ensure index creation is performed/verified at runtime (e.g., Mongoose schema.index calls are applied and the running app can verify the required indexes exist on the Azure DocumentDB collections via the driver).

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
