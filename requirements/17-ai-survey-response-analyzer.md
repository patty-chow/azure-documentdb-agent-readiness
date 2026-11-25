# Reference requirements: AI survey response analyzer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Python and Beanie ODM to define a Document model that maps to survey response documents stored in Azure DocumentDB and includes at minimum: original response text, question identifier, themes (list of strings), sentiment (label plus numeric score), representative_quote (string), embedding (numeric array), and a processed flag or processed_at timestamp.
- Read survey response documents from Azure DocumentDB via Beanie queries and process them in configurable batches (demonstrate fetching by survey id and by question id).
- For each response, invoke an LLM using prompt engineering with a structured prompt that requests: a concise list of themes, a sentiment label and numeric score, and a representative quote; require the model return machine-parseable structured output (e.g., JSON) and parse that output to populate the document fields.
- Produce and store an embedding vector for either the original response text or the extracted summary (as implemented) and save the numeric array into the document's embedding field in Azure DocumentDB.
- Update or save the enriched document back into Azure DocumentDB using Beanie, preserving the original document id and setting the processed flag/processed_at timestamp when enrichment completes.
- Implement aggregation queries (using Beanie's aggregation pipeline or the underlying PyMongo aggregation) that return, per survey question: the top-N themes with counts and the sentiment distribution (counts per sentiment label and basic statistics of sentiment scores).
- Ensure the pipeline is idempotent for repeated runs by skipping or quickly detecting documents already enriched (using the processed flag, processed_at, or presence of the embedding/themes fields) so duplicate enrichment is avoided.
- Process failures from the LLM or embedding calls deterministically: retry a configurable number of times, and when exhausted write error metadata to the Azure DocumentDB document (e.g., last_error, last_error_at) so failed items are discoverable for reprocessing.
- Include example runnable code or a script that demonstrates end-to-end behavior on sample survey response documents: reading from Azure DocumentDB, extracting themes/sentiment/quote via prompt engineering, embedding the text, saving enriched documents, and running the aggregation queries to surface top themes and sentiment distribution per question.

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
