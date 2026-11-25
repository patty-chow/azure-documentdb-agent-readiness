# Reference requirements: Medication interaction checker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the checker as a Node.js agent built with LangChain, where one agent carries out the whole check: retrieving interaction documents from Azure DocumentDB and reasoning over them with an LLM.
- Use Mongoose as the ODM: define a Mongoose model for drug interaction documents and use it for the reads and writes against the knowledge base in Azure DocumentDB.
- Let the app maintain the knowledge base by adding and updating interaction documents through Mongoose (e.g. upsert operations on the interaction model).
- Accept a list of medications as input and enumerate every unique pair among them.
- For every pair, query Azure DocumentDB through Mongoose for the interaction documents covering that pair (e.g. matching the two drug names in either order).
- Build the LLM prompt with prompt engineering: pass the retrieved interaction document content to the LLM through LangChain with explicit instructions to assess the severity of each interaction.
- Rank the interactions by the LLM-assessed severity (e.g. most severe first).
- Return the ranked list of interactions, each with a clinical recommendation (e.g. alongside its medication pair and assessed severity).

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
