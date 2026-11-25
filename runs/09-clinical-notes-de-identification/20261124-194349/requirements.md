# Reference requirements: Clinical notes de-identification

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline is written in Python and reads the raw clinical notes from Azure DocumentDB through a Beanie ODM Document model that represents a raw note.
- Each note returned by the read is sent to OpenAI, one note at a time, and the text OpenAI returns is taken as that note's de-identified version.
- The request to OpenAI carries a prompt engineered for de-identification: it instructs the model to identify PHI entities in the note and replace each with a placeholder (e.g. `[NAME]`, `[DATE]`).
- The prompt names the PHI categories to detect, covering at least names, dates, locations and IDs.
- The de-identified text is written back to Azure DocumentDB as a new, separate document through a Beanie ODM Document model, leaving the raw note document as it was.
- Each de-identified document carries a `sourceId` field holding the id of the raw note it was produced from.

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
