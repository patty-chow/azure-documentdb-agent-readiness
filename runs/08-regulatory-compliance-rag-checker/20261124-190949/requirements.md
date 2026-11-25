# Reference requirements: Regulatory compliance RAG checker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python.
- Use LlamaIndex to build the RAG agent (the code must instantiate and use a LlamaIndex-based index/retriever).
- Connect to Azure DocumentDB using the pymongo driver (connection URI or connection string must be configurable and used by the code).
- Create and/or use two separate Azure DocumentDB collections: one for regulatory documents and one for internal policy documents; provide ingestion code that writes each document’s full text and metadata (document id, title/source, clause id) into the appropriate collection.
- Build a vector index with LlamaIndex over the regulatory documents and perform vector search (similarity search) to retrieve the most relevant regulatory clauses for a given policy excerpt; top-K must be configurable.
- Ensure retrieval queries only the regulatory documents collection (not the internal policy collection) and return for each retrieved clause the stored document id/metadata and its similarity score.
- Implement the agent as a Single-agent workflow that accepts a policy excerpt input, runs retrieval against the regulatory collection, compares results, and returns a report in one end-to-end run.
- Use context engineering by implementing a structured prompt template that injects the policy excerpt, the retrieved regulatory clauses (with metadata), and explicit comparison instructions into the model prompt before producing the compliance analysis.
- The compliance gap report produced by the agent must include: a concise compliance verdict (compliant/partial/non‑compliant), a list of gaps mapped to specific regulatory clauses, suggested remediation steps for each gap, and explicit citations referencing the Azure DocumentDB collection document ids or stored source metadata.
- Provide ingestion/update functions that add or update documents in the Azure DocumentDB collections and that refresh or update the LlamaIndex vector index so newly ingested documents become searchable by the agent.

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
