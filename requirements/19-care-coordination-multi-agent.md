# Reference requirements: Care coordination multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Python and use LangChain Python as the agent framework.
- Define four distinct components named "GP agent", "specialist agent", "pharmacy agent", and "orchestrator" implemented with LangChain Python constructs (e.g., agents, tools, or AgentExecutors) so a reviewer can find those exact names in the code.
- Implement the "GP agent" to connect to Azure DocumentDB and read a patient's primary care record by a supplied patient id, returning structured data (e.g., JSON/dict) representing the primary care record.
- Implement the "specialist agent" to connect to Azure DocumentDB and retrieve the patient's referral notes by the same patient id, returning structured referral-note data.
- Implement the "pharmacy agent" to connect to Azure DocumentDB and retrieve the patient's current medications by patient id, returning a structured medication list including drug names, dosages, and frequencies.
- The "orchestrator" must invoke the GP agent, specialist agent, and pharmacy agent, collect their outputs, and synthesise them into a single unified care plan document that integrates diagnoses, referrals, and medication plan.
- The synthesized unified care plan must include provenance metadata linking to the source Azure DocumentDB document ids and timestamps for each contributing input.
- The orchestrator must write the unified care plan document back to Azure DocumentDB (the managed MongoDB-compatible service named Azure DocumentDB) and the write operation must return or log the new DocumentDB document id.
- All DocumentDB interactions must operate against Azure DocumentDB (not Cosmos DB or other services) and accept a parameterized patient id input rather than using hard-coded patient data.
- Include a runnable demonstration (script or test) that executes the orchestrator for a sample patient id, shows the agents' intermediate outputs, and shows the final unified care plan being written to Azure DocumentDB.
- Ensure the orchestrator returns or logs the stored care plan content and the DocumentDB write result so a reviewer can verify that the synthesized plan was persisted.

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
