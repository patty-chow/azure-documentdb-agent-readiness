# Reference requirements: Clinical notes de-identification

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python.
- Define Beanie ODM Document models for raw clinical notes and for de-identified notes; the de-identified model must include a sourceId field that stores the original note's id.
- Connect to Azure DocumentDB using Beanie (init_beanie with a motor client) pointed at the Mongo-compatible Azure DocumentDB endpoint and database.
- Read raw clinical note documents from the designated collection in Azure DocumentDB using Beanie queries and iterate over every note to be processed.
- For each note, call OpenAI (via its API client) with a programmatically constructed prompt that explicitly instructs the model to identify and replace PHI categories: names, dates, locations, and IDs.
- The OpenAI prompt must require replacements use clear placeholders (examples like [NAME_1], [DATE_1], [LOCATION_1], [ID_1]) and the code must send the raw note text as input to that prompt.
- Extract the de-identified text from the OpenAI response (e.g., from the assistant/content field) and validate that the returned text contains placeholders for the PHI categories rather than raw PHI from the original.
- Insert the de-identified text as a separate document into Azure DocumentDB using Beanie, setting sourceId to the original note's id and preserving the original raw note unmodified in the raw collection.
- Implement the pipeline as a Single-agent process that performs read → OpenAI call → write for each note in sequence.

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
