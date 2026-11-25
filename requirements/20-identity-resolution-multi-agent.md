# Reference requirements: Identity resolution multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Customer profile documents, golden records and audit entries are defined as Beanie ODM document models in Python, and the sample's reads and writes against Azure DocumentDB go through those models.
- A match agent built with LangChain retrieves candidate duplicate profiles from Azure DocumentDB through the Beanie models and uses an LLM call to score how similar each candidate is to the profile being resolved, returning the candidates together with their similarity scores.
- A merge agent built with LangChain takes the matched profiles and consolidates them into a single golden record (e.g. choosing or combining field values across the matched profiles).
- An audit agent built with LangChain records every merge decision in Azure DocumentDB through a Beanie model, and each record carries the confidence score of the merge and the source documents (or references to them) that went into it.
- An orchestrator coordinates the three agents for each identity resolution run, calling the match agent, handing its results to the merge agent, and then invoking the audit agent for the resulting merge decision.
- The orchestrator writes the final golden record to Azure DocumentDB through the Beanie golden record model.

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
