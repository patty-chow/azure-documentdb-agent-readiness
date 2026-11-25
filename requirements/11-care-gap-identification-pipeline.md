# Reference requirements: Care gap identification pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Python and expose a LangChain single-agent (i.e., a single Agent instance) that orchestrates the pipeline and is the entrypoint for the workflow.
- Provide a LangChain Tool named or documented as a "DocumentDB aggregation tool" that connects to Azure DocumentDB and executes aggregation pipelines (not just find queries).
- The aggregation tool must construct and run an Azure DocumentDB aggregation pipeline that joins/inspects patient documents (age, diagnosis, last-visit) and emits candidate patients who are missing recommended screenings; the pipeline must use aggregation stages (e.g., $match/$project/$lookup/$sort) in the code.
- The aggregation pipeline must compute and return for each candidate patient at minimum: patient id, age, diagnoses list, lastVisitDate (ISO), and a list of identified care gap types (e.g., "mammogram overdue", "colonoscopy missing").
- Use explicit, coded criteria in the aggregation pipeline (or a pre-processing step called by the pipeline) that determine missing screenings based on age ranges, diagnosis codes, and last-visit date comparisons (e.g., lastVisitDate older than guideline intervals); those criteria must be visible in the source code.
- Use context engineering to inject care gap guidelines into the agent's prompt context: the code must build a prompt or system message that includes guideline text (screening ages, intervals, diagnosis-specific rules) and pass that text into the LangChain prompt template used by the agent.
- After aggregation, call an LLM via LangChain to prioritise the returned patient list; the code must call the LLM with the patient records plus the injected guideline context and produce a priority score or rank for each patient (i.e., LLM-driven prioritisation is evident in code).
- For each distinct care gap type, generate outreach talking points tailored to that gap using the LangChain LLM (the code must produce per-patient or per-gap talking points, not a single generic message).
- The DocumentDB aggregation tool must return structured JSON objects (or Python dicts) that include the computed prioritisation score and the generated outreach talking points so the agent's final output is a prioritized list with talking points attached.
- Provide an example or demo script in the repo that runs the full pipeline end-to-end (connects to Azure DocumentDB, runs the aggregation tool, runs the LangChain agent with injected guidelines, and prints/returns the prioritized patient list with outreach talking points).

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
