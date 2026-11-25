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
open_questions: 6
---

# Quickstarts: explain the SRV connection string and add a "Choose an authentication method" section that surfaces the Entra ID samples

**Pages:** [quickstart-python](https://learn.microsoft.com/azure/documentdb/quickstart-python), [quickstart-nodejs](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs) (JS and TS pivots), [how-to-connect-role-based-access-control](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control) (source repo MicrosoftDocs/nosql-docs-pr).

## What happens today

- **The quickstarts paste the `mongodb+srv://` string into code with no explanation.** "Get cluster credentials" is portal-only: it does not mention `az documentdb mongocluster list-connection-strings` (`documentdb` extension) or warn that Azure Cosmos DB for MongoDB (RU) strings (`:10255`, `replicaSet=globaldb`) do not work here.
- **The quickstarts show only SCRAM-SHA-256.** Neither mentions Microsoft Entra ID or `MONGODB-OIDC`, or links the RBAC how-to. The Mongoose quickstart's production note does exist; these two quickstarts lack it.
- **The Entra code exists but is hard to find.** It is the last section of the ~6,400-word RBAC how-to, under a heading that names no driver or package, so searches land on "Enable Microsoft Entra ID authentication" instead.
- **That section is incomplete:**
  - The Python snippet has no imports.
  - There is no JavaScript or Mongoose tab (the full Mongoose example is only in `tutorial-nodejs-mongoose`).
  - There are no driver minimums, environment variables or troubleshooting.
  - The TypeScript sample subtracts seconds from `expiresOnTimestamp`, which is in milliseconds.

## Why it matters

In one experiment run, gpt-5-mini built 100 sample apps (Node `mongodb`, Mongoose, PyMongo, Motor) with the DocumentDB Agent Kit and the Learn MCP server. All counts come from that run [needs SME confirmation] (see question 5).

- **23 distinct samples (24 in-scope findings) filed this gap.** This is reconciled across both drafts: 20 samples from one draft and 4 from the other, with one sample in both. Two more bucketed findings are out of scope (a retry/backoff request, and the PyMongo `cosmosSearchOptions` ask handled in item 4).
- **Cold answers before grounding** (latest readiness record for each of 101 samples; these reflect model priors, not page defects):
  - The connection-string question was wrong, partly wrong or outdated in 91 of 101 readiness records, mostly the legacy RU string.
  - The auth question was wrong or partly wrong in 88, mostly "Entra ID is control-plane only".
  - 10 records per question could not be verified.
- **Grounding fixed the fact, not the how-to.** Learn search returned the enable step, not the code.
- **The builds shipped an admin SCRAM `DOCUMENTDB_URI`.** Their READMEs say Entra ID "is not demonstrated here". These pages are what the Learn MCP server returns for "connect with Python/Node".

## Proposed change

**1. Quickstarts, "Get cluster credentials":**
- Add the CLI command.
- Add a table for each part of the string:
  - `mongodb+srv://`: SRV lookup, so no port.
  - Host: `<cluster>.mongocluster.cosmos.azure.com`.
  - `tls=true`: required.
  - `authMechanism=SCRAM-SHA-256`: native auth (`MONGODB-OIDC` for Entra ID).
  - `retrywrites=false`: wording per question 1.
  - `maxIdleTimeMS=120000`: recommended.
- Add a Note: "Connection strings from Azure Cosmos DB for MongoDB (RU) do not work with Azure DocumentDB clusters." Tell readers to copy the string from the portal or the CLI, and link the RBAC how-to's "Get cluster credentials" option table.

**2. Quickstarts, new H3 "Choose an authentication method":**
- **Native (SCRAM-SHA-256):** for development and demos. Read it from an environment variable, keep it in Key Vault, and prefer a least-privilege secondary user over the admin user.
- **Microsoft Entra ID (`MONGODB-OIDC`):** for anything deployed to Azure.
  - Enable it with `authConfig.allowedModes`, then register the identity with `az documentdb mongocluster microsoft-entra-user assign`.
  - The free tier does not support it.
  - Link to the RBAC code section.
  - Optionally add a short `DefaultAzureCredential` snippet per pivot (scope `https://ossrdbms-aad.database.windows.net/.default`, `tls: true`, `retryWrites: false`), with one closing line: `DefaultAzureCredential` uses the `az login` session locally and the managed identity when deployed; set `AZURE_CLIENT_ID` for a user-assigned identity.
- Reuse the production Important note from `quickstart-nodejs-mongoose`: password authentication is for the free tier and quick evaluation; for production, use a paid cluster with Microsoft Entra ID and a least-privilege managed identity.

**3. RBAC how-to, code section:**
- Retitle it, for example "Connect from application code with PyMongo, the Node.js driver, Mongoose, and .NET (MONGODB-OIDC)", and name the packages in its intro.
- Move it above the secondary-identities section, or give it its own page.
- Fix the samples:
  - Add the Python imports.
  - Fix TypeScript to `Math.floor((expiresOnTimestamp - Date.now()) / 1000)`.
  - Add JavaScript and Mongoose tabs, or a link to the tutorial.
- Add Requirements (driver minimums [needs SME confirmation], see question 2), environment variables (`DOCUMENTDB_URI` without credentials, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`) and Troubleshooting:
  - `allowedModes` is missing `MicrosoftEntraID`.
  - The identity is unregistered.
  - The scope is wrong.
  - `retryWrites` was dropped [needs SME confirmation] (see question 1).
  - `ALLOWED_HOSTS` is wrong.
- Cross-link back to the quickstarts.

**4. `vector-search`, Python coverage** (from 046; fold into the Learn vector-search filing if that lands first):
- Under the HNSW and IVF tabs, add the Python `db.command({...})` form the DiskANN tab already has (same `createIndexes` document with `kind: "vector-hnsw"` or `"vector-ivf"`).
- Add one sentence that PyMongo can also pass the spec through `collection.create_index([("<field>", "cosmosSearch")], name=..., cosmosSearchOptions={...})` [needs SME confirmation] (see question 6), and repeat that vectors must be `number[]` to be indexed.

Out of scope here:
- The Agent Kit's OIDC placeholder and host suffix are tracked in Azure/documentdb-agent-kit.

## Evidence

- `runs/16-loyalty-points-ledger/20261124-184937/` (`doc-gaps.md`, `02-readiness.json`, `app/README.md` line 33)
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/doc-gaps.md` ("Connection-string and SRV vs legacy shapes")
- `runs/20-provider-directory-semantic-search/20261124-200008/` (`02-readiness.json` Q06 says Entra is unsupported for data connections)
- `runs/12-cross-border-payment-audit-trail/20261124-201744/doc-gaps.md` ("Node.js Entra (Azure AD) auth snippet for Mongo driver")
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` (which auth mode a README should lead with; Learn search returned the Bicep pivot)

## Open questions

1. **retryWrites rationale** [needs SME confirmation]: `retrywrites=false` is in the canonical string, but the drafts disagree on why:
   - One draft calls it required, says retryable writes are unsupported and says omitting it causes write errors.
   - A related draft says Learn makes no such claim and calls it recommended.

   Please give the engineering answer.
2. **Driver minimums** [needs SME confirmation]:
   - One draft proposes PyMongo 4.7+ (Motor 3.x running on PyMongo 4.7+) and Node.js driver 6.7+ (Mongoose 8.x).
   - `tutorial-nodejs-mongoose` lists tested versions 7.8.0 and 9.12.1.

   Which floors should Learn publish?
3. **`ALLOWED_HOSTS`** [needs SME confirmation]: the RBAC page uses `['*.azure.com']` and the tutorial uses `['*.mongocluster.cosmos.azure.com']`. One draft keeps the first, the other tightens it. Which is correct?
4. **`global` host** [needs SME confirmation]: when should a quickstart reader use the `global` host form rather than the plain cluster host?
5. **Counts** [needs SME confirmation]: they come from one run that had harness artifacts. Confirm them before quoting externally.
6. **PyMongo `create_index` pass-through** [needs SME confirmation]: does PyMongo's `create_index(..., cosmosSearchOptions=...)` produce a valid vector index on a cluster? The draft relies on PyMongo passing extra keyword arguments into the index spec and asks for verification before publishing.

## Source drafts

- 074-connect-and-authenticate-canonical-srv-connection-string-exp.md
- 046-entra-id-mongodb-oidc-and-cosmossearchoptions-how-to-pages-s.md
