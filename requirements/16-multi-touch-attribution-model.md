# Reference requirements: Multi-touch attribution model

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python service reads the customer journey event documents (time-ordered touchpoint events per customer) from an Azure DocumentDB collection through a MongoDB-compatible Python driver (e.g. PyMongo).
- Attribution is computed by aggregation pipelines that Azure DocumentDB executes over the journey event documents (e.g. $match, $sort and $group stages), grouping each customer's touchpoints in event-time order.
- A first-touch pipeline gives all of a customer's conversion credit (e.g. the conversion revenue) to the earliest touchpoint in that customer's journey.
- A last-touch pipeline gives all of a customer's conversion credit (e.g. the conversion revenue) to the latest touchpoint in that customer's journey.
- A linear pipeline splits a customer's conversion credit (e.g. the conversion revenue) equally across every touchpoint in that customer's journey.
- The attribution output of the models (e.g. an amount per touchpoint or channel under each model) is written back to Azure DocumentDB as a versioned document per customer: each run stores a new version carrying a version marker (e.g. a version number or run timestamp), and the previous versions of that customer's document remain stored.
- A LangChain tool, implemented in Python, takes a marketer's natural-language question about attribution results, reads the stored attribution documents from Azure DocumentDB, and returns the answer; the tool is wired into a LangChain agent or chain so the question is answered by calling it.

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
