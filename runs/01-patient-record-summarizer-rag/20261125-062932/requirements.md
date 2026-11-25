# Reference requirements: Patient record summarizer (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python RAG agent built with LlamaIndex answers a clinical question about a patient: one agent retrieves relevant record sections from Azure DocumentDB and produces the summary from them.
- Patient records are split into chunks and each chunk is stored as a document in Azure DocumentDB with its embedding on the document, written through LlamaIndex's vector store integration or a MongoDB-compatible Python driver (e.g. pymongo).
- Every stored patient-record document carries a `patientId` field.
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field, with `dimensions` matching the embedding model the app uses.
- Retrieval embeds the clinical question and runs the similarity search in Azure DocumentDB with `$search` / `cosmosSearch` (similarity COS, L2 or IP), returning the most relevant chunks.
- Retrieval is limited to the requested patient's records by `patientId`, so sections of other patients are never retrieved (e.g. a `filter` on `patientId` inside `cosmosSearch`).
- The summarization prompt is assembled deliberately (context engineering): instructions for a clinical summary, the retrieved sections as context and the clinical question are placed in a structured layout.
- The answer is grounded in the retrieved sections and returned together with references to the source documents it drew on.

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
