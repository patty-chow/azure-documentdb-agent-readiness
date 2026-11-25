---
title: "Entra ID (MONGODB-OIDC) driver samples exist on Learn but agents can't find them: surface them in quickstarts and in a discoverable section heading"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P2
sample_count: 4
findings: 5
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Entra ID (MONGODB-OIDC) driver samples exist on Learn but agents and builders cannot find them

**Pages:** `https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control`, `https://learn.microsoft.com/azure/documentdb/quickstart-python`, `https://learn.microsoft.com/azure/documentdb/quickstart-nodejs`, `https://learn.microsoft.com/azure/documentdb/vector-search`

## What happens today

A builder writing Python or Node.js who searches Learn for "connect to Azure DocumentDB with Microsoft Entra ID from PyMongo / the Node.js driver / Mongoose" lands on `how-to-connect-role-based-access-control`, a roughly 6,400-word page about Azure RBAC, enabling Microsoft Entra ID authentication, and managing administrative and secondary identities across five pivots (portal, CLI, REST, Bicep, Terraform). The working driver code is there, but only in the very last section, titled **"Connect using Microsoft Entra ID in code"**, which comes after "Manage DocumentDB secondary (nonadministrative) Microsoft Entra ID identities". That heading and its one-sentence intro do not mention Python, PyMongo, Node.js, Mongoose, `azure-identity`, `@azure/identity`, `DefaultAzureCredential`, or `OIDC_CALLBACK`, so a search for any of those terms matches the "Enable Microsoft Entra ID authentication" section instead and never surfaces the code. The Python snippet in that section also omits its imports (`from pymongo import MongoClient`, `from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult`, `from azure.identity import DefaultAzureCredential`), so it is not copy-paste runnable.

Meanwhile the language quickstarts (`quickstart-python`, `quickstart-nodejs`) show only a SCRAM connection string and never mention Microsoft Entra ID, and the one page that contains a complete Mongoose + `MONGODB-OIDC` example (`tutorial-nodejs-mongoose`, section "Connect Mongoose to Azure DocumentDB") is reachable from the Mongoose quickstart only through a sentence in an Important box.

On `vector-search`, the HNSW and IVF tabs show `cosmosSearchOptions` only as mongosh/JSON; only the DiskANN tab has a Python `db.command(...)` form, and nothing shows the PyMongo `create_index()` equivalent.

## Why it matters

In an experiment that ran 100 Azure DocumentDB sample prompts through a readiness-then-build pipeline (gpt-5-mini, DocumentDB Agent Kit skills, Learn MCP server):

- 4 of 100 samples recorded an explicit information gap "no PyMongo / Node.js / Mongoose Entra ID (MONGODB-OIDC) code sample found on Learn" during the readiness stage (`11-visual-similarity-search-image-embeddings`, `12-cross-border-payment-audit-trail`, `16-loyalty-points-ledger`, `16-subscription-billing-engine`). More samples logged the same gap at audit time.
- In those runs the agent did query Learn. The Learn MCP search for Entra data-plane driver auth returned the RBAC page's **"Enable Microsoft Entra ID authentication"** chunk (CLI or Bicep pivot), not the code section. The Mongoose + Entra query returned the password-based Mongoose quickstart.
- Consequence: the builders fell back to SCRAM credentials in `DOCUMENTDB_URI` and wrote README lines such as "A production deployment should consider Microsoft Entra ID (OIDC) per Azure guidance; that is not demonstrated here" (`16-loyalty-points-ledger`, `app/README.md` line 33). The published samples teach the less secure path even though the correct code exists on Learn.
- Cold-quiz answers before grounding commonly misstated data-plane auth as SCRAM-only (as on the RU-based Cosmos DB for MongoDB). Grounding fixed the *fact* but not the *how*, because the how is not where the search lands.
- One sample (`16-subscription-billing-engine`) also asked which mode a sample README should lead with. The Mongoose quickstart already answers this ("Password authentication is for free tier and quick evaluation here. For production, use a paid cluster with Microsoft Entra ID and a least-privilege managed identity"), but the Python and Node.js quickstarts do not.

## Proposed change

