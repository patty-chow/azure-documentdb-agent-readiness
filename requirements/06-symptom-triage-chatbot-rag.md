# Reference requirements: Symptom triage chatbot (RAG)

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the chatbot in Python with LangChain as a RAG pipeline that accepts a free-text symptom description and returns triage advice.
- Store the clinical triage guideline sections as documents in Azure DocumentDB with an embedding on each document (written with a Python MongoDB driver, e.g. PyMongo), and create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field whose dimensions match the embedding model's output.
- For each symptom description, embed the description with the same embedding model and retrieve the most relevant guideline sections with a $search / cosmosSearch query (similarity COS, L2 or IP) so the similarity runs in Azure DocumentDB.
- Pass the retrieved guideline sections into the LangChain prompt as the context the generated answer is grounded in.
- Enforce the safety guardrails through prompt engineering in the LangChain prompt template: every response recommends professional consultation and never gives a diagnosis.
- Return the triage advice as a structured output (e.g. a Pydantic model or JSON object) that includes an urgency level alongside the advice.

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
