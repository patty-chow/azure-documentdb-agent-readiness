# Reference requirements: Supplier & PO management

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service using Python and FastAPI (FastAPI app, route definitions and ASGI entrypoint must be present).
- Use Beanie ODM to model and persist documents and initialize Beanie against an Azure DocumentDB MongoDB endpoint (code must call Beanie initialization with a motor client pointed at Azure DocumentDB).
- Define a Supplier Document class using Beanie (Pydantic-based schema) that declares required fields at the Pydantic schema level (e.g., a required name and contact field) so creation fails validation if missing.
- Define a PurchaseOrder Document class using Beanie (Pydantic-based schema) that declares required fields including a supplier reference (supplier_id), a numeric value field (e.g., total_value) and a status field; these fields must be required by schema validation.
- Implement full CRUD endpoints for Supplier: create (POST), read single (GET /suppliers/{id}), list (GET /suppliers), update (PUT or PATCH), and delete (DELETE), returning appropriate HTTP status codes and the document JSON.
- Implement full CRUD endpoints for PurchaseOrder: create (POST), read single (GET /purchase-orders/{id}), list (GET /purchase-orders), update (PUT or PATCH), and delete (DELETE), returning appropriate HTTP status codes and the document JSON.
- Enforce required-field validation at the application layer: incoming request bodies are validated by Pydantic/Beanie schemas and missing or invalid required fields cause 4xx responses and no write to Azure DocumentDB; creating a PurchaseOrder must verify the referenced Supplier exists and return a 4xx error if not.
- Add an aggregation endpoint that summarizes open PO value by supplier (e.g., GET /aggregations/open-po-value-by-supplier) which executes a Mongo aggregation pipeline against Azure DocumentDB (via Beanie or motor) to filter POs with status == "open" and return per-supplier sums of the numeric value field, including supplier id (and optionally supplier name).
- Ensure API responses serialize Document IDs and Pydantic types to JSON (ObjectId/UUID converted to strings) so returned JSON is directly consumable by clients.

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
