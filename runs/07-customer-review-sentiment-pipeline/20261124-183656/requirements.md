# Reference requirements: Customer review sentiment pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python using async/await and Beanie ODM for data models and persistence.
- Define Beanie ODM Document models for raw product reviews and for enriched review documents that include the original review text, product identifier, a numeric sentiment_score field, and a tags field (array of strings).
- Initialize Beanie ODM to connect to Azure DocumentDB (the MongoDB-compatible endpoint) so all reads and writes target Azure DocumentDB.
- Read raw product reviews asynchronously from a designated Azure DocumentDB collection using Beanie async queries (e.g., async find/query that yields multiple review documents).
- For each review, make an asynchronous call to the OpenAI API to (a) classify sentiment and (b) extract key themes; parse the OpenAI response into a numeric sentiment_score and a list of tag strings.
- Enrich each review document in memory by adding the numeric sentiment_score and the tags array while preserving original review fields.
- Upsert the enriched document back into Azure DocumentDB using Beanie ODM (an upsert/replace or save operation that inserts if missing and updates if present).
- Process reviews concurrently in an asynchronous pipeline (e.g., using asyncio.gather or an async worker/queue with semaphore-based concurrency control) so OpenAI calls and DB upserts are non-blocking.
- Implement and expose a summary aggregation query executed against Azure DocumentDB that groups results by product identifier and by sentiment (label or bucket), returning at minimum counts per group and average sentiment_score; implement this aggregation using Beanie/Motor aggregation pipeline primitives.
- Provide a runnable async entry point or script that demonstrates reading raw reviews, enriching and upserting them, and printing the aggregation summary so a reviewer can execute the end-to-end flow.

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
