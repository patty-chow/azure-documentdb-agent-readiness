---
title: "data-modeling: add rule \"store monetary values as Decimal128 or integer minor units, never float\""
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 5
findings: 1
bucket: other-inventory
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# data-modeling: add rule "store monetary values as Decimal128 or integer minor units, never float"

## What happens today

`skills/data-modeling/SKILL.md` lists five rules; none covers numeric types. When an agent using the kit builds a finance sample it falls back on its prior that `float` / JS `Number` is fine for money:

- 02-swift-message-parser-store: `app/app/models.py:12` -> `amount: Optional[float]`; `app/app/parser.py:45` -> `float(amt)`; `app/app/main.py:47` -> `{"$sum": {"$ifNull": ["$amount", 0]}}` over those floats. No decision log entry, no README caveat.
- 03-core-banking-transaction-ledger: `transaction.amount` and `account.balance` are Mongoose `Number`, and `$inc` runs on them.
- 12-invoice-matching-reconciliation: `totalAmount: Number` on Invoice and PurchaseOrder.
- 13-basel-iii-capital-ratio-calculator: capital totals seeded as Python floats and summed in the pipeline.

The audit stage marked its "monetary type" check **violated** in each of these four runs (02, 03, 12, 13); in 07-multi-currency-ledger the same check was `not_assessable`. Three runs (07, 12, 13) separately logged a doc gap asking for exactly this guidance in the agent kit or Learn.

## Why it matters

- Across the 100 generated samples, a rough grep of the generated apps finds about 20 sample folders that type an `amount` / `price` / `balance` / `total` field as `float` or `Number`, and **zero** that use `Decimal128` (no `Decimal128`, `DecimalAnnotation` or `Schema.Types.Decimal128` anywhere). The kit never corrects the prior, so this will not change on its own.
- Summing IEEE doubles in `$group` produces results like `0.30000000000000004`; for a SWIFT, ledger, invoice-matching or regulatory-capital sample that is a correctness bug a reviewer can miss, and these samples are published as reference material.
- Azure DocumentDB supports BSON Decimal128 and the `$toDecimal` / `$convert` operators (compatibility page below), so the correct pattern is available and cheap; the agent just needs to be told.

## Proposed change

### 1. New file `skills/data-modeling/model-monetary-decimal128.md`

```markdown
# model-monetary-decimal128

**Category:** Data Modeling · **Priority:** HIGH

## Why it matters

Binary floating point (`double`, Python `float`, JavaScript `Number`) cannot represent most decimal fractions exactly. Storing money as a float and summing it with `$sum` or `$inc` accumulates rounding error (`0.1 + 0.2 = 0.30000000000000004`). For payments, ledgers, invoices, pricing and regulatory figures, store amounts either as **BSON Decimal128** or as an **integer in minor units** (cents) with a separate `currency` field. Azure DocumentDB stores Decimal128 natively and supports `$toDecimal` and `$convert` in aggregation pipelines.

Pick one representation per collection and keep it in the schema; do not mix floats and decimals in the same field.

## Incorrect

```python
# Python / Beanie
class SwiftMessage(Document):
    amount: float            # binary float, rounding errors on $sum
```

```javascript
// Mongoose
const txn = new Schema({ amount: { type: Number } });   // JS double
await Account.updateOne({ _id }, { $inc: { balance: 19.99 } });
```

## Correct

Option A, Decimal128 (exact decimal arithmetic, keeps the unit in the value):

```python
# Python / Beanie
from beanie import Document, DecimalAnnotation

class SwiftMessage(Document):
    amount: DecimalAnnotation     # stored as BSON Decimal128
    currency: str

# PyMongo without an ODM
from decimal import Decimal
from bson.decimal128 import Decimal128
coll.insert_one({"amount": Decimal128(Decimal("1234.56")), "currency": "EUR"})
```

```javascript
// Mongoose
const txn = new Schema({
  amount:   { type: Schema.Types.Decimal128, required: true,
              get: v => v == null ? v : v.toString() },
  currency: { type: String, required: true }
}, { toJSON: { getters: true } });
```

Option B, integer minor units (simplest, fastest to index and `$inc`):

```javascript
{ amountMinor: 123456, currency: "EUR" }   // 1234.56 EUR
```

Aggregating: `$sum` over a Decimal128 field returns Decimal128. If legacy documents hold floats, convert explicitly before summing:

```javascript
{ $group: { _id: "$messageType",
            total: { $sum: { $toDecimal: "$amount" } } } }
```

Rules of thumb:
- Never parse an amount through `float()` / `parseFloat()` on the way in; parse strings to `Decimal` / `Decimal128` directly.
- Return amounts to API clients as strings (or minor-unit integers), not JSON numbers.
- Index the Decimal128 or integer field like any scalar; both sort correctly.
- If a sample deliberately keeps floats for brevity, say so in the README and in the decision log, and name Decimal128 as the production choice.

## References

- Azure DocumentDB MQL compatibility (`$toDecimal`, `$convert` supported v5.0-v8.0): https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language
- BSON specification, Decimal128 type: https://bsonspec.org/spec.html
```

