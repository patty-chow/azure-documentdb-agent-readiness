# Reference requirements: Visual similarity search (image embeddings)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Python and expose an HTTP endpoint at /visual-search that accepts an uploaded image (multipart/form-data).
- Use the CLIP model to encode images; both stored product images and incoming query images must be encoded with CLIP into 512-dimensional embeddings.
- Include functionality (API or ingestion script) that encodes a product image with CLIP and writes a product document into Azure DocumentDB containing a product identifier, display metadata (e.g., name or image URL), and the embedding.
- Store embeddings in Azure DocumentDB as BSON binary vectors with subtype 0x09, and ensure the stored binary represents a 512-dimensional embedding (stored length consistent with 512 components).
- Create a vector-ivf index on the embedding field in Azure DocumentDB before running searches; the code or provisioning script must demonstrate index creation.
- Execute searches using Azure DocumentDB’s vector-ivf index (server-side vector search) rather than performing full in-process brute-force nearest-neighbor computation.
- The /visual-search handler must accept the uploaded image, encode it with CLIP, submit the query vector to Azure DocumentDB, and request nearest neighbors using the vector-ivf index.
- Return the top 8 visually similar products for the query image, ordered by similarity (best match first).
- Returned results must include each product’s identifier and display metadata (for example, name and/or image URL) so they can be shown to a shopper.
- Provide sample product data or an ingestion script so a reviewer can populate Azure DocumentDB and verify that /visual-search returns non-empty results.

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
