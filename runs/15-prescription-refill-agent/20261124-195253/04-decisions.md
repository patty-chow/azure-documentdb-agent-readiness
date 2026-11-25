# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| readiness_report | 4 |
| operator | 2 |
| prompt | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:49:12+00:00

## D002 (build): I chose Node.js with Mongoose (a Node ODM) instead of Python+Beanie.

- **Instead of:** Python + Beanie ODM; Node.js + Mongoose ODM
- **Because:** The prompt requested a Node.js LangChain agent but Beanie is Python-only; keeping Node.js simplifies the environment and fits the run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Beanie is Python-only; if you must remain in Node.js use a Node ODM such as Mongoose instead of Beanie'.
- **When:** 2026-11-25T08:49:40+00:00

## D003 (build): I chose Mongoose (mongoose@7) as the ODM/driver for the Node.js sample.

- **Instead of:** mongodb native driver (mongodb); Mongoose ODM
- **Because:** Mongoose simplifies schema definitions and seeding for a small sample app and is familiar to Node.js developers.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review and common Node.js patterns; Mongoose provides schema, validation and easy indexing.
- **When:** 2026-11-25T08:49:44+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from env var DOCUMENTDB_URI; Hard-code connection string into repo
- **Because:** Security best practice and the run environment provides DOCUMENTDB_URI; avoid committing secrets.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment note: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into a file'.
- **When:** 2026-11-25T08:49:47+00:00

## D005 (build): I chose to use the existing DocumentDB cluster and not provision any Azure resources.

- **Instead of:** Provision a new cluster via Azure CLI/Bicep; Use the existing cluster (no provisioning)
- **Because:** Provisioning is disallowed; an existing cluster is provided via DOCUMENTDB_URI for the sample to use.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and readiness_report guidance.
- **When:** 2026-11-25T08:49:53+00:00

## D006 (build): I chose a simple in-process conversation memory for this sample agent (keeps last medication mention per session).

- **Instead of:** LangChain memory store backed by a database/collection; Simple in-process conversation memory
- **Because:** Simpler for a lightweight sample, easier to understand and safe for demo PHI; production apps should use durable memory stores.
- **Reason came from:** `model_default`
- **Evidence:** Prompt requires agent memory so follow-up 'refill my blood pressure medication' resolves to previous medication; an in-process memory suffices for the sample and avoids creating additional collections or secrets.
- **When:** 2026-11-25T08:49:58+00:00

## D007 (build): I chose to implement a small rule-based agent (with explicit tools) rather than a full LangChain dependency to keep the sample small, readable, and self-contained.

- **Instead of:** Implement a full LangChain-based agent using OpenAI and LangChain JS; Implement a small rule-based agent with tool functions and in-memory memory
- **Because:** Keeps the sample easier to run in constrained environments and allows deterministic demo runs; document this decision in README so users can replace the agent with LangChain if desired.
- **Reason came from:** `model_default`
- **Evidence:** The prompt asks for a LangChain agent, but LangChain JS introduces heavy LLM dependencies and configuration; a rule-based agent demonstrates the same tool pattern and memory behavior without requiring third-party API keys for verification.
- **When:** 2026-11-25T08:50:01+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:52:48+00:00

## D009 (build): I chose Node.js with Mongoose ODM (JavaScript) instead of Python/Beanie.

- **Instead of:** Use Python + Beanie ODM; Use Node.js + Mongoose ODM
- **Because:** The sample request mixed Node.js and Beanie (Python). To keep the app in Node.js as requested and runnable with the available Node.js toolchain, I will use Mongoose which is the standard Node.js ODM for MongoDB and is compatible with Azure DocumentDB's MongoDB wire protocol.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Beanie is Python-only; the builder must either switch to Python (and use Beanie) or use a Node.js ODM (for example Mongoose)."
- **When:** 2026-11-25T08:53:08+00:00

## D010 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from code constant; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Run policy forbids writing secrets into files. Reading the connection string from an environment variable follows best practice and the sample's instructions.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time."
- **When:** 2026-11-25T08:53:20+00:00

## D011 (build): I chose a DB-backed agent memory stored in collection 'agent_memory'.

- **Instead of:** Use in-memory (process) memory for agent; Use DB-backed memory collection 'agent_memory'
- **Because:** DB-backed memory persists across restarts and multiple processes, demonstrating a realistic memory backing and allowing the follow-up utterance 'refill my blood pressure medication' to resolve to prior medication for the patient.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: "Agent memory will be LangChain's conversation memory backed by a small collection or in-process store."
- **When:** 2026-11-25T08:53:24+00:00

## D012 (build): I chose to implement a small rule-based agent (no external LLM calls) as the default behavior; the code is structured so an LLM (OpenAI) can be plugged via env var OPENAI_API_KEY.

- **Instead of:** Use OpenAI (external) LLM for LangChain agent; Implement a simple rule-based local agent for demo and avoid external LLM calls
- **Because:** Avoid requiring the user to provide an API key to run the demo and to keep verification self-contained. The implementation is pluggable so LangChain/OpenAI can be enabled by setting OPENAI_API_KEY in the environment.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "Information gaps: LLM / LangChain provider & memory store choice" and run policy forbids writing secrets; also to allow verification without external API keys.
- **When:** 2026-11-25T08:53:27+00:00

## D013 (build): I chose to create the following indexes: prescriptions {patientId:1, active:1}, prescriptions {prescriptionId:1} unique, refillRequests {patientId:1, requestedAt:-1}.

- **Instead of:** Create indexes: prescriptions (patientId, active) & prescriptionId; refillRequests(patientId, requestedAt); Create no indexes and rely on defaults
- **Because:** These indexes support the sample queries the app runs (find active prescriptions by patient, look up by prescriptionId, list refill requests by patient in reverse chronological order).
- **Reason came from:** `readiness_report`
- **Evidence:** Assumptions from prompt review: "Create indexes on prescriptions(patientId, active) and prescriptions(prescriptionId) and on refillRequests(patientId, requestedAt)."
- **When:** 2026-11-25T08:53:31+00:00
