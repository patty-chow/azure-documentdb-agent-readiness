# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:01:42+00:00

## D002 (build): I chose Node.js + Express + Mongoose (Mongoose 7.x)

- **Instead of:** Python/Flask + pymongo; Node.js + Express + native MongoDB driver; Node.js + Express + Mongoose (ORM)
- **Because:** The prompt requested a Node.js Mongoose sample; Mongoose offers concise schema, middleware and transaction support which speeds sample development and readability for developers learning the service.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Use a current stable Mongoose compatible with Node 24 (Mongoose 7.x)'
- **When:** 2026-11-25T06:02:04+00:00

## D003 (build): I chose SCRAM-based credentials via DOCUMENTDB_URI environment variable (do not demonstrate Entra ID in this sample)

- **Instead of:** Use Microsoft Entra ID (OIDC) auth in sample; Use SCRAM-based credentials via DOCUMENTDB_URI environment variable
- **Because:** SCRAM via DOCUMENTDB_URI is simpler, documented for quickstarts, and avoids adding Azure AD token plumbing which the readiness report found missing; it also obeys the 'do not write secrets' rule by reading URI from env.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'No concrete Node.js Mongoose + MONGODB-OIDC example found; implement SCRAM-based seed/quickstart first and add Entra ID as a separate step'
- **When:** 2026-11-25T06:02:24+00:00

## D004 (build): I chose to not provision resources and use the existing cluster (no Azure writes)

- **Instead of:** Provision resources via az/ARM/Bicep; Do not provision and use existing cluster
- **Because:** Run policy forbids creating resources; the environment already provides a reachable Azure DocumentDB cluster (DOCUMENTDB_URI), so the sample should use it.
- **Reason came from:** `prompt`
- **Evidence:** run_policy and readiness_report: 'Azure resource changes allowed: False' and 'use existing cluster'
- **When:** 2026-11-25T06:02:27+00:00

## D005 (build): I chose to keep a separate 'balances' collection (one-document per account) with unique index on accountId and an 'events' collection with compound index {accountId:1, timestamp:-1}

- **Instead of:** Store balances in same events collection (denormalized); Keep a separate balances collection with unique index
- **Because:** Separate balances collection allows fast lookups and atomic updates in transactions while events remain immutable; index shapes support history queries and fast account lookups.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Create an index on events {accountId: 1, timestamp: 1} and a unique index on balances {accountId: 1}' and readiness_report guidance about indexing
- **When:** 2026-11-25T06:02:30+00:00

## D006 (build): I chose multi-document transactions with Mongoose sessions

- **Instead of:** Use multi-document transactions with Mongoose sessions; Use single-document updates without transactions
- **Because:** Transactions ensure the event insert and balance update are atomic across collections and can enforce non-negative balance checks (prevent negative balance during redeem).
- **Reason came from:** `prompt`
- **Evidence:** sample_prompt: 'Use multi-document transactions to atomically append the event and update the running balance.'
- **When:** 2026-11-25T06:02:32+00:00

## D007 (build): I chose to expose only read endpoints (/balance and /history) per prompt and provide a seed script that demonstrates writes using transactions

- **Instead of:** Expose only read endpoints and seed writes via script; Also expose a write endpoint for events
- **Because:** The prompt asks explicitly for /balance and /history endpoints; seed script demonstrates the transactional write workflows without exposing public write API, keeping sample minimal.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: '/balance and /history endpoint' and prompt focused on ledger using transactions; seed script will show write flow
- **When:** 2026-11-25T06:02:36+00:00
