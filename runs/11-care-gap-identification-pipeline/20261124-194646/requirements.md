# Reference requirements: Care gap identification pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Python agent built with LangChain runs the whole pipeline: it calls the aggregation tool, then prioritises the resulting patient list and generates outreach talking points.
- The agent has a LangChain tool that runs an aggregation pipeline against Azure DocumentDB through the Python MongoDB driver (e.g. PyMongo) and returns the patients missing recommended screenings.
- The aggregation pipeline works out who is missing a screening inside Azure DocumentDB from the patients' age, diagnosis and last-visit documents (e.g. a $match on age and diagnosis criteria and a comparison of the last-visit date against the screening interval).
- Care gap guidelines (which screenings are recommended for whom, and how often) are injected into the agent's prompt context before it prioritises patients or writes talking points.
- The agent prioritises the patient list returned by the tool using the LLM and the injected guidelines, producing an ordered list (e.g. with a priority level per patient).
- The agent generates outreach talking points for each gap type found, and its final output pairs the prioritised patients with the talking points for their gap types.

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
