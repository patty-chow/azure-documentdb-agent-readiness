# Reference requirements: AI-powered product recommendations

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The application is written in Node.js and its single agent is built with LlamaIndex.
- The agent reads co-purchase order history from Azure DocumentDB through a MongoDB driver (e.g. the `mongodb` Node.js package) whose Azure DocumentDB connection string is read from a config file, displaying a clear error when that connection string is missing or invalid.
- The agent generates product embeddings from the co-purchase patterns it read and persists each embedding as a field on the corresponding product document in Azure DocumentDB.
- A `cosmosSearch` vector index of kind `vector-diskann` is created in code on the embedding field, with `dimensions` matching the output size of the embedding model in use and a `similarity` (COS, L2 or IP) that the queries also use.
- Similar products are retrieved with an aggregation that uses the `$search` stage and `cosmosSearch` operator against that index, with the similarity ranking performed by Azure DocumentDB.
- The agent accepts a product ID and returns the top 5 recommended items, each accompanied by reasoning for why it was recommended.
- The agent keeps memory scoped to a shopper session and uses it to personalise the recommendations returned on later requests within the same session.
- A script ingests 20,000 product purchase transactions into Azure DocumentDB.
- An artistic UI styled like an online retailer's website lets a shopper choose a product and shows the agent's recommended items with their reasoning.
- Every method is preceded by a detailed comment explaining what it does, and the code is kept simple and readable.

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
