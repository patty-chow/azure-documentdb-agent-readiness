# Reference requirements: Personalized email campaign builder

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a single LlamaIndex agent in Node.js that registers a tool which fetches customer segment profiles from Azure DocumentDB through a MongoDB-compatible driver (e.g. the `mongodb` Node.js driver).
- The fetch tool reads the requested segment's profile, including its purchase history and preferences, from Azure DocumentDB and returns it to the agent.
- The agent calls the fetch tool to obtain the segment profile before generating any copy.
- The agent injects the fetched purchase history and preferences into the prompt sent to the LLM (context engineering) so the generation is grounded in that segment's data.
- From that prompt the agent generates personalised email subject lines and body copy for the segment.
- The generated drafts are written back to a `campaigns` collection in Azure DocumentDB.
- Each stored draft contains the generated subject line and body copy and identifies the segment it was generated for (e.g. the segment's id).

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
