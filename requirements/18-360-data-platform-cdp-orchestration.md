# Reference requirements: 360 data platform (CDP) orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline as an Orchestrator using Python LangChain that coordinates three agents named exactly "ingest agent", "dedup agent", and "enrich agent"; repository code must import and use LangChain constructs for orchestration and agent/chains.
- The Orchestrator must process data in batches: a single entrypoint (script or function) triggers a batch run that invokes ingest agent → dedup agent → enrich agent in sequence and waits for each agent to complete.
- The ingest agent must normalise incoming customer records (examples in code: canonicalize name casing, normalize email formats, parse and standardize phone/address) and write the normalized documents into Azure DocumentDB; each written document must include a stable unique identifier field.
- The dedup agent must perform LLM-assisted matching (explicitly call an LLM via LangChain) to identify duplicate profiles, and must merge duplicates by updating/creating a canonical profile document in Azure DocumentDB while marking or archiving duplicate documents (preserving original IDs).
- The enrich agent must call a third-party signals provider (real or clearly documented mock/stub) to retrieve firmographic or demographic signals, append those signals to the canonical profile documents, and persist the enrichment updates back to Azure DocumentDB; each enrichment update must record source and timestamp.
- The Orchestrator must create and persist a workflow document in Azure DocumentDB for every batch run; each workflow document must include at minimum: batch_id, start_time, end_time, number_ingested, number_duplicates_found, number_merged, number_enriched, per-agent status, and any error messages.
- All profile inserts, updates, merges, archival flags, enrichment writes, and workflow documents must be persisted to Azure DocumentDB (the code/config must target Azure DocumentDB as the MongoDB-compatible persistence layer rather than a different database service).
- The dedup agent’s merge operation must be implemented so reviewers can verify in code that merged data preserves source provenance (which original documents contributed which fields) and that duplicates are either removed or flagged in Azure DocumentDB.
- The Orchestrator must record per-record or per-error details for failures (e.g., invalid records, enrichment API errors) into the workflow document so a reviewer can inspect logged failures in Azure DocumentDB.
- Include an executable example (script or test) that runs a sample batch through the full Python LangChain Orchestrator pipeline with sample raw inputs and demonstrates: records being normalized in ingest, duplicates identified/merged by dedup (using the LLM step), enrichments appended by enrich, and a workflow document created in Azure DocumentDB summarizing the run.

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
