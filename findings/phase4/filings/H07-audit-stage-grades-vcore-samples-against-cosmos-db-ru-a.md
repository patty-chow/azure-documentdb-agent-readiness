---
id: H07
title: "Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: needs_sme
priority: P1
sample_count: 57
member_drafts:
  - 107-pipeline-audit-rubric-imports-cosmos-db-nosql-ru-api-concept.md
open_questions: 2
---

# Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR. Per the filing plan it goes in together with the harness fixes for the "kit not installed" flagging (H03).

## What happens today

The audit stage (`prompts/auditor.md`, `factory/agents/auditor.py::audit_app`) marks generated Azure DocumentDB samples as `violated` against practices that are not guidance for this service, or that the sample never set out to implement:

1. **Azure Cosmos DB RU-API concepts become vCore rules.** Practice discovery (`prompts/practice_discovery.md`) records model priors about Azure Cosmos DB as `prior_knowledge_confirmed` by citing `learn.microsoft.com/azure/cosmos-db/...` pages, even though its Rules already say such a page does not confirm a belief. The auditor then grades against them: "log requestCharge", "optimistic concurrency with `_etag` / If-Match", "avoid unbounded arrays to prevent RU spikes", "handle RequestRateTooLarge / HTTP 429 and respect Retry-After". Azure DocumentDB capacity is vCore tiers, not request units; there is no request charge and no `_etag`. Clients speak the MongoDB wire protocol, and capacity is observed through CPU, memory, IOPS, storage and connection metrics.
2. **Readiness accelerators become hard requirements.** A sample that stores no embeddings and whose prompt asks for plain lookups plus an LLM is marked `violated` three times for missing vector-index fields, DiskANN/HNSW tuning and a semantic cache. Its own evidence text says "the repo does not store embeddings".
3. **Conditional advice becomes a violation.** Practices worded "where appropriate" or "if you need JSON Schema enforcement" are graded `violated` on demo-scale samples.
4. **Duplicates.** One run has two `violated` checks for the same $jsonSchema gap under two topics, citing the same URL.
5. **Inconsistent retryWrites grading.** Some checks treat `retryWrites=false` as the standard, others only ask that `retryWrites=true` be logged as a decision, and some audits say both (5 audits assert both `retryWrites=true` and `retryWrites=false`).

The existing prompt rules state the intent but nothing enforces it: `audit_app()` only rewrites URLs, with no status downgrade or de-duplication.

## Why it matters

In 117 audits across the 101 sample folders of the 100-sample run (2,199 checks), 72 `violated` checks in **57 samples** use RU / request-charge / `_etag` / 429 / Retry-After vocabulary. Also: 146 discovered practices in 55 samples were "confirmed" by a Cosmos DB page, and 37 violations in 31 samples rest only on one; 36 violations in 23 samples target a feature the sample does not use; 17 in 13 samples are on conditionally worded practices; 7 runs hold duplicate violations; 5 audits assert both `retryWrites=true` and `=false`. All counts come from one experiment run and shift by a few samples depending on how matches are made (a rough re-tally found 53 to 64 samples for the RU/Cosmos-sourced category), so treat them as indicative.

The proposed "fixes" would make samples wrong for the product (logging a request charge the driver never returns, filtering on an `_etag` field that does not exist, adding a vector index to a sample without vectors). They inflate the violation count the product team reads, and `doc-gaps.md` then asks the team to document Cosmos concepts such as a 429/Retry-After helper.

## Proposed change

### `prompts/practice_discovery.md`

Replace the first bullet under **Rules** ("Keep the two kinds of evidence apart. ...") with:

