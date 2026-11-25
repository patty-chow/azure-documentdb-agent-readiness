# Reference requirements: CLV prediction pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python with a LangChain agent that acts as the single agent of the pipeline, with the DocumentDB aggregation tool registered as a LangChain tool the agent can invoke during a run.
- The DocumentDB aggregation tool runs an aggregation pipeline in Azure DocumentDB through a MongoDB driver (e.g. PyMongo) and returns, per customer, historical purchase frequency, average order value and tenure.
- The agent includes the purchase frequency, average order value and tenure returned by the aggregation tool in the prompt it sends to the LLM.
- The prompt engineering instructs the LLM to estimate a CLV tier chosen from low, medium, high and VIP, to produce a CLV score, and to generate a rationale for the estimate.
- The agent writes the CLV score and tier back to that customer's profile document in Azure DocumentDB by updating the existing document.

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
