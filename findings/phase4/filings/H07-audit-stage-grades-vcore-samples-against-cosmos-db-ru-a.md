---
id: H07
title: "Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 57
member_drafts:
  - 107-pipeline-audit-rubric-imports-cosmos-db-nosql-ru-api-concept.md
open_questions: 0
---

# Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR. Per the filing plan it goes in together with the harness fixes for the "kit not installed" flagging (H03).

## What happens today

The audit stage (`prompts/auditor.md`, `factory/agents/auditor.py::audit_app`) marks generated Azure DocumentDB samples as `violated` against practices that are not guidance for this service, or that the sample never set out to implement:

1. **Azure Cosmos DB RU-API concepts become vCore rules.** Practice discovery (`prompts/practice_discovery.md`) records model priors about Azure Cosmos DB as `prior_knowledge_confirmed` by citing `learn.microsoft.com/azure/cosmos-db/...` pages, even though its Rules already say such a page does not confirm a belief. The auditor then grades against them: "log requestCharge", "optimistic concurrency with `_etag` / If-Match", "avoid unbounded arrays to prevent RU spikes", "handle RequestRateTooLarge / HTTP 429 and respect Retry-After". Azure DocumentDB capacity is vCore tiers, not request units; there is no request charge, no `_etag` concurrency token as a service feature (optimistic concurrency is an application pattern with a version field, as on MongoDB), and the service never returns a throttling error: error 16500 / HTTP 429 `TooManyRequests` / `RequestRateTooLarge` are request-unit errors of the RU-based Azure Cosmos DB for MongoDB, absent from the Azure DocumentDB troubleshooting table and from every error-mapping file of the open-source engine, and never observed in 120 runs (see Resolved). Clients speak the MongoDB wire protocol; capacity is observed through CPU, memory, IOPS, storage and connection metrics, and resource pressure shows up as latency and timeouts (code 50 `ExceededTimeLimit`, default query limit 120 seconds), not as a throttling code.
2. **Readiness accelerators become hard requirements.** A sample that stores no embeddings and whose prompt asks for plain lookups plus an LLM is marked `violated` three times for missing vector-index fields, DiskANN/HNSW tuning and a semantic cache. Its own evidence text says "the repo does not store embeddings".
3. **Conditional advice becomes a violation.** Practices worded "where appropriate" or "if you need JSON Schema enforcement" are graded `violated` on demo-scale samples.
4. **Duplicates.** One run has two `violated` checks for the same $jsonSchema gap under two topics, citing the same URL.
5. **Inconsistent retryWrites grading.** Some checks treat `retrywrites=false` as the standard, others only ask that `retryWrites=true` be logged as a decision, and some audits say both (5 audits assert both `retryWrites=true` and `retryWrites=false`). Only the first is right: Azure DocumentDB does not support retryable writes, so `retrywrites=false` is required, not a recommendation or a per-sample choice (see Resolved below).

The existing prompt rules state the intent but nothing enforces it: `audit_app()` only rewrites URLs, with no status downgrade or de-duplication.

## Why it matters

In 117 audits across the 101 sample folders of the 100-sample run (2,199 checks), 72 `violated` checks in **57 samples** use RU / request-charge / `_etag` / 429 / Retry-After vocabulary. Also: 146 discovered practices in 55 samples were "confirmed" by a Cosmos DB page, and 37 violations in 31 samples rest only on one; 36 violations in 23 samples target a feature the sample does not use; 17 in 13 samples are on conditionally worded practices; 7 runs hold duplicate violations; 5 audits assert both `retryWrites=true` and `=false`. All counts come from one experiment run and shift by a few samples depending on how matches are made (a rough re-tally found 53 to 64 samples for the RU/Cosmos-sourced category), so treat them as indicative.

The proposed "fixes" would make samples wrong for the product (logging a request charge the driver never returns, filtering on an `_etag` field that does not exist, adding a vector index to a sample without vectors). They inflate the violation count the product team reads, and `doc-gaps.md` then asks the team to document Cosmos concepts such as a 429/Retry-After helper.

## Proposed change

### `prompts/practice_discovery.md`

Replace the first bullet under **Rules** ("Keep the two kinds of evidence apart. ...") with:

