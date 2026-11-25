# Reference requirements: Earnings call RAG assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build a Python RAG pipeline with LlamaIndex that ingests earnings call transcripts from PDF files and extracts their text.
- Split each transcript into chunks with LlamaIndex, keeping on every chunk metadata that identifies its source transcript and the timestamp of the passage (e.g. the speaker-turn time printed in the transcript).
- Embed each chunk with the embedding model configured in LlamaIndex and store each chunk in Azure DocumentDB as a document holding the chunk text, its embedding array and its source and timestamp metadata (e.g. through pymongo or a LlamaIndex vector store integration).
- Create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field in code, with dimensions matching the embedding model's output.
- Provide a single-agent question-answering flow that takes an analyst's natural-language question, embeds it and runs a $search / cosmosSearch vector similarity query against Azure DocumentDB that returns the top-k most relevant chunks with their text and metadata.
- Apply context engineering before generation: select and trim the retrieved passages so that their combined size fits within the LLM's context window (e.g. by token counting), then assemble the prompt from those passages.
- Generate the answer with the LLM through LlamaIndex from the assembled context of retrieved passages.
- Include in each answer a citation of the source transcript and timestamp of the passages the answer draws on.

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
