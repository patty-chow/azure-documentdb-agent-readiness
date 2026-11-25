# Reference requirements: Customer complaint classifier

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution in Python and use LangChain as the agent framework to orchestrate the classification and embedding pipeline (single-agent implementation).
- Define complaint documents as Beanie ODM Document models (using Beanie) including at minimum: raw complaint text, product_category, root_cause, urgency_tier, embedding (vector), and a unique identifier.
- Connect Beanie to Azure DocumentDB (MongoDB-compatible endpoint) and use that connection to read and write complaint documents.
- Query Azure DocumentDB for unclassified complaints by selecting documents where product_category, root_cause, or urgency_tier are null/unset and load them for processing.
- Use prompt engineering via LangChain (prompt templates / formatted prompts) to call an LLM and produce structured outputs for product_category, root_cause, and urgency_tier, then parse and map those outputs into the Beanie document fields.
- Generate an embedding for each complaint's text using a LangChain embedding call and store the resulting embedding vector in the Beanie document's embedding field in Azure DocumentDB.
- Implement a similarity search over stored embeddings that, given a complaint, returns the top-N most similar complaints (use cosine similarity or equivalent), relying on the stored embedding vectors (either via an application-side similarity computation or a MongoDB-based approach).
- After classification and embedding, update/write the enriched complaint document back to Azure DocumentDB through Beanie (persisting the new classification fields and embedding).
- Support processing multiple unclassified complaints in a run (batch processing) so the agent can classify and store several documents per execution.
- Provide a MongoDB/Azure DocumentDB aggregation pipeline (run via the same Beanie/MongoDB connection) that groups complaints by product_category, counts occurrences, sorts descending, and returns the complaint hotspots by category.

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
