---
title: "Audit stage grades vCore samples against Cosmos DB RU-API practices, unrequested accelerators and conditional advice; add grounding, scope and de-dup rules"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 57
findings: 10
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Audit stage grades vCore samples against Cosmos DB RU-API practices, unrequested accelerators and conditional advice

## What happens today

The audit (`prompts/auditor.md`, `factory/agents/auditor.py::audit_app`) marks samples as `violated` against practices that are not Azure DocumentDB (vCore) guidance, or that the sample never set out to implement:

1. **Cosmos DB RU-API concepts imported as vCore rules.** Discovery (`prompts/practice_discovery.md`) records model priors about Azure Cosmos DB as `prior_knowledge_confirmed` by citing `learn.microsoft.com/azure/cosmos-db/...` pages, although the prompt says a Cosmos page cannot confirm a belief for this service. The auditor then grades against them. Examples: "instrument the app to log requestCharge" (`01-unified-customer-profile-store`, P12), "optimistic concurrency using system _etag / If-Match" (`01-unified-customer-profile-store` P17, `14-dynamic-pricing-engine` P14, both sourced to `cosmos-db/database-transactions-optimistic-concurrency`), "avoid unbounded arrays ... to prevent RU spikes" (`13-household-grouping-linkage` P13, sourced to `cosmos-db/modeling-data`), "handle RequestRateTooLarge / HTTP 429, respect Retry-After" (`03-medication-interaction-checker` P13, sourced to `cosmos-db/troubleshoot-request-rate-too-large`). vCore has no request charge, no `_etag`, and no RU-based HTTP 429/Retry-After throttling (clients speak the MongoDB wire protocol); capacity is vCore M-series tiers, observed through CPU, memory, IOPS and connection metrics.
2. **Readiness accelerators carried forward as hard requirements.** `03-medication-interaction-checker` is marked `violated` three times (P10 vector store field, P11 DiskANN/HNSW tuning, P18 "use the DocumentDB vector store as a semantic cache") although the sample stores no embeddings and the starter prompt asks for Mongoose lookups plus an LLM, not semantic retrieval. The evidence text itself says "the repo does not store embeddings".
3. **Conditional advice turned into violations.** Practices worded "where appropriate" / "if you need JSON Schema enforcement" ($jsonSchema validators) are graded `violated` for demo-scale samples (`08-insurance-pre-auth-multi-agent`, `08-interest-rate-scenario-modeler`).
4. **Duplicates.** `08-insurance-pre-auth-multi-agent` carries two `violated` checks for the same $jsonSchema gap under "JSON Schema validation" (P19) and "Collection-level JSON Schema" (P23), both pointing at the same URL.
5. **retryWrites contradiction.** Some checks hold `retryWrites=false` as the standard (`01-unified-customer-profile-store` P03), others only ask that `retryWrites=True` be logged as a decision (`14-dynamic-pricing-engine`), and `13-household-grouping-linkage` says both in one audit.

## Why it matters

Across 117 audits of 101 samples (2,199 checks):

- 146 discovered practices in 55 samples are `prior_knowledge_confirmed` by a `cosmos-db` page; 37 `violated` checks in 31 samples rest solely on one of them.
- 72 `violated` checks in 57 samples use RU / request-charge / `_etag` / 429 / Retry-After vocabulary.
- 36 `violated` checks in 23 samples target a feature the sample does not implement (vector index, embeddings, semantic cache, TTL, change streams).
- 17 `violated` checks in 13 samples are on conditionally worded practices.
- 7 runs carry two `violated` checks for the same practice; 5 audits assert both `retryWrites=true` and `=false`.

The "fixes" these checks propose would make the samples wrong for the product (logging a request charge that the driver never returns, filtering updates by a `_etag` field that does not exist, bolting a vector index onto a sample that has no vectors). They also inflate the violation count the product team reads, and `doc-gaps.md` then asks the team to ship guidance for Cosmos concepts (e.g. "honor 429 Retry-After" in `01-unified-customer-profile-store/doc-gaps.md`).

## Proposed change

### `prompts/practice_discovery.md`

The first bullet under **Rules** already says a Cosmos DB page does not confirm a belief, but 146 practices in 55 samples were still confirmed by one. Replace that bullet with this stricter, URL-based wording:

