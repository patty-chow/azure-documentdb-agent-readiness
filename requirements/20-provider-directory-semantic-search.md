# Reference requirements: Provider directory semantic search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Python and LlamaIndex to generate embeddings for provider profiles and for incoming queries (imports and calls to LlamaIndex must be present in the code).
- Store provider profiles as Azure DocumentDB documents with explicit fields: specialty (string), languages (array), accepted_insurance (array), and bio (string), and include an embedded vector field named "embedding" containing the numeric vector.
- Include code that persists provider documents into an Azure DocumentDB collection (connection and document insert/update operations targeting Azure DocumentDB must be present and exercised).
- Create or configure a vector-ivf index on the DocumentDB collection’s embedding field (index creation or ARM/infra configuration that defines a vector-ivf index on the embedding field must be included).
- Expose an HTTP endpoint at /find-provider that accepts a plain-language patient request (e.g., a POST or GET with a single plain-text parameter/body containing the query).
- Use LlamaIndex at request time to convert the plain-language patient request into an embedding, then execute a vector search against Azure DocumentDB’s embedding field using the configured vector-ivf index.
- Return results from /find-provider as a JSON array of provider matches ranked by similarity score, and include for each match: specialty, languages, accepted_insurance, bio, and the similarity score.
- Provide a seed or import script that inserts multiple example provider documents into the Azure DocumentDB collection with embeddings generated via LlamaIndex so reviewers can reproduce queries like "Spanish-speaking cardiologist accepting Medicare."
- Support a top-k limit on returned results (default to 5) configurable via a query parameter to /find-provider and applied to the vector search call.
- When no vector matches are found, return an empty results array with a successful HTTP response (e.g., 200) rather than an internal error.

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
