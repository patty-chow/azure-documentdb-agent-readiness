# Documentation and tooling gaps: 07-multi-currency-ledger

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver compatibility mapping (Mongoose/mongodb-driver → server wire-version)

- **What was missing:** A concise, authoritative table mapping common Mongoose (and underlying mongodb-driver) versions to the Azure DocumentDB supported server-wire protocol / server versions and recommended pinned releases.
- **Where the agent looked:** Searched installed skills (documentdb-driver, connection) and Learn quickstarts; readiness_findings lists this gap.
- **Effect on this build:** Builder assumed Mongoose 7.x compatibility. Without a compatibility table the builder may pick an incompatible driver causing runtime connection or aggregation errors and delaying validation.
- **Suggested fix (learn_doc):** A one-page 'Driver compatibility' doc: rows mapping Mongoose major versions → mongodb-driver versions → supported server-wire versions (5.x/6.x/7.x), recommended pin, and example package.json lines. Include verification command (connect and run db.adminCommand({ buildInfo: 1 }) or show serverVersion from cluster) and a note about SRV/URI options (tls/retryWrites).

## [high] Mongoose-with-session recipe for DocumentDB

- **What was missing:** A short, public recipe that shows how to use Mongoose sessions with Azure DocumentDB, including session.startTransaction/session.withTransaction, passing { session } to all model calls, and an explicit retry loop for transient transaction errors.
- **Where the agent looked:** Searched DocumentDB skills and Learn quickstarts (documentdb-driver, query-optimization); found no concrete Mongoose-with-session example for DocumentDB.
- **Effect on this build:** The builder designed transactional posting but did not create code. Without a tested example, agents may implement transactions incorrectly (forgetting to pass { session } to all operations) and produce non-atomic writes.
- **Suggested fix (agent_kit_rule):** Add a short skill/resource: 'Mongoose sessions on DocumentDB' containing minimal code example (connect, startSession(), await session.withTransaction(async () => { await Model.create([..], { session }); await OtherModel.updateOne(..., { session }); }), retry-loop skeleton to re-run transaction on TransientTransactionError) and a note about session timeouts.

## [high] Decimal128 / currency arithmetic guidance

- **What was missing:** Authoritative guidance for DocumentDB on storing and computing monetary amounts (Decimal128 vs integer minor units) and how to propagate Decimal128 in aggregation ($toDecimal) for safe conversion arithmetic.
- **Where the agent looked:** Searched DocumentDB skills (data-modeling, query-optimization) and public Learn pages; found only prior-knowledge statements, no DocumentDB-specific recipe.
- **Effect on this build:** Builder design lists 'amount' but did not produce the model code specifying Decimal128. Lack of authoritative guidance risks using JavaScript Number and floating-point errors in currency conversions.
- **Suggested fix (learn_doc):** A short page 'Monetary values on Azure DocumentDB' explaining recommended storage types (Decimal128 or integer cents), code examples for Mongoose schema using mongoose.Types.Decimal128, aggregation examples showing $toDecimal and $multiply/$divide with Decimal128, and test cases demonstrating rounding behavior.

## [high] .env.example and required config list

- **What was missing:** A small example .env.example showing exactly which environment variables the sample expects (DOCUMENTDB_URI, PORT, NODE_ENV, SEED_SKIP, etc.) and placeholder values.
- **Where the agent looked:** No .env.example in workspace; searched skills and quickstarts for recommended variable names but no unified sample file exists for this scenario.
- **Effect on this build:** Builder recorded the need to read DOCUMENTDB_URI from env but did not publish .env.example. This makes it harder for users to run the sample safely without exposing secrets.
- **Suggested fix (discoverability):** Add a .env.example in the repo root and a README section that says 'Copy .env.example to .env and fill DOCUMENTDB_URI'.

## [high] Transaction lifetime and retry limits guidance

- **What was missing:** Authoritative statement on recommended transaction duration limits and the recommended retry-loop for transactions on Azure DocumentDB with Mongoose (timeouts, backoff).
- **Where the agent looked:** Searched skills and Learn pages; readiness_findings flagged missing single-page guidance for transaction lifetime and retry behaviour.
- **Effect on this build:** Builder assumed conservative timeouts but did not implement or verify retry/timeouts. Missing guidance risks long-running transactions that get aborted and unexpected failures in production.
- **Suggested fix (learn_doc):** A small guidance page: 'Transactions on DocumentDB' stating recommended max duration, how to set timeouts and serverSelectionTimeoutMS, sample retry-loop pattern for transient errors, and a note about keeping transactions short and touching few documents.

## [medium] Canonical idempotent seed pattern and sample dataset for ledger

- **What was missing:** A canonical idempotent seed script pattern and sample seed data (exchange rate documents with effectiveDate, transaction examples) for the multi-currency ledger scenario.
- **Where the agent looked:** Searches over skills and quickstarts; readiness_findings noted no canonical seed dataset for ledger scenario.
- **Effect on this build:** Builder planned an idempotent seed but did not author it. Without example data and a robust idempotent upsert pattern, agents are likely to write brittle seed scripts or duplicate data during repeated runs.
- **Suggested fix (sample_or_quickstart):** Provide scripts/seed.js example that upserts exchange rate docs keyed by (fromCurrency,toCurrency,effectiveDate) with createIndex for the compound index, sample transactions, and usage instructions. Include an idempotencyKey pattern for seed transactions and a --force option to reset sample data.

## [medium] Exchange-rate document indexing pattern

- **What was missing:** A public example recommending an ExchangeRate document shape (fromCurrency, toCurrency, rate: Decimal128, effectiveDate) and a compound index { fromCurrency:1, toCurrency:1, effectiveDate:-1 } for latest-rate lookups.
- **Where the agent looked:** Searched DocumentDB indexing and data-modeling skills; the general compound-index ESR recipe exists but no canonical currency-pair + effectiveDate example was found.
- **Effect on this build:** Builder's design includes exchange rate docs and a compound index but with no public example to cite agents may choose a suboptimal index or model shape and make lookups inefficient.
- **Suggested fix (learn_doc):** A short doc: 'Modeling exchange rates' with schema, recommended indexes, $lookup example to fetch latest effectiveRate in an aggregation, and a note on TTL or archiving older rates.

## [medium] Tests that run without live cluster (mocking patterns)

- **What was missing:** A documented pattern and example tests that run without a live DocumentDB cluster (in-memory server or mocking Mongoose models) for CI.
- **Where the agent looked:** Searched skills and quickstarts; no sample tests were found that demonstrate an offline test harness for DocumentDB-specific features.
- **Effect on this build:** No tests were produced; team and agents lack a quick recipe for creating unit tests that don't require the live cluster, slowing CI setup and making regression checks harder.
- **Suggested fix (sample_or_quickstart):** Add a tests/ folder with example unit tests using sinon or an in-memory MongoDB library and instructions for which tests require live cluster vs mocked behavior. Include a CI snippet that runs unit tests without network access.

