# Reference requirements: Substitute product finder

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the backend in Python using FastAPI and define/persist product documents with Beanie ODM connected to Azure DocumentDB.
- Product JSON documents must include a numeric embedding vector field; embeddings for product attributes must be generated using OpenAI embeddings and stored on each document in Azure DocumentDB.
- The code must create or declare an Azure DocumentDB vector search index on the document embedding field so the field is searchable by vector in Azure DocumentDB.
- Provide a FastAPI /substitute endpoint that accepts a product ID parameter, queries Azure DocumentDB vector search using cosine similarity, and returns the 5 closest alternative products (include product metadata and similarity scores in the JSON response).
- The /substitute implementation must perform the nearest-neighbor retrieval via Azure DocumentDB vector search (server-side vector search query) rather than computing cosine similarity client-side.
- Include a standalone ingestion script that generates and inserts 10,000 product transactions/documents: each generated product must have attributes, an OpenAI embeddings call to produce its vector, and insertion into Azure DocumentDB via Beanie ODM.
- The ingestion script must read the same Azure DocumentDB connection string from the application config file and verify the insert count is 10,000 (e.g., report or assert the number inserted).
- Use a config file to supply the Azure DocumentDB connection string; the app must detect a missing or invalid connection string and display a clear, user-friendly error message at startup or when attempting DB access.
- Serve an artistic, retailer-style UI (HTML/CSS) from the FastAPI app (root route) that displays product details and a UI to request substitutes so the app looks like an online retailer website.
- Add detailed comments or docstrings immediately before every function or method explaining its purpose, inputs, outputs, and interactions with Beanie/Azure DocumentDB so reviewers can read each method easily.

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
