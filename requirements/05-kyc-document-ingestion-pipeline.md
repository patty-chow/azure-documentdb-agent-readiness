# Reference requirements: KYC document ingestion pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python using async/await (async def handlers and await for I/O) to ensure the ingestion, LLM call, validation, and DB operations are non-blocking.
- Use the Beanie ODM for all Document model definitions and database operations (models inherit from beanie.Document and beanie.init_beanie is used for startup).
- Connect asynchronously to Azure DocumentDB (the MongoDB-compatible service) using Beanie’s async initialization and a MongoDB connection string that targets the Azure DocumentDB cluster.
- Provide an async upload handler or function that accepts KYC document uploads (e.g., file-like object or bytes) and passes the document onward in the pipeline.
- Call OpenAI asynchronously to perform structured entity extraction and request the exact fields name, date of birth, address, and ID numbers in the response; the code must parse the OpenAI response into a structured form.
- Define a Pydantic schema (BaseModel) that models the extracted entities with typed fields for name (string), date of birth (date or ISO date string), address (object or string), and ID numbers (string or list of strings), and use Pydantic validation to validate the LLM output.
- Map and validate the OpenAI-extracted fields against the Pydantic schema; if validation succeeds, transform the validated model into a Beanie document for persistence.
- Perform an upsert (insert or update) of the validated customer record into Azure DocumentDB using Beanie, using a stable unique key (e.g., government ID number or explicitly provided customer_id) as the filter for the upsert operation.
- For records that are incomplete or fail Pydantic validation (missing required fields or invalid types), mark or persist them as flagged for manual review (e.g., a field like needs_manual_review=True or a separate manual_review collection) instead of treating them as a successful upsert.
- Return or log a clear status for each processed document indicating whether it was upserted, updated, or flagged for manual review so a reviewer can verify the pipeline outcome.

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
