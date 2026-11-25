# Decision log

| Reason came from | Decisions |
|---|---|
| operator | 2 |
| model_default | 2 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:27:44+00:00

## D002 (build): I chose Python 3.11 as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.11
- **Because:** The sample prompt requests an async Python pipeline using Beanie; Python 3.11 is a modern runtime compatible with async features and common Beanie releases.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will assume a modern Python 3.11 (or 3.10) runtime"
- **When:** 2026-11-25T05:28:05+00:00

## D003 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:30:06+00:00

## D004 (build): I chose Beanie with Motor (AsyncIOMotorClient) as the async driver for this sample.

- **Instead of:** Use Beanie with Motor (asyncio); Use Beanie with PyMongo's AsyncMongoClient
- **Because:** Beanie is most commonly used with Motor and that combination is stable and well-supported; choosing Motor avoids risking incompatibility with an unknown Beanie+pymongo mapping.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Beanie historically used Motor; documentdb-driver recommends PyMongo... but Beanie version mapping is missing.'
- **When:** 2026-11-25T05:30:23+00:00

## D005 (build): I chose to use the OpenAI model 'gpt-3.5-turbo' and the env var OPENAI_API_KEY for the API key.

- **Instead of:** gpt-4o-mini; gpt-4o; gpt-3.5-turbo
- **Because:** gpt-3.5-turbo is broadly available, cost-effective for classification tasks, and sufficient for sentiment + tag extraction for a sample. Using OPENAI_API_KEY follows common conventions and keeps the sample simple.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'OpenAI model & env var choices missing; builder must pick'
- **When:** 2026-11-25T05:30:37+00:00
