# Reference requirements: Telehealth session summarizer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Provide a Python LlamaIndex pipeline whose entry point accepts a telehealth session transcript together with the patientId of the patient it belongs to.
- Apply context engineering when building the summarisation prompt: the prompt is assembled so that it structures the requested summary around the four sections chief complaint, assessment, plan and follow-up.
- Generate the clinical summary by sending the engineered prompt to OpenAI as the LLM inside the LlamaIndex pipeline.
- Turn the OpenAI response into a structured clinical summary with one field per section (e.g. chief complaint, assessment, plan and follow-up as separate keys).
- Store the structured summary as a document in Azure DocumentDB with PyMongo (e.g. an insert into a clinical summaries collection), the document carrying the patientId field that links it to the patient record.

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
