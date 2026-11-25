# Reference requirements: Medication interaction checker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the backend in Node.js and use the LangChain agent framework to orchestrate the workflow.
- Use Mongoose as the ODM and include a Mongoose connection that targets Azure DocumentDB (DocumentDB) via a MongoDB-compatible connection URI.
- Define a Mongoose schema/model for interaction documents that includes at minimum: canonical drug identifiers (drugA, drugB or a canonical pair key), evidence text, an existing severity field (if present), clinicalRecommendation, and source/reference fields.
- Provide code that accepts a list of medications, computes all unique pairwise combinations, and performs lookups against Azure DocumentDB to retrieve any matching interaction documents for those pairs (match pairs regardless of order).
- If no interaction document exists for a given pair, the code must include that pair in the result set with an explicit "no documented interaction" outcome (rather than omitting it).
- Build a LangChain prompt template (prompt engineering) that injects each retrieved interaction document's structured fields (evidence, existing severity if any, references) and instructs the LLM to assess or re-assess severity and produce a concise clinical recommendation for that pair.
- Send the engineered prompt to an LLM via LangChain and parse the model's structured response into at least: assessed severity (numeric score or categorical label), a short clinical recommendation, and a brief explanation citing evidence when applicable.
- Aggregate the results and return a ranked list sorted by assessed severity (most severe first) with each entry containing the drug pair, assessed severity, clinical recommendation, evidence excerpt, and source reference(s).
- Expose a runnable interface (HTTP endpoint or CLI function) that accepts a medication list JSON input and returns the ranked JSON result so a reviewer can invoke the agent and validate end-to-end behavior.

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
