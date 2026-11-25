# Reference requirements: Seasonal trend spotter agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python agent built with LangChain, where one agent owns the reasoning loop and is given exactly two tools it can call: an aggregation tool and a web search tool.
- The aggregation tool runs an aggregation pipeline against Azure DocumentDB through a MongoDB driver (e.g. PyMongo's `aggregate()`), and the pipeline's stages themselves compute sales velocity per season for each product category and compare it across seasons (e.g. a `$group` by season and category followed by a stage that derives the season-to-season change).
- The web search tool calls a live web search service at run time and returns current trend signals for the agent to use.
- A context-engineering step shapes the two tool outputs into the prompt sent to the model, combining the sales-velocity comparison and the web trend signals into one prompt context (e.g. labelled sections of a prompt template) so the model reasons over both signals together.
- The agent's final answer is a ranked list of product categories that identifies which are rising and which are declining (e.g. ranked by the magnitude of the season-to-season change in sales velocity).

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
