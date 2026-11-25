# Reference requirements: Branch performance analytics

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python using FastAPI and expose at least one GET HTTP endpoint that returns branch-level aggregates suitable for a dashboard (e.g., /branches/aggregates or /branches/{branch_id}/aggregate).
- Build the aggregation query against Azure DocumentDB (MongoDB API) using a MongoDB aggregation pipeline that includes a $facet stage to compute multiple metrics in one pipeline.
- In the $facet stage include a facet that computes transaction volume per branch (count of transaction documents, grouped by branch_id) and return that count in the endpoint response.
- In the $facet stage include a facet that computes average ticket size per branch (average of an amount field, grouped by branch_id) and return that value in the endpoint response.
- In the $facet stage include a facet that computes product mix per branch (counts grouped by product_id or product_category, with counts or percentages) and return that product mix array in the endpoint response.
- Provide code that caches the rolled-up summary documents in Azure DocumentDB by writing/upserting documents into a dedicated collection (e.g., branch_summaries) keyed by branch_id and containing transaction_volume, average_ticket_size, product_mix, and a last_updated timestamp.
- Provide a programmatic mechanism that populates/refreshes the cached summaries by executing the $facet aggregation and upserting the results into the branch_summaries collection (either a POST endpoint like /refresh-summaries or a background task callable in the code).
- Expose at least one endpoint that returns the cached summary document from the branch_summaries collection for a given branch_id (and clearly falls back to live aggregation only if implemented; the cached-read endpoint must be present).
- Add a LangChain tool (a callable Tool object or equivalent in the codebase) named and registered in the LangChain code such that analysts can pass natural language questions and the tool answers by querying the cached branch_summaries in Azure DocumentDB and returning a human-readable response.
- Ensure the LangChain tool queries the branch_summaries collection (not raw transaction documents) when answering questions and that its implementation demonstrates retrieval of the cached fields (transaction_volume, average_ticket_size, product_mix) and composes a concise natural-language reply.

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
