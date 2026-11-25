# Reference requirements: Rare disease literature search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the ingestion pipeline in Python using LlamaIndex to fetch PubMed abstracts for rare diseases (the code must show PubMed as the source and perform queries or use an identifier list to select rare-disease abstracts).
- During ingestion, extract and store PubMed ID and the abstract publication year as explicit metadata fields associated with each document/chunk.
- Use LlamaIndex to chunk each abstract into smaller passages; each chunk must retain a pointer to its parent abstract (original PubMed ID) and a chunk identifier so reviewers can map chunks back to the original abstract.
- Use LlamaIndex’s embedding interface in Python to compute vector embeddings for every chunk and attach those embeddings to the chunk records prior to storage.
- Persist every chunk as a vector document in Azure DocumentDB (the MongoDB-compatible service) so that each stored record contains: the embedding vector, PubMed ID, abstract year, chunk id, and the chunk text.
- Implement retrieval that computes semantic similarity (e.g., cosine similarity) between a question embedding and stored chunk embeddings and returns results sorted by relevance score (highest relevance first); the code must expose or return the relevance score for each retrieved item.
- Expose a RAG agent implemented in Python that uses LlamaIndex retrieval over the Azure DocumentDB-stored vectors to synthesize answers grounded in retrieved chunks (the code must identify this component as a RAG agent).
- Make the RAG agent include grounded citations for every claim it uses from retrieved chunks; each citation in the agent response must include the PubMed ID and the abstract year and must be linkable to the stored chunk (e.g., by chunk id or returned snippet).
- Ensure the agent’s final answer ranks and presents supporting documents by semantic relevance and returns a structured list of citations (PubMed ID, abstract year, relevance score, and a short excerpt or snippet from the cited abstract) so a reviewer can verify grounding.
- Provide code paths or examples that demonstrate end-to-end behavior: ingest PubMed abstracts, build/store embeddings in Azure DocumentDB, run a researcher question through the RAG agent, and produce a ranked, citation-rich answer containing PubMed IDs and years.

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
