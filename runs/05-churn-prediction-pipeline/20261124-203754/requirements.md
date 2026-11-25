# Reference requirements: Churn prediction pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample as a single Python LangChain agent that is given tools and calls them to carry the pipeline through for a customer: compute RFM scores, embed the feature vector, retrieve similar churned profiles, then generate the narrative and retention action.
- Provide a LangChain tool that runs an Azure DocumentDB aggregation pipeline through the Python MongoDB driver (e.g. PyMongo) to compute recency, frequency and monetary scores per customer.
- Embed each customer's resulting RFM feature vector with an embedding model, producing one embedding per customer.
- Store each customer's embedding as a field on its document in Azure DocumentDB and create, in code, a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on that field whose dimensions match the embedding model's output.
- Retrieve the most similar churned customer profiles by running a $search / cosmosSearch vector similarity query against that index in Azure DocumentDB, restricted to churned customers.
- Expose the similar-churned-profile retrieval to the agent as a LangChain tool alongside the aggregation tool.
- Use an engineered prompt (e.g. a LangChain prompt template) that is given the customer's RFM scores and the retrieved similar churned profiles and produces, per customer, a churn risk narrative and a recommended retention action.

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
