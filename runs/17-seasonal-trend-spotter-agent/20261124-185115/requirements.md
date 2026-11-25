# Reference requirements: Seasonal trend spotter agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python and include a requirements file listing packages used (must include pymongo and langchain).
- Build a single LangChain agent (one agent instance) that is constructed using LangChain’s agent framework and exposed as the app’s main executable agent.
- Implement a tool named/implemented as the DocumentDB aggregation pipeline tool that connects to Azure DocumentDB using the pymongo MongoDB driver and programmatically executes an aggregation pipeline.
- The DocumentDB aggregation pipeline must group sales by product category and by season, compute a sales_velocity metric (e.g., sales per day) for each category/season, and calculate percent_change in velocity between seasons; the pipeline must return structured JSON/dict records containing category, season, sales_count, sales_velocity, and percent_change.
- Implement a web search tool that performs live web searches (calls an external search API at runtime), returns structured trend signals per category (including a relevance/confidence score), and includes source URLs and timestamps for each result.
- Expose both tools as LangChain Tool objects (or equivalent LangChain tool wrappers) and register them with the LangChain agent so the agent can invoke each tool during reasoning.
- Use context engineering by providing an explicit LangChain prompt template that injects the DocumentDB aggregation results and the web search signals into the prompt and gives explicit instructions (e.g., weighting rules or heuristics) for how to combine those signals to compute a final score.
- The agent must produce a ranked list of rising categories and a ranked list of declining categories, sorted by the combined score, and each list item must include the combined score plus supporting evidence: the DB metrics (sales_velocity/percent_change) and at least one web source URL and its timestamp.
- Include code that programmatically computes or validates the combined score (either via the prompt’s explicit rules or by a clear combining function invoked by the agent) so reviewers can verify numeric merging of DB and web signals.
- Provide an end-to-end example run (script or notebook cell) that connects to Azure DocumentDB (accepting connection URI/credentials and database/collection names), runs the DocumentDB aggregation pipeline, performs live web searches, runs the LangChain agent, and prints or returns the final ranked rising/declining category lists.

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
