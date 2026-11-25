# Reference requirements: Lead scoring agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Node.js and use the LangChain agent framework for the reasoning agent.
- Configure and attach agent memory (use the phrase "agent memory" in the code/config) so the agent persists recent interaction context and reuses it during scoring calls.
- Implement three LangChain tools that each accept a lead identifier and query Azure DocumentDB: (1) fetch the lead's activity history, (2) fetch the company firmographic document, and (3) fetch engagement signals; each tool must perform a DocumentDB lookup filtered by the lead id.
- The code must explicitly establish a connection to Azure DocumentDB and use that connection inside the three tools to read documents (i.e., show Azure DocumentDB connection/config and queries in the repository).
- The LangChain agent must invoke the tools via the framework's tools mechanism (i.e., register and call tools through LangChain rather than ad-hoc database calls from the prompt).
- Build and use an explicit prompt template (prompt engineering) that stitches together the fetched activity history, firmographics, and engagement signals and instructs the agent to reason over them to produce a score and rationale.
- The agent must generate a numeric score in the inclusive range 0–100; the code must validate the output is numeric and within that range before persisting.
- The agent must generate a one-paragraph rationale for the score; the code must validate the rationale is a single paragraph (no blank-line separators/newline-only paragraphs) prior to persisting.
- After validation, update the lead document in Azure DocumentDB by writing both the numeric score and the one-paragraph rationale back into the lead's document record.
- If any required DocumentDB document (activity history, firmographics, or engagement signals) is missing or incomplete, the agent must return/ log a clear error/handled response and must not write an invalid score back to the lead document.

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
