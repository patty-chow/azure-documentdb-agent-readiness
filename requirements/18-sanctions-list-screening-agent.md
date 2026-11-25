# Reference requirements: Sanctions list screening agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Single-agent in Python using a LangChain agent: the repository must contain a Python LangChain agent implementation that handles screening requests end-to-end.
- Ingestion code must embed sanctions list entries and upsert them into an Azure DocumentDB vector index: the sample must create or write vectors and associated metadata into the DocumentDB vector index.
- On a screening request, the agent must compute an embedding for the incoming customer or transaction record and perform a vector similarity search against the Azure DocumentDB vector index, returning top-N candidates with their similarity scores.
- The agent must also perform $regex-based fuzzy matching queries against Azure DocumentDB (using the MongoDB-compatible $regex operator) on relevant text fields (e.g., names, addresses, identifiers) and return matching candidates with regex match details.
- The code must consolidate results from the vector similarity search and the $regex-based fuzzy matching: merge candidate lists, deduplicate by DocumentDB document id, and record which method(s) produced each candidate.
- The agent must compute a numeric match confidence for each consolidated candidate by combining vector similarity scores and regex match signals using an explicitly implemented scoring algorithm in the code.
- For each candidate the agent must produce a recommended action derived from the computed confidence (e.g., thresholds that map to "clear", "review", "block") and include the rationale used to decide that action.
- The screening endpoint/agent response must return a structured screening report (machine-readable, e.g., JSON/dict) that, for each candidate, includes DocumentDB id, matched fields, matching method(s), raw similarity and regex details, consolidated match confidence, recommended action, and source sanctions entry text.
- The agent must accept customer and transaction records as inputs and demonstrate how input fields are mapped to both the embedding input and the $regex queries used in the DocumentDB searches.
- Provide an example or test that exercises the complete pipeline (ingest sanctions list into Azure DocumentDB vector index, submit a screening request, run both vector search and $regex-based fuzzy matching, consolidate and score results, and emit the structured screening report).

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
