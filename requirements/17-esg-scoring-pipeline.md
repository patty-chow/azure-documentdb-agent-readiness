# Reference requirements: ESG scoring pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Python and LangChain to implement a Single-agent that orchestrates the ESG scoring workflow (imports from langchain, agent loop or chain implemented in Python).
- Connect to Azure DocumentDB and read company ESG documents from a collection; connection/auth code targets Azure DocumentDB and queries documents that contain company identifier and structured ESG fields.
- Include a prompt engineering template used by the agent that instructs the LLM to score each pillar (E, S, G) on a 1–10 scale and to produce a concise numeric score plus a textual rationale for each pillar.
- Use LangChain to call the LLM with the engineered prompt and parse the model output into explicit fields: E_score, S_score, G_score and corresponding rationale texts.
- Generate embeddings for the LLM-generated rationale using LangChain embeddings and attach the resulting vector(s) to the company document for semantic search.
- Write the scored document back to Azure DocumentDB (insert or update) so the stored document contains company id, E_score, S_score, G_score, pillar rationales, and the associated embedding(s).
- Process multiple companies in batch: the agent reads multiple ESG documents, scores each one, embeds rationales, and writes all scored documents back to Azure DocumentDB.
- Implement an aggregation pipeline using Azure DocumentDB’s aggregation capabilities (MongoDB-compatible aggregation) that computes a composite ESG score per company and sorts companies by that composite score.
- Define the composite ESG score calculation explicitly in code (e.g., unweighted average of E_score, S_score, G_score) and use that formula in the aggregation pipeline so results are reproducible.
- Expose a runnable function or script that executes the aggregation pipeline and returns or prints the ranked list of companies with composite scores and references to their scored documents.
- Ensure the stored rationale text and the embedding(s) are consistent: the rationale text used to create embeddings must be the same text saved on the scored document in Azure DocumentDB.

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
