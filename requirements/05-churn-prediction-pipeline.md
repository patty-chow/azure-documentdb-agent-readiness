# Reference requirements: Churn prediction pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a single-agent Python LangChain agent (single-agent) that orchestrates the end-to-end churn prediction pipeline.
- Provide one or more agent tools that execute Azure DocumentDB aggregations (MongoDB aggregation pipelines) to compute per-customer recency, frequency, and monetary (RFM) metrics from the transactions/events collections.
- Retrieve existing behavioural embeddings stored in Azure DocumentDB for each customer and combine those behavioural embeddings with the computed RFM metrics to form a single feature vector per customer (e.g., concatenation or clearly documented normalization + concatenation).
- Compute embeddings of the combined feature vectors (the code must call an embedding function/model and produce numeric vectors for each customer feature vector).
- Create or upsert those resulting embeddings into a DocumentDB vector index in Azure DocumentDB (code must show index target and insert/upsert operations).
- Provide a tool in the agent that performs vector similarity search against the DocumentDB vector index to retrieve the most similar customer profiles, limiting or filtering results to profiles labeled as churned.
- Use the retrieved similar churned customer profiles as contextual examples / retrieval context when generating outputs (the retrieval results must be passed into the prompt used for generation).
- Use LangChain prompt engineering: include a prompt template or prompt construction code that instructs the agent to generate a churn risk narrative and a recommended retention action for the target customer using the combined features and retrieved similar churned profiles.
- The agent must, for a given customer id or list of customer ids, run the full flow (DocumentDB aggregations -> combine with behavioural embeddings -> embed feature vector -> store in DocumentDB vector index -> retrieve similar churned profiles -> generate churn risk narrative + recommended retention action) and return the narrative and action.
- Include an executable example or test script that demonstrates the pipeline end-to-end for at least one customer id and prints the churn risk narrative and recommended retention action produced by the Python LangChain agent.

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
