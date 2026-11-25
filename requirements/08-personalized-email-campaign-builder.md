# Reference requirements: Personalized email campaign builder

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a single Node.js LlamaIndex agent (instantiate one LlamaIndex agent) that orchestrates fetch → generate → write for a requested customer segment.
- Register a tool on the LlamaIndex agent that fetches customer segment profiles from Azure DocumentDB (the tool should be callable by the agent).
- The fetch tool must connect to Azure DocumentDB and query a collection containing customer segment profiles (queryable by segment id or segment name) and return the profile document(s) to the agent.
- The fetched profile object must include and expose purchase history and preferences fields; the code must extract those fields from the profile document returned by Azure DocumentDB.
- Use explicit context engineering: construct the LLM prompt sent from the agent so it injects the segment's purchase history and preferences into the prompt context (the prompt text in code must contain those injected fields).
- Invoke LlamaIndex to generate personalised email subject lines and body copy using the injected context; the agent must request both a subject line and full body copy in the LLM call.
- Parse the LLM response into discrete fields (at minimum subject and body) in the Node.js code before persisting.
- Write the generated drafts back to Azure DocumentDB by inserting a document into a campaigns collection named "campaigns" (each saved document must include the segment id/name, subject, body, raw LLM output, and a creation timestamp).
- Provide a sample invocation (e.g., a script or handler) that runs the agent for a specific segment id and demonstrates that a new document with subject and body appears in the campaigns collection.

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
