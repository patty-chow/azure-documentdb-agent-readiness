# Decision log

| Reason came from | Decisions |
|---|---|
| operator | 1 |
| prompt | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:46:52+00:00

## D002 (build): I chose Node.js with Express and Mongoose (MongoDB driver via Mongoose) for the sample app.

- **Instead of:** Python/Flask; Node.js/Express; Go/Fiber
- **Because:** The prompt explicitly requests Node.js and Mongoose.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'Using the DocumentDB skill, build a Node.js multi-currency ledger using Mongoose and DocumentDB transactions.'
- **When:** 2026-11-25T06:47:09+00:00

## D003 (build): I chose mongoose 7.x (latest 7.x) to match Node 24 and provide schema/index convenience.

- **Instead of:** mongoose 6.x; mongoose 7.x; native mongodb driver without mongoose
- **Because:** Mongoose 7.x is compatible with Node 24 and provides schemas, indexes and transaction session helpers used in this sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption from prompt review: 'Use a recent stable Mongoose compatible with Node 24 (e.g., mongoose 7.x)'.
- **When:** 2026-11-25T06:47:12+00:00
