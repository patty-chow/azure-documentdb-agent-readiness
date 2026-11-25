# Reference requirements: Customer review sentiment pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline is written in Python with async/await and uses the Beanie ODM to read the raw product review documents from Azure DocumentDB (e.g. a Beanie `Document` model for reviews queried with an awaited `find`).
- For each review, the pipeline calls OpenAI to classify the review's sentiment and to extract its key themes.
- The OpenAI classification call is made asynchronously inside the pipeline (e.g. the async OpenAI client awaited per review).
- Each review document is enriched with a sentiment score field and a tags field derived from the OpenAI result (the tags holding the extracted themes).
- The enriched document is upserted back into Azure DocumentDB through Beanie (e.g. an awaited `save`/`replace`, or an upsert on the underlying collection), so an existing review is updated in place.
- A summary aggregation query runs against Azure DocumentDB (via Beanie's aggregate or the underlying collection) and groups the enriched reviews by product and by sentiment (e.g. a `$group` on a compound key returning a count per group).

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
