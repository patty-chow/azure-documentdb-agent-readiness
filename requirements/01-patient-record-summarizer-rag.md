# Reference requirements: Patient record summarizer (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Single-agent LlamaIndex RAG agent in Python that performs retrieval-augmented generation for clinical questions.
- Chunk lengthy patient records into configurable-size text chunks (with configurable overlap) and index each chunk as a separate vector document in Azure DocumentDB.
- Store vector embeddings for each chunk in an Azure DocumentDB vector index (i.e., create/configure and write to a DocumentDB vector index so vectors are queryable).
- Model and persist metadata on each indexed chunk that links it to the original record: include a patientId field, original document id, chunk id (or section id), and character/line offsets or section boundaries.
- During retrieval, query Azure DocumentDB by vector similarity to return the most relevant chunks (top-k) and apply a filter by patientId so only chunks belonging to the requested patient are considered (enforces access control).
- Construct a context-engineered prompt template that the agent uses for clinical summaries: it must combine retrieved sections, available clinical metadata (when present), the clinician’s question, and explicit instructions to produce a concise clinical summary suitable for clinicians.
- Ensure the LlamaIndex generation call receives the structured prompt and retrieved chunks, and that the agent returns a grounded answer that cites source chunks.
- Include explicit, machine-checkable citations in the agent response mapping statements to source chunks (e.g., document id + chunk id or offsets) so each claim can be traced back to the original Azure DocumentDB document.
- Provide a callable function or endpoint (e.g., answer_clinical_question(patient_id, question, top_k)) that wires: patientId-based access control, vector retrieval from Azure DocumentDB, prompt construction (context engineering), LlamaIndex generation, and returning the grounded summary plus references.
- Implement HIPAA-aware handling in code: avoid emitting full patient PHI to console or persistent logs during indexing/querying (e.g., redact or omit identifiable fields in debug logs) and show this behavior in the codebase.
- Include a runnable example or automated test that indexes a sample patient record, then issues a clinical question for that patient and verifies the returned summary uses only that patient’s chunks and includes document citations.

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
