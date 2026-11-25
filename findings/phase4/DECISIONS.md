# Phase 4 decisions and answered questions

## retryWrites: answered 2026-11-25

**Answer.** `retrywrites=false` is required, not a style choice. Azure DocumentDB does not support
retryable writes. The DocumentDB product team confirmed this in an internal sync on 2026-11-23 and is
changing every sample in Learn and the Azure-Samples repositories to `retrywrites=false`; by
2026-11-25 the TypeScript and .NET Learn samples were consistent. The kit's own
`skills/azure-deployment/SKILL.md` (line 291) already says the feature is not supported, while three
other kit files still show `retryWrites: true` (`skills/connection/SKILL.md:60`,
`skills/driver/driver-singleton-client.md:26`, `skills/security/security-tls-required.md:26`).

**Mechanism, from the engine.** Open issue documentdb/documentdb#767 (filed 2026-10-05): the gateway
passes a NULL transaction id to the engine, so the engine's retryable-write de-duplication table is
never used; sending the same `lsid` + `txnNumber` twice applies the write twice. A driver with
`retryWrites=true` therefore gets no exactly-once protection: a retried non-idempotent write (for
example `$inc`) can be applied twice, and a retried insert reports a duplicate key for a write that
succeeded. That is the concrete risk behind "not supported".

**What is not established.** No source shows that `retryWrites=true` by itself produces connection
errors, which is what the kit's azure-deployment sentence claims. Filings must not assert that.

**What Learn says today.** Every quickstart and the Entra ID page carry `retrywrites=false` in the
connection string, but no Learn page (limitations, compatibility, connect) explains why. That gap is
part of the Learn filings L03 (write semantics) and L07 (connection-string reference) as a concrete
ask rather than a question.

**Canonical one-liner for the kit and samples.**
"Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support
retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a
non-idempotent write twice. Handle transient write failures in application code with idempotent
operations (upserts, deterministic keys)."

Sources: DocumentDB product team, internal sync 2026-11-23 and follow-up 2026-11-25;
https://github.com/documentdb/documentdb/issues/767;
https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs;
https://learn.microsoft.com/en-us/azure/documentdb/limitations;
https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language.
