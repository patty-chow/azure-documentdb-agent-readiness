# Reference requirements: Prescription refill agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Node.js LangChain agent, built with Beanie ODM for its data access, handles the patient's refill request conversationally and decides which of its tools to call as the conversation proceeds.
- A tool looks up the patient's active prescriptions in Azure DocumentDB through Beanie ODM (e.g. by the patient's identifier and whether the prescription is active) and returns them to the agent.
- A tool checks a prescription's refill eligibility from its days supply remaining and its refill count and returns the result to the agent.
- A tool creates a refill request document in Azure DocumentDB through Beanie ODM for the prescription being refilled.
- Agent memory keeps context across turns so that a follow-up such as "refill my blood pressure medication" resolves to the patient's prescription without the patient naming the drug again.
- The agent completes a refill by using these tools together: it looks up the prescription, checks its eligibility, and creates the refill request document when the prescription is eligible.

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
