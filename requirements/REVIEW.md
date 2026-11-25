# Review of the drafted requirements (first draft)

A 126-agent review of all 100 files in `requirements/`: 25 reviewers read four files each against the starter prompt and the installed Agent Kit skills; every flagged file then got an independent skeptic who tried to refute each issue; a critic looked for systematic patterns. 418 issues were upheld. Verdicts: 82 files minor edits, 18 need rework.

## Upheld issues by kind

| Kind | Count |
|---|---|
| not_in_prompt | 296 |
| duplicate | 84 |
| vague | 19 |
| not_checkable | 5 |
| wrong_fact | 4 |
| missing | 4 |
| contradicts_prompt | 4 |
| infeasible | 2 |

## Systematic patterns (critic)

Worth regenerating after fixing the drafter: **True**.

Where the files are: /Users/julietai/claude/azure-documentdb-agent-readiness/requirements/ holds 101 files, one per sample, named after the starter prompt's file stem (e.g. retail-04 -> requirements/04-natural-language-product-search.md, because samples/index.json maps id retail-04 to samples/retail/04-natural-language-product-search.md). The mapping id -> file is in samples/index.json ('prompt' field); the five verticals reuse the same 01-20 numbering so the filename alone does not say which vertical. requirements/retail-semantic-search.md is the hand-written example whose '## What a gallery sample also needs' section is copied verbatim into every file by loop/draft_requirements.py (gallery_section()).

Ultracode: nothing in the project (outside runs/) mentions it, and it is not referenced by the drafter or the pipeline, so I cannot say how it helps here; if it is a tool you have in mind for the fix-and-regenerate step, the relevant place is the INSTRUCTIONS constant at loop/draft_requirements.py:27-41 and the command `python loop/draft_requirements.py --overwrite` (optionally `--ids ...`).

