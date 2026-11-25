# Reference requirements: Medication interaction checker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Single-agent LangChain implementation in Node.js that orchestrates retrieving interaction documents from Azure DocumentDB and calling an LLM to reason about them.
- Use Mongoose as the ODM to query the DocumentDB collection of drug interactions for every unique pair of medications supplied (enumerate all unique pairs and query Mongoose for documents matching the pair in either order — e.g. fields like drugA/drugB or a normalized pair field).
- Provide Mongoose-based functions to add and update interaction documents in the DocumentDB knowledge base so the app can maintain the interaction KB (create/update operations implemented via Mongoose).
- For each pairwise interaction found, pass the interaction document details into a prompt template (prompt engineering) via LangChain that explicitly instructs the LLM to assess clinical severity and to produce a concise clinical recommendation for management.
- In the prompt/template, require the LLM to return a sortable severity assessment (for example a numeric score or an ordered label such as high/medium/low) and use that value in the application to rank interactions.
- Deduplicate results so that each medication pair appears only once in the final output even if multiple matching documents were returned by the database.
- Return a ranked list (most severe first) of interactions as structured output (e.g., a JSON array) where each item includes the medication pair, the LLM-assessed severity, and the LLM-provided clinical recommendation.

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
