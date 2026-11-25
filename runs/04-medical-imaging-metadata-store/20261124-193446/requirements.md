# Reference requirements: Medical imaging metadata store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The app is a Python service that stores medical imaging metadata documents (modality, body part, findings) in Azure DocumentDB through a Python MongoDB-compatible driver (e.g. pymongo).
- For each imaging record, the findings text is embedded with OpenAI and the resulting vector is stored on the same document as a BSON binary vector.
- A cosmosSearch index of kind vector-ivf is created in code on the embedding field, with dimensions matching the OpenAI embedding model's output.
- The service exposes a search endpoint that accepts a clinical query string (e.g. as a query parameter or JSON body field).
- The search endpoint embeds the clinical query string with OpenAI and runs the similarity search in Azure DocumentDB with a $search / cosmosSearch query over the vector-ivf index using that query vector (similarity e.g. COS).
- The search endpoint returns the imaging metadata documents matched by that vector search, ordered by semantic similarity to the query.

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
