# Reference requirements: Natural language product search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution in Python and build the search agent using LangChain.
- Provide a single LangChain agent (no multi-agent orchestration) that exposes a hybrid search tool callable by the agent.
- Implement a prompt-engineering rewrite step (a LangChain chain or function) that takes the raw user query and returns a well-formed "search intent" string; the agent must invoke this rewrite step programmatically before any database queries.
- The hybrid search tool must query Azure DocumentDB using a full-text $text query constructed from the rewritten search intent (the code must send a query document containing "$text").
- The hybrid search tool must perform a vector search using an embedding of the rewritten search intent and the app's vector index/field stored in Azure DocumentDB (compute an embedding for the rewritten intent and use it to retrieve nearest neighbors).
- Both the $text and vector queries must return per-document relevance scores (or a score that the code exposes) that the hybrid tool uses for ranking.
- The hybrid tool must merge the two ranked lists by normalizing/combining the $text and vector relevance scores, deduplicate documents present in both lists, and produce a single combined ranking.
- The merged result set must be sorted by the combined relevance score and the tool must return the top-N matches (N must be configurable in code).
- Returned matches must include product document fields sufficient for presentation (at minimum product ID, title/name, and a description/snippet) taken from Azure DocumentDB documents.
- The agent must handle the case where one side of the hybrid search (either $text or vector) returns zero results by still returning merged results from the other side rather than failing.
- All queries to the database must be sent to Azure DocumentDB (the MongoDB-compatible cluster) from the running Python code (i.e., the hybrid search tool must execute real queries against Azure DocumentDB, not only simulated or in-memory searches).

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
