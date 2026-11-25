# Reference requirements: Telehealth session summarizer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python and expose a callable entry point that accepts a telehealth session transcript (string) and a patientId, and returns the generated structured summary.
- Build the pipeline using LlamaIndex components so LlamaIndex is used to assemble/drive the summarisation workflow.
- Use context engineering to construct the summarisation prompt template that explicitly requests separate sections for "chief complaint", "assessment", "plan", and "follow-up".
- Invoke OpenAI as the LLM (via LlamaIndex or direct call) to generate the clinical summary from the context-engineered prompt.
- Parse and validate the OpenAI output into a structured Python object (dict) containing distinct fields for chief complaint, assessment, plan, and follow-up, and include metadata fields patientId and a timestamp.
- Persist the parsed summary as a structured document in Azure DocumentDB (MongoDB-compatible) so the document stores separate fields (not a single free-text blob) for chief complaint, assessment, plan, follow-up, patientId, and timestamp.
- Connect to Azure DocumentDB from Python using the MongoDB-compatible API and insert the summary into a clinical_summaries (or similarly named) collection; confirm the insertion returns a document id.
- Ensure the pipeline links the summary to the patient record by verifying the provided patientId exists in a patients collection (or otherwise validating referential integrity) and failing or logging if it does not.
- Provide an end-to-end runnable example or test script that submits a sample telehealth transcript and patientId, shows the OpenAI-generated structured summary, and demonstrates that the document was written to Azure DocumentDB (e.g., by retrieving the inserted document by patientId).

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
