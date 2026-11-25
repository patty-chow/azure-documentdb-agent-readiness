# Reference requirements: Adverse event reporting pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implementation is in Python and exposes a callable ingestion function or endpoint that accepts a free-text adverse event report string as input.
- Define a Beanie ODM document model (a class inheriting from beanie.Document) representing an adverse event with at least the fields drug, event, severity, and onset_date, using Pydantic types for each field.
- Include a Pydantic schema (the model used by Beanie or a separate Pydantic model) that enforces types and constraints (e.g., onset_date parsed to a date/datetime type; severity restricted to a clear set or enum) and raise/return validation errors when data does not conform.
- Use prompt engineering: include a prompt template in the code and call an LLM to extract the structured fields drug, event, severity, and onset date from the free-text input; the code must parse the LLM response (preferably JSON) and map it to the schema fields.
- Only write documents to Azure DocumentDB after the extracted data has been validated by the Pydantic schema; if validation fails the code must not insert the document and must surface the validation errors.
- Connect Beanie ODM to Azure DocumentDB (MongoDB-compatible endpoint) and persist validated adverse event documents to an Azure DocumentDB collection via Beanie insert/save operations.
- Store the onset_date as a date/datetime value in the saved Azure DocumentDB document (not as an unparsed string).
- Provide a server-side aggregation implementation (using an aggregation pipeline against Azure DocumentDB via Beanie or the underlying driver) that groups by drug and event, counts occurrences, sorts by count descending, and returns the most frequently reported events by drug.
- Include example usage or a short integration test that demonstrates: ingesting a sample free-text report, running the LLM extraction + Pydantic validation, writing the validated document to Azure DocumentDB, and executing the aggregation to show the expected top events per drug.

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