> A prior belief is `prior_knowledge_confirmed` only when the source is an Azure DocumentDB page (`learn.microsoft.com/azure/documentdb/...`, `learn.microsoft.com/documentdb/...`, or a page under `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`, the service's former name), the open-source DocumentDB docs, or an installed skill. Any other page under `learn.microsoft.com/azure/cosmos-db/` (NoSQL, RU-based MongoDB API), a MongoDB Atlas page or an Amazon DocumentDB page never confirms a belief: the belief stays `prior_knowledge_only`, and you may cite the page in `how_found`. When you write a `practice`, use this service's vocabulary: CPU, memory, IOPS, connection and storage metrics (not RU or request charge); a version field in a conditional update (not `_etag` / If-Match); document size and working-set growth (not RU spikes); application-level retry of idempotent writes on transient errors such as connection errors and code 50 `ExceededTimeLimit` (not RU throttling with 16500 / 429 / `RequestRateTooLarge` / Retry-After, which Azure DocumentDB never returns, and not driver retryable writes, which the service does not support).

### `prompts/auditor.md`

Add to **Step 2: check the app against each practice** (under "Practices: reconcile, then check the app"), after the `not_assessable` bullet:

> - A practice may be `violated` only if a source cited for it is an Azure DocumentDB page, the open-source DocumentDB docs or an installed skill. If its only sources are Azure Cosmos DB, MongoDB Atlas or Amazon DocumentDB pages, the status is `not_assessable`, and `searched` says the guidance was found only for a neighbouring service.
> - Grade only practices tied to a feature the app implements or the starter prompt explicitly asks for. A practice about vector indexes, embeddings, semantic caching, TTL, change streams or transactions in an app that does not use them is `not_applicable`; put the suggestion in `fix` prefixed "Optional accelerator:" so the report lists it without counting it as a violation.
> - A practice worded conditionally ("where appropriate", "if you need", "consider", "optionally") is advisory. It is never `violated`; use `not_applicable` with the suggestion in `fix`.
> - Do not use RU, request charge, `_etag`, If-Match, Retry-After, 429, 16500, `TooManyRequests` or `RequestRateTooLarge` in a practice, evidence or fix; these are Azure Cosmos DB RU-API concepts, and a check that needs them is a sign the source is about that service. Azure DocumentDB has no request-unit throttling and never returns 16500 or 429 to a MongoDB client (its troubleshooting table lists no throttling code and the engine has none). Resource pressure appears as latency, timeouts (code 50 `ExceededTimeLimit`; raise `maxTimeMS` or narrow the query) and, when the backend connection limit is exhausted, code 261 `TooManyLogicalSessions` ("There are too many open connections."), which means reduce connections, not back off and retry. A practice about handling throttling is therefore `not_assessable`.
> - Every Azure DocumentDB connection string must carry `retrywrites=false`; this is a requirement, not a recommendation. If a sample sets `retryWrites=true` (or omits the option, since drivers default to true), mark it `violated` once, under connection handling, and do not also list it as an audit-trail or decision-logging gap. Use this reason in `fix`: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Do not claim that `retryWrites=true` causes connection errors; that is not established.
> - Before you return, merge checks that state the same recommendation under different topics; keep one and cite both discovery ids in `evidence`.

### `factory/agents/auditor.py` (`audit_app`, after the URL rewrite loop and before the `return`; add `import re`, and `PracticeCheck` to the `..models` import)

A deterministic pass so the rules hold when the model slips. Former-name vCore pages are exempt:

```python
_VCORE_FORMER = "learn.microsoft.com/azure/cosmos-db/mongodb/vcore/"
_NEIGHBOUR = ("learn.microsoft.com/azure/cosmos-db/", "mongodb.com/docs/atlas", "docs.aws.amazon.com/documentdb")
_BANNED = re.compile(r"\b(RU|RUs|RU/s|request ?charge|_etag|ETag|If-Match|Retry-After|RequestRateTooLarge|TooManyRequests|16500|429)\b", re.I)

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9$ ]", "", text.lower()).strip()

seen: dict[str, PracticeCheck] = {}
for c in checks:
    neighbour = any(n in c.source_url for n in _NEIGHBOUR) and _VCORE_FORMER not in c.source_url
    if c.status == "violated" and (neighbour or _BANNED.search(c.practice)):
        c = c.model_copy(update={"status": "not_assessable",
                                 "searched": (c.searched + " Downgraded: only neighbouring-service sources or RU/ETag vocabulary.").strip()})
    k = _norm(c.practice)[:80]
    if k in seen:
        seen[k] = seen[k].model_copy(update={"evidence": f"{seen[k].evidence} Also {c.discovery_id or c.topic}."})
        continue
    seen[k] = c
checks = list(seen.values())
```

`429`, `16500` and `TooManyRequests` are in `_BANNED` because Azure DocumentDB never returns them (see Resolved); a practice that names them is RU-API guidance by construction.

### `tests/`

Add one unit test that feeds an `AuditReport` with a Cosmos-sourced `violated` check, a `violated` "handle 429 / RequestRateTooLarge throttling" check sourced to an Azure DocumentDB page, and a duplicated $jsonSchema pair, and asserts two `not_assessable` checks and one surviving merged check.

## Evidence

- `runs/01-unified-customer-profile-store/20261124-203120/05a-practice-discovery.json` and `05-audit.json` (P11, P12, P17 confirmed by cosmos-db pages, then `violated`; `doc-gaps.md` asks for a 429/Retry-After helper)
- `runs/03-medication-interaction-checker/20261124-193347/05-audit.json` (P10, P11, P18 vector/semantic-cache violations with no embeddings; P13 429 handling sourced to a cosmos-db page)
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/05-audit.json` (P19 and P23 duplicate, conditionally worded $jsonSchema violations)
- `runs/14-dynamic-pricing-engine/20261124-184622/05-audit.json` (`_etag` concurrency `violated`; retryWrites graded only as an audit-trail gap)
- `runs/13-household-grouping-linkage/20261124-204947/05-audit.json` ("RU spikes" check; retryWrites true and false in one audit)
- findings/phase4/DECISIONS.md (Throttling and transient errors): 63 to 64 of the 120 `05-audit.json` files list "handle 429 / RequestRateTooLarge throttling" as a discovered best practice, and the only hits for 16500 / TooManyRequests / RequestRateTooLarge in `events.jsonl` are `learn_microsoft_docs_search` queries and their Cosmos DB RU results (9 run folders by exact string, about 28 with a broader pattern, for example `runs/07-voice-of-customer-sentiment-hub/20261124-204049`, `runs/03-substitute-product-finder/20261124-183232`); no agent ever received a throttling error from the server

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

16500 / HTTP 429 throttling: settled 2026-11-25 from engine source, see findings/phase4/DECISIONS.md (Throttling and transient errors). Azure DocumentDB never returns 16500 / 429 / `TooManyRequests` / `RequestRateTooLarge` to a MongoDB client: 16500 is a request-unit error of the RU-based Azure Cosmos DB for MongoDB, the Azure DocumentDB troubleshooting page's Error Codes table lists no throttling code, the open-source engine at commit a5f1636 has no code 16500 in `error_mappings.csv`, `documentdb_errors.csv` or `pg_documentdb_gw/include/all_error_mappings_oss_generated.csv` and no rate-limiting path in the gateway, and no agent received a throttling error in 120 runs; the documented resource-pressure signals are timeouts and latency (120-second default query limit, code 50 `ExceededTimeLimit`, which the managed-service test of 2026-11-25 confirmed for `maxTimeMS` expiry, never `MaxTimeMSExpired`; ENGINE-TESTS.md, Managed service), and the only admission-style error is 261 `TooManyLogicalSessions` on connection exhaustion, which the gateway does not retry. Sources: https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/error-codes-solutions (row 16500, RU-based API); https://learn.microsoft.com/en-us/azure/documentdb/troubleshoot-common-issues (Error Codes table); https://learn.microsoft.com/en-us/azure/documentdb/limitations (MongoDB execution limitations); github.com/documentdb/documentdb @ a5f1636269e5062fa22a24bfa4d58d3cc92a0bc7 (mapping CSVs; `responses/pg.rs:277-295`, `:507-511`; `error.rs:518-521`; `query_dispatch.rs:75-143`); the 120 run folders under `runs/`. Consequence for this filing: bare `429`, `16500` and `TooManyRequests` join `_BANNED`, and the auditor rule names the signals that do exist.

## Open questions

None.

## Source drafts

- 107-pipeline-audit-rubric-imports-cosmos-db-nosql-ru-api-concept.md
