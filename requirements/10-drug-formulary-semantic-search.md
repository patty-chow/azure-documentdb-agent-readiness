# Reference requirements: Drug formulary semantic search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python and use LlamaIndex as the indexing/retrieval framework (i.e., a "Python LlamaIndex service") so the codebase and dependencies clearly reflect Python + LlamaIndex usage.
- Persist each drug formulary entry as an Azure DocumentDB document with explicit fields: name, indications, contraindications, dosing, and an "embedded vectors" field stored in the DocumentDB document.
- Provide a reusable ingestion function or script that creates Azure DocumentDB documents from input formulary data and computes and stores the document embeddings (the "embedded vectors") at insert time.
- Expose an HTTP endpoint exactly named /formulary-search that accepts a clinical intent description (e.g., POST JSON with a "query" text field) and returns JSON results.
- At query time, embed the incoming clinical intent text using the same embedding pipeline used for documents (via LlamaIndex) and use that embedding to perform the vector search against Azure DocumentDB.
- Use Azure DocumentDB's vector search capability to retrieve candidate documents and rank them by vector similarity; explicitly use cosine similarity for ranking the top matches.
- Return the top 10 matches sorted by descending cosine similarity; each returned item must include the document's name, indications, contraindications, dosing, and the similarity score.
- Ensure the /formulary-search handler performs the vector similarity ranking server-side (i.e., via Azure DocumentDB vector search or via LlamaIndex retrieval over the DocumentDB-backed index), not by returning all documents and filtering client-side.
- Include error handling and clear HTTP responses for missing/invalid query text (e.g., 400 for empty query) and for successful searches (200 with JSON array), so a reviewer can exercise the endpoint and validate results.

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
