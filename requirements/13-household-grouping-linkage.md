# Reference requirements: Household grouping & linkage

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Node.js using the Mongoose ODM and connect to Azure DocumentDB’s MongoDB-compatible endpoint (connection string configurable).
- Define a Mongoose Customer schema containing at minimum: address, phone, surname, lifetime_value (numeric), and products (array), and ensure Customer documents are stored in Azure DocumentDB.
- Define a Mongoose Household schema that stores household group documents with a members array of DocumentDB document references (Mongoose ObjectId refs) to Customer documents.
- Provide an endpoint (e.g., POST /households/resolve) that builds an identity graph from Customer documents: create nodes for customers and add edges when customers share a matching address OR phone OR surname to identify connected components as households.
- Normalize matching fields before comparing (e.g., trim/case-normalize address and surname, canonicalize phone digits) so matches are deterministic and verifiable in code.
- For each connected component discovered, create and persist a Household document in Azure DocumentDB that contains DocumentDB document references to all member Customer ObjectIds; the created Household documents must be queryable in the DB.
- Expose an aggregation endpoint that computes household-level CLV (e.g., GET /households/:id/clv) by aggregating/summing the lifetime_value of all Customer members referenced by the Household document using the MongoDB aggregation pipeline via Mongoose.
- Expose an aggregation endpoint that computes household-level product holdings (e.g., GET /households/:id/products) by aggregating products across all referenced members—returning the union of products and optional counts—using Mongoose/MongoDB aggregation.
- Implement the aggregation queries so they operate by following the Household.members references (not by re-scanning customers independently), demonstrating use of DocumentDB document references and aggregation pipelines to compute household metrics.

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