### 2. `skills/data-modeling/SKILL.md`

Add to the Rules list:

```markdown
- [model-monetary-decimal128](model-monetary-decimal128.md) — Store money as BSON Decimal128 or integer minor units with a `currency` field; never as `float` / `Number`. Parse and return amounts as strings or decimals, and `$toDecimal` before summing legacy floats.
```

And extend the front-matter `description` so the skill is selected for finance prompts, e.g. append: `..., choosing numeric types for monetary or regulatory values (Decimal128 vs integer minor units),`.

## Related (not in this PR)

The 02-swift sample itself should either adopt the rule or add a decisions.jsonl entry and a README "Precision caveat" paragraph stating that floats are a sample-only simplification and production code must use Decimal128 or integer cents. Once the rule above lands, re-running the sample should produce that outcome without manual intervention.

## Evidence (run folders)

- runs/02-swift-message-parser-store/20261124-200226/05-audit.json (check P12 "Monetary amounts type": violated; doc_gap "Repository decision audit: storing amounts as floats")
- runs/02-swift-message-parser-store/20261124-200226/app/app/models.py line 12
- runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json (checks "Monetary types" and "Numeric types in updates": violated)
- runs/12-invoice-matching-reconciliation/20261124-191603/05-audit.json (check "Monetary storage type": violated; doc_gap "Recommendation for monetary types")
- runs/13-basel-iii-capital-ratio-calculator/20261124-201926/05-audit.json (check "Monetary numeric type": violated; doc_gap asking for agent-kit guidance)
- runs/07-multi-currency-ledger/20261124-190814/05-audit.json (check "Decimal128 for money": not_assessable; doc_gap "Decimal128 / currency arithmetic guidance", priority high)

## Verification

### 1. Already covered? -- confirmed (not there)
`skills/data-modeling/SKILL.md` in Azure/documentdb-agent-kit lists exactly five rules (model-embed-vs-reference, model-16mb-limit, model-denormalize-reads, model-schema-versioning, model-large-field-split) and its description covers "embed vs reference, 16 MB document limit, denormalization ..., schema versioning" only. A grep of `skills/` and `knowledge-base/` for `decimal128|monetary|money|currency|minor unit` returns no modeling guidance (only unrelated hits such as "wastes money" in `skills/sharding/sharding-scaling-out-vs-up.md` and fp32/fp16 vector floats in `skills/vector-search/vector-half-precision.md`). On Learn, the MQL compatibility page lists `$toDecimal` and `$convert` as supported but gives no monetary-type guidance; the runs' own doc_gaps (07, 12, 13) report the same absence.

### 2. Premise true? -- confirmed, with count corrections applied
- Sample code verified: `runs/02-swift-message-parser-store/20261124-200226/app/app/models.py` line 12 `amount: Optional[float]`; `parser.py` line 45 `float(amt)`; `main.py` lines 46-47 `$sum` over `$amount`.
- Audit statuses verified: "violated" in 02 (Monetary amounts type), 03 (Monetary types; Numeric types in updates), 12 (Monetary storage type), 13 (Monetary numeric type); 07 "Decimal128 for money" is `not_assessable`, not violated. The draft's "flagged as violated in each" was corrected to four runs plus 07 as not_assessable.
- The draft's "11 samples use float/number, one uses integer cents" could not be reproduced: a rough grep matches about 20 sample folders and the integer-cents claim was not verified, so the body now states "about 20" and drops the cents claim. Zero uses of Decimal128 confirmed.
- Service facts: https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language lists `$toDecimal` and `$convert` (Type Expression Operators) as "Yes" for v5.0, v6.0, v7.0 and v8.0, and `$sum` / `$inc` as supported. Decimal128 is a standard BSON type (https://bsonspec.org/spec.html); `$sum` over Decimal128 returns Decimal128 per MQL semantics. Beanie exports `DecimalAnnotation` for Pydantic v2 Decimal128 storage; Mongoose exposes `Schema.Types.Decimal128`. Nothing in the draft contradicts the Azure DocumentDB facts (vCore, mongoClusters, PostgreSQL-based engine).

### 3. Maintainer skeptic -- confirmed
Names exact files (`skills/data-modeling/model-monetary-decimal128.md` new, `skills/data-modeling/SKILL.md` rules list and description), follows the existing rule-file shape, and ties the guidance to DocumentDB by citing the compatibility page for `$toDecimal` / `$convert`. The underlying practice is general MongoDB hygiene, but the kit's data-modeling skill is the place a DocumentDB coding agent reads for schema choices and four audited finance samples violated it, so I would accept it with the small edits above. The sample-level fix (decision log / README caveat in 02-swift) is correctly scoped out of this PR.

## Finding ids

- F0302
