# Reference requirements: Identity resolution multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Python using a LangChain multi-agent architecture and include a top-level orchestrator component named "orchestrator" that coordinates the flow between agents.
- Implement a LangChain agent named "match agent" that queries Azure DocumentDB via Beanie ODM to retrieve candidate customer profile documents for a given input profile.
- Have the "match agent" call an LLM-assisted similarity scoring routine and attach a numeric similarity score to each candidate; the agent must return a ranked list of candidates with those scores.
- Model profiles and golden records as Beanie ODM Document classes; saved documents in Azure DocumentDB must use these Beanie models (including unique identifiers).
- Implement a LangChain agent named "merge agent" that accepts the scored candidate list and deterministically consolidates matched profiles into a single golden record object, recording which source profile supplied each field (per-field provenance).
- The "merge agent" must produce an aggregate confidence score for the merged golden record derived from the input similarity scores and include that confidence on the golden record object.
- Implement a LangChain agent named "audit agent" that logs every merge decision to an audit collection in Azure DocumentDB via Beanie ODM; each audit record must include timestamp, merged source document ids, the final golden record id, the aggregate confidence score, and either embedded copies or direct references to the source documents.
- The orchestrator must sequence the flow: invoke "match agent" → pass results to "merge agent" → pass merge decision to "audit agent", and only after audit logging completes, write or upsert the final golden record into Azure DocumentDB via Beanie ODM.
- The orchestrator's write to Azure DocumentDB must use upsert semantics (insert new golden record or update existing golden record with the same canonical id) so the golden record stored in Azure DocumentDB reflects the merge.
- Provide observable, structured outputs/logs from each agent (match candidate list with scores, merged golden record, audit entry) and an end-to-end example run that demonstrates: sample source profiles present in Azure DocumentDB, the orchestrator invoking match/merge/audit, and the final golden record and corresponding audit log present in Azure DocumentDB.

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