### 1. `how-to-connect-role-based-access-control`: make the code section findable and runnable

- Retitle the last section so the heading carries the search terms, for example **"Connect from application code with PyMongo, the MongoDB Node.js driver, Mongoose, and .NET (MONGODB-OIDC)"**.
- Add a short intro paragraph that names the packages per language (`pymongo` + `azure-identity`; `mongodb` + `@azure/identity`; `mongoose` + `@azure/identity`; `MongoDB.Driver` + `Azure.Identity`), the token scope `https://ossrdbms-aad.database.windows.net/.default`, that free tier clusters don't support Microsoft Entra ID, and the minimum tested driver versions (as `tutorial-nodejs-mongoose` already does under "Tested driver version").
- In the Node.js snippet, tighten `ALLOWED_HOSTS` from the broad `['*.azure.com']` to `['*.mongocluster.cosmos.azure.com']` and add the one-line reason the Mongoose tutorial gives (the driver's default OIDC allow list doesn't include the service domain; it checks hosts returned by SRV resolution; don't use `*`).
- Add the missing imports to the Python snippet so it runs as pasted.
- Add a **JavaScript** tab next to TypeScript (the Node.js quickstart has a JS pivot; many samples are plain `.mjs`), and a **Mongoose** tab that reuses the `database.mjs` connect block from `tutorial-nodejs-mongoose#connect-mongoose-to-azure-documentdb`, or at minimum a direct anchor link to it.
- Move the section above "Manage DocumentDB secondary (nonadministrative) Microsoft Entra ID identities", or split it into its own how-to page (for example `how-to-connect-entra-id-drivers`) with language pivots, so search returns it as a top-level hit instead of a trailing chunk of a management page.

### 2. `quickstart-python` and `quickstart-nodejs`: say which auth to use and link the Entra path

- Add the Important note already present in `quickstart-nodejs-mongoose`: password authentication is for the free tier and quick evaluation; for production use a paid cluster with Microsoft Entra ID and a least-privilege managed identity.
- Add a two-line "Connect with Microsoft Entra ID" subsection under "Authenticate the client" that links to the retitled section above. No new code is needed; the point is that a builder on the quickstart sees that the Entra path exists and where the snippet lives.

### 3. `vector-search`: finish the Python coverage

- Under the **HNSW** and **IVF** tabs add the Python `db.command({...})` form the DiskANN tab already has (same `createIndexes` document, `kind: "vector-hnsw"` / `"vector-ivf"`).
- Add one sentence noting that PyMongo also accepts the index spec through `collection.create_index([("contentVector", "cosmosSearch")], name="vectorSearchIndex", cosmosSearchOptions={"kind": "vector-hnsw", "m": 16, "efConstruction": 64, "similarity": "COS", "dimensions": 1536})` (PyMongo passes extra keyword arguments through into the index specification; please verify on a cluster before publishing), and repeat that vectors must be `number[]` to be indexed.

All three changes are additive; no existing content is wrong apart from the overly broad `ALLOWED_HOSTS` value and the missing Python imports.

## Evidence (run folders from the experiment)

- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` (information_gaps[0], confusions[Q06]); `events.jsonl` shows the Learn search for Entra driver auth returned the "Enable Microsoft Entra ID authentication" chunk; `app/README.md` line 33 documents the SCRAM fallback
- `runs/16-loyalty-points-ledger/20261124-184937/doc-gaps.md`, section "Node.js Mongoose + Microsoft Entra ID example"
- `runs/12-cross-border-payment-audit-trail/20261124-201744/doc-gaps.md`, section "Node.js Entra (Azure AD) auth snippet for Mongo driver"; `05-audit.json` requirement_results on the SCRAM default
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/02-readiness.json`, information_gaps on the PyMongo OIDC flow and the PyMongo `cosmosSearchOptions` call
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json`, information_gap "Which auth mode to demonstrate in README"; `events.jsonl` shows the Learn search returned the Bicep pivot of the RBAC page

## Related, not part of this ask

The Agent Kit's `skills/security/security-entra-rbac.md` "Correct" snippet is a placeholder (`// credentialProvider: Azure Managed Identity`, "or the current documented mechanism") and uses a `mongocluster.documentdb.azure.com` host suffix (the real suffix is `mongocluster.cosmos.azure.com`); `skills/local-deployment/local-env-driven-config.md` has the same wrong suffix. Agents read these before Learn. That should be fixed in `Azure/documentdb-agent-kit` by copying the real snippets, and is tracked separately.

## Verification

### 1. Already covered? partially_covered

The code the builders asked for exists but is not where agents look, and two parts are missing.
- `https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control` (word_count 6387): headings in order are Prerequisites, Manage Azure role-based access control, Enable Microsoft Entra ID authentication, Manage DocumentDB administrative Microsoft Entra ID identities and native users, Get cluster credentials, Connect using Microsoft Entra ID in Visual Studio Code, Connect using Microsoft Entra ID in MongoDB Compass or MongoDB Shell, Manage DocumentDB secondary (nonadministrative) Microsoft Entra ID identities, **Connect using Microsoft Entra ID in code** (last). That section has Python (`AzureIdentityTokenCallback(OIDCCallback)`, scope `https://ossrdbms-aad.database.windows.net/.default`, `authMechanism="MONGODB-OIDC"`, no imports), TypeScript (`ALLOWED_HOSTS: ['*.azure.com']`) and C# snippets. No JavaScript or Mongoose tab. Intro: "Validate that you correctly granted access using application code and the appropriate client library for your preferred language."
- `https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose`: full `database.mjs` with `MONGODB-OIDC`, `ALLOWED_HOSTS: ['*.mongocluster.cosmos.azure.com']`, explanation of why, and "Tested driver version" (Node.js driver 7.8.0 / Mongoose 9.12.1). States free tier doesn't support Microsoft Entra ID.
- `https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-mongoose`: Important note "Password authentication is for free tier and quick evaluation here. For production, use a paid cluster with Microsoft Entra ID ..." linking the tutorial.
- `https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python` and `quickstart-nodejs`: SCRAM connection string only; no mention of Entra ID, OIDC or managed identity. Not covered.
- `https://learn.microsoft.com/en-us/azure/documentdb/vector-search`: DiskANN tab has Python `db.command({"createIndexes": ...})`; HNSW and IVF tabs use mongosh `db.runCommand` only; no PyMongo `create_index(..., cosmosSearchOptions=...)`. Not covered.

### 2. Premise true? confirmed (with corrections applied)

Core claims verified against the pages above: the code section exists and is last; headings carry no language/library terms; quickstarts are SCRAM-only; Python vector coverage exists only for DiskANN; token scope and `MONGODB-OIDC` match Learn; hostname suffix `mongocluster.cosmos.azure.com` matches the service. Corrections applied to the body: (a) the original draft called the RBAC page's `'*.azure.com'` ALLOWED_HOSTS value "narrower"; it is broader than `*.mongocluster.cosmos.azure.com`, so the ask is now to tighten it; (b) added that the Python snippet lacks imports; (c) added the free-tier limitation (no Entra ID on free tier, per tutorial-nodejs-mongoose); (d) the "98 of 100" cold-quiz count and "at least 8 more samples" audit count could not be re-verified in this stage and were softened to qualitative statements; (e) the PyMongo `create_index(..., cosmosSearchOptions=...)` form relies on PyMongo passing extra kwargs into the index spec, so it is flagged for verification before publishing. Agent Kit related-note claims verified: `skills/security/security-entra-rbac.md` lines 26-27 contain "or the current documented mechanism" and "credentialProvider: Azure Managed Identity"; line 15 and `skills/local-deployment/local-env-driven-config.md` line 68 use `mongocluster.documentdb.azure.com`.

### 3. Maintainer skeptic: confirmed

Names four specific Learn pages, the exact section heading to rename, the exact tabs to add, a specific wrong-ish value (`ALLOWED_HOSTS`) and missing imports, and reuses content already on Learn. It is DocumentDB-specific (MONGODB-OIDC token scope, service host allow list, cosmosSearchOptions) and belongs in the Learn docs (MicrosoftDocs/nosql-docs-pr). Agent Kit follow-up is correctly split out.

## Finding ids

- F1901
- F1903
- F2028
- F2695
- F2789
