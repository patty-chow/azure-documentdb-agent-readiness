# Reference requirements: Supplier & PO management

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python with FastAPI, using Beanie ODM as the data layer over Azure DocumentDB.
- Model suppliers as a Beanie Document class whose Pydantic schema declares the supplier's fields and marks the required ones.
- Model purchase orders as a Beanie Document class whose Pydantic schema declares the PO's fields, including those the aggregation needs (e.g. a reference to the supplier, a status and a monetary value), and marks the required ones.
- Expose FastAPI endpoints that create, read (e.g. get one and list), update and delete supplier documents through the Beanie model.
- Expose FastAPI endpoints that create, read (e.g. get one and list), update and delete purchase-order documents through the Beanie model.
- Create and update requests are validated against the Pydantic schemas in the application layer, and a request that omits a required field is rejected by the service.
- Expose an aggregation endpoint that runs an aggregation pipeline in Azure DocumentDB through Beanie (e.g. match open purchase orders, then group by supplier summing their value) and returns the total open PO value per supplier.

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