Why regenerate rather than hand-edit: 418 upheld issues across 100 files, and seven of the nine patterns are consequences of the drafter instructions, not of individual prompts. The three files I read in full (04-natural-language-product-search.md, 03-portfolio-tracker-with-live-alerts.md, 05-appointment-scheduling-assistant.md) each show four or more of the patterns, so hand editing is roughly 4 edits per file with the same rewrites repeated 100 times. Two structural causes worth fixing alongside the sentences above: (1) the '6 to 12 bullets' rule forces padding on two-sentence prompts (fintech-03's prompt has four asks; the draft has eight bullets), so change it to 'as many bullets as the prompt has distinct asks, typically 4 to 9; fewer is better than padding'; (2) the drafter is given 'Agent type' and 'Concepts' lines, which it turns into literal naming requirements (pattern 6); either drop them from the user message or tell the model they are catalogue metadata. Caveats: the 4 'missing' items (retail-04 createSearchIndexes, retail-20 GeoJSON order, fintech-15 portfolio collection, fintech-17 rationale vector index) are file-specific and the DocumentDB-facts sentence will only catch the vector-index one, so re-check those four after regeneration; and regeneration will produce new variance, so keep the verification pass and expect a second, much smaller round of hand edits rather than zero. The 4 wrong_fact / 2 infeasible / 4 contradicts_prompt items all fall under pattern 8 and should disappear with the feature-vocabulary sentence.

### 68 files: Invented concrete specifics the prompt never gives: exact field names and schemas, collection names, route paths, HTTP status codes, function/tool names, index definitions, response-shape field lists, 'must match exactly'

Invented concrete specifics the prompt never gives: exact field names and schemas, collection names, route paths, HTTP status codes, function/tool names, index definitions, response-shape field lists, 'must match exactly'. The drafter fills every prompt noun with an implementation detail of its own choosing, then the auditor fails builds that chose differently. Confirmed in fintech-03 (Position/AlertRule field lists, GET /portfolio/:userId/summary, fullDocument:'updateLookup' - the prompt says only 'positions and alert rules' and 'an aggregation'), healthcare-05 (patientId/providerId/slotId/start/end/status fields, 'appointments collection') and retail-04 (top-N configurable, score normalisation).

**Drafter rule:** State requirements at the level of detail the prompt uses: never invent field names, collection names, route paths, status codes, function or tool names, index keys or output-field lists the prompt does not give; where a detail is needed to make the bullet checkable, write it as an example in parentheses ('e.g. ...'), not as the requirement.

### 38 files: Demands for tests, demo/e2e scripts, seed/sample data and 'so a reviewer can reproduce' artifacts that the starter prompt never asks for

Demands for tests, demo/e2e scripts, seed/sample data and 'so a reviewer can reproduce' artifacts that the starter prompt never asks for. The shared gallery section already requires a seed script and unit tests, so these are both not_in_prompt and duplicates. Confirmed in healthcare-05 (last bullet: 'Include an end-to-end example or test script that demonstrates...'), retail-04/fintech-03 do not have it but retail-18, banking-04, customer-360-08 do.

**Drafter rule:** Do not require tests, demo or end-to-end scripts, example invocations, seed or sample data, or anything 'so a reviewer can reproduce it': the shared section appended later covers seeding and tests, and the prompt's behaviour is checked in the code itself.

### 32 files: Invented robustness and edge-case behaviour: graceful empty-result handling, retries, idempotency guards, resume tokens, concurrency locks, input validation, 'do not overwrite on failure', HIPAA redaction, safety-guardrail checks, error-status documents

Invented robustness and edge-case behaviour: graceful empty-result handling, retries, idempotency guards, resume tokens, concurrency locks, input validation, 'do not overwrite on failure', HIPAA redaction, safety-guardrail checks, error-status documents. None appears in the prompt; the drafter adds production hardening. Confirmed in retail-04 ('handle the case where one side returns zero results') and healthcare-05 ('Detect and handle concurrent booking conflicts ... offering next available slot alternatives').

**Drafter rule:** Do not add error handling, retries, idempotency, concurrency protection, input validation, empty-result handling, logging or compliance safeguards unless the prompt itself asks for them; a requirement describes what the prompt asks the app to do, not how a production system would harden it.

### 32 files: Restating or negating an earlier bullet as a new one: 'the X must be performed server-side (not client-side)', 'all queries must actually be sent to Azure DocumentDB (not simulated)', 'ensure the pipeline contains $geoNear rather than other operators', 'the stored document must clearly reflect the outputs'

Restating or negating an earlier bullet as a new one: 'the X must be performed server-side (not client-side)', 'all queries must actually be sent to Azure DocumentDB (not simulated)', 'ensure the pipeline contains $geoNear rather than other operators', 'the stored document must clearly reflect the outputs'. These are the same behaviour as a neighbouring bullet phrased as a prohibition or an assurance, and verification marked them 'delete' or 'merge into previous bullet'. Confirmed in retail-04 (last bullet duplicates the hybrid-search bullets) and healthcare-05 (reschedule/cancel bullets each restate the atomic-transaction bullet).

**Drafter rule:** Each bullet must name a distinct behaviour: never add a bullet that restates an earlier one as a prohibition ('not client-side', 'not simulated', 'rather than...'), as an assurance ('ensure that...', 'so a reviewer can confirm...'), or as a consequence of it; fold such clauses into the bullet they qualify or leave them out.

### 23 files: Standalone 'connect to Azure DocumentDB via a configurable connection string / environment variable' and 'all reads and writes target Azure DocumentDB (not Cosmos DB, not a mock)' bullets

Standalone 'connect to Azure DocumentDB via a configurable connection string / environment variable' and 'all reads and writes target Azure DocumentDB (not Cosmos DB, not a mock)' bullets. Every file gets one; the gallery section already requires env-var configuration and one reused client, and every other bullet already says the operation is against Azure DocumentDB. Confirmed as the first bullet of fintech-03 and in retail-04's last bullet.

**Drafter rule:** Do not write a separate bullet about connecting to Azure DocumentDB, where the connection string comes from, or that operations 'really' target Azure DocumentDB; name the driver or ODM inside the bullet that first uses it and leave configuration to the shared section.

### 19 files: Taxonomy labels and prompt nouns turned into literal naming requirements: agents 'named exactly "forecast agent"', a tool 'named exactly "DocumentDB aggregation tool"', 'use the phrase "agent memory" in the code', 'label the pipeline as an Orchestration implementation', 'a Single-agent application where a single process

Taxonomy labels and prompt nouns turned into literal naming requirements: agents 'named exactly "forecast agent"', a tool 'named exactly "DocumentDB aggregation tool"', 'use the phrase "agent memory" in the code', 'label the pipeline as an Orchestration implementation', 'a Single-agent application where a single process...', 'exact phrasing "Beanie ODM"', 'use the name "LlamaIndex" in the code'. The drafter reads the 'Agent type:' and 'Concepts:' lines of its input, and descriptive phrases in the prompt, as identifiers the code must contain. Confirmed in retail-04 ('single LangChain agent (no multi-agent orchestration)' derived from Agent type: Single-agent).

**Drafter rule:** The agent type, concept list and the prompt's descriptive phrases ('policy agent', 'DocumentDB aggregation tool', 'agent memory', 'Single-agent', 'Orchestration') describe roles and architecture, not identifiers: require the role or component to exist and behave as described, never that code, names or strings match that wording exactly.

### 18 files: Reviewer-verifiability and provenance padding: 'must include explicit citations / document ids / collection names and _ids in the payload', 'log or return the aggregation outputs and metric values so a reviewer can verify', 'all inter-agent messages logged as structured JSON', 'expose the exact matching logic', 'return raw results not only a summary'

Reviewer-verifiability and provenance padding: 'must include explicit citations / document ids / collection names and _ids in the payload', 'log or return the aggregation outputs and metric values so a reviewer can verify', 'all inter-agent messages logged as structured JSON', 'expose the exact matching logic', 'return raw results not only a summary'. The drafter writes for the auditor rather than for the prompt. Related to pattern 3 but distinct: it adds observability, not resilience.

**Drafter rule:** Do not require citations, provenance metadata, document ids in outputs, structured logging of intermediate results or exposed internals 'so a reviewer can verify' unless the prompt asks for them; the auditor reads the code, so a behaviour the code performs is already checkable.

### 18 files: Wrong or mis-targeted Azure DocumentDB facts, and client-side work where the prompt means database vector search: DiskANN described as index files written by the project; $text full-text query on DocumentDB (infeasible); 'binary embedding format' with binary similarity; 'DocumentDB Atlas-compat API'; 'Microsoft

Wrong or mis-targeted Azure DocumentDB facts, and client-side work where the prompt means database vector search: DiskANN described as index files written by the project; $text full-text query on DocumentDB (infeasible); 'binary embedding format' with binary similarity; 'DocumentDB Atlas-compat API'; 'Microsoft.DocumentDB/mongoClusters' or 'MongoDB API' used as the connection target; cosine similarity computed in service code when the prompt says vector search (contradicts_prompt); and the converse omission - no bullet requiring the cosmosSearch vector index to be created (the 4 'missing' items). The INSTRUCTIONS constant gives the drafter no feature vocabulary, so it borrows MongoDB Atlas/Cosmos DB RU idioms.

**Drafter rule:** Vector search in Azure DocumentDB means a cosmosSearch index of kind vector-ivf, vector-hnsw or vector-diskann on the embedding field, created in code and queried with $search/cosmosSearch (similarity COS, L2 or IP); full-text search uses a search index created with createSearchIndexes and $search, never $text; there is no Atlas API, no 'binary embedding' option and no client-side similarity when the prompt says vector search; whenever the prompt names vector search, include one bullet requiring that index to be created with dimensions matching the embedding model.

### 10 files: 'Configurable' knobs invented as requirements: configurable top-N, batch size, chunk size and overlap, retry count, thresholds, moving-average window, TTL timeout, pause/backoff between bulk chunks

'Configurable' knobs invented as requirements: configurable top-N, batch size, chunk size and overlap, retry count, thresholds, moving-average window, TTL timeout, pause/backoff between bulk chunks. The prompt gives a fixed behaviour; the drafter requires a parameter for it.

**Drafter rule:** Do not require a value to be configurable, parameterised or exposed as a setting unless the prompt says so; a constant in code satisfies a prompt that gives no parameter.

## Per-file issues

Each line is a bullet the second reviewer upheld, with the proposed fix. `delete` means remove the bullet.

### banking-01 (minor_edits, 10 bullets)

- **not_in_prompt**: Build counterparty chains by following transaction document references (transaction reference fields) using graph-like aggregation (e.g., a $graphLookup-style stage) with a configurable max traversal depth, returning ful
  - why: The prompt says the tool 'follows transaction document references to build counterparty chains'; it does not ask for a configurable max traversal depth or for returning 'reference paths'. (The skills list $lookup as supported and say advanced stages may have partial support, so the $graphLookup-styl
  - fix: Build counterparty chains by following transaction document references across documents using aggregation (e.g., a $graphLookup-style or iterative $lookup pipeline), returning the chain of linked transaction documents.
- **not_in_prompt**: Ensure the aggregation pipeline preserves key transaction fields needed for analysis (at minimum: transactionId, from/to party IDs, amount, timestamp, and reference fields) in the returned chain documents so the agent ca
  - why: The prompt names no document schema; the 'at minimum' field list is invented, and citing source documents is only implied by the narrative requirement already covered in a later bullet.
  - fix: delete
- **not_in_prompt**: Provide an example script or notebook that demonstrates end-to-end usage: seeding or querying sample transactions, invoking the LangChain agent which calls the DocumentDB aggregation tool, and printing the aggregation re
  - why: The prompt does not ask for an example script or notebook; sample data and run instructions are covered by the shared 'gallery sample also needs' section (seed script, README).
  - fix: delete
- **duplicate**: Connect the DocumentDB aggregation tool to Azure DocumentDB (transactions collection) via configurable connection parameters so the tool can run live aggregations against the cluster.
  - why: The previous bullet already requires the tool to execute aggregation pipelines against Azure DocumentDB; this restates it, and the 'transactions collection' name is not in the prompt.
  - fix: delete

### banking-02 (minor_edits, 10 bullets)

- **not_in_prompt**: Initialize Beanie against an Azure DocumentDB MongoDB-compatible endpoint (async Motor client + Beanie init), with connection configuration clearly visible in the code.
  - why: The prompt names Beanie ODM, not Motor; the documentdb-connection skill says new Python async code should use PyMongo's AsyncMongoClient, not Motor, so mandating Motor pins a driver the prompt did not name and the skill discourages. 'Connection configuration clearly visible in the code' also reads a
  - fix: Initialize Beanie (init_beanie) against an Azure DocumentDB endpoint using an async client, with the connection string supplied through configuration.
- **not_in_prompt**: From MT103 and MT202 messages extract and map standard fields into the document model at minimum: transaction reference (field 20), value date/currency/amount (field 32A), ordering customer (field 50A/50K), beneficiary/c
  - why: The prompt asks to parse MT103/MT202 fields into structured documents; it does not ask to store the raw message or a received_at timestamp.
  - fix: From MT103 and MT202 messages extract and map standard fields into the document model, at minimum: transaction reference (field 20), value date/currency/amount (field 32A), ordering customer (field 50A/50K), beneficiary (field 59), and instructing/receiving agents where present (e.g., 52/53/54).
- **not_in_prompt**: Implement async batch collection and bulk-writes batches for throughput: accumulate parsed documents into configurable batches and perform async bulk insert operations (via Beanie insert_many or by calling the underlying
  - why: The prompt asks for bulk-writing batches for throughput; a configurable batch size and a flush interval are not in the prompt, and 'Motor collection' again names a driver the prompt does not.
  - fix: Accumulate parsed documents into batches and persist each batch with an async bulk insert (Beanie insert_many or the underlying collection's bulk/insert API) rather than one insert per message.
- **not_in_prompt**: The aggregation result must include counts and summed amounts; if multiple currencies exist, the endpoint must return totals broken down by currency (i.e., group by date + message_type + currency) so totals are unambiguo
  - why: The prompt asks for daily volume and total value by message type; a per-currency breakdown is not asked for, and counts/sums are already required by the previous bullet.
  - fix: delete
- **duplicate**: Ensure bulk write operations target Azure DocumentDB collections and are performed as efficient bulk/unordered inserts (i.e., use insert_many/unordered bulk write options) so throughput behavior is testable.
  - why: Restates the previous bullet's bulk-insert requirement; 'unordered' is an implementation choice the prompt does not state.
  - fix: delete

### banking-03 (minor_edits, 11 bullets)

- **not_in_prompt**: Includes a demonstrable example or script in the sample showing a successful transaction commit and a retry with the same transactionRef that does not double-post (verifiable by inspecting the transaction and account sna
  - why: The prompt asks the ledger to prevent double-posting; it does not ask for a demonstration script. Verification belongs to the shared section (seed script, unit tests).
  - fix: delete
- **duplicate**: Stores account balance as a separate snapshot document and updates that snapshot within the transaction to reflect the new balance after applying the inserted transaction.
  - why: The previous bullet already requires inserting the transaction document and updating the account balance snapshot document inside the same multi-document transaction.
  - fix: delete

### banking-04 (minor_edits, 10 bullets)

- **not_in_prompt**: Include a data-extraction agent named "data-extraction agent" that queries multiple DocumentDB collections for a provided reporting period parameter and returns the combined dataset.
  - why: The prompt describes the agent's role ('a data-extraction agent'); it does not require that literal name in code.
  - fix: Include a data-extraction agent that queries multiple Azure DocumentDB collections for a given reporting period and returns the extracted data.
- **not_in_prompt**: Implement a validation agent named "validation agent" that programmatically checks completeness (e.g., required fields present) and applies business rules (at least one rule implemented, e.g., totals reconciliation or cr
  - why: The literal name 'validation agent' is not required by the prompt, and the summary format (pass/fail counts, detailed failure records) is invented.
  - fix: Implement a validation agent that checks completeness (e.g., required fields present) and applies at least one business rule, returning a validation result the orchestrator can act on.
- **not_in_prompt**: Implement a filing agent named "filing agent" that transforms the validated data into the required regulatory schema (produce a final payload that matches the target schema in code) and returns the formatted output.
  - why: The literal name 'filing agent' is not required by the prompt.
  - fix: Implement a filing agent that formats the validated data into the required regulatory schema defined in code and returns the formatted output.
- **not_in_prompt**: The filing agent must persist the formatted regulatory output (the final payload) into Azure DocumentDB (store into a DocumentDB collection or return it alongside a persisted record).
  - why: The prompt says the filing agent formats the output to the regulatory schema; only the orchestrator's workflow document is said to be written to DocumentDB. The 'or return it alongside a persisted record' alternative also makes the bullet uncheckable.
  - fix: delete
- **not_in_prompt**: The orchestrator must log each step's status as a workflow document in DocumentDB: for each agent run include agent name, step start and end timestamps, status (success/failure), error messages if any, and pointers to th
  - why: The prompt asks the orchestrator to log each step's status as a workflow document; timestamps and pointers to input/output documents are invented detail.
  - fix: The orchestrator logs each step's status as a workflow document in Azure DocumentDB, with one entry per agent step recording the step, its status (success/failure) and any error.
- **not_in_prompt**: Provide code examples or test scripts that demonstrate the full run: supplying a reporting period parameter, executing data extraction across multiple DocumentDB collections, running validation rules, producing the regul
  - why: The prompt does not ask for demonstration scripts or tests; those belong to the shared section (unit tests, README, seed script).
  - fix: delete
- **duplicate**: If the validation agent reports failures, the orchestrator must record the failure and halt the filing step; the workflow document must include the validation failure details.
  - why: Halting on failure is already covered by the bullet requiring the orchestrator to proceed only when the previous agent reports success, and recording failure is covered by the workflow-document bullet.
  - fix: delete

### banking-05 (minor_edits, 10 bullets)

- **not_in_prompt**: Provide code that caches the rolled-up summary documents in Azure DocumentDB by writing/upserting documents into a dedicated collection (e.g., branch_summaries) keyed by branch_id and containing transaction_volume, avera
  - why: The prompt says only "Cache rolled-up summary documents in DocumentDB". A last_updated timestamp is not asked for, and the field names are prescribed as mandatory rather than as examples.
  - fix: Provide code that caches the rolled-up summary documents in Azure DocumentDB by writing/upserting one document per branch into a dedicated collection (e.g., branch_summaries), each holding that branch's transaction volume, average ticket size and product mix.
- **duplicate**: Ensure the LangChain tool queries the branch_summaries collection (not raw transaction documents) when answering questions and that its implementation demonstrates retrieval of the cached fields (transaction_volume, aver
  - why: The preceding bullet already requires the LangChain tool to answer natural-language questions by querying the cached branch_summaries and returning a human-readable response; this restates it with extra field names.
  - fix: delete (or fold the clause "not the raw transaction documents" into the previous bullet)
- **vague**: Expose at least one endpoint that returns the cached summary document from the branch_summaries collection for a given branch_id (and clearly falls back to live aggregation only if implemented; the cached-read endpoint m
  - why: The parenthetical ("falls back to live aggregation only if implemented") is not a checkable condition and muddles what the reviewer must verify.
  - fix: Expose at least one endpoint that serves a branch's dashboard metrics from the cached summary documents rather than re-running the $facet aggregation on every request.

### banking-06 (minor_edits, 9 bullets)

- **not_in_prompt**: Add an LLM classification step that runs on create and on every valuation update and writes classification results into the document fields type and eligibilityTier before persisting the new version.
  - why: The prompt says "Add an LLM classification step that tags each asset by type and eligibility tier". It does not require re-classification on every valuation update; a sample that classifies once per asset would satisfy the prompt but fail this line.
  - fix: Add an LLM classification step that tags each collateral asset by type and eligibility tier and stores the resulting type and eligibility-tier fields on the persisted asset document(s).
- **not_in_prompt**: Provide an HTTP endpoint that returns the full audit history (all versions) for a given assetId by querying Azure DocumentDB and ordering by version or createdAt.
  - why: The prompt names only one endpoint (the aggregation endpoint). The description's "full audit history" is already covered by the bullet that requires every update to be persisted as a new retained document; an extra history endpoint is invented.
  - fix: delete
- **not_in_prompt**: Include tests or example requests demonstrating: creating an asset, performing a valuation update that creates a new version and receives type and eligibilityTier tags, retrieving that asset’s audit history, and calling 
  - why: The prompt does not ask for tests or example requests; testing is covered by the shared "What a gallery sample also needs" section, and this bullet also depends on the invented history endpoint.
  - fix: delete

### banking-07 (needs_rework, 10 bullets)

- **not_in_prompt**: The underwriting agent must perform an affordability assessment and return a structured result containing at minimum: an affordability decision (approve/decline/conditional), numeric metrics (e.g., income, monthly debt, 
  - why: The prompt says only that the underwriting agent "assesses affordability". The three-way decision vocabulary, numeric metrics such as DTI, and a rationale field are invented detail an auditor would check literally.
  - fix: The underwriting agent assesses affordability from the application's financial fields and returns its assessment in a structured form that the compliance and comms agents consume.
- **not_in_prompt**: The comms agent must generate a decision letter text (string) that incorporates the final decision, the key reasons from underwriting and compliance, and clear next steps for the applicant; the letter must be returned as
  - why: The prompt says the comms agent "drafts the decision letter". Requiring "clear next steps for the applicant" adds content the prompt does not ask for.
  - fix: The comms agent drafts a decision letter (text) that states the decision and reflects the underwriting and compliance results, and the letter is returned as part of the agent's output.
- **not_in_prompt**: The orchestrator must combine the original application id, underwriting assessment, compliance report, comms decision letter, a final pipeline decision/status, agent identifiers, and timestamps into a single outcome obje
  - why: "Agent identifiers" and "timestamps" are not in the prompt ("Write the outcome back to DocumentDB"); the prompt only implies the outcome includes the agents' results and the decision.
  - fix: The orchestrator assembles a single outcome containing the application identifier, the underwriting assessment, the compliance result, the drafted decision letter and the final decision.
- **not_in_prompt**: If any agent produces an error or a failing outcome, the orchestrator must set and persist an appropriate final decision/status (e.g., declined, needs-follow-up) and include error or failure details in the stored outcome
  - why: The prompt says nothing about error handling or failure statuses; this is an invented requirement.
  - fix: delete
- **not_in_prompt**: Each agent implementation and the orchestrator must expose or record the agent inputs and outputs (structured data) so a reviewer can inspect the prompt/response exchange in the Node.js LangChain multi-agent logs or the 
  - why: Logging or exposing every agent's prompt/response exchange is not asked for by the prompt; the "or the saved outcome object" alternative also overlaps the outcome bullet. The phrase "Node.js LangChain multi-agent logs" is not a checkable artefact.
  - fix: delete

### banking-08 (minor_edits, 10 bullets)

- **not_in_prompt**: Define explicit maturity bucket boundaries in code or config (e.g., 0-1y, 1-3y, 3-5y, 5y+) and use those exact definitions in the aggregation pipeline so each position is assigned to a bucket by the DocumentDB query.
  - why: The prompt asks for a tool that "groups fixed and floating rate positions by maturity bucket"; it does not require the pipeline to compute the bucket from boundaries. A sample whose position documents carry a maturity_bucket field and group on it meets the prompt but fails this line. The grouping-in
  - fix: Maturity buckets are defined explicitly (as boundaries in code/config or as a stored bucket field on each position) and the aggregation pipeline groups positions by that bucket.
- **not_in_prompt**: Have the aggregation pipeline return numeric aggregates needed for NII calculations for each (rate type, maturity bucket) group: total balance, weighted-average interest rate, and count of positions.
  - why: The prompt does not name the aggregates; "weighted-average interest rate" and "count of positions" are specific invented outputs. Only some balance and rate measure per group is implied by the NII reasoning.
  - fix: Have the aggregation pipeline return, for each (rate type, maturity bucket) group, numeric aggregates (at least a total balance and a rate measure) that the LLM uses for its NII reasoning.
- **not_in_prompt**: Require the agent to return a machine-readable structured scenario analysis report (JSON) containing, for each scenario and maturity bucket: scenario name, bucket name, rate type, baseline NII, shocked NII, absolute delt
  - why: The prompt asks for "a structured scenario analysis report". Mandating JSON and this exact eight-field schema per scenario and bucket is invented detail.
  - fix: The agent returns the scenario analysis as a structured report (e.g., JSON or a typed model, not free prose) that covers the parallel shift, steepening and inversion scenarios and states the NII impact of each.
- **duplicate**: Include a small set of sample position documents and a script or instructions to insert them into Azure DocumentDB so the demo aggregation returns both fixed and floating positions across the defined maturity buckets.
  - why: The prompt does not ask for sample data; seed data is already covered by the shared "A seed script loads sample data" line in the gallery section.
  - fix: delete

### banking-09 (minor_edits, 10 bullets)

- **not_in_prompt**: Each transition event appended to eventLog must include at least: fromState, toState, timestamp, and a reason/actor field so reviewers can verify transitions are logged with those attributes.
  - why: The prompt says only 'log each transition'. From/to state and a timestamp are what a transition log is; a 'reason/actor' field is an added requirement the prompt does not state.
  - fix: Each logged transition records at least the previous state, the new state and a timestamp.
- **not_in_prompt**: When the change stream detects a state change to "failed", trigger an exception workflow implemented in the app; the workflow must perform a verifiable side effect in Azure DocumentDB (for example, insert an "Exception" 
  - why: The prompt says 'trigger an exception workflow' without saying what it does or where its output goes; requiring a write to Azure DocumentDB would fail a build whose workflow logs, enqueues or notifies instead.
  - fix: When the change stream detects a state change to "failed", the handler invokes an exception workflow in the app (a function that receives the failed trade and performs an observable action, such as writing an exception record, logging or enqueuing a notification).
- **not_in_prompt**: Provide a replay/reconstruction function that derives a trade's current state by replaying its eventLog (demonstrable via a unit test or an endpoint), showing the system implements event-sourcing semantics for trade stat
  - why: Neither the prompt, title nor description asks for state replay or reconstruction; the prompt asks to model the trade as a state machine document and log each transition, which other bullets already cover.
  - fix: delete
- **duplicate**: Within that transaction, atomically push a transition event into eventLog and update the trade's state in the same transaction so the state change and its event are committed together.
  - why: Repeats the previous bullet's 'atomically update the trade's state ... within the same transaction'; the only new content (the log write happens in the same transaction) belongs in that bullet, which currently says only 'perform other writes'.
  - fix: Merge into the previous bullet: 'Implement a state-transition function in Node.js using Mongoose that opens a session (startSession) and uses a transaction (session.withTransaction or equivalent) to update the trade's state and append the transition log entry in the same transaction.'

### banking-10 (minor_edits, 10 bullets)

- **not_in_prompt**: Index a corpus of wealth management research documents into a DocumentDB vector store: ingestion code must create embeddings and persist the index/vectors into Azure DocumentDB (the "DocumentDB vector store") with per-do
  - why: The prompt asks only to index research documents in a DocumentDB vector store; it says nothing about per-document metadata fields.
  - fix: Ingestion code embeds the wealth management research documents and persists the vectors into Azure DocumentDB as the LlamaIndex vector store.
- **not_in_prompt**: Implement a tool used by the agent that, given a client identifier, fetches that client's portfolio document from Azure DocumentDB and returns structured portfolio fields (positions, allocations, risk profile) to the age
  - why: The prompt says the tool 'fetches the client's portfolio document'; the specific fields (positions, allocations, risk profile) are invented and stated as required rather than as examples.
  - fix: Implement a tool, registered with the LlamaIndex agent, that given a client identifier fetches that client's portfolio document from Azure DocumentDB and returns its contents to the agent.
- **not_in_prompt**: The agent’s response routine must include explicit citations or references showing which retrieved research documents and which portfolio fields were used to form the answer (e.g., document IDs or metadata included in th
  - why: Neither the prompt, title nor description asks for citations or source references in the answer.
  - fix: delete
- **not_in_prompt**: Persist the LlamaIndex index and agent memory state back to Azure DocumentDB so that both the vector index and memory survive agent restarts and can be reloaded from Azure DocumentDB.
  - why: Persisting the vector index in DocumentDB is already the third bullet. The prompt asks for 'agent memory' but does not say where it is stored or that it must survive restarts; requiring memory in Azure DocumentDB adds a constraint the prompt does not state.
  - fix: delete

### banking-11 (needs_rework, 10 bullets)

- **contradicts_prompt**: On each review cycle, load sanctions list and adverse media documents (including their stored embeddings) from Azure DocumentDB and perform a vector similarity search in Python (e.g., cosine similarity) between the corre
  - why: The prompt stores the vectors in DocumentDB and 'searches against' them, and the description says the comparison is against watchlists 'stored in DocumentDB'; loading all documents and computing cosine similarity in Python bypasses DocumentDB vector search. The documentdb-vector-search skill says kN
  - fix: On each review cycle, for each correspondent run a vector similarity search in Azure DocumentDB (`$search` with `cosmosSearch` over a vector index on the embedding field) against the stored sanctions list and adverse media entries, returning the top N matches per source.
- **not_in_prompt**: Persist correspondent profiles, sanctions entries and adverse media documents in Azure DocumentDB using the MongoDB-compatible API via the pymongo driver; each stored document must include a metadata block and an "embedd
  - why: The prompt names Python and LangChain but not pymongo, a 'metadata block' or an 'embedding' field name; a build that stores vectors through LangChain's DocumentDB vector store integration would fail this bullet without violating the prompt.
  - fix: Persist correspondent profiles, sanctions list entries and adverse media entries in Azure DocumentDB with each entry's embedding vector stored on the document.
- **not_in_prompt**: Provide an upsert path for sanctions and adverse media entries that either accepts precomputed embeddings or computes embeddings via the LangChain embeddings component and stores them into Azure DocumentDB.
  - why: The prompt does not mention upserts or accepting precomputed embeddings; embedding and storing sanctions/adverse media entries is already covered by the second and third bullets.
  - fix: delete
- **not_in_prompt**: Configure the code to connect to a real Azure DocumentDB instance (Microsoft.DocumentDB/mongoClusters) via connection string/URI (not a file-backed mock), and ensure collections for correspondents, sanctions, and adverse
  - why: Connecting via a connection string is the shared gallery requirement ('The connection string ... come from environment variables'), and the collection names and 'automated' cycles are not in the prompt; persistence is already covered by the third bullet.
  - fix: delete

### banking-12 (minor_edits, 9 bullets)

- **not_in_prompt**: Use Node.js and Mongoose to connect to Azure DocumentDB: the code must call mongoose.connect(...) using a MongoDB URI read from an environment variable that clearly indicates Azure DocumentDB (e.g., AZURE_DOCUMENTDB_URI)
  - why: Reading the connection string from an environment variable is the shared gallery requirement, and the prompt says nothing about how the variable is named; only the Node.js + Mongoose part is traceable.
  - fix: The service is written in Node.js and uses Mongoose (mongoose.connect and Mongoose models) to read and write the audit documents in Azure DocumentDB.
- **not_in_prompt**: Create an index on paymentReference and a TTL index on the createdAt/timestamp field (using schema.index(..., { expireAfterSeconds: <env-configured value> })) so the TTL value is configurable via environment (e.g., AUDIT
  - why: The prompt, title and description never mention TTL or expiry; the description says the documents are immutable audit records 'for regulatory inspection', which auto-deleting them works against. The env-configured TTL value is likewise invented.
  - fix: Create an index on paymentReference to support the timeline lookup by payment reference.

### banking-13 (minor_edits, 10 bullets)

- **not_in_prompt**: Include a DocumentDB aggregation tool component, named or documented exactly as "DocumentDB aggregation tool", that connects to Azure DocumentDB and executes server-side aggregation pipelines (i.e., uses collection.aggre
  - why: The prompt asks for 'a DocumentDB aggregation tool' as a description of what the tool does; it does not require a literal name or doc string, so an auditor could wrongly fail a tool called e.g. aggregate_positions.
  - fix: Include a LangChain tool that connects to Azure DocumentDB and runs server-side aggregation pipelines (collection.aggregate with $group/$sum) to sum risk-weighted assets and capital elements, rather than summing client-side.
- **not_in_prompt**: The DocumentDB aggregation tool must read from the position documents and RWA documents (configurable collection names) in Azure DocumentDB and return aggregated totals in a single aggregation pipeline result.
  - why: Neither the prompt nor the description requires configurable collection names or that totals come back from a single pipeline; position and RWA documents may legitimately live in two collections summed by two pipelines or joined with $lookup/$unionWith.
  - fix: The aggregation tool reads position documents and RWA documents from Azure DocumentDB and returns the aggregated totals (one or more aggregation pipelines).
- **not_in_prompt**: The agent must return a machine-readable result (e.g., JSON or dict) containing at minimum: aggregated totals (RWA, CET1, total capital), computed ratios (CET1 ratio, total capital ratio), the Basel III threshold values 
  - why: The prompt and description ask for computed ratios and a board-ready narrative commentary; nothing asks for a JSON/dict result or for the thresholds to be echoed in a structured payload.
  - fix: The agent's output includes the aggregated totals and both computed ratios alongside the LLM commentary.
- **not_in_prompt**: The code must detect and handle missing or zero total RWA in the aggregation result: if RWA is zero or absent, the agent must not perform division and must include an explicit warning or caveat in both the structured out
  - why: Zero/missing RWA handling is sensible engineering but is not asked for by the prompt, title or description.
  - fix: delete
- **duplicate**: The LLM-generated commentary must include the LLM's reasoning or rationale (a short explanation of how the interpretation was reached, e.g., which thresholds were breached or met and by what margin) as part of the output
  - why: The previous bullet already requires the commentary to contain an interpretation of each ratio vs. the Basel III thresholds, which is the same 'which thresholds were met or breached' content.
  - fix: delete

### banking-14 (minor_edits, 10 bullets)

- **not_in_prompt**: Query Azure DocumentDB for unclassified complaints by selecting documents where product_category, root_cause, or urgency_tier are null/unset and load them for processing.
  - why: The prompt says 'reads unclassified complaint documents'; it does not prescribe that 'unclassified' means null classification fields. A sample using a status/classified flag would satisfy the prompt but fail this bullet.
  - fix: Query Azure DocumentDB through Beanie for complaint documents that have not yet been classified (e.g., classification fields unset or a status flag) and load them for processing.
- **not_in_prompt**: Generate an embedding for each complaint's text using a LangChain embedding call and store the resulting embedding vector in the Beanie document's embedding field in Azure DocumentDB.
  - why: The prompt says 'embeds the complaint text'; it does not require the embedding to go through a LangChain embeddings wrapper, so calling the embedding provider's SDK directly is a valid reading.
  - fix: Generate an embedding for each complaint's text and store the vector in the Beanie document's embedding field in Azure DocumentDB.
- **vague**: Implement a similarity search over stored embeddings that, given a complaint, returns the top-N most similar complaints (use cosine similarity or equivalent), relying on the stored embedding vectors (either via an applic
  - why: Allowing 'application-side similarity computation' means a sample that never uses DocumentDB's vector search still passes; the documentdb-vector-search skill says similarity search on Azure DocumentDB uses a cosmosSearch vector index queried with the $search / cosmosSearch aggregation stage, and tha
  - fix: Implement similarity search in Azure DocumentDB: create a cosmosSearch vector index on the embedding field and query it with the $search / cosmosSearch aggregation stage to return the top-k most similar complaints for a given complaint.

### banking-15 (minor_edits, 10 bullets)

- **not_in_prompt**: Implement the orchestration pipeline in Python using the LangChain framework and label the pipeline as an Orchestration implementation.
  - why: The prompt asks for a Python LangChain orchestration pipeline; it does not ask for any label, and 'label as an Orchestration implementation' is not a meaningful code check.
  - fix: Implement the orchestration pipeline in Python using LangChain.
- **not_in_prompt**: Define a Beanie document model that represents an onboarding application as a state machine document stored in Azure DocumentDB; the model must include a current_state field and an explicit set of states covering at leas
  - why: The prompt asks for a state machine document driven by three agents; the specific field name current_state and the exact state names are invented and would fail an otherwise correct sample that names its states differently.
  - fix: Define a Beanie document model that represents an onboarding application as a state machine document in Azure DocumentDB, with a current-state field and an explicit, enumerated set of states covering the ID-verification, risk-assessment and account-opening steps plus a terminal state.
- **not_in_prompt**: Include a transition history/log array on the state machine document; each logged transition must contain the agent name, outcome/status, timestamp, and optional detail payload.
  - why: The prompt says 'logging the transition' but does not say the log must be an array embedded on the document; a separate transitions collection is an equally valid reading.
  - fix: Log every state transition (as an array on the state machine document or in a transitions collection), each entry recording the agent, the outcome, and a timestamp.
- **not_in_prompt**: If an agent returns a failure/non-success result, the orchestrator must update the state machine document to a failure/rejected state and append a failure transition record before halting or following a defined error pat
  - why: Neither the prompt nor the description mentions failure or rejection handling.
  - fix: delete
- **duplicate**: Initialize Beanie with a Motor/Mongo client connected to Azure DocumentDB via a configurable MongoDB connection URI (i.e., repository contains connection configuration and Beanie.init usage).
  - why: The second bullet already requires Beanie ODM for all database interactions against Azure DocumentDB, and the shared section covers the connection string coming from configuration.
  - fix: delete
- **duplicate**: Ensure every state change and transition log entry is written to Azure DocumentDB (using Beanie methods or explicit atomic update operations) so the DocumentDB-hosted state machine is the single source of truth for the o
  - why: The atomic-update bullet already requires each step to set the new state and append the transition record in Azure DocumentDB; this restates it.
  - fix: delete

### banking-16 (minor_edits, 11 bullets)

- **not_in_prompt**: Implement a Node.js service that accepts ATM heartbeat JSON documents over an HTTP endpoint and writes them to Azure DocumentDB using Mongoose.
  - why: The prompt says the monitor 'receives status heartbeat documents from ATMs'; it does not specify HTTP. A queue consumer or in-process simulator feeding Mongoose writes satisfies the prompt but fails this bullet.
  - fix: Implement a Node.js service that receives ATM heartbeat documents (e.g., via an HTTP endpoint or ingest function) and writes them to Azure DocumentDB using Mongoose.
- **not_in_prompt**: Update the live network summary document atomically (e.g., using $inc and $set or a transaction) from change-stream handlers to avoid race conditions on concurrent events.
  - why: The prompt asks to 'maintain a live network summary document'; it does not ask for atomic $inc updates or race-condition handling. Prescribing $inc also penalises the simpler, more robust pattern of recomputing per-ATM latest status with an aggregation.
  - fix: Update the live network summary document from the change-stream handler so its counts reflect the latest known status of each ATM.
- **not_in_prompt**: When computed availability falls below the configurable threshold, create an alert record in Azure DocumentDB's alerts collection that includes timestamp, availability, threshold, and the summary snapshot; optionally als
  - why: The prompt says 'trigger alerts'; it does not require alerts to be stored in a DocumentDB alerts collection with a prescribed field set. Logging or a webhook alone would satisfy the prompt.
  - fix: When computed availability falls below the configurable threshold, trigger an alert (log, webhook, or alert document) that includes the timestamp, the computed availability, and the threshold.
- **not_in_prompt**: Implement resume/reconnect logic for the change stream (using resumeToken or automatic re-establishment) so the long-running watcher recovers from transient errors without losing events.
  - why: Resume tokens and reconnect logic are good practice but are not asked for by the prompt, title, or description.
  - fix: delete
- **not_in_prompt**: Provide a simple heartbeat sender or example script that posts sample heartbeats (including status transitions) to the service so a reviewer can reproduce status changes and verify summary updates and alerts.
  - why: The prompt does not ask for a sender script; the shared section's seed-script bullet already covers loading sample data.
  - fix: delete
- **duplicate**: Connect to Azure DocumentDB with a MongoDB-compatible connection string provided via configuration or environment variable and use that connection for all Mongoose operations.
  - why: The shared section already requires the connection string to come from environment variables and a single reused database client; the first bullet already requires Mongoose writes to Azure DocumentDB.
  - fix: delete

### banking-17 (minor_edits, 8 bullets)

- **not_in_prompt**: The scenario agent produces structured macroeconomic shock parameters (e.g., interest_rate_shift, fx_rate_changes, credit_spread_shift) as a JSON/dict containing a unique scenario_id and timestamp.
  - why: The prompt only says the scenario agent "generates macroeconomic shock parameters"; requiring the agent's output to carry a scenario_id and timestamp is an added detail a reviewer would fail a valid sample on.
  - fix: The scenario agent produces structured macroeconomic shock parameters (e.g., interest_rate_shift, fx_rate_changes, credit_spread_shift) as a JSON/dict that the impact agent consumes.
- **not_in_prompt**: The impact agent returns both per-position impact documents and aggregated statistics (total P&L, counts by asset class) that the reporting agent can consume.
  - why: "Counts by asset class" is not in the prompt ("compute P&L impacts"); the handoff to the reporting agent is the only traceable part and it largely repeats the previous impact-agent bullet.
  - fix: The impact agent returns its computed P&L impact results in a structured form that the reporting agent consumes.
- **not_in_prompt**: The reporting agent synthesises a structured stress test report (JSON/dict) that includes scenario metadata, aggregate P&L (total, mean, percentiles), per-asset-class breakdown, and a list of top-N worst positions, and r
  - why: The prompt asks for "a structured stress test report"; percentiles, a per-asset-class breakdown and a top-N worst-positions list are invented contents.
  - fix: The reporting agent synthesises a structured stress test report (JSON/dict) from the scenario parameters and the impact agent's P&L results, and returns it programmatically.
- **not_in_prompt**: All scenario runs — including the scenario parameters, raw impact results, aggregated statistics, and the final report — are persisted as Azure DocumentDB documents in an audit collection (each stored document contains s
  - why: The prompt says "Store all scenario runs as DocumentDB documents for audit"; the parenthetical field list (scenario_id, timestamp, references/counts of affected positions) is not stated.
  - fix: Every scenario run — the scenario parameters, the impact results and the final report — is persisted as Azure DocumentDB document(s) in an audit collection.
- **not_in_prompt**: The codebase includes an executable example or test that runs the orchestrator end-to-end for at least one scenario, demonstrates the aggregation query against a positions collection, shows the generated report, and veri
  - why: The prompt does not ask for an end-to-end example or test; running the sample and tests are covered by the shared gallery section (README run instructions, unit tests).
  - fix: delete

### banking-18 (minor_edits, 10 bullets)

- **not_in_prompt**: For each candidate the agent must produce a recommended action derived from the computed confidence (e.g., thresholds that map to "clear", "review", "block") and include the rationale used to decide that action.
  - why: The prompt asks for a report "with match confidence and recommended action"; a rationale per action is not requested.
  - fix: For each candidate the agent produces a recommended action derived from the computed match confidence (e.g., thresholds mapping to "clear", "review", "block").
- **not_in_prompt**: The screening endpoint/agent response must return a structured screening report (machine-readable, e.g., JSON/dict) that, for each candidate, includes DocumentDB id, matched fields, matching method(s), raw similarity and
  - why: The prompt specifies a "structured screening report with match confidence and recommended action"; matched fields, raw regex details and source sanctions entry text are invented, and the method(s)/score parts repeat the consolidation and scoring bullets.
  - fix: The agent returns a structured, machine-readable screening report (JSON/dict) listing each candidate match with its match confidence and recommended action.
- **not_in_prompt**: Provide an example or test that exercises the complete pipeline (ingest sanctions list into Azure DocumentDB vector index, submit a screening request, run both vector search and $regex-based fuzzy matching, consolidate a
  - why: The prompt does not ask for an end-to-end example or test; running the sample and tests are covered by the shared gallery section.
  - fix: delete

### banking-19 (minor_edits, 10 bullets)

- **not_in_prompt**: Compute and persist a historical centroid per employee in Azure DocumentDB: code computes the mean of an employee’s historical embeddings, stores that centroid document keyed by employee id and history window, and update
  - why: The prompt says the nightly job compares against "their own historical centroid"; persisting a centroid document keyed by history window and updating it as history grows is not stated (a centroid computed at comparison time would satisfy the prompt).
  - fix: Compute a historical centroid per employee as the mean of that employee's historical embeddings, and use it in the nightly comparison.
- **not_in_prompt**: Flag and persist alerts when deviations exceed configurable thresholds: on significant deviation, code writes an alert record into Azure DocumentDB including employee id, timestamp, similarity/distance scores, which prof
  - why: The prompt says "flagging significant deviations"; writing alert records into DocumentDB with this specific field list is an added requirement.
  - fix: Flag employees whose recent embedding deviates significantly from their historical centroid or matches a known anomaly profile, recording the employee id and the deviation/similarity score for each flag.
- **duplicate**: Expose comparison parameters as configurable settings (distance metric and threshold values) so a reviewer can change thresholds and reproduce different flagging outcomes.
  - why: Configurable thresholds already appear in the previous alerting bullet, and a configurable distance metric is not something the prompt asks for.
  - fix: delete

### banking-20 (minor_edits, 9 bullets)

- **not_in_prompt**: Implement a daily schedule that invokes the batch processor once per day (e.g., cron or timer) and is configurable for the run time.
  - why: The prompt says "runs on a daily schedule"; a configurable run time is not requested.
  - fix: Implement a daily schedule (e.g., cron or timer) that invokes the batch processor once per day.
- **not_in_prompt**: Chunk bulkWrite operations into configurable maximum bulk sizes and include a configurable pause/backoff between bulk chunks to provide controlled throughput to Azure DocumentDB.
  - why: The description says "controlled throughput" and the prompt "maximum throughput"; neither asks for a pause/backoff between chunks, and a reviewer would fail a sample that controls throughput only by bounding chunk size.
  - fix: Bulk writes are issued in bounded chunks (a maximum number of journal documents per bulkWrite call) so write throughput to Azure DocumentDB is controlled.
- **duplicate**: Process accounts in configurable batches (batch size parameter) so the processor works on bounded groups of documents per iteration.
  - why: Cursor-paginated batch retrieval is already required by the previous bullet; this only adds a configurable batch size, which the prompt does not state.
  - fix: delete
- **duplicate**: Ensure the implementation uses streaming/pagination semantics so memory usage remains bounded (no accumulation of all account documents in memory before writing).
  - why: Restates the cursor-pagination bullet ("retrieved in cursor-paginated batches rather than loaded all at once").
  - fix: delete

### customer-360-01 (minor_edits, 9 bullets)

- **not_in_prompt**: Define a Mongoose schema for the canonical customer profile that includes a top-level stable customerId field and create a unique index on customerId to drive identity resolution.
  - why: The prompt says "Use a stable customerId for identity resolution"; it never asks for a unique index. A sample that upserts keyed on customerId without declaring unique: true meets the prompt but would fail this bullet.
  - fix: Define a Mongoose schema for the canonical customer profile with a top-level stable customerId field that is the key used for identity resolution (the upsert filter).
- **duplicate**: Use atomic MongoDB update semantics (upsert + $set) to handle concurrent updates safely rather than replacing whole documents.
  - why: Upsert + $set without document replacement is already required by the two preceding bullets; the added "handle concurrent updates safely" claim is not in the prompt and is not something a reviewer can check in code.
  - fix: delete

### customer-360-02 (needs_rework, 10 bullets)

- **not_in_prompt**: Implement the service in Node.js and connect to Azure DocumentDB using the MongoDB Node.js driver.
  - why: The prompt names only "a Node.js event ingestion service"; it does not name the raw MongoDB Node.js driver (Mongoose's bulkWrite would also satisfy the prompt).
  - fix: Implement the service in Node.js and connect it to Azure DocumentDB with a MongoDB-compatible Node.js driver or ODM.
- **not_in_prompt**: Expose an HTTP endpoint (e.g., POST /events) that accepts customer behavioural events containing at minimum customerId, eventId, type (pageView|click|purchase), and timestamp, and returns an immediate 2xx on receipt.
  - why: The prompt says the service "receives customer behavioural events (page views, clicks, purchases)"; it does not specify HTTP, a timestamp field, or an immediate 2xx response. A queue/stream consumer would meet the prompt but fail this bullet.
  - fix: Provide an intake path (for example an HTTP endpoint or stream consumer) that receives customer behavioural events (page views, clicks, purchases), each carrying a customerId and an eventId.
- **not_in_prompt**: Buffer incoming events into batches and flush them with unordered bulk operations using collection.bulkWrite(operations, { ordered: false }) to maximize throughput; batch size and flush interval must be configurable.
  - why: "Unordered bulk operations for throughput" is in the prompt; configurable batch size and flush interval are not (and the same configuration is repeated in the last bullet).
  - fix: Write events to Azure DocumentDB in batches using unordered bulk operations (bulkWrite with { ordered: false } or equivalent) for throughput.
- **not_in_prompt**: Create a composite unique index on (customerId, eventId) with unique: true on the Azure DocumentDB collection at service startup (createIndex or equivalent) to provide deduplication.
  - why: The index itself is in the prompt; "at service startup" is not, and a seed/setup script creating the index would wrongly fail this bullet.
  - fix: Create a compound unique index on { customerId: 1, eventId: 1 } (unique: true) on the events collection, in the service or a setup script, so duplicate events are rejected.
- **not_in_prompt**: Provide a simple simulation or load-test script that emits high-throughput events (including duplicates) to the ingestion endpoint and verifies that unordered bulkWrite is used and duplicates are deduplicated by the comp
  - why: Neither the prompt nor the description asks for a load-test or simulation script; this invents a component.
  - fix: delete
- **not_in_prompt**: Ensure the service creates the target collection (or verifies it exists) before performing bulk writes or opening the change stream.
  - why: Nothing in the prompt, title or description asks for collection creation or existence checks.
  - fix: delete
- **not_in_prompt**: Expose configuration for the Azure DocumentDB connection string, collection name, batch size and flush interval in code or config constants so reviewers can run the service against an Azure DocumentDB instance.
  - why: Not in the prompt; configuration via environment variables is already covered by the shared gallery section, and "in code or config constants" conflicts with that section's env-var rule.
  - fix: delete
- **not_checkable**: On each insert change event, invoke an asynchronous profile update job handler (e.g., call a profileUpdateHandler function or enqueue a job) passing the event's customerId and payload; do not perform long synchronous wor
  - why: Triggering a downstream profile update job is in the prompt; "do not perform long synchronous work" is not, and "long" has no checkable threshold.
  - fix: On each insert change event, trigger a downstream profile update job (for example call a handler or enqueue a job) with the event's customerId and payload.

### customer-360-03 (minor_edits, 10 bullets)

- **not_in_prompt**: The channel agent reads the customer's preference documents from Azure DocumentDB and returns a single optimal contact channel (e.g., "email", "sms", "push") along with the preference document id used.
  - why: The prompt asks the channel agent to select the optimal channel from preference documents; it does not ask it to return the preference document id.
  - fix: The channel agent reads the customer's preference documents from Azure DocumentDB and returns a single optimal contact channel (e.g., "email", "sms", "push").
- **not_in_prompt**: The timing agent analyzes customer interaction timestamps (sourced from Azure DocumentDB history or preference documents) and returns the best send time as an ISO 8601 timestamp (or a consistent datetime object) for the 
  - why: The prompt only says "a timing agent determines the best send time"; it does not say the agent must analyze interaction timestamps or where it sources them.
  - fix: The timing agent determines the best send time for the customer and returns it as a timestamp or datetime value the orchestrator can store.
- **not_in_prompt**: The NBA recommendation object created by the orchestrator must include at minimum: customer_id, recommended_action, action_scores (from propensity agent), channel (from channel agent), send_time (from timing agent), and 
  - why: A created_at field is not asked for by the prompt; the other fields trace to the three agents' outputs.
  - fix: The NBA recommendation document written by the orchestrator includes at minimum the customer identifier, the recommended action, the propensity scores, the selected channel and the send time.
- **not_in_prompt**: The orchestrator writes the NBA recommendation document into Azure DocumentDB (e.g., a recommendations collection) and returns the inserted document id or the stored document as proof of persistence.
  - why: The write is in the prompt; the return-value requirement ("inserted document id or stored document as proof") is not.
  - fix: The orchestrator writes the combined NBA recommendation document to an Azure DocumentDB collection.
- **not_in_prompt**: Agents must exchange structured data (e.g., Python dicts/JSON) so the orchestrator can combine outputs programmatically, rather than relying on free-form text parsing of agent responses.
  - why: The prompt says the orchestrator "combines the outputs"; it does not prescribe structured versus text exchange, and the propensity bullet already requires structured scores.
  - fix: delete
- **not_in_prompt**: Provide an executable example (entrypoint or script) that runs the orchestrator for a sample customer_id, prints the final NBA recommendation, and demonstrates retrieving the stored recommendation from Azure DocumentDB.
  - why: An entrypoint follows from "build a ... system", but reading the stored recommendation back is not asked for.
  - fix: Provide an entrypoint or script that runs the orchestrator for a sample customer id and outputs the resulting NBA recommendation.
- **duplicate**: All reads and writes against customer history and preference documents are performed against Azure DocumentDB (the service) and visibly reference the history and preference document collections in the code.
  - why: Already covered by the propensity-agent bullet (history from Azure DocumentDB), the channel-agent bullet (preference documents from Azure DocumentDB) and the orchestrator write bullet.
  - fix: delete

### customer-360-04 (minor_edits, 10 bullets)

- **not_in_prompt**: The aggregation pipeline must accept a customer identifier (customer_id) and optional time-range parameters, and use $match to filter event documents for that customer and range.
  - why: The prompt asks to reconstruct "a customer's journey"; time-range parameters are not mentioned.
  - fix: The aggregation pipeline accepts a customer identifier and uses $match to filter touchpoint event documents to that customer.
- **not_in_prompt**: The aggregation result returned by the DocumentDB aggregation tool must include, for each touchpoint event, at minimum: timestamp, channel, event_type, and a metadata/object field for additional attributes.
  - why: The prompt names timestamp and channel as the sort/group fields; event_type and a metadata object are invented field requirements.
  - fix: The aggregation result returned by the tool includes, for each touchpoint event, at minimum its timestamp and channel.
- **not_in_prompt**: Produce a visual timeline view (for example an HTML timeline endpoint or file) that renders the reconstructed journey grouped by channel and annotated with timestamps and event labels, derived directly from the aggregati
  - why: Only the description's word "visualise" supports this; the prompt asks for a structured timeline in the prompt and a plain-language summary. The specific HTML rendering grouped by channel with event labels is not asked for anywhere.
  - fix: Provide a human-readable rendering of the reconstructed journey timeline (the description asks to visualise it), such as a console, Markdown or HTML timeline built from the aggregation results.
- **not_in_prompt**: Provide a runnable example or script that performs an end-to-end run: query a sample customer_id, call the DocumentDB aggregation tool, feed the structured timeline to the LlamaIndex agent, and output both the visual tim
  - why: The end-to-end run is a fair reading of the prompt, but the required assertions (chronological order, at least one inflection point) are test requirements the prompt does not state.
  - fix: Provide a runnable example that, for a sample customer id, calls the DocumentDB aggregation tool, feeds the structured timeline to the LlamaIndex agent and outputs the plain-language journey summary.
- **duplicate**: The generated plain-language summary must identify and highlight demonstrable inflection points such as channel switches, conversion events (e.g., purchase or signup), and significant inactivity or sudden changes in enga
  - why: The preceding bullet already requires the summary to highlight key inflection points; this one only adds example categories the prompt does not define.
  - fix: delete

### customer-360-05 (minor_edits, 10 bullets)

- **not_in_prompt**: Retrieve existing behavioural embeddings stored in Azure DocumentDB for each customer and combine those behavioural embeddings with the computed RFM metrics to form a single feature vector per customer
  - why: The prompt says to compute RFM scores and "embed the resulting feature vectors"; nothing in the prompt or description says pre-existing behavioural embeddings are already stored in DocumentDB and must be retrieved and concatenated. The description's "behavioural embeddings" are what this pipeline pr
  - fix: Build a per-customer feature vector from the computed RFM scores; this feature vector is the input to the embedding step.
- **not_in_prompt**: Include an executable example or test script that demonstrates the pipeline end-to-end for at least one customer id and prints the churn risk narrative and recommended retention action produced by the Python LangChain ag
  - why: The prompt does not ask for a demo or test script; run instructions, seed script and tests are covered by the shared "What a gallery sample also needs" section.
  - fix: delete
- **duplicate**: The agent must, for a given customer id or list of customer ids, run the full flow (DocumentDB aggregations -> combine with behavioural embeddings -> embed feature vector -> store in DocumentDB vector index -> retrieve s
  - why: Restates bullets 1-8 as a single flow (bullet 1 already says the agent orchestrates the end-to-end pipeline) and repeats the unsupported "combine with behavioural embeddings" step. The only new, checkable content is the per-customer entry point.
  - fix: The agent accepts a customer id (or list of ids) and returns a churn risk narrative and a recommended retention action for each customer.

### customer-360-06 (minor_edits, 9 bullets)

- **not_in_prompt**: Define one Mongoose model (single collection) for all channels (e.g., "interactions") with required fields channel (String), customerId (String), timestamp (Date) and a flexible field for channel-specific payload (Mixed/
  - why: The prompt names only channel, customerId and timestamp fields; a "flexible field for channel-specific payload (Mixed/Map)" is not asked for and would fail a build that models channel payloads with typed subdocuments.
  - fix: Define one Mongoose model (single collection) for all channels with required fields channel, customerId and timestamp (Date); documents for web, mobile, email and call centre are all stored in this collection.
- **not_in_prompt**: Create compound indexes on the schema using schema.index(...) for { customerId: 1, timestamp: -1 } and { channel: 1, timestamp: -1 } so the compound indexes exist in Azure DocumentDB.
  - why: The prompt asks for compound indexes on (customerId, timestamp) and (channel, timestamp) without specifying sort direction or the Mongoose API; a build using timestamp: 1 or createIndex() satisfies the prompt but would fail this bullet.
  - fix: Create compound indexes on (customerId, timestamp) and (channel, timestamp) (e.g. via schema.index()) so both compound indexes exist in Azure DocumentDB.
- **not_in_prompt**: Implement an HTTP ingestion endpoint that validates and writes interaction documents into the single collection, enforcing presence and types of channel, customerId and timestamp and storing timestamp as a Date/ISODate.
  - why: The prompt names the endpoints to expose (paginated history and channel-breakdown aggregation); it says the service stores interaction documents but does not ask for an HTTP ingestion endpoint or input validation.
  - fix: Provide a write path (endpoint, module or seed) that stores interaction documents with channel, customerId and timestamp (stored as a Date) in the single collection.
- **duplicate**: Ensure the paginated history query builds a Mongo query that includes the customerId (when provided) or channel (when provided) plus a timestamp range filter so the query can use the appropriate compound index, and imple
  - why: Filtering by customerId or channel, pagination and sorting by timestamp are already required by the previous bullet; the only new content is index alignment.
  - fix: The history query's filter and sort fields form a prefix of one of the compound indexes (customerId or channel, then timestamp), so the query can use that index.
- **duplicate**: Ensure aggregation pipelines include the $match stage(s) on customerId and timestamp range (and channel when supplied) so the pipeline can leverage the (customerId, timestamp) or (channel, timestamp) compound indexes as 
  - why: The previous bullet already requires the channel-breakdown pipeline to $match by customerId and timestamp range before $group; adding a channel filter to a channel-breakdown pipeline is not in the prompt.
  - fix: delete
- **duplicate**: Parse timestamp query parameters into Date objects before querying and store/query timestamps as Date types so range queries behave correctly against the timestamp field.
  - why: Storing timestamp as a Date is already required by the model bullet (timestamp (Date)) and the ingestion bullet; only the query-parameter parsing is new.
  - fix: Parse timestamp query parameters into Date objects before using them in queries and pipelines.

### customer-360-07 (minor_edits, 11 bullets)

- **not_in_prompt**: Define a persistent document model using Beanie ODM (e.g., FeedbackDocument) and include at minimum these fields: channel (string), original_text (string), sentiment_label (string), sentiment_score (numeric), topics (lis
  - why: The prompt asks for an enriched document holding sentiment, key topics, a verbatim quote and the embedding; it does not prescribe exact field names, a separate numeric sentiment_score, or a metadata object. A build with different field names would fail this bullet while satisfying the prompt.
  - fix: Define a Beanie Document model for enriched feedback with fields for channel, original text, extracted sentiment, key topics, verbatim quote, embedding vector and timestamp (field names may vary).
- **not_in_prompt**: Produce both a categorical sentiment_label and a numeric sentiment_score per feedback item (the numeric score must be stored and used for aggregation).
  - why: The prompt says "extract sentiment" and "net sentiment trends"; net sentiment can be computed from labels (positive minus negative share) and the prompt does not require both a label and a numeric score.
  - fix: Store the extracted sentiment in a form the aggregation pipelines can compute a net sentiment metric from (a label, a numeric score, or both).
- **not_in_prompt**: Implement MongoDB aggregation pipelines (invoked from Python) that compute net sentiment trends by channel, by topic, and by time period (supporting at least daily and weekly buckets); each pipeline must return net senti
  - why: "At least daily and weekly buckets" and "document counts" are not in the prompt, which only asks for net sentiment trends by channel, topic and time period.
  - fix: Implement MongoDB aggregation pipelines, invoked from Python, that compute net sentiment trends by channel, by topic and by time period (bucketed by date), each returning a net sentiment metric.
- **not_in_prompt**: Provide runnable example scripts or tests that ingest sample feedback items, run the enrichment (prompt + embedding), persist them to Azure DocumentDB, and execute the aggregation pipelines to demonstrate expected trend 
  - why: The prompt does not ask for demo scripts or tests; seed data, tests and run instructions are covered by the shared section.
  - fix: delete
- **duplicate**: Expose Python functions or callable routines that run the aggregation pipelines with parameters for channel(s), topic(s), time range, and time-bucket granularity and return results formatted for reporting/visualization.
  - why: The previous bullet already requires the pipelines to be invoked from Python; the parameterization (channel(s), topic(s), time range, granularity) and reporting formatting are not in the prompt.
  - fix: delete

### customer-360-08 (minor_edits, 10 bullets)

- **not_in_prompt**: Provide a LangChain-accessible tool named "DocumentDB aggregation tool" that executes aggregation pipelines against event data stored in Azure DocumentDB.
  - why: The prompt describes "a DocumentDB aggregation tool"; it does not require the tool to carry that literal name. A build with a tool named e.g. compute_customer_metrics satisfies the prompt but fails this bullet.
  - fix: Provide a LangChain tool that runs server-side aggregation pipelines (not client-side computation) against the events collection in Azure DocumentDB and returns the results to the agent.
- **not_in_prompt**: The aggregation pipelines must compute, per customer id on demand, the behavioural metrics recency (time since last event), frequency (event count per configurable lookback window), and category affinity (per-category pr
  - why: "Configurable lookback window" is not in the prompt; a build with a fixed window computes frequency as asked but fails this bullet.
  - fix: The aggregation pipelines compute, per customer id on demand, recency (time since last event), frequency (event count over a lookback window) and category affinity (per-category proportions or top categories).
- **not_in_prompt**: After the agent assigns a segment label, the application must write that segment label back into the customer's profile document in Azure DocumentDB (update the profile document with the label and a timestamp) using an u
  - why: The prompt asks to write the segment label back to the customer profile document; it does not ask for a timestamp.
  - fix: After the agent assigns a segment label, the application writes that label into the customer's profile document in Azure DocumentDB using an update operation on the profile collection.
- **not_in_prompt**: Include at least one end-to-end demonstration or automated integration test in the repository that inserts sample event data into Azure DocumentDB, invokes the agent for a sample customer id, and verifies that the custom
  - why: The prompt does not ask for a demo or integration test, and it repeats the timestamp requirement that is not in the prompt; tests and seed data are covered by the shared section.
  - fix: delete
- **duplicate**: The "DocumentDB aggregation tool" must run server-side aggregation pipelines (aggregation pipelines) against an events collection in Azure DocumentDB (not only client-side aggregation) and return the aggregation results 
  - why: Same tool as the previous bullet; the server-side/return-results detail belongs in that bullet (see its fix).
  - fix: delete
- **duplicate**: The code must log or return the aggregation pipeline outputs and the metric values used for segmentation so a reviewer can verify the agent's decision (e.g., structured JSON containing recency, frequency, category affini
  - why: The on-demand invocation bullet already requires the computed metrics to be returned, and the label-capture bullet already requires the chosen label to be captured; the structured-JSON logging format is not in the prompt.
  - fix: delete

### customer-360-09 (minor_edits, 10 bullets)

- **not_in_prompt**: Configure and attach agent memory (use the phrase "agent memory" in the code/config) so the agent persists recent interaction context and reuses it during scoring calls.
  - why: The prompt asks for a LangChain agent "with agent memory"; it does not ask that the literal phrase "agent memory" appear in the code or config. A reviewer should check for a configured LangChain memory component, not a string.
  - fix: Configure a LangChain memory component on the agent so it retains interaction context across scoring calls.
- **not_in_prompt**: The agent must generate a numeric score in the inclusive range 0–100; the code must validate the output is numeric and within that range before persisting.
  - why: The prompt says the agent "assigns a score from 0-100"; it does not ask for a validation step before persisting. The range is traceable, the validation gate is not.
  - fix: The agent produces a numeric score in the inclusive range 0–100, and the value written to the lead document is a number in that range.
- **not_in_prompt**: The agent must generate a one-paragraph rationale for the score; the code must validate the rationale is a single paragraph (no blank-line separators/newline-only paragraphs) prior to persisting.
  - why: The prompt asks for "a one-paragraph rationale"; it does not ask for a paragraph-structure validator, and the no-blank-line rule is an invented check.
  - fix: The agent produces a one-paragraph rationale for the score, stored as a single string field on the lead document.
- **not_in_prompt**: If any required DocumentDB document (activity history, firmographics, or engagement signals) is missing or incomplete, the agent must return/ log a clear error/handled response and must not write an invalid score back to
  - why: Nothing in the prompt, title or description asks for missing-document error handling; this is general robustness, not a stated requirement.
  - fix: delete

### customer-360-10 (minor_edits, 10 bullets)

- **not_in_prompt**: Load past ticket resolutions and knowledge base articles from Azure DocumentDB collections and convert them into LlamaIndex documents for indexing.
  - why: The prompt says the agent "indexes past ticket resolutions and knowledge base articles in a DocumentDB vector store"; it does not say the source corpus is read from DocumentDB collections. The source could be files or seed data.
  - fix: Index both past ticket resolutions and knowledge base articles (two content types) as LlamaIndex documents into the Azure DocumentDB vector store.
- **not_in_prompt**: Store and preserve document metadata (e.g., source id, title, timestamp, collection name) alongside each indexed document so retrieved items are inspectable and traceable.
  - why: The prompt does not ask for metadata on indexed documents or for traceability of retrieved items.
  - fix: delete
- **not_in_prompt**: Return both the generated suggested resolution and the 5 retrieved documents (or their IDs/metadata) in the agent response so reviewers can verify which contexts were used.
  - why: The prompt asks only for a generated suggested resolution; returning the retrieved documents alongside it is not requested.
  - fix: delete

### customer-360-11 (minor_edits, 9 bullets)

- **not_in_prompt**: Include an append-only consent history sub-array on the same Beanie Document model; each history entry must include at minimum a timestamp, consentVersion, channel states, and an event type (e.g., "grant" or "withdraw").
  - why: The prompt asks for "an append-only consent history sub-array for audit" and says nothing about the fields of each entry; the four-field minimum is invented.
  - fix: Include an append-only consent history sub-array on the Beanie Document model, each entry recording a consent change (what changed and when).
- **not_in_prompt**: The record-consent endpoint must append a new entry to the consent history sub-array and update the top-level current preference snapshot and consentVersion in a single atomic operation (e.g., a single $push plus $set-st
  - why: The prompt asks for a record-consent endpoint, a consentVersion field and an append-only history; it does not require the write to be a single atomic $push+$set update.
  - fix: The record-consent endpoint appends an entry to the consent history sub-array and updates the document's current channel preferences and consentVersion.
- **not_in_prompt**: The withdraw-consent endpoint must append a withdrawal event to the consent history sub-array (do not modify or delete prior history entries) and update the top-level current preference snapshot and consentVersion to ref
  - why: Same as the record-consent bullet: atomicity is not asked for by the prompt. The "do not modify or delete prior history entries" clause also duplicates the dedicated append-only bullet.
  - fix: The withdraw-consent endpoint appends a withdrawal entry to the consent history sub-array and updates the document's current channel preferences to reflect the withdrawal.
- **not_in_prompt**: The retrieve-current-preferences endpoint must return the current preference state and consentVersion (a snapshot stored on the document or derived deterministically from the latest history entry) without exposing or mod
  - why: The prompt asks to "retrieve the current preference state"; it does not say the response must hide the history, so "without exposing" would fail a valid implementation that also returns it.
  - fix: The retrieve endpoint returns the customer's current channel preferences and consentVersion.
- **duplicate**: Include example request/response shapes or FastAPI route implementations for the three required endpoints (record consent, withdraw consent, retrieve current preference state) so a reviewer can exercise them against an A
  - why: The three endpoint bullets above already require the FastAPI route implementations; example request/response shapes are not asked for by the prompt.
  - fix: delete

### customer-360-12 (minor_edits, 10 bullets)

- **not_in_prompt**: Implement the solution in Python and instantiate a Single-agent LangChain agent (imports and agent construction must show Python and LangChain).
  - why: "Single-agent" is a taxonomy label, not wording from the prompt, which says "a Python LangChain agent".
  - fix: Implement the solution in Python and construct a LangChain agent (imports and agent construction show LangChain).
- **not_in_prompt**: Register and expose a DocumentDB aggregation tool as a LangChain tool that the agent can call (tool implementation must be named or documented as the "DocumentDB aggregation tool").
  - why: The prompt describes the tool as "a DocumentDB aggregation tool"; it does not require the implementation to carry that exact name or label. A reviewer should check that the tool runs an aggregation against DocumentDB, not its name.
  - fix: Register a LangChain tool, callable by the agent, that runs an aggregation pipeline against Azure DocumentDB.
- **not_in_prompt**: Include a runnable end-to-end example (script or main function) that, for a sample customer ID, runs the aggregation tool, invokes the LangChain agent prompt flow, logs the rationale and outputs, and persists the CLV sco
  - why: The prompt does not ask for a demo script or for logging the rationale; a runnable entry point is a gallery-level need covered by the shared README/run bullets, and the rest duplicates the tool, prompt and write-back bullets.
  - fix: delete

### customer-360-13 (minor_edits, 9 bullets)

- **not_in_prompt**: Provide an endpoint (e.g., POST /households/resolve) that builds an identity graph from Customer documents: create nodes for customers and add edges when customers share a matching address OR phone OR surname to identify
  - why: The prompt says only "identifies household members by matching on shared address, phone, and surname fields"; it does not say the match is OR-ed per field, that connected components define a household, or that the step must be an HTTP endpoint (only the aggregation endpoints are asked for). A builde
  - fix: Implement household identification that groups Customer documents sharing address, phone and surname field values; the matching logic is in the service code and produces one household group per set of linked customers.
- **not_in_prompt**: Normalize matching fields before comparing (e.g., trim/case-normalize address and surname, canonicalize phone digits) so matches are deterministic and verifiable in code.
  - why: Nothing in the prompt, title or description asks for field normalization; it is a quality improvement the drafter added.
  - fix: delete
- **duplicate**: Implement the aggregation queries so they operate by following the Household.members references (not by re-scanning customers independently), demonstrating use of DocumentDB document references and aggregation pipelines 
  - why: The CLV and product-holdings bullets already require aggregating "the lifetime_value of all Customer members referenced by the Household document" and "products across all referenced members" with the aggregation pipeline, so this bullet re-states them.
  - fix: delete

### customer-360-14 (minor_edits, 9 bullets)

- **not_in_prompt**: Wire agent memory to load (and on subsequent calls, retrieve from) the fetched profile, segment, and recent interaction documents so the LlamaIndex agent can consult them as memory.
  - why: The prompt asks for "a Node.js LlamaIndex agent with agent memory that fetches the customer's profile, segment, and recent interaction documents"; it does not say the memory must be populated with those documents. The first bullet already requires a configured agent memory component; this one fixes 
  - fix: Show the LlamaIndex agent memory being written to and read from during a run (e.g., memory persisted after a request and consulted on the next request for the same customer).
- **not_in_prompt**: Return a ranked list of recommended content items (ordered by relevance), where each item includes at least: content id, title (or short text), and a numeric relevance score; the code must build this structured output.
  - why: The prompt asks for a "ranked list for the customer"; the required per-item fields (title, numeric relevance score) are not in the prompt, title or description.
  - fix: Return a ranked (ordered) list of recommended content items that identifies each content piece; the code builds this structured output.
- **not_in_prompt**: Ensure the generated rationale links each ranked item to the specific retrieved content piece(s) and DocumentDB source documents used in ranking (e.g., by referencing document ids or snippets).
  - why: The prompt asks for "a personalised content selection rationale"; per-item citation of document ids is not asked for, and the previous bullet already covers the rationale citing customer facts.
  - fix: delete

### customer-360-15 (minor_edits, 9 bullets)

- **not_in_prompt**: Connect to Azure DocumentDB using the DocumentDB Atlas-compat API from Python (for example, configuring pymongo to the Azure DocumentDB Atlas-compat endpoint) and perform all reads/writes against Azure DocumentDB.
  - why: The prompt never mentions Atlas; it asks for "a Python FastAPI service ... backed by DocumentDB aggregation". No installed skill describes an "Atlas-compat endpoint" for Azure DocumentDB (documentdb-vector-search/vector-knn-query.md even calls Atlas syntax "not supported in DocumentDB"), so a review
  - fix: Connect to Azure DocumentDB from Python using a MongoDB-compatible driver (connection string configurable) and perform all reads/writes against Azure DocumentDB.
- **not_in_prompt**: Implement a scheduled weekly refresh job that runs the aggregation pipelines and upserts the materialised cohort snapshot documents in Azure DocumentDB (the scheduler code must be part of the service).
  - why: The prompt says "Cache cohort snapshots as materialised documents refreshed weekly"; it does not say the scheduler must live inside the FastAPI process. A refresh entry point driven by cron or a documented job would satisfy the prompt.
  - fix: Provide a weekly refresh mechanism (an in-process scheduler or a documented refresh entry point intended to run weekly) that re-runs the aggregation pipelines and upserts the materialised cohort snapshot documents in Azure DocumentDB.

### customer-360-16 (minor_edits, 10 bullets)

- **not_in_prompt**: Store attribution results as versioned documents per customer in Azure DocumentDB: each pipeline run must INSERT a new versioned document (do not overwrite prior versions) and include a version identifier (numeric or ISO
  - why: The prompt says "Store the attribution output as a versioned document per customer"; it does not require one new document per run (an embedded version history in one document per customer also fits), and "metadata referencing the source event time range" is not asked for anywhere.
  - fix: Store the attribution output as a versioned document per customer in Azure DocumentDB: each stored result carries a version identifier, and prior versions remain retrievable (as separate version documents or an embedded version history) rather than being overwritten.
- **not_in_prompt**: The LangChain tool responses must include which attribution model and which version identifier (version id or timestamp) were used to produce the answer, and support at minimum queries such as “What was the first-touch a
  - why: The prompt asks only for "a LangChain tool that lets marketers ask natural language questions about attribution results"; the required response fields and the specific example questions are invented, and whether an LLM answers a given phrasing is not something a reviewer can check in the code.
  - fix: delete
- **not_in_prompt**: Include an end-to-end demonstration in code that loads a sample set of time-series event documents into Azure DocumentDB, runs the three aggregation pipelines to create versioned attribution documents, and shows the Lang
  - why: The prompt does not ask for a demonstration script; loading sample data is already covered by the shared "seed script" requirement, and the rest re-states the pipeline and LangChain bullets.
  - fix: delete
- **duplicate**: Provide an API or function in the Python service to re-run attribution pipelines for a given customer or time range that creates a new versioned attribution document rather than replacing existing versions.
  - why: Re-running the pipelines and producing a new version is already what the versioned-storage bullet requires; "for a given customer or time range" is an added parameter the prompt does not state.
  - fix: delete

### customer-360-17 (minor_edits, 9 bullets)

- **not_in_prompt**: Use Python and Beanie ODM to define a Document model that maps to survey response documents stored in Azure DocumentDB and includes at minimum: original response text, question identifier, themes (list of strings), senti
  - why: The prompt asks to extract themes, sentiment and a representative quote, embed the text and write the enriched document back; it says nothing about a processed flag or processed_at timestamp.
  - fix: Use Python and Beanie ODM to define a Document model that maps to survey response documents stored in Azure DocumentDB and includes at minimum: original response text, question identifier, themes (list of strings), sentiment (label plus numeric score), representative_quote (string), and embedding (n
- **not_in_prompt**: Read survey response documents from Azure DocumentDB via Beanie queries and process them in configurable batches (demonstrate fetching by survey id and by question id).
  - why: The prompt only says the pipeline "reads survey response documents from DocumentDB"; configurable batches and fetching by survey id and by question id are invented.
  - fix: Read survey response documents from Azure DocumentDB via Beanie queries.
- **not_in_prompt**: Update or save the enriched document back into Azure DocumentDB using Beanie, preserving the original document id and setting the processed flag/processed_at timestamp when enrichment completes.
  - why: "writes the enriched document back" is in the prompt; setting a processed flag/processed_at is not.
  - fix: Update or save the enriched document back into Azure DocumentDB using Beanie, preserving the original document id.
- **not_in_prompt**: Ensure the pipeline is idempotent for repeated runs by skipping or quickly detecting documents already enriched (using the processed flag, processed_at, or presence of the embedding/themes fields) so duplicate enrichment
  - why: Idempotency on repeated runs is not asked for anywhere in the prompt, title or description.
  - fix: delete
- **not_in_prompt**: Process failures from the LLM or embedding calls deterministically: retry a configurable number of times, and when exhausted write error metadata to the Azure DocumentDB document (e.g., last_error, last_error_at) so fail
  - why: Retries and error-metadata fields are not mentioned in the prompt, title or description.
  - fix: delete

### customer-360-18 (needs_rework, 10 bullets)

- **not_in_prompt**: The ingest agent must normalise incoming customer records (examples in code: canonicalize name casing, normalize email formats, parse and standardize phone/address) and write the normalized documents into Azure DocumentD
  - why: The prompt says the ingest agent "normalises incoming customer records and writes them to DocumentDB"; a stable unique identifier field is not asked for.
  - fix: The ingest agent must normalise incoming customer records (for example name casing, email format, phone/address) and write the normalized documents into Azure DocumentDB.
- **not_in_prompt**: The enrich agent must call a third-party signals provider (real or clearly documented mock/stub) to retrieve firmographic or demographic signals, append those signals to the canonical profile documents, and persist the e
  - why: The prompt asks the enrich agent to append third-party firmographic or demographic signals; recording source and timestamp per enrichment is not in the prompt.
  - fix: The enrich agent must call a third-party signals provider (real or clearly documented mock/stub) to retrieve firmographic or demographic signals, append those signals to the profile documents, and persist the updates to Azure DocumentDB.
- **not_in_prompt**: The Orchestrator must create and persist a workflow document in Azure DocumentDB for every batch run; each workflow document must include at minimum: batch_id, start_time, end_time, number_ingested, number_duplicates_fou
  - why: The prompt says only "The orchestrator logs each batch run as a workflow document"; the mandatory field list is invented and an auditor would fail a conforming build that lacks, say, number_duplicates_found.
  - fix: The orchestrator must create and persist one workflow document in Azure DocumentDB for every batch run that records the run (for example an identifier, timing, and the outcome of each agent).
- **not_in_prompt**: The dedup agent’s merge operation must be implemented so reviewers can verify in code that merged data preserves source provenance (which original documents contributed which fields) and that duplicates are either remove
  - why: The prompt says the dedup agent "identifies and merges duplicate profiles using LLM-assisted matching"; per-field provenance is not asked for, and the removed/flagged duplicates point repeats the dedup bullet.
  - fix: delete
- **not_in_prompt**: The Orchestrator must record per-record or per-error details for failures (e.g., invalid records, enrichment API errors) into the workflow document so a reviewer can inspect logged failures in Azure DocumentDB.
  - why: Per-record failure logging is not in the prompt, title or description; the workflow-document bullet already covers logging each batch run.
  - fix: delete
- **duplicate**: All profile inserts, updates, merges, archival flags, enrichment writes, and workflow documents must be persisted to Azure DocumentDB (the code/config must target Azure DocumentDB as the MongoDB-compatible persistence la
  - why: The ingest, dedup, enrich and workflow-document bullets already each require their writes to go to Azure DocumentDB; this bullet adds nothing checkable.
  - fix: delete
- **not_checkable**: Implement the pipeline as an Orchestrator using Python LangChain that coordinates three agents named exactly "ingest agent", "dedup agent", and "enrich agent"; repository code must import and use LangChain constructs for
  - why: The prompt names the agent roles in prose; it does not require code identifiers to carry those exact strings (which cannot contain spaces anyway), so "named exactly" cannot be checked meaningfully.
  - fix: Implement the pipeline in Python using LangChain as an orchestrator that coordinates three agents with the roles ingest agent, dedup agent and enrich agent; repository code must import and use LangChain constructs for the orchestration and agents.

### customer-360-19 (minor_edits, 9 bullets)

- **not_in_prompt**: The trigger agent must use DocumentDB change streams (the DocumentDB change streams feature) against Azure DocumentDB via the MongoDB Node.js driver to subscribe to changes on the relevant collections.
  - why: The prompt names Node.js and LangChain but no driver or ODM; requiring the MongoDB Node.js driver would fail a build that uses, for example, Mongoose.
  - fix: The trigger agent must use DocumentDB change streams against Azure DocumentDB to subscribe to changes on the relevant collections.
- **not_in_prompt**: All outcomes must be logged back to Azure DocumentDB: the pipeline must write a log document to a dedicated collection (for example "outreach_logs") containing the original event, generated copy, selected channel, send r
  - why: The prompt says "Log outcomes to DocumentDB" and names no driver; the trailing "using the MongoDB Node.js driver" is not in the prompt.
  - fix: All outcomes must be logged back to Azure DocumentDB: the pipeline must write a log document (for example to an "outreach_logs" collection) containing the original event, generated copy, selected channel, send result (success/failure and any provider message IDs or errors), and timestamps.
- **not_in_prompt**: Provide example configuration/fixtures in the sample that allow a reviewer to exercise the three event types (sample change-stream event documents or a script that writes test events to Azure DocumentDB), so the reviewer
  - why: The prompt does not ask for fixtures or test-event scripts; the previous bullet already requires a runnable entrypoint demonstrating an end-to-end event, and the detection bullet already requires checkable logic for each event type.
  - fix: delete

### customer-360-20 (minor_edits, 10 bullets)

- **not_in_prompt**: Implement a LangChain agent named "merge agent" that accepts the scored candidate list and deterministically consolidates matched profiles into a single golden record object, recording which source profile supplied each 
  - why: The prompt says the merge agent "consolidates matched profiles into a golden record"; neither "deterministically" nor per-field provenance is asked for (source documents are logged by the audit agent, at document level).
  - fix: Implement a LangChain agent named "merge agent" that accepts the scored candidate list and consolidates the matched profiles into a single golden record object.
- **not_in_prompt**: The "merge agent" must produce an aggregate confidence score for the merged golden record derived from the input similarity scores and include that confidence on the golden record object.
  - why: The prompt only says the audit agent logs every merge decision "with confidence score"; it does not say the merge agent derives it from similarity scores or stores it on the golden record.
  - fix: A confidence score is computed for each merge decision and passed to the audit agent.
- **not_in_prompt**: The orchestrator must sequence the flow: invoke "match agent" → pass results to "merge agent" → pass merge decision to "audit agent", and only after audit logging completes, write or upsert the final golden record into A
  - why: The prompt says the orchestrator writes the final golden record to DocumentDB; it does not impose that the write happen only after audit logging completes.
  - fix: The orchestrator must sequence the flow match agent → merge agent → audit agent and write the final golden record into Azure DocumentDB via Beanie ODM.
- **not_in_prompt**: The orchestrator's write to Azure DocumentDB must use upsert semantics (insert new golden record or update existing golden record with the same canonical id) so the golden record stored in Azure DocumentDB reflects the m
  - why: Upsert semantics and a canonical id are not in the prompt; the orchestrator write is already covered by the sequencing bullet.
  - fix: delete

### fintech-01 (minor_edits, 10 bullets)

- **wrong_fact**: Ensure the vector search and stored vectors use the binary embedding format and an appropriate binary similarity metric in the query parameters (e.g., binary similarity/distance configured for the vector-ivf index).
  - why: The documentdb-vector-search skill lists the cosmosSearch similarity options as COS, L2 and IP only; there is no binary similarity or distance metric to configure on a vector-ivf index. The binary format itself is also not in the prompt.
  - fix: Ensure the vector-ivf index's dimensions and similarity (COS, L2 or IP) match the embeddings that are inserted and the vector used at query time.
- **not_in_prompt**: Provide code that encodes transaction features into embeddings in binary embedding format (i.e., binary embeddings) and exposes the embedding step as a callable function the agent uses.
  - why: The prompt says only "encodes transaction features as embeddings"; neither the prompt, title nor description says the embeddings are binary. Binary embeddings appear only in the concepts tag list, and the vector-search skill does not describe a binary embedding format.
  - fix: Provide code that encodes transaction features into embedding vectors and exposes the embedding step as a callable function the agent uses.
- **not_in_prompt**: Create and configure an Azure DocumentDB vector-ivf index in code and verify the index exists before inserting vectors.
  - why: The prompt asks for a vector-ivf index; it does not ask the app to verify index existence before inserts, which is an added implementation step an auditor would fail a valid sample on.
  - fix: Create an Azure DocumentDB cosmosSearch index of kind vector-ivf on the fraud pattern embedding field in code.

### fintech-02 (minor_edits, 9 bullets)

- **duplicate**: Ensure the aggregation output uses calendar months (year-month) as the time key and includes category, total amount, and month in the JSON response so a reviewer can verify the grouping and sums.
  - why: The preceding two bullets already require grouping by year-month and category with summed amount, and an endpoint returning per-month, per-category JSON; this bullet restates both.
  - fix: delete
- **duplicate**: Ensure the agent’s categorization step only relies on merchant name and amount (and, if present, date) as input features and the code demonstrates those fields being passed into the LangChain prompt.
  - why: The third bullet already requires merchant name and amount to be passed into the LangChain prompt. The added "only" restriction is not in the prompt or description ("reasons over merchant names and amounts" does not exclude other fields).
  - fix: delete
- **vague**: Have the LangChain agent write the chosen category back to the same Azure DocumentDB document (update the document’s "category" field) and mark only the processed transaction as updated.
  - why: "mark only the processed transaction as updated" is unclear: the prompt only asks to write the category back to the document, and a reviewer cannot tell what "mark as updated" means to check.
  - fix: Write the chosen category back to the same Azure DocumentDB transaction document (update that document's "category" field) without modifying other transactions.

### fintech-03 (needs_rework, 8 bullets)

- **not_in_prompt**: Provide Mongoose models for the positions collection and the alert rules collection (models named e.g., Position and AlertRule) with fields sufficient to evaluate alerts (positions: userId, symbol, shares, avgCost, curre
  - why: The prompt names no fields; the parenthetical reads as a required schema (userId, scope, metric, comparison, active, updatedAt) that a valid sample could reasonably differ from, so an auditor would fail it on invented details.
  - fix: Provide Mongoose models for the positions collection and the alert rules collection, with position fields sufficient to compute P&L and sector allocation (e.g., symbol, shares, cost basis, current price, sector) and alert rule fields sufficient to evaluate a threshold and deliver a webhook (e.g., ta
- **not_in_prompt**: Open a change stream on the positions collection using the Azure DocumentDB change streams feature (use positions.watch(...) via Mongoose/driver) and configure the stream to retrieve the latest document (fullDocument: "u
  - why: The prompt asks for a change stream on positions to detect price updates; it does not prescribe fullDocument: "updateLookup" (re-fetching the position is an equally valid way to evaluate rules). The skills do not cover change streams, so feasibility was not judged.
  - fix: Open a change stream on the positions collection (positions.watch(...) via Mongoose/driver) and obtain the updated position document for rule evaluation (for example with fullDocument: "updateLookup" or by re-reading the document).
- **not_in_prompt**: For each position change that passes the price-change detection, query the alert rules collection for active rules applicable to that position (match by userId and symbol or by global scope) and evaluate each rule's cond
  - why: The prompt says "evaluate each alert rule document" and "fire a webhook when a threshold is breached"; it does not require two metric types, a global scope, or an active flag. These are invented acceptance criteria.
  - fix: For each detected price update, load the alert rule documents that apply to that position and evaluate each rule's threshold against the updated position document.
- **not_in_prompt**: When a rule is breached, send an HTTP POST webhook to the alert rule's webhookUrl with a JSON payload that includes the position document, the alert rule document, the breached metric name and value, and a UTC timestamp;
  - why: The prompt only says "fire a webhook when a threshold is breached"; the exact payload contents, UTC timestamp and recording the HTTP status are not asked for.
  - fix: When a rule's threshold is breached, send an HTTP POST to the rule's webhook URL with a JSON payload identifying the position, the rule and the breached value.
- **not_in_prompt**: Expose the aggregation via an HTTP endpoint (e.g., GET /portfolio/:userId/summary) that returns a JSON object containing total P&L and an array of sectors with their marketValue and percentage allocation computed by the 
  - why: The prompt says "Include an aggregation that computes portfolio P&L and sector allocation"; it does not require an HTTP endpoint, and the previous bullet already covers what the aggregation computes.
  - fix: Make the P&L and sector allocation aggregation callable from the service (for example as an exported function or an HTTP endpoint) and return its results as JSON/objects containing total P&L and per-sector allocation.
- **duplicate**: Use Node.js and Mongoose to connect to Azure DocumentDB via a MongoDB-compatible connection string supplied by an environment variable (connection established with Mongoose.connect).
  - why: The environment-variable clause repeats the shared bullet "The connection string and model credentials come from environment variables"; only the Node.js + Mongoose connection is traceable to the prompt.
  - fix: Use Node.js and Mongoose to connect to Azure DocumentDB (connection established with mongoose.connect).

### fintech-04 (minor_edits, 11 bullets)

- **not_in_prompt**: Build the system as a Single-agent application where a single agent/process performs ingestion, vector storage, retrieval, and answer generation.
  - why: The prompt asks for a LlamaIndex RAG pipeline; it never mentions an agent or a single-agent architecture, and the bullet adds nothing a reviewer could check beyond bullet 1.
  - fix: delete
- **duplicate**: Store vector documents in Azure DocumentDB using its MongoDB-compatible API so that the vector collection is queryable for similarity search (vector and metadata persisted together).
  - why: Persisting vector and metadata together is already required by the previous bullet, and similarity search is required by the next one; what this bullet should capture, and does not, is the vector index that the description's "indexing transcripts in DocumentDB" implies.
  - fix: Create an Azure DocumentDB cosmosSearch vector index (vector-diskann, vector-hnsw or vector-ivf) on the embedding field of the chunk collection, with dimensions and similarity matching the embedding model.
- **vague**: During ingestion, chunk the extracted transcript text into segments with configurable chunk size and overlap; chunking must be parameterized relative to the target LLM context window to enable context engineering.
  - why: The prompt asks to chunk the transcripts and, separately, to fit retrieved passages into the context window. "parameterized relative to the target LLM context window" is not something a reviewer can check concretely, and the prompt does not require chunk size to be derived from the context window.
  - fix: During ingestion, chunk the extracted transcript text into segments with an explicit chunk size and overlap defined in code or configuration.
- **not_checkable**: Generate answers by combining the retrieved context and the analyst question through LlamaIndex (RAG), and ensure each factual claim or quoted passage in the answer includes an explicit citation showing the source transc
  - why: The prompt asks to "cite the source transcript and timestamp in each answer"; requiring a citation on every factual claim or quoted passage is a stricter, per-sentence property a code reviewer cannot verify.
  - fix: Generate answers by combining the retrieved context and the analyst question through LlamaIndex (RAG), and ensure each answer includes citations giving the source transcript identifier and timestamp of the chunks used.

### fintech-05 (minor_edits, 10 bullets)

- **not_in_prompt**: Return or log a clear status for each processed document indicating whether it was upserted, updated, or flagged for manual review so a reviewer can verify the pipeline outcome.
  - why: The prompt asks to upsert records and flag incomplete ones; it does not ask for per-document status logging or for distinguishing 'upserted' from 'updated'. The flag itself (previous bullet) is what the prompt makes observable.
  - fix: delete
- **duplicate**: Map and validate the OpenAI-extracted fields against the Pydantic schema; if validation succeeds, transform the validated model into a Beanie document for persistence.
  - why: Validating the LLM output against the Pydantic schema is already the previous bullet; persisting through a Beanie document is already the upsert bullet. Nothing here is separately checkable.
  - fix: delete

### fintech-06 (needs_rework, 10 bullets)

- **not_in_prompt**: The scoring agent must also invoke an LLM via LangChain (e.g., an LLMChain or equivalent LangChain call) to produce or refine a final credit score, and include both the rule-based score and the LLM-derived final score in
  - why: The prompt says the scoring agent 'applies risk rules and an LLM to produce a credit score' (one score). Requiring two separate scores (rule-based and LLM-derived) in the output is an added design constraint.
  - fix: The scoring agent must invoke an LLM through LangChain and combine the LLM output with the risk-rule evaluations to produce the credit score.
- **not_in_prompt**: After the explainer agent completes, the app must write the final credit score and the generated explanation back into the same applicant document in Azure DocumentDB, adding a timestamp and agent metadata (agent names, 
  - why: The prompt says 'Store the final score and explanation back in DocumentDB'. It does not require writing to the same applicant document, nor a timestamp, nor agent metadata; a sample storing scores in a separate collection would wrongly fail.
  - fix: After the explainer agent completes, write the final credit score and the generated explanation to Azure DocumentDB (for example on the applicant document or in a scores collection).
- **not_in_prompt**: The code must handle missing applicants or Azure DocumentDB errors gracefully: log the error, avoid writing incomplete results back to the database, and return a clear error/status from the pipeline.
  - why: Nothing in the prompt, title or description asks for error handling for missing applicants or database failures.
  - fix: delete
- **not_in_prompt**: Include an automated test or runnable example that exercises the full pipeline end-to-end against a test Azure DocumentDB dataset and asserts that the final score and explanation were written to Azure DocumentDB for the 
  - why: The prompt does not ask for an end-to-end test against a live dataset; testing is covered by the shared section ('Unit tests run without a live cluster'), which this bullet pulls in the opposite direction.
  - fix: delete

### fintech-07 (minor_edits, 11 bullets)

- **not_in_prompt**: When posting a transaction, perform the write(s) that record the transaction and update any related balance or ledger documents inside a single DocumentDB transaction (using Mongoose sessions / session.withTransaction) s
  - why: The prompt asks for DocumentDB transactions but never asks for materialized balance documents; it says balances are computed by aggregation at query time. Requiring balance-document updates inside the transaction assumes a design the prompt does not state (the skills confirm multi-document transacti
  - fix: Posting a transaction performs its writes inside a DocumentDB multi-document transaction (a Mongoose session with session.withTransaction or startTransaction/commitTransaction), so the posting is atomic.
- **duplicate**: The POST /transactions handler must check the idempotencyKey and avoid creating duplicate postings (returning the existing transaction or a suitable status) and must rely on the DB-level unique constraint as part of the 
  - why: The DB-level unique constraint on idempotencyKey is already its own bullet ('Create a unique index on the idempotencyKey field'). Only the handler behaviour is new here.
  - fix: The POST /transactions handler must check the idempotencyKey and must not create a second posting for a key already seen (returning the existing transaction or a suitable status).
- **duplicate**: The transaction document stored must include the currency field and a reference to the exchange rate document (do not inline the rate as the only source of truth).
  - why: The Transaction model bullet already requires a currency field and an ObjectId reference to the exchange-rate document.
  - fix: delete

### fintech-08 (needs_rework, 10 bullets)

- **not_in_prompt**: Connect to Azure DocumentDB using the pymongo driver (connection URI or connection string must be configurable and used by the code).
  - why: The prompt names LlamaIndex and DocumentDB but no driver; it never says pymongo. A sample that connects through LlamaIndex's vector-store integration without importing pymongo directly would wrongly fail this line.
  - fix: Connect to Azure DocumentDB using a configurable connection string that the code reads and uses for both collections.
- **not_in_prompt**: Build a vector index with LlamaIndex over the regulatory documents and perform vector search (similarity search) to retrieve the most relevant regulatory clauses for a given policy excerpt; top-K must be configurable.
  - why: The prompt asks to retrieve the most relevant regulatory clauses; it says nothing about a configurable top-K.
  - fix: Build a vector index with LlamaIndex over the regulatory documents and use vector search to retrieve the most relevant regulatory clauses for a given policy excerpt.
- **not_in_prompt**: The compliance gap report produced by the agent must include: a concise compliance verdict (compliant/partial/non‑compliant), a list of gaps mapped to specific regulatory clauses, suggested remediation steps for each gap
  - why: The prompt asks for 'a compliance gap report' produced by comparing the excerpt to retrieved clauses. The three-value verdict scale, per-gap remediation steps and citation format are invented structure that a correct sample could reasonably omit.
  - fix: The agent produces a compliance gap report that states the gaps between the policy excerpt and the retrieved regulatory clauses and identifies which regulatory clauses each gap relates to.
- **duplicate**: Ensure retrieval queries only the regulatory documents collection (not the internal policy collection) and return for each retrieved clause the stored document id/metadata and its similarity score.
  - why: Returning the similarity score is not in the prompt and is already the shared bullet 'Search results include the similarity score'. Restricting retrieval to the regulatory collection is the checkable part that is traceable to the prompt.
  - fix: Retrieval queries only the regulatory documents collection (not the internal policy collection) and returns each retrieved clause with its stored document id/metadata.
- **duplicate**: Provide ingestion/update functions that add or update documents in the Azure DocumentDB collections and that refresh or update the LlamaIndex vector index so newly ingested documents become searchable by the agent.
  - why: Ingestion into the two collections is already the 'two separate collections' bullet and vector indexing is already the 'Build a vector index with LlamaIndex' bullet; the extra 'update existing documents' capability is not in the prompt.
  - fix: delete

### fintech-09 (needs_rework, 10 bullets)

- **contradicts_prompt**: The LangChain agent must compute and flag statistical outliers from the returned daily metrics using a documented, reproducible method (for example, z-score thresholding or IQR) and mark which days are anomalous in the r
  - why: The prompt's grammar puts outlier flagging in the aggregation tool, so requiring the agent (rather than the tool) to do it could fail a build that follows the prompt literally. The method requirement itself is fine.
  - fix: Statistical outliers in the daily volume/frequency metrics are flagged (by the aggregation tool or the agent) using an explicit statistical method such as z-score thresholding or IQR, and the anomalous days are identified in the results.
- **not_in_prompt**: Implement the project in Python and expose a runnable Single-agent LangChain agent (use the term "LangChain agent") as the entrypoint that accepts a wallet address string input.
  - why: The prompt says "a Python LangChain agent"; it never says "Single-agent", and "(use the term ...)" asks the code to use a phrase rather than a checkable behaviour.
  - fix: Implement the project in Python and expose a runnable LangChain agent as the entrypoint that accepts a wallet address string.
- **not_in_prompt**: Register and use a LangChain Tool named exactly "DocumentDB aggregation tool" that the agent calls to perform the database analysis.
  - why: The prompt describes "a DocumentDB aggregation tool" as a kind of tool, not a name; requiring that exact string as the tool name would fail any sensibly named tool.
  - fix: Register a LangChain Tool that runs an aggregation pipeline against Azure DocumentDB (the prompt's "DocumentDB aggregation tool"), and have the agent call it to perform the wallet analysis.
- **not_in_prompt**: The tool must return the raw aggregation results to the agent (not only a formatted summary) so the agent can perform statistical analysis client-side.
  - why: The prompt attributes grouping, metric computation and outlier flagging to the aggregation tool itself ("a DocumentDB aggregation tool that groups ..., computes ..., and flags statistical outliers"); it does not dictate that outlier detection happens client-side in the agent, so this mandates an arc
  - fix: delete
- **duplicate**: The aggregation pipeline must perform the volume and frequency metric computations server-side (in the pipeline) and return daily documents containing at minimum: date, daily_volume, daily_count.
  - why: The previous bullet already requires the pipeline to group by day and compute per-day volume (sum) and frequency (count) in the pipeline; the only addition is invented field names (daily_volume, daily_count) that the prompt does not state.
  - fix: delete
- **duplicate**: The agent code must invoke the "DocumentDB aggregation tool" programmatically when given a wallet address (e.g., provide a function analyze_wallet(address: str) -> str or an agent.run(...) call) and return the plain-lang
  - why: Accepting a wallet address (bullet 1), the agent calling the tool (bullet 2) and returning the plain-language summary (bullet 8) are each already required.
  - fix: delete
- **duplicate**: The code must explicitly target Azure DocumentDB in its connection/configuration and use MongoDB aggregation pipeline semantics when calling the database aggregate operation.
  - why: Bullet 3 already requires the tool to connect to Azure DocumentDB and execute a MongoDB-style aggregation pipeline.
  - fix: delete

### fintech-10 (minor_edits, 10 bullets)

- **wrong_fact**: Connect Beanie to an Azure DocumentDB (MongoDB API) cluster and query for expense report documents with a "submitted" status (or equivalent) to select reports to process.
  - why: "(MongoDB API)" is the naming of the neighbouring product (Azure Cosmos DB for MongoDB); the skills describe Azure DocumentDB as MongoDB wire-protocol compatible, and the shared section forbids neighbouring product names.
  - fix: Connect Beanie to an Azure DocumentDB cluster and query for expense report documents with a "submitted" status (or equivalent) to select reports to process.
- **duplicate**: Ensure the stored enriched report documents clearly reflect the agent’s outputs (categories and violation flags/reasons) so a reviewer can verify categorisation and flagged policy violations in Azure DocumentDB.
  - why: Bullets 6 and 7 already require the category/violation fields on each line item and persisting the enriched report back via Beanie; this adds nothing checkable.
  - fix: delete

### fintech-11 (needs_rework, 10 bullets)

- **not_in_prompt**: Implement the alert agent to query Azure DocumentDB for a watchlist collection and determine matches by exact ticker symbol comparison between extracted tickers and watchlist entries.
  - why: The prompt says the alert agent "checks DocumentDB for matching watchlist entries"; it does not require exact (e.g. case-sensitive) comparison, so a normalised match would wrongly fail.
  - fix: Implement the alert agent to query the watchlist collection in Azure DocumentDB and determine whether any extracted ticker matches a watchlist entry.
- **not_in_prompt**: When a watchlist match occurs, the alert agent must fire a notification by sending a JSON payload that includes the article unique id, headline, matched ticker(s), and sentiment score to a configurable webhook (or other 
  - why: The prompt only says the alert agent "fires notifications"; the JSON payload shape and the configurable webhook are invented.
  - fix: When a watchlist match occurs, the alert agent fires a notification (e.g. a webhook call or a logged alert) that identifies the article, the matched ticker(s) and the sentiment score.
- **not_in_prompt**: Structure the code so each agent is a separate module/function/class and the LangChain orchestrator explicitly invokes the scraper agent → sentiment agent → store in Azure DocumentDB → alert agent sequence for each headl
  - why: The prompt lists scraper, sentiment and alert agents and separately says to store scored articles; it does not require the store step to precede the alert step per headline, so a build that alerts and then stores would wrongly fail.
  - fix: Structure the code so each agent is a separate module/function/class and the LangChain orchestrator invokes the scraper agent, then the sentiment agent, then the alert agent, with scored articles stored in Azure DocumentDB.
- **not_in_prompt**: Include an end-to-end demo or test script that runs the pipeline on at least one scraped headline, shows the sentiment score and extracted tickers, verifies the document was written into Azure DocumentDB, and demonstrate
  - why: The prompt does not ask for a demo or end-to-end test script; tests and run instructions are covered by the shared section (unit tests without a live cluster, README run steps).
  - fix: delete
- **duplicate**: Use Azure DocumentDB for both the stored signals/articles collection and the watchlist collection—all reads and writes for those features must go to Azure DocumentDB (not to in-memory stores or other databases).
  - why: Bullet 4 already requires the watchlist to be queried from Azure DocumentDB and bullet 6 already requires scored articles to be persisted there.
  - fix: delete
- **duplicate**: Make Azure DocumentDB connection parameters (connection string/URI and database/collection names) and the notification webhook endpoint configurable (for example via environment variables) so a reviewer can run the pipel
  - why: Connection settings from environment variables and a .env.example are already required in the shared "What a gallery sample also needs" section; the webhook endpoint is not in the prompt.
  - fix: delete

### fintech-12 (minor_edits, 11 bullets)

- **not_in_prompt**: Implement the solution in Node.js and instantiate a LangChain agent named exactly "LangChain agent" to coordinate LLM calls, database queries, tools and memory.
  - why: The prompt says "build a Node.js LangChain agent"; it does not ask for an agent whose name is the literal string "LangChain agent", which is not a meaningful or checkable code requirement.
  - fix: Implement the solution in Node.js using a LangChain agent that coordinates LLM calls, database queries, tools and memory.
- **not_in_prompt**: Extract structured invoice fields by invoking an LLM extraction tool (the prompt’s "LLM extraction tool") from within the LangChain agent; the extraction must produce at minimum: invoiceNumber, vendorName, totalAmount, i
  - why: The prompt says only "extracts structured fields using an LLM tool" and matches on amount and vendor; invoiceDate, lineItems and referencedPoNumber are invented minimums.
  - fix: Extract structured invoice fields by invoking an LLM extraction tool from within the LangChain agent; the extracted fields must include at least the vendor and the total amount used for PO matching.
- **not_in_prompt**: Compute a combined numeric match score for each candidate PO that combines vendor similarity and amount difference (and whether an explicit PO number was present); include a score breakdown (vendorScore, amountDelta, com
  - why: The PO-number factor depends on the invented referencedPoNumber field, and the exact breakdown field names are not in the prompt; the prompt asks only that each candidate is scored on amount and vendor.
  - fix: Compute a numeric match score for each candidate PO that combines vendor similarity and amount difference.
- **vague**: Sort candidate POs by combined score and select or rank top candidates; include enough candidate metadata so a human can inspect why a match was chosen.
  - why: "Enough candidate metadata so a human can inspect why" is a judgement call a reviewer cannot check against the code.
  - fix: Rank candidate POs by match score and select the best match (if any) for the reconciliation result.
- **not_checkable**: Support manual corrections during a session by exposing a callable/manual-correction path that the LangChain agent records into its agent memory (exactly "agent memory"), and require that subsequent matching decisions in
  - why: "(exactly "agent memory")" asks for a literal phrase rather than a behaviour; the rest of the bullet (correction path, memory consulted by later matches, session scope) is traceable and checkable.
  - fix: Expose a manual-correction path that records corrections in the LangChain agent's memory, and have subsequent matching decisions in the same session consult that memory so corrected mappings are preferred; the memory is session-scoped.

### fintech-13 (minor_edits, 10 bullets)

- **not_in_prompt**: Package the aggregation pipelines as reusable functions that accept filtering parameters (at least strategy_id and an optional time range: start_timestamp, end_timestamp) and return structured numeric results for win rat
  - why: The prompt asks for pipelines per strategy; an optional start/end time range, total P&L and trade count are not asked for, and the metrics list repeats the two previous bullets.
  - fix: The aggregation pipelines are exposed as Python functions parameterised by strategy_id that return the computed win rate, average P&L and max drawdown.
- **not_in_prompt**: Add a context engineering layer in Python named/organized as such that accepts the aggregation output and formats a deterministic, LLM-ready text summary including strategy_id, analyzed period, trade count, win rate as p
  - why: The prompt says the layer "formats the aggregated stats for LLM-driven strategy review"; analyzed period, trade count, total P&L and top 3 trades are invented.
  - fix: A context engineering module takes the aggregation output and formats strategy_id, win rate, average P&L and max drawdown into a deterministic text block intended as LLM input for strategy review.
- **not_in_prompt**: Provide automated tests (unit or integration) that run the aggregation pipelines on the seeded data and assert the computed win rate, average P&L, and max drawdown match the expected values, and that the context engineer
  - why: The prompt does not ask for tests; the shared section already covers unit tests.
  - fix: delete
- **duplicate**: Include a Python data-seeding script that inserts representative signals, executions, and outcome documents for at least two different strategy_id values across a time range; the seeded dataset must be constructed so exp
  - why: The prompt does not ask for a seed script; the shared section already requires "A seed script loads sample data".
  - fix: delete
- **vague**: Each journal document inserted must include at minimum these fields: strategy_id (string), timestamp (stored in ISO 8601 / UTC), type (one of "signal", "execution", "outcome"), and for outcome documents a numeric pnl fie
  - why: "when applicable" gives the reviewer no way to decide whether a missing version field is a failure; the version rule is also restated in the next bullet.
  - fix: Each journal document includes at minimum strategy_id, a timestamp, a type of "signal", "execution" or "outcome", and for outcome documents a numeric pnl field.
- **vague**: Enforce immutability of journal entries in code by never issuing update operations for signal/execution/outcome events; implement document versioning by writing a new document with the same strategy_id and an incremented
  - why: The prompt only says the documents are immutable; "whenever a new version is created" never says what event produces a new version, so a reviewer cannot tell what code to look for.
  - fix: Journal entries are never updated or deleted in code; a correction to an existing entry is written as a new document that references the original and carries an incremented version field.
- **vague**: Create a time-series-optimized storage layout for the journal in Azure DocumentDB by either configuring a time-series collection (if supported) or creating an index on (strategy_id, timestamp) to support efficient time-s
  - why: The installed skills say nothing about time-series collections, and "if supported" leaves the reviewer two different things to check. The indexing skill (index-compound-esr) covers the compound index, which is the checkable part.
  - fix: Create a compound index on (strategy_id, timestamp) so the per-strategy, time-ordered aggregations are index-supported.

### fintech-14 (minor_edits, 10 bullets)

- **not_in_prompt**: For every state transition, append a transition log entry to the document that includes at least: previous state, new state, agent name (which specialist agent performed the step), decision/outcome, and an ISO8601 timest
  - why: The prompt asks only for "logging every transition with a timestamp"; agent name and decision/outcome are added fields the prompt does not require.
  - fix: Every state transition appends an entry to the document's transition log containing at least the previous state, the new state and a timestamp taken when the transition is applied.
- **not_in_prompt**: Use Beanie’s document read/write APIs for standard operations (and if a raw MongoDB atomic operation is required for the combined update, call it in code with an inline comment justifying why Beanie was not sufficient), 
  - why: The prompt asks for Beanie; it does not ask for a justifying inline comment, which is a code-style demand rather than a requirement.
  - fix: Loan application reads and writes go through Beanie document APIs; any raw Motor/PyMongo call is limited to the atomic state-update operation.

### fintech-15 (minor_edits, 10 bullets)

- **missing**: Client portfolio data is stored in a DocumentDB collection (the description says "client portfolio data in DocumentDB"), and the seed loads sample portfolios into it.
  - fix: Client portfolio data is stored in a DocumentDB collection (the description says "client portfolio data in DocumentDB"), and the seed loads sample portfolios into it.
- **not_in_prompt**: Ensure the agent’s final responses reference or cite the specific DocumentDB knowledge articles and the relevant portfolio values used in reasoning (e.g., include article titles/IDs and portfolio allocation numbers in th
  - why: The prompt asks to combine the two sources, not to cite articles or print portfolio numbers in the answer.
  - fix: delete
- **not_in_prompt**: Provide automated or manual tests that verify: (a) DocumentDB vector search returns expected articles for a sample query, (b) the portfolio tool returns structured client data, and (c) a follow-up conversational query pr
  - why: The prompt does not ask for tests, and (c) depends on non-deterministic LLM output so it cannot be checked reliably; the shared section already covers unit tests.
  - fix: delete
- **duplicate**: Add a clear Azure DocumentDB connection/configuration mechanism (environment variables or config file) and use it in the code paths that upsert and query the DocumentDB vector index.
  - why: The shared section already requires the connection string to come from environment variables; this bullet also weakens it by allowing a config file.
  - fix: delete
- **vague**: Implement the application in Node.js and instantiate a LlamaIndex RAG agent (use the name "LlamaIndex" in the code) to handle user conversations.
  - why: "use the name LlamaIndex in the code" is not something to check; what a reviewer can check is the dependency and the agent API used.
  - fix: The application is Node.js, package.json depends on llamaindex, and the conversational agent is built with LlamaIndex's agent API.
- **vague**: Expose a tool function the agent can call to fetch a client's live portfolio data (structured JSON with holdings, allocations, and quantities); the agent must call this tool during query handling rather than reading a st
  - why: The description says the portfolio data lives "in DocumentDB"; the bullet never says where the tool reads from, so a tool returning a hard-coded object would pass.
  - fix: Expose a LlamaIndex tool the agent calls to fetch a client's portfolio (holdings and allocations) from a DocumentDB collection; the agent invokes this tool during query handling.

### fintech-16 (minor_edits, 11 bullets)

- **not_in_prompt**: Provide an automated check or example (script or test) that simulates concurrent/process calls using the same idempotencyKey and verifies only one ChargeEvent is persisted and the subscription update is applied once.
  - why: The prompt asks for idempotency key checks, not for a concurrency test; the shared section already covers tests.
  - fix: delete
- **duplicate**: Ensure transactional error handling: on any error during the DocumentDB transaction the code aborts the transaction and does not persist a partial ChargeEvent or subscription update.
  - why: The earlier transaction bullet already requires commit/abort via withTransaction so that the two writes are atomic; this restates it.
  - fix: delete

### fintech-17 (minor_edits, 11 bullets)

- **missing**: Create a vector index (cosmosSearch) on the rationale embedding field so the stored rationales can be searched semantically (the prompt says the rationale is embedded "for semantic search", and the shared section assumes
  - fix: Create a vector index (cosmosSearch) on the rationale embedding field so the stored rationales can be searched semantically (the prompt says the rationale is embedded "for semantic search", and the shared section assumes a vector index exists, but no prompt-derived bullet requires creating one).
- **not_in_prompt**: Use LangChain to call the LLM with the engineered prompt and parse the model output into explicit fields: E_score, S_score, G_score and corresponding rationale texts.
  - why: The prompt asks only to "score each pillar (E, S, G) on a 1-10 scale with reasoning"; it does not dictate the field names E_score/S_score/G_score. An auditor reading these as required names would fail a correct implementation that names them differently (e.g. environmental.score).
  - fix: Use LangChain to call the LLM with the engineered prompt and parse the model output into a separate numeric score and rationale text for each of the three pillars (E, S, G).
- **not_in_prompt**: Write the scored document back to Azure DocumentDB (insert or update) so the stored document contains company id, E_score, S_score, G_score, pillar rationales, and the associated embedding(s).
  - why: Same issue: the exact field names E_score/S_score/G_score are not in the prompt. The prompt says "writes the scored document back".
  - fix: Write the scored document back to Azure DocumentDB (insert or update) so the stored document contains the company identifier, the three pillar scores, the pillar rationales, and the rationale embedding(s).

### fintech-18 (needs_rework, 10 bullets)

- **not_in_prompt**: Expose an HTTP endpoint (for example via Express) that the orchestrator uses to receive a chargeback claim (includes claim id) and that triggers the agent workflow end-to-end.
  - why: The prompt says only that "an orchestrator receives a chargeback claim"; it does not ask for an HTTP endpoint or Express. A CLI or function entry point would satisfy the prompt.
  - fix: The orchestrator has an entry point (function, CLI or HTTP endpoint) that accepts a chargeback claim and starts the agent workflow.
- **not_in_prompt**: When fetching evidence, the implementation must record and include the Azure DocumentDB collection names and document _id values in the evidence payload that is passed to downstream agents.
  - why: Nothing in the prompt, title or description asks for collection names or _id values to be carried in the evidence payload; the prompt only says the evidence agent "fetches transaction and communication documents from DocumentDB" and the evidence is passed on.
  - fix: delete
- **not_in_prompt**: The policy-reasoning agent must load dispute rules (from a JSON file or an Azure DocumentDB rules collection) and produce a human-readable rationale that maps which rules fired and why given the evidence; the agent
  - why: The prompt says the policy-reasoning agent "interprets the dispute rules". Requiring rule ids and the specific evidence fields that triggered each rule in the output is an invented output contract.
  - fix: The policy-reasoning agent applies the dispute rules (from a file or an Azure DocumentDB collection) to the gathered evidence and produces a reasoning output that the decision agent consumes.
- **not_in_prompt**: The decision agent must write an accept or reject outcome back to Azure DocumentDB by updating the original claim document or inserting a decision document; the written record must contain at minimum: claim id
  - why: The prompt asks the decision agent to "write the accept/reject outcome back to DocumentDB". The required UTC timestamp, decisioning agent identifier, rationale text and evidence document ID references are not in the prompt.
  - fix: The decision agent writes the accept/reject outcome back to Azure DocumentDB, either by updating the claim document or inserting a decision document, and the stored record links the outcome to the claim.
- **not_in_prompt**: All inter-agent messages and handoff payloads must be represented and logged as structured JSON so a reviewer can trace inputs and outputs between orchestrator → evidence → policy → decision.
  - why: Structured JSON logging of every handoff is not asked for by the prompt; the previous bullet already covers the sequential handoffs being implemented in code.
  - fix: delete
- **not_in_prompt**: Include automated tests (unit or integration) that submit a sample chargeback claim to the orchestrator endpoint and assert that Azure DocumentDB contains the expected final decision document with the correct
  - why: The prompt does not ask for tests, and an integration test asserting against a live Azure DocumentDB sits awkwardly beside the shared requirement that unit tests run without a live cluster.
  - fix: delete
- **duplicate**: Provide a script or instructions (and sample JSON) to seed Azure DocumentDB with example transaction and communication documents plus a sample claim so the reviewer can exercise the full workflow against Azur
  - why: Not in the prompt, and the shared "What a gallery sample also needs" section already requires a seed script that loads sample data.
  - fix: delete

### fintech-19 (minor_edits, 10 bullets)

- **not_in_prompt**: Chunk very large snapshots into bounded batches and send multiple unordered bulk write calls so the service can handle high-volume document ingestion without exceeding single-call limits.
  - why: The prompt asks for ordered=False bulk writes "for throughput"; it does not ask for chunking snapshots into bounded batches or mention single-call limits. A sample that bulk-writes a whole snapshot in one call satisfies the prompt.
  - fix: delete
- **not_in_prompt**: Implement the query to filter by equality on underlying and expiry and to sort results by strike (so the query uses the (underlying, expiry, strike) compound index to avoid full collection scans).
  - why: Filtering by underlying and expiry is traceable to "return the full chain for a given underlying and expiry date", but sorting by strike is not asked for anywhere; an auditor would fail an unsorted but index-backed query.
  - fix: Implement the chain query to filter by equality on underlying and expiry so that it is served by the (underlying, expiry, strike) compound index rather than a full collection scan.

### fintech-20 (minor_edits, 10 bullets)

- **not_in_prompt**: Implement deterministic cache key derivation from the incoming open banking API request (including HTTP method, URL/path, and relevant headers/body) and use that key to look up documents in Azure DocumentDB.
  - why: A cache key is implied by "checks DocumentDB for a cached response document", but the prompt does not dictate that the key must include HTTP method, URL/path, headers and body. A key built from the API call identity alone satisfies the prompt.
  - fix: Derive a deterministic cache key from the intercepted open banking API call and use it to look up the cached response document in Azure DocumentDB.
- **not_in_prompt**: Prevent duplicate concurrent background refreshes for the same cache key (for example by using an atomic findOneAndUpdate flag or an in-memory/per-key lock) so only one refresh is in-flight per key.
  - why: Refresh de-duplication is a quality refinement not asked for by the prompt, which only asks to "serve stale data immediately while refreshing in the background".
  - fix: delete
- **not_in_prompt**: Ensure failed background refreshes do not overwrite existing cached data with error responses; on refresh failure keep the previous cached document unchanged and retry on a subsequent stale-while-revalidate tri
  - why: Failure handling for background refreshes is not stated in the prompt, title or description.
  - fix: delete
- **not_in_prompt**: Include observable indicators in logs or responses that let a reviewer verify whether each response was served as a cache hit (fresh), cache hit (stale-while-revalidate served), or cache miss (live fetch), so
  - why: Hit/stale/miss indicators in logs or responses are not asked for by the prompt; they are a testability aid the drafter added.
  - fix: delete

### healthcare-01 (minor_edits, 11 bullets)

- **not_in_prompt**: Chunk lengthy patient records into configurable-size text chunks (with configurable overlap) and index each chunk as a separate vector document in Azure DocumentDB.
  - why: The prompt says only "stores chunked patient records in a DocumentDB vector index"; it does not ask for configurable chunk size or configurable overlap, so a builder with fixed-size chunks would fail an audit line the prompt never set.
  - fix: Chunk each patient record into text sections and write each chunk as its own document, with its embedding, to the Azure DocumentDB vector-indexed collection.
- **not_in_prompt**: Model and persist metadata on each indexed chunk that links it to the original record: include a patientId field, original document id, chunk id (or section id), and character/line offsets or section boundaries.
  - why: The prompt asks for a patientId field and "document references"; character/line offsets or section boundaries are invented detail the prompt does not state.
  - fix: Each indexed chunk document carries a patientId field and a reference to its source record (source document id and chunk or section id) so the answer can cite it.
- **not_in_prompt**: Include explicit, machine-checkable citations in the agent response mapping statements to source chunks (e.g., document id + chunk id or offsets) so each claim can be traced back to the original Azure DocumentDB document
  - why: The prompt asks for "a grounded answer with document references"; a per-statement mapping of each claim to a chunk is a stronger requirement than the prompt states.
  - fix: The agent response includes document references (e.g., source document id and chunk id) for the Azure DocumentDB chunks the answer was grounded in.
- **not_in_prompt**: Implement HIPAA-aware handling in code: avoid emitting full patient PHI to console or persistent logs during indexing/querying (e.g., redact or omit identifiable fields in debug logs) and show this behavior in the codeba
  - why: Neither the prompt, the title nor the description mentions logging or PHI redaction; the prompt's only access-control ask is the patientId field, which the retrieval-filter bullet already covers.
  - fix: delete
- **not_in_prompt**: Include a runnable example or automated test that indexes a sample patient record, then issues a clinical question for that patient and verifies the returned summary uses only that patient’s chunks and includes document 
  - why: The prompt does not ask for an example run or an end-to-end test; tests are already covered by the shared "Unit tests run without a live cluster" line, and the patient-scoped retrieval and citations are covered by their own bullets.
  - fix: delete
- **duplicate**: Ensure the LlamaIndex generation call receives the structured prompt and retrieved chunks, and that the agent returns a grounded answer that cites source chunks.
  - why: The prompt-construction half repeats the preceding context-engineering bullet, the citation half repeats the following citations bullet, and the wiring is repeated again by the answer_clinical_question bullet.
  - fix: delete

### healthcare-02 (minor_edits, 10 bullets)

- **not_in_prompt**: Compute an embedding from the patient_profile and perform a vector search against the DocumentDB index of trial criteria, issuing a vector query that returns a top-N list of candidate trials (N must be a configurable par
  - why: The prompt says "uses vector search against a DocumentDB index of trial criteria to find candidate trials"; it never asks for the candidate count to be configurable.
  - fix: Compute an embedding from the patient profile and run a vector search (cosmosSearch query visible in the code) against the Azure DocumentDB index of trial criteria, returning the top-k candidate trials.
- **not_in_prompt**: Implement a LangChain "eligibility agent" that receives the patient_profile and the candidate trials and applies trial-specific inclusion/exclusion rules, producing a per-trial eligibility decision (eligible / ineligible
  - why: The prompt says the eligibility agent "applies inclusion/exclusion rules"; the three-way eligible/ineligible/conditional outcome and rule-level reasons are not in the prompt, so a boolean decision would be marked as failing.
  - fix: Implement a LangChain eligibility agent that receives the patient profile and the candidate trials, applies each trial's inclusion/exclusion rules, and produces a per-trial eligibility decision.
- **not_in_prompt**: Implement a LangChain "consent agent" that, for each eligible (or conditionally eligible) trial, generates a plain-language trial summary for the patient that explains purpose, procedures, and key consent points; the out
  - why: The prompt asks for "a plain-language trial summary for the patient"; the required content (purpose, procedures, key consent points) is not stated in the prompt, and "conditionally eligible" depends on the invented three-way decision.
  - fix: Implement a LangChain consent agent that, for each eligible trial, generates a plain-language trial summary written for the patient.
- **not_in_prompt**: Persist the final match results to Azure DocumentDB: insert or upsert a document that includes at minimum patient identifier (or generated match id), timestamp, list of candidate trials, eligibility decisions with reason
  - why: The prompt says only "Store match results in DocumentDB"; a timestamp and per-decision reasons are not asked for.
  - fix: Persist the match results to Azure DocumentDB: write a document that identifies the patient (or match) and contains the candidate trials, their eligibility decisions and the consent summaries.
- **not_in_prompt**: Include a runnable example or sample invocation in code that demonstrates the full end-to-end flow: accept a sample patient_profile, perform vector search, run eligibility agent, run consent agent, and store the result i
  - why: The prompt does not ask for a sample invocation; the entrypoint bullet already requires the callable pipeline, and running it is covered by the shared README line.
  - fix: delete
- **duplicate**: Connect to Azure DocumentDB and execute the vector search on the DocumentDB index of trial criteria (show the DocumentDB query/SDK call that performs vector similarity search and returns trial documents).
  - why: This restates the preceding bullet (vector search against the trial-criteria index returning trial documents); the only addition, that the query call is visible in code, belongs in that bullet.
  - fix: delete

### healthcare-03 (minor_edits, 9 bullets)

- **not_in_prompt**: Define a Mongoose schema/model for interaction documents that includes at minimum: canonical drug identifiers (drugA, drugB or a canonical pair key), evidence text, an existing severity field (if present), clinicalRecomm
  - why: The prompt says the agent "maintains a drug interaction knowledge base"; evidence text, a stored clinicalRecommendation and source/reference fields are invented, and "an existing severity field (if present)" cannot be checked either way.
  - fix: Define a Mongoose schema/model for interaction documents keyed by a pair of drug identifiers with a description of the interaction.
- **not_in_prompt**: If no interaction document exists for a given pair, the code must include that pair in the result set with an explicit "no documented interaction" outcome (rather than omitting it).
  - why: The prompt asks for "a ranked list of interactions"; it says nothing about reporting pairs that have no interaction document.
  - fix: delete
- **not_in_prompt**: Build a LangChain prompt template (prompt engineering) that injects each retrieved interaction document's structured fields (evidence, existing severity if any, references) and instructs the LLM to assess or re-assess se
  - why: The field list (evidence, existing severity, references) comes from the invented schema in the earlier bullet, not from the prompt, which only says "uses prompt engineering to instruct the LLM to assess severity".
  - fix: Build a LangChain prompt template that injects the retrieved interaction documents and instructs the LLM to assess the severity of each pair and give a clinical recommendation.
- **not_in_prompt**: Send the engineered prompt to an LLM via LangChain and parse the model's structured response into at least: assessed severity (numeric score or categorical label), a short clinical recommendation, and a brief explanation
  - why: The prompt asks for severity and clinical recommendations; "a brief explanation citing evidence when applicable" is neither in the prompt nor checkable ("when applicable").
  - fix: Send the engineered prompt to an LLM via LangChain and parse the response into an assessed severity (score or label) and a clinical recommendation for each pair.
- **not_in_prompt**: Aggregate the results and return a ranked list sorted by assessed severity (most severe first) with each entry containing the drug pair, assessed severity, clinical recommendation, evidence excerpt, and source reference(
  - why: "evidence excerpt" and "source reference(s)" are not in the prompt, which asks for "a ranked list of interactions with clinical recommendations".
  - fix: Return a ranked list sorted by assessed severity (most severe first), each entry containing the drug pair, the assessed severity and the clinical recommendation.

### healthcare-04 (minor_edits, 9 bullets)

- **duplicate**: Return similarity scores or distances with search results and sort results by similarity.
  - why: The prompt does not ask for scores, and the shared section already has "Search results include the similarity score"; the preceding search-endpoint bullet already requires a semantic-similarity search.
  - fix: delete
- **duplicate**: Use the Azure DocumentDB (MongoDB‑compatible) cluster API to create the index and run the vector search operations (i.e., index creation and vector query calls are visible in the code).
  - why: Index creation is already required by the vector-ivf bullet and the vector query by the search-endpoint bullet; this adds nothing checkable beyond them.
  - fix: delete

### healthcare-05 (needs_rework, 10 bullets)

- **not_in_prompt**: Provide a booking tool that creates an appointment document in Azure DocumentDB (appointments collection) with explicit fields patientId, providerId, slotId, start, end, status ('booked'), and created/updated timestamps.
  - why: The prompt only says the tools "create appointment documents"; it names no collection and no field names, so an implementation with different field names would wrongly fail this line.
  - fix: Provide a booking tool that creates an appointment document in Azure DocumentDB that links the patient, the provider and the chosen slot and records the appointment's time and status.
- **not_in_prompt**: Ensure booking is atomic: the booking tool must mark the chosen slot document’s status to 'booked' and create the appointment document inside a single MongoDB multi-document transaction (startSession/startTransaction + c
  - why: The prompt attaches "atomically" to rescheduling ("handle rescheduling by updating slot status atomically") and never mandates a multi-document transaction; a conditional single-document update (findOneAndUpdate with a status precondition) also satisfies "updating slot status atomically". The shardi
  - fix: The booking tool claims the slot atomically so that two patients cannot book the same slot (e.g. a conditional update of the slot's status from 'available' to 'booked', or a transaction covering the slot update and the appointment insert).
- **not_in_prompt**: Implement rescheduling that updates the appointment and swaps slot statuses atomically: in the reschedule flow update the old slot to 'available', update or create the appointment for the new slot, and mark the new slot 
  - why: Rescheduling atomically is in the prompt, but "inside a single transaction" prescribes one mechanism; the prompt says "updating slot status atomically", which a conditional update of the new slot's status also meets.
  - fix: Implement rescheduling that releases the old slot, claims the new slot and updates the appointment, with the slot status change performed atomically (conditional update or transaction) so the new slot cannot be double-booked.
- **not_in_prompt**: Implement cancellation that sets appointment.status to 'cancelled' and sets the associated slot.status to 'available' atomically in one transaction against Azure DocumentDB.
  - why: Cancellation is traceable to the description, but neither the prompt nor the description asks for cancellation to be transactional or names the status values.
  - fix: Implement cancellation that marks the appointment cancelled and makes its slot available again.
- **not_in_prompt**: Detect and handle concurrent booking conflicts: booking/rescheduling code must verify transaction/update results (e.g., matched/modified counts or transaction commit status) and return a clear user-facing message when a 
  - why: Checking the update result follows from "atomically", but "offering next available slot alternatives" is a feature the prompt never mentions.
  - fix: Booking/rescheduling code checks the update or transaction result and returns a clear user-facing message when the slot was no longer available.
- **not_in_prompt**: Include an end-to-end example or test script that demonstrates: a user books a slot, then says "move it an hour later", and the agent uses agent memory + the LangChain tools to perform the reschedule
  - why: The prompt asks for the agent behaviour, not for a demo or test script; the behaviour itself is already covered by the agent-memory bullet.
  - fix: delete

### healthcare-06 (minor_edits, 10 bullets)

- **not_in_prompt**: Ensure the chatbot returns structured triage advice on each request, including at minimum an urgency level field, recommended next steps, and references to source guideline sections
  - why: The prompt says "structured triage advice with urgency level"; "recommended next steps" and "references to source guideline sections" are added fields (and the sources clause duplicates the provenance bullet).
  - fix: The chatbot returns structured triage advice (JSON or a structured object) that includes an urgency level field.
- **not_in_prompt**: Include provenance in responses by listing DocumentDB document identifiers, snippets, or links to the specific guideline sections retrieved
  - why: The prompt asks to retrieve the most relevant guideline sections and ground the answer in them; it does not ask the response to cite or list them.
  - fix: delete
- **not_in_prompt**: Verify outputs conform to the safety guardrails at runtime: responses must contain a professional-consultation recommendation and must not state definitive diagnoses; if a generated response fails this check the system r
  - why: The prompt says to "use prompt engineering to enforce safety guardrails"; runtime output validation, sanitisation and fallback responses are a different mechanism the prompt does not ask for.
  - fix: delete
- **duplicate**: Build the embedding-and-indexing pipeline that generates embeddings for each guideline section and writes those embeddings into the DocumentDB vector index alongside section IDs and metadata
  - why: The previous bullet already requires the guideline documents in Azure DocumentDB to carry text, metadata and the vector field covered by the vector index; this line checks the same code.
  - fix: Merge into the previous bullet: "...each guideline section is stored in Azure DocumentDB with its text, metadata and an embedding vector, and a DocumentDB vector index is created on the vector field."
- **vague**: Expose a single-agent runtime that accepts a patient symptom description, performs retrieval from the DocumentDB vector index, and returns the structured triage advice in one end-to-end flow
  - why: "single-agent runtime" is not a term from the prompt and retrieval + generation + structured output are already covered by the retriever, chain and structured-advice bullets.
  - fix: The chatbot accepts a free-text symptom description and returns the structured triage advice in one request/response flow.

### healthcare-07 (minor_edits, 10 bullets)

- **not_in_prompt**: Define a Beanie Document model for lab results that stores patientId, testCode, value, and timestamp fields (types and names must match exactly).
  - why: The prompt names the four fields but gives no types, so "types ... must match exactly" has nothing to match against.
  - fix: Define a Beanie Document model for lab results with fields named exactly patientId, testCode, value and timestamp.
- **not_in_prompt**: Make the moving-average aggregation window configurable (by number of samples or by a time range parameter) and show the pipeline accepts that parameter.
  - why: The prompt asks for pipelines that compute moving averages; it says nothing about the window being configurable.
  - fix: delete
- **not_in_prompt**: When the change stream detects a critical value (defined by configurable critical thresholds), the async listener must trigger a real-time alert action (for example, call an async callback, emit a log message marked as a
  - why: "configurable" thresholds and a demo script are not in the prompt, which asks only that the change stream trigger real-time alerts when critical values are written.
  - fix: When the change stream delivers a newly written lab result whose value is critical, the async listener triggers an alert action (for example an async callback, an alert-level log message, or a queued notification).
- **not_checkable**: Create indexes and a storage pattern appropriate for time-series queries (e.g., compound index on patientId and timestamp or an explicit time-series document pattern) and show that queries sort/scan by timestamp efficien
  - why: "show that queries sort/scan by timestamp efficiently" is a performance claim a code reviewer cannot verify; the prompt only asks that results be stored as time-series documents with the given fields.
  - fix: Lab results are stored following a time-series document pattern (one measurement per document with patientId, testCode, value, timestamp), with an index that supports per-patient, per-test queries ordered by timestamp.

### healthcare-08 (needs_rework, 10 bullets)

- **not_in_prompt**: Implement the system in Node.js and use LangChain for Node.js to build a multi-agent architecture with an orchestrator component and two agents named exactly "medical-review agent" and "insurer-comms agent".
  - why: The prompt names the agents' roles, not identifiers in code; requiring the exact strings would fail a correct implementation that calls them medicalReviewAgent or similar.
  - fix: Implement the system in Node.js with LangChain, as a multi-agent architecture with an orchestrator and two distinct agents: a medical-review agent and an insurer-comms agent.
- **not_in_prompt**: The orchestrator must read a pre-auth request from Azure DocumentDB (a configurable collection/namespace) by connecting to Azure DocumentDB and querying for a queued or new pre-auth request document.
  - why: The prompt says the orchestrator "reads a pre-auth request from DocumentDB"; a configurable collection and a queued/new status model are invented and would fail a sample that reads the request by id.
  - fix: The orchestrator reads a pre-auth request document from Azure DocumentDB and starts the workflow with it.
- **not_in_prompt**: The "medical-review agent" must retrieve clinical criteria stored in Azure DocumentDB (from a configurable collection) and run a deterministic clinical-necessity check that compares the pre-auth request data against thos
  - why: "deterministic" is not in the prompt; a LangChain agent that reasons over the stored criteria with the LLM also "checks clinical necessity against stored criteria".
  - fix: The medical-review agent retrieves the clinical criteria stored in Azure DocumentDB and checks the pre-auth request's clinical necessity against them.
- **not_in_prompt**: The "medical-review agent" must return a structured review object containing at minimum: a decision (e.g., pass/fail), the IDs of matched criteria, and a short rationale string explaining the decision.
  - why: The prompt does not specify the shape of the review; "IDs of matched criteria" in particular is invented.
  - fix: The medical-review agent returns a review result (its clinical-necessity decision and the reasoning behind it) that the orchestrator passes to the insurer-comms agent.
- **not_in_prompt**: The "insurer-comms agent" must produce a submission document (single text or structured object) that includes the original request identifier, key request details, the clinical-review decision and cited criteria, and a h
  - why: The prompt says the insurer-comms agent "drafts the submission letter"; the required list of contents (request identifier, cited criteria, etc.) is not in the prompt.
  - fix: The insurer-comms agent drafts the submission letter from the pre-auth request and the medical review's outcome.
- **not_in_prompt**: The medical-review check must be auditable in code: the implementation must expose the exact criteria matching logic (e.g., function or module) so a reviewer can inspect how criteria IDs map to decision outcomes.
  - why: Auditability and an explicit criteria-ID-to-decision mapping are not asked for; the prompt assigns the check to a LangChain agent.
  - fix: delete
- **not_in_prompt**: Include at least one end-to-end example or test script that inserts or uses a sample pre-auth request in Azure DocumentDB, runs the orchestrator, and verifies that the submission document and updated status are written b
  - why: The prompt asks for the workflow and the write-back, not for a test or demo script; the write-back is already covered by the preceding store bullet.
  - fix: delete
- **duplicate**: All Azure DocumentDB operations (reads and writes) must use a single configurable connection URI/connection string or environment-variable configuration and demonstrate authentication and connection setup before performi
  - why: Connection string from environment variables and a single reused client are already in the shared "What a gallery sample also needs" section; the prompt itself says nothing about connection configuration.
  - fix: delete

### healthcare-09 (minor_edits, 9 bullets)

- **not_in_prompt**: Connect to Azure DocumentDB using Beanie (init_beanie with a motor client) pointed at the Mongo-compatible Azure DocumentDB endpoint and database.
  - why: The prompt names only "Beanie ODM"; it never names Motor. The documentdb-connection skill explicitly says Python async code for Azure DocumentDB should use PyMongo's AsyncMongoClient, not Motor (deprecated May 2024), so the bullet pins a driver the prompt does not ask for and the skills discourage.
  - fix: Connect to Azure DocumentDB through Beanie (init_beanie) with an async MongoDB-compatible client pointed at the Azure DocumentDB endpoint and database.
- **not_in_prompt**: Extract the de-identified text from the OpenAI response (e.g., from the assistant/content field) and validate that the returned text contains placeholders for the PHI categories rather than raw PHI from the original.
  - why: The prompt asks the pipeline to send each note to OpenAI and write the de-identified version back; it does not ask for a post-hoc validation step that checks the output for placeholders or residual PHI.
  - fix: Extract the de-identified text from the OpenAI response and use it as the content of the de-identified document.
- **duplicate**: Implement the pipeline as a Single-agent process that performs read → OpenAI call → write for each note in sequence.
  - why: "Single-agent" and "in sequence" appear nowhere in the prompt, and the read → OpenAI → write flow is already required by the read, OpenAI-call and insert bullets above it.
  - fix: delete

### healthcare-10 (minor_edits, 9 bullets)

- **not_in_prompt**: Use Azure DocumentDB's vector search capability to retrieve candidate documents and rank them by vector similarity; explicitly use cosine similarity for ranking the top matches.
  - why: The prompt says "ranked by vector similarity" and the description says "using DocumentDB vector search"; neither names cosine. Cosine appears only in the concepts list, which is not one of the traceability sources, so requiring it specifically goes beyond what the builder is told.
  - fix: Use Azure DocumentDB vector search (a cosmosSearch vector index and a $search/cosmosSearch query) to retrieve and rank formulary documents by vector similarity using the index's configured similarity metric.
- **duplicate**: Return the top 10 matches sorted by descending cosine similarity; each returned item must include the document's name, indications, contraindications, dosing, and the similarity score.
  - why: The prompt asks only for "the top 10 formulary matches ranked by vector similarity"; the mandatory field list and the similarity score are not in the prompt, and "Search results include the similarity score" is already a shared gallery bullet.
  - fix: Return exactly the top 10 formulary matches ordered by descending vector similarity.
- **duplicate**: Include error handling and clear HTTP responses for missing/invalid query text (e.g., 400 for empty query) and for successful searches (200 with JSON array), so a reviewer can exercise the endpoint and validate results.
  - why: The prompt does not ask for input validation or error responses; the shared gallery section already requires a clear error for an empty query, so this bullet duplicates it under the prompt-derived heading.
  - fix: delete

### healthcare-11 (minor_edits, 10 bullets)

- **contradicts_prompt**: The DocumentDB aggregation tool must return structured JSON objects (or Python dicts) that include the computed prioritisation score and the generated outreach talking points so the agent's final output is a prioritized 
  - why: The prompt has the aggregation tool find the patients and the agent then prioritise and generate talking points. The tool runs before the LLM, so it cannot return the LLM-produced priority score and talking points; the bullet assigns the agent's job to the tool.
  - fix: The agent's final output is a prioritised patient list with outreach talking points attached for each care gap type.
- **not_in_prompt**: The aggregation pipeline must compute and return for each candidate patient at minimum: patient id, age, diagnoses list, lastVisitDate (ISO), and a list of identified care gap types (e.g., "mammogram overdue", "colonosco
  - why: The prompt names the inputs (age, diagnosis, last-visit documents) and the goal (patients missing recommended screenings) but prescribes no output schema; the exact field list and ISO date format are invented.
  - fix: The aggregation output identifies each candidate patient together with the recommended screenings they are missing, so the agent can prioritise and generate talking points per gap type.
- **duplicate**: Use explicit, coded criteria in the aggregation pipeline (or a pre-processing step called by the pipeline) that determine missing screenings based on age ranges, diagnosis codes, and last-visit date comparisons (e.g., la
  - why: The preceding bullet already requires the aggregation pipeline to inspect age, diagnosis and last-visit data and emit patients missing recommended screenings; this bullet restates the same requirement with more detail.
  - fix: delete
- **vague**: For each distinct care gap type, generate outreach talking points tailored to that gap using the LangChain LLM (the code must produce per-patient or per-gap talking points, not a single generic message).
  - why: The prompt says "generate outreach talking points for each gap type"; allowing "per-patient" as an alternative lets an implementation that never produces per-gap-type talking points pass.
  - fix: For each distinct care gap type, have the LangChain agent generate outreach talking points for that gap type (not a single generic message).

### healthcare-12 (minor_edits, 10 bullets)

- **not_in_prompt**: On startup create a TTL index (using Mongoose/collection.createIndex) on the cleaningExpiresAt field with expireAfterSeconds set from a configurable TTL timeout; create the index as a partial index that only applies to d
  - why: The prompt asks for TTL indexes that expire cleaning-state documents after a configurable timeout; it does not ask for a partial index. The next bullet (set cleaningExpiresAt only when the bed enters "cleaning") already restricts expiry to cleaning-state documents, and the documentdb-indexing TTL ru
  - fix: On startup create a TTL index (Mongoose schema index or collection.createIndex) on the cleaning expiry Date field with expireAfterSeconds derived from a configurable timeout, so cleaning-state documents expire automatically.
- **not_in_prompt**: Open a DocumentDB change streams watch on the bed status collection using Mongoose (model.watch or underlying collection.watch) configured to provide the needed document images (e.g., fullDocument and pre-image/fullDocum
  - why: The prompt asks to open a change stream to detect status transitions; it does not prescribe pre-images or fullDocumentBeforeChange, and the "as supported" hedge makes that part uncheckable. The skills say nothing about pre-image support on Azure DocumentDB.
  - fix: Open a change stream on the bed status collection using Mongoose (model.watch or the underlying collection.watch) and derive status transitions (occupied, available, cleaning) from its events.
- **duplicate**: Ensure deletion events originating from TTL index expiration are handled by the change stream handler and cause the occupancy summary cleaning count to decrement so the live summary stays correct.
  - why: The transition-detection bullet already lists "deletes from TTL expiration" as an event to handle, and the alert bullet already says the summary update "runs on every transition including deletions caused by TTL expiry".
  - fix: delete

### healthcare-13 (minor_edits, 10 bullets)

- **not_in_prompt**: Include a small sample high-risk patient cohort preloaded into the DocumentDB vector index and at least one documented example new patient input that demonstrates the full embedding, retrieval, and narrative-generation f
  - why: The prompt does not ask for sample data or a documented example input. Sample data loading is already covered by the shared bullet "A seed script loads sample data and creates the index".
  - fix: delete
- **duplicate**: Persist agent memory in Azure DocumentDB so that stored high-risk profile embeddings are recoverable across runs (code demonstrates loading memory from and saving memory to the DocumentDB vector index).
  - why: Bullet 2 already requires creating and persisting the agent memory that stores embeddings in the DocumentDB vector index (with insert/upsert visible in code). This bullet restates the same requirement with different wording.
  - fix: delete
- **vague**: Connect to an Azure DocumentDB instance (resource type Microsoft.DocumentDB/mongoClusters) and target its vector index APIs/collection for storing and querying embeddings.
  - why: "target its vector index APIs/collection" does not say what a reviewer should look for in the code; the resource type is an infrastructure fact already covered by the shared section. The vector-search skill says the native vector index type is `cosmosSearch` (vector-diskann / vector-hnsw / vector-iv
  - fix: Connect to Azure DocumentDB and create a `cosmosSearch` vector index (vector-diskann, vector-hnsw or vector-ivf) on the embedding field of the high-risk profile collection, used for both storing and querying embeddings.

### healthcare-14 (minor_edits, 9 bullets)

- **not_in_prompt**: Parse and validate the OpenAI output into a structured Python object (dict) containing distinct fields for chief complaint, assessment, plan, and follow-up, and include metadata fields patientId and a timestamp.
  - why: The prompt names the four sections and patientId; it never asks for a timestamp. A build without a timestamp field would be failed for something the prompt did not request (same timestamp requirement is repeated in bullet 6).
  - fix: Parse and validate the OpenAI output into a structured Python object (dict) with distinct fields for chief complaint, assessment, plan, and follow-up, plus the patientId.
- **not_in_prompt**: Persist the parsed summary as a structured document in Azure DocumentDB (MongoDB-compatible) so the document stores separate fields (not a single free-text blob) for chief complaint, assessment, plan, follow-up, patientI
  - why: "timestamp" is not in the prompt (see bullet 5); the rest of the bullet is traceable to "stores the result as a structured DocumentDB document linked to the patient record by patientId".
  - fix: Persist the parsed summary as a structured document in Azure DocumentDB so the document stores separate fields (not a single free-text blob) for chief complaint, assessment, plan, follow-up, and patientId.
- **not_in_prompt**: Ensure the pipeline links the summary to the patient record by verifying the provided patientId exists in a patients collection (or otherwise validating referential integrity) and failing or logging if it does not.
  - why: The prompt says the document is "linked to the patient record by patientId", i.e. the summary carries a patientId reference. It does not ask for a patients collection lookup or referential-integrity validation. The patientId reference is already required by bullet 6.
  - fix: delete
- **not_in_prompt**: Provide an end-to-end runnable example or test script that submits a sample telehealth transcript and patientId, shows the OpenAI-generated structured summary, and demonstrates that the document was written to Azure Docu
  - why: The prompt asks for a pipeline that accepts a transcript (covered by bullet 1), not for a demo script with a sample transcript or a read-back by patientId. Run instructions and tests are covered by the shared section.
  - fix: delete

### healthcare-15 (needs_rework, 10 bullets)

- **infeasible**: Define persistent document models using Beanie ODM (exact phrasing "Beanie ODM") for at least two collections: prescriptions and refill requests, with prescription fields including medicationName, patientId, daysSupplyRe
  - why: Beanie is a Python-only ODM (built on Pydantic and PyMongo/Motor); it cannot be used from the Node.js LangChain agent that bullet 1 and the prompt require. The prompt itself is contradictory on this point, and the bullet carries the contradiction forward so that no build can satisfy both bullets 1 a
  - fix: Define document models for prescriptions (including patientId, medication name, days supply remaining, refill count and an active/inactive marker) and refill requests through an ODM. The prompt names "Beanie ODM", which is Python-only and cannot run in Node.js; the auditor should note the prompt mis
- **not_in_prompt**: Implement a LangChain tool that checks refill eligibility for a given prescription by evaluating daysSupplyRemaining and refillCount and returns a deterministic result object {eligible: boolean, reason: string, daysSuppl
  - why: The prompt asks for an eligibility check based on days supply remaining and refill count; the exact return shape {eligible, reason, daysSupplyRemaining, refillCount} is invented and would fail a correct build that returns, say, a string or a differently shaped object.
  - fix: Implement a LangChain tool that checks refill eligibility for a given prescription by evaluating its days supply remaining and refill count and returns an eligible/not-eligible decision.
- **not_in_prompt**: Implement a LangChain tool that creates and persists a refill request document into Azure DocumentDB using the Beanie ODM model, setting requestedDate, createdBy='agent', eligible per the eligibility tool, and initial st
  - why: The prompt asks for a tool that creates a refill request document; the field values requestedDate, createdBy='agent', eligible and status='pending' are invented. Also inherits the Beanie/Node.js infeasibility from bullet 2.
  - fix: Implement a LangChain tool that creates and persists a refill request document (referencing the patient and the prescription/medication) in Azure DocumentDB through the ODM model.
- **not_in_prompt**: If the user utterance is ambiguous (multiple active prescriptions match the remembered or queried description), the agent must ask a clarifying question listing the matched medicationName values and wait for the user to 
  - why: The prompt does not mention ambiguity handling or clarifying questions; it only asks that memory lets the patient omit the drug name.
  - fix: delete
- **not_in_prompt**: On successful creation of a refill request, the agent must return a confirmation message to the user including the created refill request ID (DocumentDB document _id), medicationName, requestedDate, and current status; t
  - why: The prompt does not specify confirmation message contents (_id, medicationName, requestedDate, status). Persistence of the refill request document is already required by bullet 5.
  - fix: After creating a refill request, the agent confirms to the user that the request was submitted.
- **duplicate**: If the eligibility tool returns eligible=false, the agent must not create a refill request document and must return a clear message to the user explaining the reason (e.g., no refills remaining or daysSupplyRemaining too
  - why: Bullet 6 already requires that the agent calls the refill-creation tool only if eligible. The only new content is the explanatory message, which the prompt does not ask for.
  - fix: delete (or fold "and tells the user when a refill is not eligible" into bullet 6)

### healthcare-16 (minor_edits, 9 bullets)

- **not_in_prompt**: Endpoints must read and return a materialised summary document when a fresh summary exists (determined from lastRefreshed vs. the configured schedule); if no fresh summary exists the endpoint must run the aggregation pip
  - why: The prompt says summaries are "refreshed on a schedule" (covered by bullet 7). The compute-on-miss-and-persist fallback and the freshness test against the schedule are invented behaviour; a build that serves only scheduled summaries would be failed.
  - fix: Dashboard endpoints for expensive aggregations read and return the materialised summary documents from Azure DocumentDB instead of re-running the aggregation pipeline on every request.
- **vague**: Connect to Azure DocumentDB via the DocumentDB Atlas-compat API using the PyMongo driver (MongoClient) and load connection settings from configuration.
  - why: "via the DocumentDB Atlas-compat API" is not something a reviewer can check in code; no skill defines such an API (the skills describe MongoDB wire-protocol compatibility, and the vector-search skill explicitly says Atlas `$vectorSearch` syntax is not supported). It mirrors a concept tag, but the ch
  - fix: Connect to Azure DocumentDB with the PyMongo driver (MongoClient) over its MongoDB-compatible API, loading the connection string from configuration.
- **vague**: Ensure aggregation pipelines are written to scale to millions of patient records by applying $match stages early, performing grouping/counting inside the pipeline, and consuming results via aggregation cursors/batched fe
  - why: "written to scale to millions of records" is not checkable as stated, and the cursor/batched-fetching clause does not fit a `$facet` pipeline, which returns a single result document; a correct build could be failed on it. The checkable part is stage ordering, which the query-optimization skill suppo
  - fix: Aggregation pipelines place `$match` stages before `$group`/`$facet` so filtering happens in the database before grouping (checkable in the pipeline definitions), and grouping/counting is done inside the pipeline rather than in Python.

### healthcare-17 (minor_edits, 10 bullets)

- **not_in_prompt**: Implement the ingestion pipeline in Python using LlamaIndex to fetch PubMed abstracts for rare diseases (the code must show PubMed as the source and perform queries or use an identifier list to select rare-disease abstra
  - why: The prompt says the pipeline "ingests PubMed abstracts for rare diseases"; it does not say the code must fetch them live by query or identifier list. A sample that ingests a bundled PubMed abstract dataset satisfies the prompt but would fail this bullet.
  - fix: Implement the ingestion pipeline in Python using LlamaIndex to ingest PubMed abstracts for rare diseases (the code or bundled data must identify PubMed as the source of the abstracts).
- **duplicate**: Ensure the agent’s final answer ranks and presents supporting documents by semantic relevance and returns a structured list of citations (PubMed ID, abstract year, relevance score, and a short excerpt or snippet from the
  - why: Ranking by semantic relevance with a returned score is already the retrieval bullet, and citations carrying PubMed ID, abstract year and a chunk id or snippet is already the grounded-citations bullet; this bullet restates both.
  - fix: delete
- **duplicate**: Provide code paths or examples that demonstrate end-to-end behavior: ingest PubMed abstracts, build/store embeddings in Azure DocumentDB, run a researcher question through the RAG agent, and produce a ranked, citation-ri
  - why: Every element listed (ingest, embed and store, RAG agent answering a question, ranked citations with PubMed ID and year) is already its own bullet, and the shared section already requires a seed script and README run instructions; this adds nothing checkable beyond them.
  - fix: delete
- **vague**: Implement retrieval that computes semantic similarity (e.g., cosine similarity) between a question embedding and stored chunk embeddings and returns results sorted by relevance score (highest relevance first); the code m
  - why: As written this can be satisfied by loading all chunks and computing cosine similarity in Python, which bypasses the DocumentDB vector search the prompt implies with "stores vectors in DocumentDB" and the concept "Vector search". The documentdb-vector-search skill (vector-knn-query) says kNN in Azur
  - fix: Implement retrieval as a vector search executed in Azure DocumentDB (the $search stage with the cosmosSearch operator over a cosmosSearch vector index on the embedding field) that returns chunks ordered by relevance score, highest first, with the score returned for each retrieved item.

### healthcare-18 (minor_edits, 9 bullets)

- **duplicate**: Include example usage or a short integration test that demonstrates: ingesting a sample free-text report, running the LLM extraction + Pydantic validation, writing the validated document to Azure DocumentDB, and executin
  - why: The prompt does not ask for an integration test, and each step listed (ingestion entry point, LLM extraction, Pydantic validation, write to Azure DocumentDB, aggregation) is already a separate bullet; the shared section covers the seed script, README run steps and unit tests.
  - fix: delete

### healthcare-19 (minor_edits, 11 bullets)

- **not_in_prompt**: Implement the "pharmacy agent" to connect to Azure DocumentDB and retrieve the patient's current medications by patient id, returning a structured medication list including drug names, dosages, and frequencies.
  - why: The prompt says the pharmacy agent "checks current medications"; it does not require dosages or frequencies, so a sample whose medication records lack those fields would be marked wrong for something never asked.
  - fix: Implement the pharmacy agent to connect to Azure DocumentDB and retrieve the patient's current medications by patient id, returning a structured medication list.
- **not_in_prompt**: The synthesized unified care plan must include provenance metadata linking to the source Azure DocumentDB document ids and timestamps for each contributing input.
  - why: Neither the prompt, title nor description mentions provenance, source document ids or timestamps in the care plan; this is an invented requirement.
  - fix: delete
- **duplicate**: All DocumentDB interactions must operate against Azure DocumentDB (not Cosmos DB or other services) and accept a parameterized patient id input rather than using hard-coded patient data.
  - why: The naming/service constraint is the shared bullet "The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name", and the three agent bullets already require reads "by a supplied patient id" / "by the same patient id".
  - fix: delete
- **duplicate**: Ensure the orchestrator returns or logs the stored care plan content and the DocumentDB write result so a reviewer can verify that the synthesized plan was persisted.
  - why: The write-back bullet already requires the write operation to return or log the new document id, and the runnable-demonstration bullet already requires showing the final care plan being written; this restates both.
  - fix: delete
- **vague**: Define four distinct components named "GP agent", "specialist agent", "pharmacy agent", and "orchestrator" implemented with LangChain Python constructs (e.g., agents, tools, or AgentExecutors) so a reviewer can find thos
  - why: Python identifiers cannot contain spaces, so "those exact names" (e.g. "GP agent") cannot literally appear as component names; a reviewer must decide whether GPAgent or gp_agent counts. The prompt names the roles, not the identifiers.
  - fix: Define four distinct components, a GP agent, a specialist agent, a pharmacy agent and an orchestrator, each implemented with LangChain Python constructs (e.g., agents, tools, or AgentExecutors) and clearly identifiable by that role in its class, function or variable name.

### healthcare-20 (minor_edits, 10 bullets)

- **not_in_prompt**: Store provider profiles as Azure DocumentDB documents with explicit fields: specialty (string), languages (array), accepted_insurance (array), and bio (string), and include an embedded vector field named "embedding" cont
  - why: The prompt lists the four profile attributes and "embedded vectors" but never names the vector field; requiring the exact name "embedding" (and the exact key accepted_insurance) would fail a correct sample that names them differently.
  - fix: Store provider profiles as Azure DocumentDB documents with fields for specialty (string), languages (array), accepted insurance (array) and bio (string), plus an embedded vector field holding the numeric embedding for the profile.
- **not_in_prompt**: Support a top-k limit on returned results (default to 5) configurable via a query parameter to /find-provider and applied to the vector search call.
  - why: The prompt asks only for "ranked provider matches"; a configurable top-k query parameter with a default of 5 is not stated anywhere in the prompt, title or description.
  - fix: delete
- **not_in_prompt**: When no vector matches are found, return an empty results array with a successful HTTP response (e.g., 200) rather than an internal error.
  - why: The prompt specifies no behavior for the no-match case; this is invented API behavior, and the shared section already covers the endpoint's error handling it does require.
  - fix: delete
- **duplicate**: Provide a seed or import script that inserts multiple example provider documents into the Azure DocumentDB collection with embeddings generated via LlamaIndex so reviewers can reproduce queries like "Spanish-speaking car
  - why: The shared section already requires "A seed script loads sample data and creates the index". The only prompt-traceable addition is that the sample data must be able to answer the prompt's example query, which this bullet buries in a clause.
  - fix: The seeded provider data includes at least one provider that matches the prompt's example request (a Spanish-speaking cardiologist accepting Medicare), so that query returns a relevant top result.

### retail-01 (minor_edits, 11 bullets)

- **not_in_prompt**: For each product, compute a single embedding over the product title and description using the text-embedding-ada-002 model (code must call that model to produce embeddings).
  - why: The prompt says "Embed product titles and descriptions using text-embedding-ada-002"; it does not say one combined embedding. A build that embeds title and description separately would fail this check for no reason in the prompt.
  - fix: For each product, compute embedding(s) of the product title and description using the text-embedding-ada-002 model (code must call that model to produce the embeddings).
- **not_in_prompt**: When /search is called, embed the incoming natural language query using text-embedding-ada-002 and convert that embedding to the same BSON binary vector format used for stored product vectors.
  - why: The prompt asks only that the endpoint "embeds it"; converting the query vector to BSON binary is not requested, and the vector-knn-query rule in documentdb-vector-search passes the query as a plain `vector: queryVector` inside `$search`/`cosmosSearch`, so a correct build would likely fail this chec
  - fix: When /search is called, embed the incoming natural language query using text-embedding-ada-002 and use that vector as the query vector of the DocumentDB vector search.
- **duplicate**: Ensure the vector-ivf index is created with a dimension parameter that matches the embedding length returned by text-embedding-ada-002 (dimension value set programmatically or in the index creation code).
  - why: The prompt does not state this; it is already covered by the shared bullet "The vector index dimensions match the embedding model's output" in the gallery section of the same file.
  - fix: delete
- **duplicate**: Include a seeding or ingestion routine (script or endpoint) that adds product documents to Azure DocumentDB by computing embeddings with text-embedding-ada-002 and storing them as BSON binary vectors and ensuring the vec
  - why: Restates bullets 3, 4 and 5 (ada-002 embeddings, BSON binary storage, vector-ivf index) and the shared gallery bullet "A seed script loads sample data and creates the index". The prompt itself does not ask for a seed script.
  - fix: delete

### retail-02 (minor_edits, 11 bullets)

- **wrong_fact**: Generated embeddings are persisted into a DiskANN index (the project builds/writes a DiskANN index and stores the index files; source shows DiskANN index creation or update from the embeddings).
  - why: On Azure DocumentDB, DiskANN is a server-side `cosmosSearch` index of kind `vector-diskann` created with `createIndex` on the collection (documentdb-vector-search: vector-create-diskann-index, vector-choose-index-type); the app stores embeddings in documents and declares the index. There are no inde
  - fix: Product embeddings are stored on documents in Azure DocumentDB and the code creates a `cosmosSearch` vector index of kind `vector-diskann` on the embedding field (createIndex with cosmosSearchOptions: kind "vector-diskann", dimensions, similarity).
- **not_in_prompt**: The repository includes an ingest script that inserts 20,000 product purchase transactions into Azure DocumentDB and the script validates that 20,000 transactions were written (e.g., insertion counter or post-insert coun
  - why: The prompt says only "include a script to ingest 20,000 product purchase transactions"; it does not ask the script to validate or report the written count.
  - fix: The repository includes a script that ingests 20,000 product purchase transactions into Azure DocumentDB.
- **not_in_prompt**: The agent performs LlamaIndex vector search against the DiskANN index to find similar or co-purchased items (the search path uses LlamaIndex vector search APIs and queries DiskANN as the vector index backend).
  - why: The prompt asks for a Node.js LlamaIndex agent and a DiskANN index; it does not require the vector search itself to go through LlamaIndex's vector-store APIs. An agent tool that runs `$search`/`cosmosSearch` through the MongoDB driver (the path shown in the vector-knn-query rule) satisfies the promp
  - fix: The agent finds similar items with Azure DocumentDB vector search (`$search` with `cosmosSearch`) against the vector-diskann index, using the product embeddings.
- **not_in_prompt**: Web UI styled as an artistic online retailer is included and exposes product browsing and a recommendation widget where users can input a product ID and see the top 5 recommendations with reasoning (UI assets and CSS/HTM
  - why: The prompt asks for "an artistic UI to look like an online retailer's website". "Product browsing" and the specific recommendation-widget layout are not in the prompt.
  - fix: The app includes an artistic UI (HTML/CSS assets) styled to look like an online retailer's website.

### retail-03 (minor_edits, 10 bullets)

- **not_in_prompt**: Include a standalone ingestion script that generates and inserts 10,000 product transactions/documents: each generated product must have attributes, an OpenAI embeddings call to produce its vector, and insertion into Azu
  - why: The prompt asks for "a script to ingest 10,000 product transactions". It does not say each ingested record is a product that must receive its own OpenAI embeddings call, nor that the script must go through Beanie; product embeddings are already covered by bullet 2.
  - fix: Include a script that ingests 10,000 product transactions into Azure DocumentDB.
- **not_in_prompt**: The ingestion script must read the same Azure DocumentDB connection string from the application config file and verify the insert count is 10,000 (e.g., report or assert the number inserted).
  - why: The prompt does not ask the script to verify or report an insert count.
  - fix: The ingestion script reads the Azure DocumentDB connection string from the same config file as the app.
- **not_in_prompt**: Serve an artistic, retailer-style UI (HTML/CSS) from the FastAPI app (root route) that displays product details and a UI to request substitutes so the app looks like an online retailer website.
  - why: The prompt asks only for "an artistic UI to look like an online retailer's website". Serving it from the FastAPI root route and showing product details are implementation choices the prompt does not make.
  - fix: The app includes an artistic UI (HTML/CSS) styled to look like an online retailer's website.
- **duplicate**: Provide a FastAPI /substitute endpoint that accepts a product ID parameter, queries Azure DocumentDB vector search using cosine similarity, and returns the 5 closest alternative products (include product metadata and sim
  - why: The parenthetical "include ... similarity scores" repeats the shared gallery bullet "Search results include the similarity score"; the prompt itself does not ask for scores in the response.
  - fix: Provide a FastAPI /substitute endpoint that accepts a product ID, queries Azure DocumentDB vector search using cosine similarity (server-side, not client-side cosine computation), and returns the 5 closest alternative products.
- **duplicate**: The /substitute implementation must perform the nearest-neighbor retrieval via Azure DocumentDB vector search (server-side vector search query) rather than computing cosine similarity client-side.
  - why: Bullet 4 already requires the endpoint to query Azure DocumentDB vector search; this bullet only adds the "not client-side" clause, which belongs in bullet 4.
  - fix: delete

### retail-04 (needs_rework, 11 bullets)

- **infeasible**: The hybrid search tool must query Azure DocumentDB using a full-text $text query constructed from the rewritten search intent (the code must send a query document containing "$text").
  - why: The prompt names `$text`, but the documentdb-full-text-search SKILL.md and index-text-prefer-textsearch rule say the community `$text` operator is "not the DocumentDB search path" and mark it Incorrect; the DocumentDB path is a `createSearchIndexes` index queried with the `$search` stage and `text` 
  - fix: The hybrid search tool runs a full-text (keyword) query on Azure DocumentDB built from the rewritten search intent, using the DocumentDB full-text search path (`$search` stage with the `text` operator over a `createSearchIndexes` index); this is the prompt's `$text` arm.
- **missing**: The code creates the index that the full-text arm needs on Azure DocumentDB (a search index via `createSearchIndexes`) in addition to the vector index, since the query-optimizer skill notes a text query without a text in
  - fix: The code creates the index that the full-text arm needs on Azure DocumentDB (a search index via `createSearchIndexes`) in addition to the vector index, since the query-optimizer skill notes a text query without a text index errors.
- **not_in_prompt**: Provide a single LangChain agent (no multi-agent orchestration) that exposes a hybrid search tool callable by the agent.
  - why: The prompt asks for "a Python LangChain agent with a hybrid search tool"; it says nothing about forbidding multi-agent orchestration.
  - fix: The LangChain agent has a hybrid search tool that it calls to answer product searches.
- **not_in_prompt**: Both the $text and vector queries must return per-document relevance scores (or a score that the code exposes) that the hybrid tool uses for ranking.
  - why: The prompt says "merges the ranked results"; it does not require score-based fusion. The fts-hybrid-search rule fuses with Reciprocal Rank Fusion, which uses ranks and ignores scores, so a skill-conformant build would fail this check.
  - fix: delete
- **not_in_prompt**: The hybrid tool must merge the two ranked lists by normalizing/combining the $text and vector relevance scores, deduplicate documents present in both lists, and produce a single combined ranking.
  - why: "Normalizing/combining relevance scores" is one fusion method; the prompt only asks to merge the ranked results, and the skill's recommended method (RRF) is rank-based.
  - fix: The hybrid tool merges the full-text and vector ranked lists into one combined ranking (for example Reciprocal Rank Fusion or score fusion), deduplicating documents that appear in both.
- **not_in_prompt**: The merged result set must be sorted by the combined relevance score and the tool must return the top-N matches (N must be configurable in code).
  - why: The prompt says the tool "returns the best matches"; it does not ask for N to be configurable.
  - fix: The tool returns the top matches from the merged ranking, ordered by combined rank/score.
- **not_in_prompt**: The agent must handle the case where one side of the hybrid search (either $text or vector) returns zero results by still returning merged results from the other side rather than failing.
  - why: The prompt does not state this fallback behaviour; it is a robustness requirement the drafter added.
  - fix: delete
- **duplicate**: All queries to the database must be sent to Azure DocumentDB (the MongoDB-compatible cluster) from the running Python code (i.e., the hybrid search tool must execute real queries against Azure DocumentDB, not only simula
  - why: Bullets 4 and 5 already require the full-text and vector queries to be run against Azure DocumentDB; this adds nothing checkable beyond them.
  - fix: delete

### retail-05 (minor_edits, 11 bullets)

- **not_in_prompt**: Detect and handle optimistic-lock conflicts (zero documents matched due to version mismatch) by retrying a configurable number of times or returning a specific conflict error if retries are exhausted.
  - why: The prompt says only "Handle optimistic locking with a version field"; it does not ask for a retry loop or a configurable retry count.
  - fix: Detect an optimistic-lock conflict (the conditional update matched zero documents because the version changed) and handle it explicitly, either by retrying or by returning a distinct conflict error.
- **not_in_prompt**: Include an automated integration test or concurrency simulation that issues parallel add-to-cart requests and asserts that no overselling occurs (inventory never drops below zero and total reserved items do not exceed in
  - why: Neither the prompt nor the description asks for a test or a concurrency simulation; overselling prevention is already checkable through the conditional stock >= qty update bullet.
  - fix: delete
- **duplicate**: Apply the cart change (insert or update item quantities) within the same transaction session so the inventory change and cart change are committed or aborted together.
  - why: The preceding bullet already requires the inventory decrement and the cart insert/update to run inside the same session and transaction, and the commit/abort bullet covers the atomic outcome.
  - fix: delete

### retail-06 (needs_rework, 11 bullets)

- **not_in_prompt**: The fetch_order_history tool queries Azure DocumentDB (orders collection) with a MongoDB find() that returns recent orders for a customer (includes fields such as order_id, order_date, items, total_amount, status) and pa
  - why: The prompt asks for a tool that fetches order history; it says nothing about pagination or limiting results.
  - fix: The order-history tool queries the orders collection in Azure DocumentDB and returns a customer's orders (e.g. order id, date, items, total, status).
- **not_in_prompt**: Uses LangChain agent memory (agent memory) to persist conversation context across turns and explicitly stores at minimum the last-referenced customer identifier and the last-referenced time-range so follow-up questions c
  - why: The prompt asks for agent memory that maintains conversation context so follow-ups resolve; it does not prescribe explicitly storing a customer identifier and time range as separate memory slots, which rules out the ordinary LangChain conversation-history memory.
  - fix: Uses LangChain agent memory to carry conversation context across turns, so a follow-up such as "what about last month?" is resolved against the customer discussed in the previous turn.
- **not_in_prompt**: Handles empty or error cases gracefully: when no orders match a query or aggregation returns no data the agent responds with an informative message (e.g., "no orders found for that customer/time range") and database erro
  - why: Nothing in the prompt, title or description asks for empty-result or database-error handling.
  - fix: delete
- **duplicate**: All database operations in code explicitly run against Azure DocumentDB (resource = Azure DocumentDB) and use MongoDB-compatible query/aggregation operators; the repository includes at least one documented example aggreg
  - why: Targeting Azure DocumentDB is already in the connection bullet, and the aggregation pipeline and find() query are already required by the spend-summary and order-history tool bullets; the "documented example" wording adds a documentation requirement the prompt does not state.
  - fix: delete

### retail-07 (minor_edits, 10 bullets)

- **not_in_prompt**: Process reviews concurrently in an asynchronous pipeline (e.g., using asyncio.gather or an async worker/queue with semaphore-based concurrency control) so OpenAI calls and DB upserts are non-blocking.
  - why: The prompt asks for an "async Python pipeline" using Beanie, which the first bullet (async/await + Beanie) already covers; it does not require concurrent fan-out of reviews via gather or a semaphore.
  - fix: delete
- **not_in_prompt**: Implement and expose a summary aggregation query executed against Azure DocumentDB that groups results by product identifier and by sentiment (label or bucket), returning at minimum counts per group and average sentiment
  - why: The prompt asks for a summary aggregation grouped by product and sentiment; "average sentiment_score" and "Motor" are not in the prompt, and the documentdb-connection skill says new Python async code should use PyMongo's AsyncMongoClient rather than the deprecated Motor, so naming Motor steers the c
  - fix: Includes a summary aggregation pipeline, run through Beanie against Azure DocumentDB, that groups reviews by product and by sentiment and returns a count per group.

### retail-08 (minor_edits, 9 bullets)

- **not_in_prompt**: Write the generated drafts back to Azure DocumentDB by inserting a document into a campaigns collection named "campaigns" (each saved document must include the segment id/name, subject, body, raw LLM output, and a creati
  - why: The prompt says "Write the generated drafts back to a campaigns collection"; it does not ask for the raw LLM output or a creation timestamp to be stored.
  - fix: Writes each generated draft (subject line and body copy, together with the segment it was generated for) as a document in a `campaigns` collection in Azure DocumentDB.

### retail-09 (minor_edits, 9 bullets)

- **not_in_prompt**: Implement the system in Python using a LangChain multi-agent architecture with three agents named exactly "forecast agent", "supplier agent", and "orchestrator agent".
  - why: The prompt describes the three roles but never requires the code to use those exact names; a builder with classes like ForecastAgent/SupplierAgent/Orchestrator would fail this bullet for no reason.
  - fix: Implement the system in Python using a LangChain multi-agent architecture with three distinct agents: a forecast agent, a supplier agent, and an orchestrator agent.
- **not_in_prompt**: The "supplier agent" must read supplier lead time DocumentDB documents from Azure DocumentDB and select a best supplier per product based on lead time (selection logic must be coded and return at least supplier_id and le
  - why: The prompt says only "selects the best supplier based on lead time documents"; the specific field names supplier_id and lead_time are invented.
  - fix: The supplier agent must read supplier lead time documents from Azure DocumentDB and select a best supplier per product based on lead time, returning the chosen supplier's identifier and its lead time.
- **not_in_prompt**: The "orchestrator agent" must deterministically reconcile the agents' outputs per product (use the forecast agent's quantity together with the supplier agent's selected supplier) and produce a single purchase order decis
  - why: "Deterministically" is not in the prompt or description ("reconciled by an orchestrator"); an LLM-driven LangChain orchestrator agent, which the prompt allows, would not be deterministic.
  - fix: The orchestrator agent must reconcile the agents' outputs per product (the forecast agent's quantity together with the supplier agent's selected supplier) into a single purchase order decision per product.
- **not_in_prompt**: Provide an end-to-end demonstration or test run that seeds Azure DocumentDB with sample sales velocity and supplier lead time documents, executes the LangChain multi-agent flow, and verifies that exactly one purchase ord
  - why: The prompt does not ask for a demo or verification run; seed data and tests are covered by the shared gallery section ("A seed script loads sample data", "Unit tests run without a live cluster").
  - fix: delete
- **duplicate**: The system must avoid writing duplicate purchase order documents to Azure DocumentDB for the same product when a pending or recently-created order exists in shared agent memory (i.e., orchestrator skips writing and retur
  - why: Restates the previous bullet (consult shared agent memory to detect and prevent duplicate orders) and adds an invented behaviour ("returns existing order info") the prompt does not ask for.
  - fix: delete

### retail-10 (minor_edits, 11 bullets)

- **not_in_prompt**: Declare Mongoose compound indexes index({ tenantId: 1, sku: 1 }) on the Product and Inventory schemas.
  - why: The prompt asks for compound indexes on (tenantId, sku) and (tenantId, createdAt) but does not say which collections get which; assigning (tenantId, sku) to both Product and Inventory is the drafter's choice and would fail a reasonable build that indexes only the sku-bearing collection(s).
  - fix: Declare a Mongoose compound index { tenantId: 1, sku: 1 } (schema.index) on every schema that has a sku field.
- **not_in_prompt**: Prevent direct model usage from business logic by exposing only the repository API; include at least one automated test or runtime check that attempts a query without tenantId and asserts the repository rejects it.
  - why: The prompt asks to enforce isolation at the repository layer; it does not ask for an automated test of the rejection. Tests belong to the shared section ("Unit tests run without a live cluster").
  - fix: Business logic/route handlers use only the repository API and never call Mongoose models directly.
- **not_in_prompt**: Ensure index creation is performed/verified at runtime (e.g., Mongoose schema.index calls are applied and the running app can verify the required indexes exist on the Azure DocumentDB collections via the driver).
  - why: The prompt asks to create the compound indexes; a runtime verification step ("the running app can verify the required indexes exist via the driver") is not requested, and index creation itself is covered by the two schema.index bullets plus the shared seed-script bullet.
  - fix: The declared compound indexes are actually created on the Azure DocumentDB collections (Mongoose autoIndex/syncIndexes or the seed script), not only declared in code.
- **duplicate**: Connect Mongoose to Azure DocumentDB using a configurable connection string (e.g., environment variable) so the app runs against an Azure DocumentDB MongoDB-compatible endpoint.
  - why: The configurable/environment-variable connection string is already the first bullet of the shared gallery section; only "connect via Mongoose to Azure DocumentDB" is prompt-specific.
  - fix: The app connects to Azure DocumentDB through Mongoose (mongoose.connect) and all data access goes through that connection.

### retail-11 (minor_edits, 10 bullets)

- **duplicate**: The /visual-search handler must accept the uploaded image, encode it with CLIP, submit the query vector to Azure DocumentDB, and request nearest neighbors using the vector-ivf index.
  - why: Each clause is already a bullet: accepting the upload (bullet 1), encoding query images with CLIP (bullet 2), and querying through the vector-ivf index server-side (bullet 6).
  - fix: delete
- **duplicate**: Provide sample product data or an ingestion script so a reviewer can populate Azure DocumentDB and verify that /visual-search returns non-empty results.
  - why: The ingestion path is already bullet 3 ("Include functionality (API or ingestion script) that encodes a product image..."), and sample data loading is the shared section's seed-script bullet.
  - fix: delete

### retail-12 (minor_edits, 10 bullets)

- **not_in_prompt**: Query Azure DocumentDB for carts abandoned for over 2 hours (e.g., lastActivity or updatedAt older than now minus 2 hours) and only return carts not already marked processed; the query must run against Azure DocumentDB.
  - why: The prompt asks only for "carts abandoned for over 2 hours"; excluding already-processed carts is not stated anywhere in the prompt or description.
  - fix: Query Azure DocumentDB for carts abandoned for over 2 hours (e.g., last-activity timestamp older than now minus 2 hours); the query must run against Azure DocumentDB.
- **not_in_prompt**: Log the outcome of each cart's attempt back to Azure DocumentDB by inserting or updating a record with at minimum: cartId, personalisedMessage, channelUsed (email or SMS), deliveryResult/status, and timestamp.
  - why: The prompt says "Log outcomes back to DocumentDB"; the required field list (notably storing the full personalised message) is invented.
  - fix: Log the outcome of each cart's recovery attempt back to Azure DocumentDB, recording at minimum which cart, which channel was used (email or SMS), and the send result.
- **not_in_prompt**: Mark processed carts to avoid duplicate recovery attempts (e.g., set processedAt timestamp or status flag in Azure DocumentDB) as part of the same run after a successful or failed send attempt.
  - why: Neither the prompt nor the description asks for marking carts processed or preventing repeat attempts.
  - fix: delete
- **duplicate**: Capture and persist errors from the copy-generation agent or the channel agent to Azure DocumentDB (error message and stack or provider response), so each cart record reflects success or failure.
  - why: Overlaps the outcome-logging bullet (deliveryResult/status already covers success vs failure); the stack trace / provider response detail is not in the prompt.
  - fix: Outcome logging to Azure DocumentDB covers failed attempts as well as successful ones (a failure in the copy-generation agent or channel agent is recorded for that cart, not dropped).
- **vague**: The channel agent must call checkable send functions named sendEmail and sendSMS (or clear provider integration functions) and pass the personalised message plus necessary recipient info; the code must show the channel s
  - why: The function names sendEmail/sendSMS are invented, and the "(or clear provider integration functions)" escape hatch makes the check indeterminate.
  - fix: The channel agent's selection logic invokes an email send function when the customer's preference is email and an SMS send function when it is SMS, passing the personalised message and the recipient's address or phone number.

### retail-13 (minor_edits, 10 bullets)

- **not_in_prompt**: Ingest product data types (descriptions, specs, and reviews) and create Document objects with metadata indicating product_id and source_type (description/spec/review) before indexing.
  - why: The prompt only says to index 'product descriptions, specs, and reviews'; it never asks for product_id or source_type metadata on each Document, so an auditor would fail a sample that indexes the three sources without those exact metadata keys.
  - fix: Ingest product descriptions, specs, and reviews into the LlamaIndex index (all three source types must be present in the ingestion code).
- **not_in_prompt**: Ensure generated answers are grounded by including explicit citations or identifiers for the source chunks (e.g., product_id and chunk_id or source_type) alongside or within the response.
  - why: The prompt asks for a 'grounded answer', not for citations or chunk identifiers in the response. Grounding is already checkable through the prompt assembly (retrieved chunks injected as context) plus an instruction to answer from that context.
  - fix: The LLM prompt instructs the model to answer only from the retrieved product context (and to say so when the context does not cover the question), so the answer is grounded in the retrieved chunks.
- **not_in_prompt**: Include an end-to-end example or automated test that indexes sample product descriptions/specs/reviews, queries with a sample shopper question, verifies retrieval returned 5 chunks, and asserts the LLM output contains gr
  - why: The prompt does not ask for a test or end-to-end example, and the bullet depends on the invented citation requirement above. Tests are already covered by the shared 'Unit tests run without a live cluster' line.
  - fix: delete

### retail-14 (minor_edits, 9 bullets)

- **not_in_prompt**: The competitor-prices tool must query competitor price documents and return the most recent prices (timestamped) for the requested product SKU or product id.
  - why: The prompt says only that a tool queries DocumentDB for 'competitor price documents'; 'most recent' and 'timestamped' are added requirements the prompt does not state.
  - fix: The competitor-prices tool queries competitor price documents in Azure DocumentDB for the requested product and returns them to the agent.
- **not_in_prompt**: Implement a LangChain Tool (or use the agent) that performs the update back to the product document in Azure DocumentDB using a single atomic update operation (a single find-and-modify / find_one_and_update or equivalent
  - why: The prompt asks to 'write the updated price back to the product document atomically'. Setting an updated_at timestamp and returning the updated document are extra requirements, and 'Implement a LangChain Tool (or use the agent)' leaves it unclear what is required.
  - fix: Write the recommended price back to the product document in Azure DocumentDB with a single atomic update operation (e.g. update_one or find_one_and_update with $set), not a read-then-replace sequence.
- **not_in_prompt**: Before performing the atomic write, the agent must validate the recommended price against the retrieved margin rule documents and adjust or reject the recommendation so the stored price never violates the margin rules; t
  - why: The prompt has the LLM reason over margin rule documents returned by a tool and then write the price; it does not ask for a code-level validation/adjustment step before the write. A builder who follows the prompt literally would fail this bullet.
  - fix: delete

### retail-15 (minor_edits, 9 bullets)

- **not_in_prompt**: Enforce required-field validation at the application layer: incoming request bodies are validated by Pydantic/Beanie schemas and missing or invalid required fields cause 4xx responses and no write to Azure DocumentDB; cr
  - why: The first half is traceable to 'enforce required fields at the application layer'. The clause requiring a supplier-existence check on PO creation is a referential-integrity rule the prompt never asks for.
  - fix: Enforce required-field validation at the application layer: incoming request bodies are validated by the Pydantic/Beanie schemas, and missing or invalid required fields return a 4xx response with no write to Azure DocumentDB.
- **not_in_prompt**: Ensure API responses serialize Document IDs and Pydantic types to JSON (ObjectId/UUID converted to strings) so returned JSON is directly consumable by clients.
  - why: Nothing in the prompt, title or description asks for ID serialization behaviour; this is a general implementation detail, not a stated requirement.
  - fix: delete

### retail-16 (minor_edits, 10 bullets)

- **wrong_fact**: When recording an earn or redeem, open a MongoDB session and use multi-document transactions (session.startTransaction / session.commitTransaction / session.abortTransaction) to atomically (a) insert the new event docume
  - why: The parenthetical names one specific API; Mongoose transactions are equally correct via session.withTransaction() or mongoose.connection.transaction(), so an auditor reading the list literally would fail a valid implementation. The core requirement (one transaction covering event insert + balance up
  - fix: When recording an earn or redeem, run a multi-document transaction (session.withTransaction, or startTransaction/commitTransaction/abortTransaction) that (a) inserts the new event document and (b) updates the account's running balance, so both commit or roll back together.
- **not_in_prompt**: For redeem operations, enforce within the same multi-document transaction that the resulting running balance does not become negative (transactionally check current balance and abort if insufficient funds).
  - why: The prompt asks for atomic append-plus-balance-update; it does not state an insufficient-points rule. 'Ensuring consistency' in the description refers to event and balance agreeing, not to a business rule on redemption.
  - fix: delete
- **duplicate**: Ensure the /balance endpoint includes the aggregation result (lifetime points and tier) alongside the running balance so the tier is derived from event history via the aggregation, not just from the balances document.
  - why: Restates the previous two bullets: the /balance bullet already says it returns running balance plus tier status, and the aggregation bullet already says the tier comes from an aggregation over events and is returned in the API response.
  - fix: delete
- **duplicate**: Demonstrate connection configuration that targets Azure DocumentDB (MongoDB API) in the code (connection usage via Mongoose) so reviewers can confirm the app is written for Azure DocumentDB and uses multi-document transa
  - why: Already covered by the first bullet (Node.js + Mongoose against Azure DocumentDB) and the transaction bullet; the connection-string side is covered by the shared section. The '(MongoDB API)' suffix also reads like the neighbouring Cosmos DB for MongoDB product name, which the shared naming line forb
  - fix: delete
- **vague**: Expose an HTTP GET /history endpoint that returns the full event-sourced ledger for a specified accountId, ordered chronologically (oldest first) and read from the events collection (no projection that omits event immuta
  - why: The prompt asks only for a /history endpoint. 'Oldest first' is an invented ordering, and 'no projection that omits event immutability fields' is not a defined concept a reviewer can check.
  - fix: Expose an HTTP GET /history endpoint that returns the account's earn and redeem events, read from the events collection, in chronological order.

### retail-17 (needs_rework, 10 bullets)

- **not_in_prompt**: Implement the sample in Python and include a requirements file listing packages used (must include pymongo and langchain).
  - why: The prompt names Python and LangChain but no MongoDB driver, so "must include pymongo" adds a constraint the prompt does not state; the requirements-file part duplicates the shared bullet "Dependencies are pinned in requirements.txt".
  - fix: Implement the sample in Python using LangChain.
- **not_in_prompt**: The DocumentDB aggregation pipeline must group sales by product category and by season, compute a sales_velocity metric (e.g., sales per day) for each category/season, and calculate percent_change in velocity between sea
  - why: The prompt only says the pipeline compares "sales velocity across seasons"; the exact output field names (sales_count, sales_velocity, percent_change) and the percent-change metric are invented and would fail a valid build that uses other names or a different comparison.
  - fix: The aggregation pipeline groups sales by category and season and computes a sales-velocity measure per category/season that compares seasons, with the comparison done inside the pipeline.
- **not_in_prompt**: Implement a web search tool that performs live web searches (calls an external search API at runtime), returns structured trend signals per category (including a relevance/confidence score), and includes source URLs and 
  - why: The prompt says only "a web search tool that fetches current trend signals"; the relevance/confidence score, source URLs and timestamps per result are not asked for.
  - fix: Implement a web search tool that calls an external search API at runtime and returns current trend signals for the agent to use.
- **not_in_prompt**: The agent must produce a ranked list of rising categories and a ranked list of declining categories, sorted by the combined score, and each list item must include the combined score plus supporting evidence: the DB metri
  - why: The prompt asks for "a ranked list of rising and declining categories"; requiring a numeric combined score, DB metrics, a web URL and a timestamp on every item is invented.
  - fix: The agent's final output is a ranked list of rising categories and a ranked list of declining categories.
- **not_in_prompt**: Include code that programmatically computes or validates the combined score (either via the prompt’s explicit rules or by a clear combining function invoked by the agent) so reviewers can verify numeric merging of DB and
  - why: The prompt says to combine both signals "in the prompt" through context engineering, i.e. the model does the combining; requiring code that numerically merges the signals is not asked for, and the "either via the prompt's explicit rules or ..." alternative makes it uncheckable.
  - fix: delete

### retail-18 (needs_rework, 10 bullets)

- **not_in_prompt**: Have the "policy agent" return a structured result that includes at minimum: eligibility (boolean) and eligibilityReason (string); if eligibility is false the orchestration must not perform refund calculations and must f
  - why: The prompt says the policy agent "determines eligibility" and the flow goes policy, then refund, then comms; the field names and the short-circuit (skip refund when ineligible) are not in the prompt.
  - fix: The policy agent returns an eligibility decision for the return, derived from the fetched order document, and that decision is passed on to the refund-calculation agent.
- **not_in_prompt**: Have the "comms agent" generate a structured customer notification that includes customer contact/identifier from the order, eligibility status, refundAmount (if any), eligibilityReason, and a messageBody suitable for no
  - why: The prompt says the comms agent "generates the customer notification"; the required fields and notificationChannel are invented.
  - fix: The comms agent generates the customer notification text from the policy and refund results.
- **not_in_prompt**: After orchestration completes, persist a final return document to Azure DocumentDB using Mongoose; the saved document must include orderId, status ("approved", "rejected", or "error"), refundAmount (number, zero if rejec
  - why: The prompt says "Write the final return document back to DocumentDB via Mongoose"; the status enum, timestamps and raw-agent-output fields are an invented schema.
  - fix: After the comms agent runs, the final return document (eligibility decision, refund amount, notification) is written to Azure DocumentDB through a Mongoose model.
- **not_in_prompt**: Ensure the flow accepts a return request input (e.g., orderId and return reason), triggers the order fetch + orchestration, and returns the final persisted return document as the API response.
  - why: The prompt says the flow "accepts a return request" but does not ask for an HTTP API or for the persisted document to be returned as a response.
  - fix: The flow takes a return request (identifying the order) as its input and triggers the order fetch followed by the policy, refund and comms agents in that order.
- **not_in_prompt**: Implement error handling so that if the order is not found or any agent throws an error, the code writes a return document with status "error" and an error field to Azure DocumentDB via Mongoose, and the API responds wit
  - why: No error-handling behaviour is asked for in the prompt, title or description.
  - fix: delete
- **not_in_prompt**: Provide runnable tests or a demo script that exercises both an approved return path and a rejected return path, verifying that agent outputs are produced and that final documents are written to Azure DocumentDB via Mongo
  - why: Tests are not in the prompt and are covered by the shared section; verifying writes to Azure DocumentDB also conflicts with the shared "Unit tests run without a live cluster".
  - fix: delete
- **duplicate**: Have the "refund agent" compute and return a structured numeric refundAmount (and optionally a breakdown such as itemRefunds and shippingRefund) based on the order document and the policy result; refund calculations must
  - why: The "skipped when ineligible" clause repeats the previous bullet and is itself not in the prompt; the refund amount part is fine (description: "a refund agent calculates the amount").
  - fix: The refund-calculation agent computes and returns a numeric refund amount from the order document and the policy agent's decision.

### retail-19 (needs_rework, 12 bullets)

- **contradicts_prompt**: Perform all vector similarity (cosine similarity) calculations in the service code using the stored embeddings retrieved from Azure DocumentDB (do not rely on an external DB vector-search capability).
  - why: The sample's concepts list "vector search" and the prompt says the service "stores the vectors" in DocumentDB; forbidding the database's vector search inverts the concept, and the documentdb-vector-search skill describes exactly this capability (cosmosSearch index, $search query). The shared section
  - fix: Vector similarity over the stored pair embeddings runs in Azure DocumentDB through a cosmosSearch vector index on the ProductPair embedding field (queried with $search / cosmosSearch), not by loading all pairs and computing cosine similarity client-side.
- **not_in_prompt**: Define a Beanie Order document model that stores order history with an order identifier, timestamp, and a list of product IDs.
  - why: The prompt says "order history" with product pairs derived from it; an order timestamp is not asked for and a build without one would fail this line.
  - fix: Define a Beanie Order document model for order history that holds the product IDs of each order.
- **not_in_prompt**: Compute an affinity score for each candidate by aggregating across basket items: for each basket item, retrieve the ProductPair document for (basket_item, candidate), and combine the pair's co_purchase_count with the cos
  - why: The prompt asks only for candidates "ranked by affinity score"; this prescribes one invented formula, and it is incoherent (the cosine similarity between a pair's stored embedding and "the basket-item–candidate embedding" compares a vector with itself).
  - fix: The /cross-sell handler computes an affinity score per candidate from the co-purchase data and the stored pair vectors and ranks candidates by that score.
- **duplicate**: Persist embeddings in Azure DocumentDB as arrays of floats inside the ProductPair documents so they are retrievable for similarity calculations.
  - why: Repeats the ProductPair embedding field bullet and the "persist that embedding into the ProductPair.embedding field" bullet.
  - fix: delete

### retail-20 (minor_edits, 10 bullets)

- **missing**: The $geoNear `near` point is built in GeoJSON order `[longitude, latitude]` from the endpoint's latitude and longitude inputs (the prompt accepts lat/lng and stores GeoJSON; the documentdb-indexing skill calls the revers
  - fix: The $geoNear `near` point is built in GeoJSON order `[longitude, latitude]` from the endpoint's latitude and longitude inputs (the prompt accepts lat/lng and stores GeoJSON; the documentdb-indexing skill calls the reversed order the most common geospatial mistake).
- **not_in_prompt**: Expose an HTTP endpoint at /nearby that accepts latitude, longitude, and radius (as query parameters or JSON body), parses them as numbers, and returns a 400 error for missing or invalid values.
  - why: The prompt says the endpoint "accepts a latitude, longitude, and radius"; input validation with a 400 response is not asked for.
  - fix: Expose an HTTP endpoint at /nearby that accepts latitude, longitude and radius inputs and parses them as numbers.
- **duplicate**: Ensure the $geoNear aggregation is used (i.e., the pipeline contains a $geoNear stage) rather than only using other operators like $nearSphere or manual filtering.
  - why: Repeats the earlier bullet that already requires constructing and executing a $geoNear aggregation stage.
  - fix: delete
- **duplicate**: Connect Mongoose to an Azure DocumentDB (MongoDB‑compatible) endpoint for data storage; the connection URI must be configurable (e.g., via an environment variable) and used by the service at runtime.
  - why: The configurable-URI clause repeats the shared bullet "The connection string and model credentials come from environment variables".
  - fix: Connect Mongoose to Azure DocumentDB and use that connection for all store reads and writes.

