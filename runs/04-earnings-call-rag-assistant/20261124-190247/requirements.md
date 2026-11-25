# Reference requirements: Earnings call RAG assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python and use LlamaIndex as the indexing/retrieval framework for ingestion, embedding, indexing, and retrieval.
- Build the system as a Single-agent application where a single agent/process performs ingestion, vector storage, retrieval, and answer generation.
- Ingest earnings call PDF transcripts: accept PDF files, extract full transcript text, and record a persistent source identifier (e.g., filename or transcript ID) for each transcript.
- During ingestion, chunk the extracted transcript text into segments with configurable chunk size and overlap; chunking must be parameterized relative to the target LLM context window to enable context engineering.
- Embed every chunk and persist the embedding vectors and chunk text into Azure DocumentDB, storing for each vector a document containing at minimum: the embedding array, chunk text, source transcript identifier, and chunk timestamp range (start and end timestamps or page/offset).
- Store vector documents in Azure DocumentDB using its MongoDB-compatible API so that the vector collection is queryable for similarity search (vector and metadata persisted together).
- Implement a similarity-search retrieval function that queries the Azure DocumentDB vector collection and returns the top-k most relevant chunks for a natural-language analyst query, ranked by similarity score.
- Apply context engineering on retrieval: compose the retrieved chunks so their combined token/character length fits inside the configured LLM context window (drop or truncate lower-ranked chunks until within limit) before passing context to the LLM.
- Generate answers by combining the retrieved context and the analyst question through LlamaIndex (RAG), and ensure each factual claim or quoted passage in the answer includes an explicit citation showing the source transcript identifier and the chunk timestamp range.
- Provide a runnable demo entrypoint (CLI or minimal HTTP endpoint) that accepts an analyst natural-language question, runs retrieval against Azure DocumentDB, and returns a grounded answer with cited transcript filenames and timestamps.
- Include an automated or example script that demonstrates the full end-to-end flow: ingest at least one earnings call PDF, build/store vectors in Azure DocumentDB, run a sample query, and output an answer with source+timestamp citations.

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
