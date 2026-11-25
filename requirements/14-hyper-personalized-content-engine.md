# Reference requirements: Hyper-personalized content engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Node.js and use LlamaIndex as the agent framework with a configured agent memory component.
- Accept a customer identifier input and use it to fetch that customer's profile, segment, and recent interaction documents from Azure DocumentDB.
- Wire agent memory to load (and on subsequent calls, retrieve from) the fetched profile, segment, and recent interaction documents so the LlamaIndex agent can consult them as memory.
- Construct a vector query derived from the customer's profile and recent interactions (e.g., concatenated context or weighted prompt) and execute Azure DocumentDB vector search to retrieve semantically relevant content pieces.
- Use LlamaIndex to orchestrate retrieval: pass the Azure DocumentDB vector search results into the LlamaIndex retrieval pipeline so retrieved content pieces are available to the agent.
- Apply explicit context engineering in the prompt assembly: include the customer profile, segment, recent interactions, and the retrieved content pieces as distinct sections when calling the language model via LlamaIndex.
- Produce a personalised content selection rationale that explicitly cites facts from the customer's profile, segment, or recent interactions used to justify recommendations.
- Return a ranked list of recommended content items (ordered by relevance), where each item includes at least: content id, title (or short text), and a numeric relevance score; the code must build this structured output.
- Ensure the generated rationale links each ranked item to the specific retrieved content piece(s) and DocumentDB source documents used in ranking (e.g., by referencing document ids or snippets).

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
