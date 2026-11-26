---
id: L05
title: "Quickstarts: explain the SRV connection string and add a 'Choose an authentication method' section that surfaces the Entra ID samples"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 23
member_drafts:
  - 074-connect-and-authenticate-canonical-srv-connection-string-exp.md
  - 046-entra-id-mongodb-oidc-and-cosmossearchoptions-how-to-pages-s.md
open_questions: 2
---

# Quickstarts: explain the SRV connection string and add a "Choose an authentication method" section that surfaces the Entra ID samples

**Pages:** [quickstart-python](https://learn.microsoft.com/azure/documentdb/quickstart-python), [quickstart-nodejs](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs) (JS and TS pivots), [how-to-connect-role-based-access-control](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control) (source repo MicrosoftDocs/nosql-docs-pr).

## What happens today

- **The quickstarts paste the `mongodb+srv://` string into code with no explanation.** "Get cluster credentials" is portal-only: it does not mention `az documentdb mongocluster list-connection-strings` (`documentdb` extension) or warn that Azure Cosmos DB for MongoDB (RU) strings (`:10255`, `replicaSet=globaldb`) do not work here. The code hard-codes `<your-cluster-name>.global.mongocluster.cosmos.azure.com` while the text says to copy "the Connection string field", although the portal shows two fields (Self (always this cluster) and Global read-write) and the mongosh, Cloud Shell and training-unit pages use the plain `<cluster>.mongocluster.cosmos.azure.com` host. Neither form is wrong; no quickstart says that two exist or when each one matters.
- **The quickstarts show only SCRAM-SHA-256.** Neither mentions Microsoft Entra ID or `MONGODB-OIDC`, or links the RBAC how-to. The Mongoose quickstart's production note does exist; these two quickstarts lack it.
- **The Entra code exists but is hard to find.** It is the last section of the ~6,400-word RBAC how-to, under a heading that names no driver or package, so searches land on "Enable Microsoft Entra ID authentication" instead.
- **That section is incomplete:**
  - The Python snippet has no imports.
  - There is no JavaScript or Mongoose tab (the full Mongoose example is only in `tutorial-nodejs-mongoose`).
  - There are no driver minimums, environment variables or troubleshooting. The Python sample sets no `ALLOWED_HOSTS`, so it fails on PyMongo 4.7.0 to 4.10.1, which refuse an Azure host for a custom callback without it; it works from PyMongo 4.11 (managed test of the sample's callback class with `AzureCliCredential`, not the sample's `DefaultAzureCredential`: 4.7.0 and 4.10.1 refused before calling the callback, 4.11 connected on the plain host and 4.20.2 on the plain and `.global.` hosts; the other releases are inferred from a source check).
  - The TypeScript sample subtracts seconds from `expiresOnTimestamp`, which is in milliseconds (`@azure/core-auth` documents the field as epoch milliseconds; the driver expects `expiresInSeconds`). The JavaScript pivot of `how-to-build-nodejs-console-app` already has the correct arithmetic.
  - The Node.js sample sets `ALLOWED_HOSTS: ['*.azure.com']`, while `tutorial-nodejs-mongoose` and the MCP README use `*.mongocluster.cosmos.azure.com`; nothing explains what the list is checked against.

## Why it matters

In one experiment run, gpt-5-mini built 100 sample apps (Node `mongodb`, Mongoose, PyMongo, Motor) with the DocumentDB Agent Kit and the Learn MCP server. All counts come from that single run, which had known harness defects; recount after the re-run before quoting them externally (see question 1).

- **23 distinct samples (24 in-scope findings) filed this gap.** This is reconciled across both drafts: 20 samples from one draft and 4 from the other, with one sample in both. Two more bucketed findings are out of scope (a retry/backoff request, and the PyMongo `cosmosSearchOptions` ask handled in item 4).
- **Cold answers before grounding** (latest readiness record for each of 101 samples; these reflect model priors, not page defects):
  - The connection-string question was wrong, partly wrong or outdated in 91 of 101 readiness records, mostly the legacy RU string.
  - The auth question was wrong or partly wrong in 88, mostly "Entra ID is control-plane only".
  - 10 records per question could not be verified.
- **Grounding fixed the fact, not the how-to.** Learn search returned the enable step, not the code.
- **The builds shipped an admin SCRAM `DOCUMENTDB_URI`.** Their READMEs say Entra ID "is not demonstrated here". These pages are what the Learn MCP server returns for "connect with Python/Node".

## Proposed change

**1. Quickstarts, "Get cluster credentials":**
- Add the CLI command, `az documentdb mongocluster list-connection-strings`. It returns `GlobalReadWrite` first and `Self` second, plus `GlobalMicrosoftEntraId` and `MicrosoftEntraId` (`MONGODB-OIDC`, no credentials) once Entra ID is enabled, so pick a string by `name`, not by position.
- Add a table for each part of the string:
  - `mongodb+srv://`: SRV lookup, so no port. The cluster hosts are SRV names with no A record, so a `mongodb://` string with the cluster host fails.
  - Host: `<cluster>.mongocluster.cosmos.azure.com` (the portal's Self string) or `<cluster>.global.mongocluster.cosmos.azure.com` (the Global read-write string). On a single cluster the two are interchangeable. If the cluster has or may get a cross-region replica, use the Global read-write string for writes so that a promotion needs no code change; the old primary's Self string becomes read-only after promotion, and replica clusters expose only a Self string. Never construct the host from the cluster name; use the string the portal, CLI or REST API returns.
  - `tls=true`: required.
  - `authMechanism=SCRAM-SHA-256`: native auth (`MONGODB-OIDC` for Entra ID).
  - `retrywrites=false`: required. Proposed text: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)."
  - `maxIdleTimeMS=120000`: recommended.
- Explain why `retrywrites=false` is required, with the de-duplication reason (documentdb/documentdb#767). Every quickstart carries the setting today, but no Learn page explains it.
- Add a Note: "Connection strings from Azure Cosmos DB for MongoDB (RU) do not work with Azure DocumentDB clusters." Tell readers to copy the string from the portal or the CLI, and link the RBAC how-to's "Get cluster credentials" option table.
- Make the code and the text agree on the host: either keep the hard-coded `.global.` host and add the one-sentence Self/Global explanation above, or switch to the plain host so the quickstarts match mongosh, Cloud Shell, the training unit and the REST API's default connection string. Name both portal fields (Self (always this cluster), Global read-write) wherever the reader is told to copy "the Connection string field".

**2. Quickstarts, new H3 "Choose an authentication method":**
- **Native (SCRAM-SHA-256):** for development and demos. Read it from an environment variable, keep it in Key Vault, and prefer a least-privilege secondary user over the admin user.
- **Microsoft Entra ID (`MONGODB-OIDC`):** for anything deployed to Azure.
  - Enable it with `authConfig.allowedModes` (`az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID`; Terraform `authentication_methods`, azurerm 4.55.0 or later), then register the identity with `az documentdb mongocluster microsoft-entra-user assign` (`--type User` for a person; `--type ServicePrincipal --object-id <principalId>` for a service principal or managed identity, using the object ID, not the application/client ID; `--type` accepts only these two values).
  - The free tier does not support it.
  - Link to the RBAC code section.
  - Optionally add a short `DefaultAzureCredential` snippet per pivot (scope `https://ossrdbms-aad.database.windows.net/.default`, `tls: true`, `retryWrites: false`; in Node.js also `ALLOWED_HOSTS: ['*.mongocluster.cosmos.azure.com']`, which the Node driver requires for a custom `OIDC_CALLBACK` and PyMongo 4.11 and later do not check for machine callbacks; 4.7.0 to 4.10.1 refuse the Azure host without it), with one closing line: `DefaultAzureCredential` uses the `az login` session locally and the managed identity when deployed; set `AZURE_CLIENT_ID` for a user-assigned identity. State the driver floors: PyMongo 4.11 (or 4.7 with `ALLOWED_HOSTS` set) and Node.js driver 6.7.0 with `ALLOWED_HOSTS`, as observed on the managed service.
- Reuse the production Important note from `quickstart-nodejs-mongoose`: password authentication is for the free tier and quick evaluation; for production, use a paid cluster with Microsoft Entra ID and a least-privilege managed identity.

**3. RBAC how-to, code section:**
- Retitle it, for example "Connect from application code with PyMongo, the Node.js driver, Mongoose, and .NET (MONGODB-OIDC)", and name the packages in its intro.
- Move it above the secondary-identities section, or give it its own page.
- Fix the samples:
  - Add the Python imports.
  - Fix TypeScript to `Math.floor((expiresOnTimestamp - Date.now()) / 1000)`, as the JavaScript pivot of `how-to-build-nodejs-console-app` already does; fix the TypeScript pivot of that page too.
  - Change the Node.js sample's `ALLOWED_HOSTS: ['*.azure.com']` to `['*.mongocluster.cosmos.azure.com']` so the page agrees with `tutorial-nodejs-mongoose` and the MCP README. Both patterns match both host forms (a leading `*.` matches nested subdomains), but the tighter one is the better default. Add the tutorial's explanation: the driver checks the hosts returned by DNS SRV resolution, not just the cluster hostname in the URI, so the entry must be a wildcard on the service domain; never use `*`.
  - Add JavaScript and Mongoose tabs, or a link to the tutorial, and link the Java callback on `how-to-build-java-console-app` (the page has only Python, TypeScript and C# tabs today).
- Add Requirements (driver minimums for `MONGODB-OIDC`: PyMongo 4.11 for the page's sample, which sets no `ALLOWED_HOSTS`, or 4.7 with `ALLOWED_HOSTS` set; Node.js driver 6.7.0 with `ALLOWED_HOSTS`; Java driver 5.1; .NET driver 2.25.0; for Mongoose, the versions `tutorial-nodejs-mongoose` lists as tested, 7.8.0 and 9.12.1; and a statement of whether Microsoft Entra ID needs a particular cluster compatibility version, since MongoDB's driver docs scope `MONGODB-OIDC` to Atlas and Enterprise Advanced 7.0 or later and no Learn page says what Azure DocumentDB requires; the managed test saw it work on server version 8.0, and 5.0, 6.0 and 7.0 were not tested), environment variables (`DOCUMENTDB_URI` without credentials, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`) and Troubleshooting:
  - `allowedModes` is missing `MicrosoftEntraID` (code 18 `AuthenticationFailed`, "The authentication mechanism provided is not supported in the service.").
  - The identity is unregistered (code 18, "External identity is not present in the system.").
  - The scope is wrong.
  - The callback sends no token (code 18, "JWT token missing from OIDC payload").
  - `retryWrites` was dropped or set to `true`: Azure DocumentDB does not support retryable writes; the server does not de-duplicate a retried write (documentdb/documentdb#767), so a retried non-idempotent write can be applied twice. Keep `retrywrites=false`.
  - `ALLOWED_HOSTS` is missing or wrong (Node.js, and PyMongo 4.7.0 to 4.10.1): the Node driver validates `ALLOWED_HOSTS` after SRV resolution for every custom `OIDC_CALLBACK`, and its default list has no Azure domain, so a connection without it fails with `MongoInvalidArgumentError: Host '...' is not valid for OIDC authentication with ALLOWED_HOSTS of ...`; PyMongo 4.7.0 to 4.10.1 fail with `ConfigurationError` "Refusing to connect to ..., which is not in authOIDCAllowedHosts". Use `['*.mongocluster.cosmos.azure.com']`, or PyMongo 4.11 or later.
- Cross-link back to the quickstarts.
- Other fixes on the same page that a reader choosing an authentication method hits:
  - The Terraform pivot of "Enable Microsoft Entra ID authentication" sets `authentication_enabled = true`, which is not an argument of `azurerm_mongo_cluster`; the argument is `authentication_methods = ["NativeAuth", "MicrosoftEntraID"]` (azurerm 4.55.0 or later), and `azurerm_mongo_cluster_user` exists for the administrator registration the pivot does with azapi.
  - The overview sentence "A cluster must have native authentication enabled; the supported configurations are native-only or Microsoft Entra ID authentication only or native and Microsoft Entra ID authentication" contradicts itself; say which configurations are supported.

**4. `vector-search`, Python coverage** (from 046; fold into the Learn vector-search filing if that lands first):
- Under the HNSW and IVF tabs, add the Python `db.command({...})` form the DiskANN tab already has (same `createIndexes` document with `kind: "vector-hnsw"` or `"vector-ivf"`).
- Add one sentence that PyMongo can also pass the spec through `collection.create_index([("<field>", "cosmosSearch")], name=..., cosmosSearchOptions={...})` [needs SME confirmation] (see question 2), and repeat that vectors must be `number[]` to be indexed.

Out of scope here:
- The Agent Kit's OIDC placeholder and host suffix are tracked in Azure/documentdb-agent-kit.

## Evidence

- `runs/16-loyalty-points-ledger/20261124-184937/` (`doc-gaps.md`, `02-readiness.json`, `app/README.md` line 33)
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/doc-gaps.md` ("Connection-string and SRV vs legacy shapes")
- `runs/20-provider-directory-semantic-search/20261124-200008/` (`02-readiness.json` Q06 says Entra is unsupported for data connections)
- `runs/12-cross-border-payment-audit-trail/20261124-201744/doc-gaps.md` ("Node.js Entra (Azure AD) auth snippet for Mongo driver")
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` (which auth mode a README should lead with; Learn search returned the Bicep pivot)

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Driver minimums: settled 2026-11-25 (DECISIONS.md, SME topic 4, items 4.1 to 4.4). The `MONGODB-OIDC` floors are PyMongo 4.7, Node.js driver 6.7.0, Java driver 5.1 and .NET driver 2.25.0, from the drivers' own changelogs and releases; Learn publishes no floor today. Sources: https://raw.githubusercontent.com/mongodb/mongo-python-driver/master/doc/changelog.rst (4.7.0); https://github.com/mongodb/node-mongodb-native/releases/tag/v6.7.0; https://github.com/mongodb/mongo-java-driver/releases/tag/r5.1.0 and MongoCredential.java (`@since 5.1`); https://github.com/mongodb/mongo-csharp-driver/releases/tag/v2.25.0. Which versions the quickstarts were tested with stays open in filing L01, not here. **Qualified by the managed test (2026-11-25):** with a custom callback, PyMongo 4.6.3 cannot use a callback at all, 4.7.0 to 4.10.1 refuse an Azure host unless `ALLOWED_HOSTS` is set, and 4.11 and later connect without it (4.7.0, 4.10.1, 4.11 and 4.20.2 were run; the other releases are inferred from a source check), so the page states PyMongo 4.11, or 4.7 with `ALLOWED_HOSTS`; Node 6.6.0 rejects `OIDC_CALLBACK`, and 6.7.0 and 7.9.1 connect only with `ALLOWED_HOSTS`; this was on server version 8.0 (5.0, 6.0 and 7.0 not tested), and Java and .NET were not tested (ENGINE-TESTS.md, Managed service; DECISIONS.md topics 4 and 5).
- `ALLOWED_HOSTS`: settled 2026-11-25 (DECISIONS.md, SME topics 3 and 5). Both `*.azure.com` (RBAC page) and `*.mongocluster.cosmos.azure.com` (Mongoose tutorial, MCP README) match both host forms because a leading `*.` matches nested subdomains; the tighter pattern is the better default and the pages should agree. The Node driver checks the list after SRV resolution for custom callbacks and rejects Azure hosts without it; PyMongo 4.11 and later do not check it for machine callbacks, but 4.7.0 to 4.10.1 do (corrected by the managed test, which also saw both patterns work with Node 6.7.0 and 7.9.1; ENGINE-TESTS.md, Managed service; DECISIONS.md topic 5). Sources: https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose ("Connect Mongoose to Azure DocumentDB", troubleshooting); https://github.com/mongodb/specifications/blob/master/source/auth/auth.md (ALLOWED_HOSTS); https://github.com/mongodb/node-mongodb-native/blob/main/src/mongo_client.ts and src/utils.ts (hostMatchesWildcards); https://github.com/mongodb/mongo-python-driver/blob/master/pymongo/auth_oidc_shared.py.
- `global` host: settled 2026-11-25 (DECISIONS.md, SME topic 3). The `.global.` host is never required: on a single cluster the Self and Global read-write strings are interchangeable; use the Global read-write string for writes on a cluster that has or may get a cross-region replica so a promotion needs no code change; replica clusters expose only Self strings; take the host from the returned connection string, never construct it. Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ("Get cluster credentials"); https://learn.microsoft.com/en-us/azure/documentdb/how-to-cluster-replica#use-connection-strings; https://learn.microsoft.com/en-us/azure/documentdb/cross-region-replication; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose ("Verify the cluster from a terminal"); https://learn.microsoft.com/en-us/training/modules/create-configure-azure-documentdb-cluster/3-connect-to-cluster. Confirmed on one cluster with no replica by the managed test of 2026-11-25: the `.global.` host resolves, authenticates and takes writes, data written through either host is visible through the other, both hosts are SRV-only (no A record), and `list-connection-strings` returns `GlobalReadWrite` first and `Self` second; a replica's list was not tested (ENGINE-TESTS.md, Managed service; DECISIONS.md topic 3).

## Open questions

1. **Counts** (internal, not an SME question): they come from one run that had harness artifacts. Recount after the re-run before quoting them externally.
2. **PyMongo `create_index` pass-through** [needs SME confirmation]: does PyMongo's `create_index(..., cosmosSearchOptions=...)` produce a valid vector index on a cluster? The draft relies on PyMongo passing extra keyword arguments into the index spec and asks for verification before publishing.

## Source drafts

- 074-connect-and-authenticate-canonical-srv-connection-string-exp.md
- 046-entra-id-mongodb-oidc-and-cosmossearchoptions-how-to-pages-s.md
