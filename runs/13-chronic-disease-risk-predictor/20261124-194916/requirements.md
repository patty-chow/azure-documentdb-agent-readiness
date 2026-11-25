# Reference requirements: Chronic disease risk predictor

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python as a single LlamaIndex agent that takes a new patient's clinical features as input and carries out the embed, retrieve, reason and generate flow end to end.
- Store high-risk patient profiles as documents in an Azure DocumentDB collection (e.g. via PyMongo), with each profile's embedding vector held in a field on its document.
- Create, in code, a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on that embedding field, with dimensions matching the embedding model's output and a similarity of COS, L2 or IP.
- Embed the new patient's clinical features with the same embedding model used for the stored high-risk profiles.
- Retrieve the most similar high-risk profiles by running a $search / cosmosSearch aggregation against the Azure DocumentDB vector index with the new patient's embedding (e.g. the top-k nearest neighbours).
- Wire the Azure DocumentDB vector store of high-risk profiles into the LlamaIndex agent as its agent memory (e.g. as a retriever, tool or memory component the agent calls), and have the agent recall the stored profiles from it when handling a new patient.
- Have the agent reason over the similarities between the new patient's features and the retrieved high-risk profiles (e.g. which features they share) and generate a personalised risk narrative for that patient.
- Include recommended interventions for the patient in the generated output, derived from that reasoning.

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
