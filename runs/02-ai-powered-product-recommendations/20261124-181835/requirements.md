# Reference requirements: AI-powered product recommendations

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Node.js and integrate LlamaIndex for vector search operations (code imports/uses Node.js and LlamaIndex).
- Use the Azure DocumentDB skill to read co-purchase order history from Azure DocumentDB (code shows an explicit call or adapter labeled "Azure DocumentDB skill" that queries the database).
- Parse order documents from Azure DocumentDB to extract co-purchase relationships (orders containing multiple product IDs) and use that history as the source data for generating product representations.
- Generate vector embeddings for products from the co-purchase data (code contains a clearly defined step that creates embeddings per product from the mined co-purchase information).
- Persist those embeddings into a DiskANN index stored on disk (code builds and saves a DiskANN index file and uses it for subsequent lookups).
- Build the agent using LlamaIndex so that vector search against the DiskANN index is performed via LlamaIndex APIs (code shows LlamaIndex creating/using the DiskANN-backed index for nearest-neighbor queries).
- Implement agent memory (explicitly named "agent memory") with per-session storage so recommendations are personalized across a user session and the memory influences returned recommendations (code demonstrates reading/writing session memory and using it when scoring or ranking items).
- Provide an interactive API or UI entry point that accepts a product ID and returns the top 5 recommended items plus a human-readable reasoning/explanation for each recommendation (response includes five product IDs/items and textual reasoning).
- Include a script in the repository that ingests exactly 20,000 product purchase transactions into Azure DocumentDB (the script inserts 20,000 order documents when run and the repository documents how to execute it).
- Use a configuration file for the Azure DocumentDB connection string and, when the connection string is missing or invalid, surface a clear, user-facing error message explaining the problem (code reads the connection string from a config file and explicitly validates it, failing with a clear error if absent or invalid).
- Provide an artistic, retailer-style UI for interacting with the agent (project contains frontend assets styled to look like an online retailer product page or catalog where users can submit a product ID and view recommendations).
- Add detailed comments before each method/function in the codebase (every function/method file contains a descriptive comment header explaining purpose, inputs, outputs, and high-level behavior to improve readability).

## What a gallery sample also needs (the starter prompt does not say these)

- The connection string and model credentials come from environment variables; none appear in the repository.
- A `.env.example` lists every setting with placeholder values.
- The vector index dimensions match the embedding model's output.
- The vector index parameters are chosen for the catalog size, and the README says how to change them for a larger one.
- One database client is created and reused across requests.
- A seed script loads sample products and creates the index, and can be run twice without duplicating data.
- `/search` returns a clear error for an empty query and when the embedding call fails.
- Search results include the similarity score.
- Dependencies are pinned in `requirements.txt`.
- Unit tests run without a live cluster.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name.
