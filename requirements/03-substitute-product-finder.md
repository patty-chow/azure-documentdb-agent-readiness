# Reference requirements: Substitute product finder

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python FastAPI app uses the Beanie ODM to define a product document model and store product JSON documents in Azure DocumentDB.
- An embedding is generated from each product's attributes and stored as a vector field on that product's document in Azure DocumentDB (e.g. an `embedding` array of floats).
- A cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) is created in code on the embedding field, with similarity COS and dimensions matching the embedding model's output size.
- A `/substitute` endpoint accepts a product ID, looks up that product's stored embedding and runs an Azure DocumentDB `$search` / cosmosSearch query with similarity COS that returns the 5 closest alternative products (the requested product itself excluded).
- A script ingests 10,000 product transactions into Azure DocumentDB through the Beanie model.
- The app serves an artistic UI styled like an online retailer's website that shows the substitutes returned by the `/substitute` endpoint.
- The Azure DocumentDB connection string is read from a config file, and the app displays a clear error when that connection string is missing or invalid.
- The code is kept simple and readable, with a detailed comment placed before each method or function describing what it does.

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
