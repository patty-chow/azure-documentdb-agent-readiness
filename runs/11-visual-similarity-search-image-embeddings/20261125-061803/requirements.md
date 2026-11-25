# Reference requirements: Visual similarity search (image embeddings)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the app in Python and encode each product image with the CLIP model into a 512-dimensional embedding.
- Store each product as a document in Azure DocumentDB (e.g. with PyMongo) whose image embedding is saved as a BSON binary vector with subtype 0x09 (e.g. in an "embedding" field) holding the 512-dimensional vector.
- In code, create a cosmosSearch index of kind vector-ivf on the embedding field, with dimensions set to 512 to match the CLIP model's output.
- Expose a /visual-search HTTP endpoint that accepts an uploaded image (e.g. as multipart/form-data) and encodes it with the same CLIP model into a 512-dimensional query embedding.
- The /visual-search handler runs the similarity search in Azure DocumentDB with a $search / cosmosSearch query over the vector-ivf index, passing the encoded query embedding.
- The /visual-search endpoint returns the top 8 visually similar products from that query (k = 8).

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
