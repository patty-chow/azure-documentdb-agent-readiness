# Reference requirements: AI-powered product recommendations

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Project implements a Node.js LlamaIndex agent (Node.js codebase with LlamaIndex usage evident in package.json and source files).
- Agent code reads co-purchase order history from Azure DocumentDB (contains a query module that fetches order/transaction documents from Azure DocumentDB and uses them as the data source for embeddings and co-purchase analysis).
- The repository includes an ingest script that inserts 20,000 product purchase transactions into Azure DocumentDB and the script validates that 20,000 transactions were written (e.g., insertion counter or post-insert count check).
- Code generates product embeddings from the co-purchase / product data (there is a dedicated embedding step/function that computes and returns embeddings for each product).
- Generated embeddings are persisted into a DiskANN index (the project builds/writes a DiskANN index and stores the index files; source shows DiskANN index creation or update from the embeddings).
- The agent performs LlamaIndex vector search against the DiskANN index to find similar or co-purchased items (the search path uses LlamaIndex vector search APIs and queries DiskANN as the vector index backend).
- Agent uses agent memory to personalise recommendations per session (there is a session-scoped agent memory store and recommendation logic uses that memory to alter or re-rank results for the same session).
- The agent accepts a product ID input and returns the top 5 recommended items with human-readable reasoning for each recommendation (an API endpoint or UI action that, given a product ID, returns exactly 5 recommended product IDs/records plus explanatory text for why each was recommended).
- Web UI styled as an artistic online retailer is included and exposes product browsing and a recommendation widget where users can input a product ID and see the top 5 recommendations with reasoning (UI assets and CSS/HTML show retail-like layout and the recommendation output).
- Configuration for the Azure DocumentDB connection string is read from a config file (explicit config file present and used by the app); if the connection string is missing or invalid the app displays a clear, user-facing error message explaining the problem.
- Every method/function in the codebase is preceded by a detailed comment describing its purpose, inputs, outputs, and high-level approach (check source files to confirm a comment block exists immediately before each method/function).

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
