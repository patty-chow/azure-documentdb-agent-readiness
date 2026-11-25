# Reference requirements: Symptom triage chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the chatbot in Python and use LangChain for the RAG architecture (repository contains Python code that imports and uses LangChain constructs).
- Store the clinical triage guideline texts and their metadata in Azure DocumentDB and index them using a DocumentDB vector index (documents persisted to Azure DocumentDB include the original text, metadata, and vector field used by the vector index).
- Build the embedding-and-indexing pipeline that generates embeddings for each guideline section and writes those embeddings into the DocumentDB vector index alongside section IDs and metadata (code shows embeddings created and saved with each DocumentDB document).
- Implement a LangChain retriever that queries the DocumentDB vector index to return the most relevant guideline sections for a given symptom description (retriever component configured to run nearest-neighbor searches against the DocumentDB vector index).
- Compose a retrieval-augmented generation chain in LangChain that supplies retrieved guideline sections as context to the LLM to produce triage advice (code uses LangChain RetrievalQA or a custom chain that passes retrieved docs to the LLM).
- Use prompt engineering in the chain’s prompt templates to enforce safety guardrails by explicitly instructing the model to always recommend professional consultation and to never diagnose (prompt templates contain explicit clauses: “always recommend professional consultation” and “never diagnose”).
- Ensure the chatbot returns structured triage advice on each request, including at minimum an urgency level field, recommended next steps, and references to source guideline sections (responses are emitted as JSON or a structured dict with fields such as urgency_level, recommended_actions, and sources).
- Include provenance in responses by listing DocumentDB document identifiers, snippets, or links to the specific guideline sections retrieved (responses include guideline IDs or DocumentDB references and optionally retrieval scores).
- Expose a single-agent runtime that accepts a patient symptom description, performs retrieval from the DocumentDB vector index, and returns the structured triage advice in one end-to-end flow (there is one agent/process that handles retrieval + generation for a request).
- Verify outputs conform to the safety guardrails at runtime: responses must contain a professional-consultation recommendation and must not state definitive diagnoses; if a generated response fails this check the system returns a guarded fallback recommending professional consultation (tests or runtime assertions demonstrate that diagnostic statements are removed/sanitized and the consultation recommendation appears).

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