> A prior belief is `prior_knowledge_confirmed` only when the source is an Azure DocumentDB page (`learn.microsoft.com/azure/documentdb/...`, `learn.microsoft.com/documentdb/...`, or a page under `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`, the service's former name), the open-source DocumentDB docs, or an installed skill. Any other page under `learn.microsoft.com/azure/cosmos-db/` (NoSQL, RU-based MongoDB API), a MongoDB Atlas page or an Amazon DocumentDB page never confirms a belief: the belief stays `prior_knowledge_only`, and you may cite the page in `how_found`. When you write a `practice`, use this service's vocabulary: CPU, memory, IOPS, connection and storage metrics (not RU or request charge); a version field in a conditional update (not `_etag` / If-Match); document size and working-set growth (not RU spikes); driver transient-error retry with backoff (not RU throttling with `RequestRateTooLarge` / Retry-After).

### `prompts/auditor.md`

Add to **Step 2: check the app against each practice** (under "Practices: reconcile, then check the app"), after the `not_assessable` bullet:

> - A practice may be `violated` only if a source cited for it is an Azure DocumentDB page, the open-source DocumentDB docs or an installed skill. If its only sources are Azure Cosmos DB, MongoDB Atlas or Amazon DocumentDB pages, the status is `not_assessable`, and `searched` says the guidance was found only for a neighbouring service.
> - Grade only practices tied to a feature the app implements or the starter prompt explicitly asks for. A practice about vector indexes, embeddings, semantic caching, TTL, change streams or transactions in an app that does not use them is `not_applicable`; put the suggestion in `fix` prefixed "Optional accelerator:" so the report lists it without counting it as a violation.
> - A practice worded conditionally ("where appropriate", "if you need", "consider", "optionally") is advisory. It is never `violated`; use `not_applicable` with the suggestion in `fix`.
> - Do not use RU, request charge, `_etag`, If-Match or Retry-After in a practice, evidence or fix; these are Azure Cosmos DB RU-API concepts, and a check that needs them is a sign the source is about that service.
> - The canonical connection string for this service carries `retrywrites=false` (see the agent kit's `azure-deployment` skill). If a sample sets `retryWrites=true`, flag it once, under connection handling, as a deviation from the canonical string; do not also list it as an audit-trail gap, and do not state a reason for the setting.
> - Before you return, merge checks that state the same recommendation under different topics; keep one and cite both discovery ids in `evidence`.

### `factory/agents/auditor.py` (`audit_app`, after the URL rewrite loop and before the `return`; add `import re`, and `PracticeCheck` to the `..models` import)

A deterministic pass so the rules hold when the model slips. Former-name vCore pages are exempt:

```python
_VCORE_FORMER = "learn.microsoft.com/azure/cosmos-db/mongodb/vcore/"
_NEIGHBOUR = ("learn.microsoft.com/azure/cosmos-db/", "mongodb.com/docs/atlas", "docs.aws.amazon.com/documentdb")
_BANNED = re.compile(r"\b(RU|RUs|RU/s|request ?charge|_etag|ETag|If-Match|Retry-After|RequestRateTooLarge)\b", re.I)

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

Bare `429` is left out of `_BANNED` until the open question below is answered; `RequestRateTooLarge` and `Retry-After` already catch the RU-throttling wording.

### `tests/`

Add one unit test that feeds an `AuditReport` with a Cosmos-sourced `violated` check and a duplicated $jsonSchema pair, and asserts one `not_assessable` check and one surviving merged check.

## Evidence

- `runs/01-unified-customer-profile-store/20261124-203120/05a-practice-discovery.json` and `05-audit.json` (P11, P12, P17 confirmed by cosmos-db pages, then `violated`; `doc-gaps.md` asks for a 429/Retry-After helper)
- `runs/03-medication-interaction-checker/20261124-193347/05-audit.json` (P10, P11, P18 vector/semantic-cache violations with no embeddings; P13 429 handling sourced to a cosmos-db page)
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/05-audit.json` (P19 and P23 duplicate, conditionally worded $jsonSchema violations)
- `runs/14-dynamic-pricing-engine/20261124-184622/05-audit.json` (`_etag` concurrency `violated`; retryWrites graded only as an audit-trail gap)
- `runs/13-household-grouping-linkage/20261124-204947/05-audit.json` ("RU spikes" check; retryWrites true and false in one audit)

## Open questions

1. [needs SME confirmation] Does Azure DocumentDB ever return error 16500 / HTTP-429-style throttling to MongoDB clients (for example under connection or resource limits), or is it never returned? The draft assumed it is never returned; until engineering confirms, the proposal bans only RU-specific wording (`RequestRateTooLarge`, `Retry-After`), not a bare `429`.
2. [needs SME confirmation] Why does the canonical connection string set `retrywrites=false`? Some drafts in this experiment say retryable writes are unsupported and cause write errors; others say Learn does not claim they are unsupported and the setting is a recommendation. The auditor rule above only enforces consistency with the canonical string and states no reason; please give the engineering answer so the rule (and the agent kit, whose `skills/connection/SKILL.md` example URI and `skills/driver/driver-singleton-client.md` show `retryWrites=true` while `skills/azure-deployment/SKILL.md` shows `retrywrites=false`) can cite it.

## Source drafts

- 107-pipeline-audit-rubric-imports-cosmos-db-nosql-ru-api-concept.md