> A prior belief is `prior_knowledge_confirmed` only when the source is an Azure DocumentDB page (`learn.microsoft.com/azure/documentdb/...`, `learn.microsoft.com/documentdb/...`, or a page under `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`, the service's former name), the open-source DocumentDB docs, or an installed skill. Any other page under `learn.microsoft.com/azure/cosmos-db/` (NoSQL, RU-based MongoDB API), a MongoDB Atlas page or an Amazon DocumentDB page never confirms a belief: the belief stays `prior_knowledge_only`, and you may cite the page in `how_found`. When you write a `practice`, use this service's vocabulary: CPU, memory, IOPS, connection and storage metrics (not RU or request charge); a version field in a conditional update (not `_etag` / If-Match); document size and working-set growth (not RU spikes); driver transient-error retry with backoff (not HTTP 429 / Retry-After).

### `prompts/auditor.md`

Add to **Step 2: check the app against each practice**, after the `not_assessable` bullet:

> - A practice may be `violated` only if a source cited for it is an Azure DocumentDB page, the open-source DocumentDB docs or an installed skill. If its only sources are Azure Cosmos DB, MongoDB Atlas or Amazon DocumentDB pages, the status is `not_assessable`, and `searched` says the guidance was found only for a neighbouring service.
> - Grade only practices tied to a feature the app implements or the starter prompt explicitly asks for. A practice about vector indexes, embeddings, semantic caching, TTL, change streams or transactions in an app that does not use them is `not_applicable`; put the suggestion in `fix` prefixed "Optional accelerator:" so the report lists it without counting it as a violation.
> - A practice worded conditionally ("where appropriate", "if you need", "consider", "optionally") is advisory. It is never `violated`; use `not_applicable` with the suggestion in `fix`.
> - Do not use RU, request charge, `_etag`, If-Match, HTTP 429 or Retry-After in a practice, evidence or fix. The service has none of these; a check that needs them is a sign the source is about Azure Cosmos DB.
> - Connection strings for this service use `retrywrites=false` (see the `azure-deployment` skill). Treat `retryWrites=true` as a deviation to flag once under connection handling; do not also list it as an audit-trail gap.
> - Before you return, merge checks that state the same recommendation under different topics; keep one and cite both discovery ids in `evidence`.

### `factory/agents/auditor.py` (`audit_app`, after the URL rewrite loop)

Add a deterministic pass so the rules hold even when the model slips (the prompt-only rules already in `auditor.md` Step 2 were not enough). Requires `import re`. Former-name vCore pages are exempt, matching the existing rule that a page using a former product name still counts as a source:

```python
_VCORE_FORMER = "learn.microsoft.com/azure/cosmos-db/mongodb/vcore/"
_NEIGHBOUR = ("learn.microsoft.com/azure/cosmos-db/", "mongodb.com/docs/atlas", "docs.aws.amazon.com/documentdb")
_BANNED = re.compile(r"\b(RU|RUs|RU/s|request ?charge|_etag|ETag|If-Match|429|Retry-After|RequestRateTooLarge)\b", re.I)

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9$ ]", "", text.lower()).strip()

seen: dict[str, PracticeCheck] = {}
for c in checks:
    neighbour = any(n in c.source_url for n in _NEIGHBOUR) and _VCORE_FORMER not in c.source_url
    if c.status == "violated" and (neighbour or _BANNED.search(c.practice)):
        c = c.model_copy(update={"status": "not_assessable",
                                 "searched": (c.searched + " Downgraded: only neighbouring-service sources or RU/ETag/429 vocabulary.").strip()})
    k = _norm(c.practice)[:80]
    if k in seen:
        seen[k] = seen[k].model_copy(update={"evidence": f"{seen[k].evidence} Also {c.discovery_id or c.topic}."})
        continue
    seen[k] = c
checks = list(seen.values())
```

Add one unit test under `tests/` that feeds an `AuditReport` with a Cosmos-sourced violated check and a duplicated $jsonSchema pair and asserts one `not_assessable` and one surviving check.

## Evidence

- `runs/01-unified-customer-profile-store/20261124-203120/05a-practice-discovery.json` (P11, P12, P17: `prior_knowledge_confirmed` with `prior_belief_about: azure_cosmos_db` and cosmos-db URLs) and `05-audit.json` (same ids graded `violated`; `doc-gaps.md` asks for a 429/Retry-After helper)
- `runs/03-medication-interaction-checker/20261124-193347/05-audit.json` (P10, P11, P18 `violated` while evidence says no embeddings exist; P13 429 handling sourced to a cosmos-db page)
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/05-audit.json` (P19 and P23 duplicate $jsonSchema violations, both conditionally worded)
- `runs/14-dynamic-pricing-engine/20261124-184622/05-audit.json` (`_etag` optimistic concurrency `violated`; retryWrites graded only as an audit-trail gap)
- `runs/13-household-grouping-linkage/20261124-204947/05-audit.json` ("RU spikes" unbounded-array check sourced to cosmos-db/modeling-data; retryWrites true-vs-false in the same audit)

Related but out of scope here: `skills/connection/SKILL.md` in the agent kit shows `retryWrites=true` in its example URI while `skills/azure-deployment/SKILL.md` says `retrywrites=false`; the auditor rule above should cite the latter until the kit is reconciled.

## Verification

### 1. Already covered? partially_covered
The pipeline already states the intent in prose but does not enforce it, and the auditor prompt has none of the scope, conditional-wording, vocabulary, de-dup or retrywrites rules.
- `prompts/practice_discovery.md` (Rules, first bullet): "A page about MongoDB, Amazon DocumentDB or Azure Cosmos DB that agrees with the belief does not confirm it for this service; that belief stays `prior_knowledge_only`". Runs show it was ignored, e.g. `runs/01-unified-customer-profile-store/20261124-203120/05-audit.json` P17 is `violated`, sourced to `learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency`.
- `prompts/auditor.md` Step 2: `not_assessable` is required for `prior_knowledge_only` practices, and the prompt says "Do not use your own memory of MongoDB, Amazon DocumentDB or Azure Cosmos DB as the standard." It has no rule on unrequested features, conditional wording, RU/ETag/429 vocabulary, duplicate checks or retrywrites.
- `factory/agents/auditor.py` `audit_app()` (lines ~161-173) only rewrites URLs and source links; there is no status downgrade or de-duplication pass.
So the draft was reworded to say it tightens an existing rule rather than adding a missing one.

### 2. Premise true? confirmed (one correction applied)
- Azure DocumentDB (vCore) capacity is vCore M-series tiers, not request units; it returns no request charge and has no `_etag`/If-Match or RU 429/Retry-After throttling. These are Azure Cosmos DB for NoSQL / RU concepts. Consistent with the task's ground facts.
- Connection strings use `retrywrites=false`: agent-kit `skills/azure-deployment/SKILL.md` line 288-291 ("Azure DocumentDB does not support retryable writes"). The kit's `skills/connection/SKILL.md` line 60 shows `retryWrites=true`, as the draft notes.
- Evidence spot-checked in run files: 01 P12 (RU/request-charge monitoring, violated), P17 (ETag/If-Match, cosmos-db URL, violated); 03 P10/P11/P18 (vector/semantic-cache practices, violated), P13 (RequestRateTooLarge/429, cosmos-db URL, violated); 08-insurance P19 and P23 (same $jsonSchema URL, P23 worded "If you need", both violated).
- Correction: the draft's URL rule and `_NEIGHBOUR` list treated every `learn.microsoft.com/azure/cosmos-db/` page as a neighbouring service. Pages under `azure/cosmos-db/mongodb/vcore/` document this service under its former name ("Azure Cosmos DB for MongoDB vCore"), and the existing discovery rule counts them as valid sources. The proposed rule text and code now exempt that path. (No current run cites such a page, so the evidence counts are unchanged.) Also said in the body that the 429/Retry-After absence is about RU throttling, and named vCore metrics.

### 3. Maintainer skeptic: confirmed
It names exact files (`prompts/practice_discovery.md`, `prompts/auditor.md`, `factory/agents/auditor.py` `audit_app`, `tests/`), gives replacement prompt text and a code patch that fits the existing `PracticeCheck` fields (`status`, `source_url`, `practice`, `searched`, `evidence`, `discovery_id`, `topic` in `factory/models.py`), and has counted evidence across 57 samples. It is specific to Azure DocumentDB vs Cosmos DB RU confusion. Small edits applied: say `import re` is needed, exempt former-name vCore pages. The agent-kit retryWrites inconsistency is correctly left as a separate kit issue.

## Finding ids

- F0172
- F0173
- F0409
- F0410
- F0415
- F1249
- F1251
- F1292
- F2236
- F2380
