# Reference requirements: AI survey response analyzer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python pipeline that uses the Beanie ODM to read survey response documents from Azure DocumentDB (a Beanie Document model for the survey response collection, iterated with a Beanie query).
- For each response, a prompt-engineered LLM call (e.g. OpenAI) whose prompt instructs the model to extract themes, sentiment (e.g. a label or a score) and a representative quote from the response text, with the model's reply parsed into those three values.
- The response text is embedded with an embedding model call (e.g. OpenAI embeddings) to produce a vector for the response.
- The enriched document, carrying the themes, sentiment, representative quote and embedding, is written back to the original document in Azure DocumentDB through Beanie (e.g. saving or updating the existing document by its id).
- An aggregation pipeline, executed in Azure DocumentDB through Beanie, that surfaces the top themes per survey question (e.g. unwinding each response's themes, grouping by question and theme, and sorting by count).
- An aggregation pipeline, executed in Azure DocumentDB through Beanie, that returns the sentiment distribution per survey question (e.g. grouping by question and sentiment value and counting, or bucketing scores).

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
