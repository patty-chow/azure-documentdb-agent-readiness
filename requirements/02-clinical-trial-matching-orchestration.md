# Reference requirements: Clinical trial matching orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Provide a Python LangChain Orchestrator pipeline entrypoint (e.g., a function run_orchestration(patient_profile)) that accepts a structured patient profile (dictionary or dataclass) and returns the final match document.
- Compute an embedding from the patient_profile and perform a vector search against the DocumentDB index of trial criteria, issuing a vector query that returns a top-N list of candidate trials (N must be a configurable parameter).
- Connect to Azure DocumentDB and execute the vector search on the DocumentDB index of trial criteria (show the DocumentDB query/SDK call that performs vector similarity search and returns trial documents).
- Implement a LangChain "eligibility agent" that receives the patient_profile and the candidate trials and applies trial-specific inclusion/exclusion rules, producing a per-trial eligibility decision (eligible / ineligible / conditional) plus explicit rule-level reasons for any exclusions.
- The Orchestrator must invoke the eligibility agent, consume its outputs, and either filter out ineligible trials or annotate candidates with the eligibility decision and reasons (code must show the filtering/annotation step).
- Implement a LangChain "consent agent" that, for each eligible (or conditionally eligible) trial, generates a plain-language trial summary for the patient that explains purpose, procedures, and key consent points; the output must be natural-language text intended for a patient audience.
- The Orchestrator must hand off eligibility-annotated trial data to the consent agent and attach the generated plain-language consent summary to each corresponding trial record in the pipeline output.
- Persist the final match results to Azure DocumentDB: insert or upsert a document that includes at minimum patient identifier (or generated match id), timestamp, list of candidate trials, eligibility decisions with reasons, and the consent summaries.
- Include a runnable example or sample invocation in code that demonstrates the full end-to-end flow: accept a sample patient_profile, perform vector search, run eligibility agent, run consent agent, and store the result in Azure DocumentDB.
- All agent interactions and orchestration logic must use LangChain constructs (agents/chains) and clearly label the components as the Orchestrator, the eligibility agent, and the consent agent in the code so a reviewer can verify the separation of responsibilities.

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
