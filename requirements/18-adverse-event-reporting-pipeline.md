# Reference requirements: Adverse event reporting pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python pipeline that accepts a free-text adverse event report and runs it through extraction, schema validation and storage in sequence.
- An LLM call driven by an engineered prompt (e.g. instructions, definitions of the wanted fields and a required output format in the prompt text) that extracts the structured fields drug, event, severity and onset date from the free text.
- A Pydantic schema for the extracted report with the fields drug, event, severity and onset date, and validation of the LLM output against that schema before the report is stored.
- A Beanie ODM Document model representing the structured adverse event report with those four fields.
- The validated report written to Azure DocumentDB through that Beanie Document model.
- An aggregation pipeline, run through Beanie ODM against the stored reports, that groups them by drug and event, counts the reports in each group and orders the result so the most frequently reported events for each drug come first.

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
