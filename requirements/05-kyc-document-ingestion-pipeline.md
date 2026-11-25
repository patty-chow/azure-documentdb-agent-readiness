# Reference requirements: KYC document ingestion pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline accepts uploaded KYC documents as its input (e.g. a file upload or document bytes handed to an ingestion entry point).
- The pipeline is written in async Python, with the OpenAI calls and the Beanie ODM database operations awaited.
- Each uploaded document is sent to OpenAI with a request for structured entity extraction covering name, DOB, address and ID numbers.
- A Pydantic schema declares the extracted entities (name, DOB, address, ID numbers), and the OpenAI output is validated against that schema before it is stored.
- The customer record is modelled as a Beanie ODM Document, and a validated record is upserted into Azure DocumentDB through Beanie (updated when a matching customer already exists, inserted otherwise; matched on e.g. an ID number).
- A record whose extraction fails schema validation or lacks required entities is stored as incomplete and flagged for manual review (e.g. a review flag on the stored document).

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
