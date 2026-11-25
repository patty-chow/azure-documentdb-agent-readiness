---
title: "Quickstarts: explain the SRV connection string and add a \"Choose an authentication method\" section with side-by-side SCRAM and Entra ID (MONGODB-OIDC) snippets for Python and Node"
repo: learn-docs
type: pr
status: ready_with_edits
priority: P1
sample_count: 20
findings: 21
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Quickstarts: explain the SRV connection string and add "Choose an authentication method" (SCRAM vs Microsoft Entra ID) with Python and Node snippets

**Pages:** `azure/documentdb/quickstart-python.md`, `azure/documentdb/quickstart-nodejs.md` (TS and JS pivots), `azure/documentdb/how-to-connect-role-based-access-control.md` (repo MicrosoftDocs/nosql-docs-pr)
Live: https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python , https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs , https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control

## What happens today

- Both quickstarts paste the placeholder string `mongodb+srv://<your-username>:<your-password>@<your-cluster-name>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` into code with no explanation of any option. "Get cluster credentials" is portal-only; `az documentdb mongocluster list-connection-strings` (which exists in the `documentdb` CLI extension) is not mentioned.
- Neither quickstart mentions Microsoft Entra ID, `MONGODB-OIDC`, or links to the RBAC how-to. The only auth path a reader sees is the admin user in a connection string.
- The RBAC how-to already explains the scheme/host/tls/retrywrites/maxIdleTimeMS options, contains the `authConfig.allowedModes: ["MicrosoftEntraID","NativeAuth"]` enable step, the `az documentdb mongocluster microsoft-entra-user assign` step, and Python / TypeScript / C# `MONGODB-OIDC` snippets. But it is not linked from the quickstart flow, has no Mongoose example, gives no minimum driver versions, env vars or troubleshooting, and its TypeScript sample computes `expiresInSeconds` incorrectly (it subtracts seconds from `expiresOnTimestamp`, which `@azure/identity` returns in milliseconds).

## Why it matters

In an experiment that had gpt-5-mini build 100 Azure DocumentDB sample apps (Node `mongodb`, Mongoose, PyMongo, Motor) with the DocumentDB Agent Kit and the Learn MCP server:

- The cold-quiz connection-string question was wrong or partly wrong in **100/100** samples: the model produced legacy `*.mongo.cosmos.azure.com:10255` / `ssl=true&replicaSet=globaldb` strings and had to be corrected by grounding.
- The auth-methods question ("how does a driver authenticate with Entra ID?") was wrong or partly wrong in **98/100**: the model asserted Entra ID is control-plane only and drivers must use username/password.
- **20 samples** filed an explicit doc gap on this point (21 findings). Every one shipped a static `DOCUMENTDB_URI` with the admin user, and the generated READMEs could not point readers to a production path because the builder could not find a copy-paste Entra ID snippet for its driver from the quickstart.

Fixing the quickstarts fixes the agents too: these pages are what the Learn MCP server returns for "connect to Azure DocumentDB with Python/Node".

## Proposed change

### 1. `quickstart-python.md` and `quickstart-nodejs.md` — expand "Get cluster credentials"

Add after the portal steps:

> You can also get the connection strings from the Azure CLI (requires the `documentdb` extension):
>
> ```azurecli
> az documentdb mongocluster list-connection-strings \
>   --resource-group <resource-group> --cluster-name <cluster-name>
> ```
>
> The string has this shape. Keep every option.
>
> | Part | Value | Why |
> | --- | --- | --- |
> | scheme | `mongodb+srv://` | DNS SRV lookup; no port in the string |
> | host | `<cluster>.global.mongocluster.cosmos.azure.com` or `<cluster>.mongocluster.cosmos.azure.com` | the `global` host follows the writable cluster after a replica promotion / region swap; in a single-cluster setup either works |
> | `tls=true` | required | the cluster only accepts TLS connections |
> | `authMechanism=SCRAM-SHA-256` | native user/password auth | use `MONGODB-OIDC` instead for Microsoft Entra ID (see below) |
> | `retrywrites=false` | required | retryable writes are not supported; leaving the driver default (`true`) causes write errors |
> | `maxIdleTimeMS=120000` | recommended | closes idle pooled connections before they go stale |
>
> > [!NOTE]
> > Connection strings from Azure Cosmos DB for MongoDB (RU), such as `mongodb://<account>.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb`, do not work with Azure DocumentDB clusters. Copy the string from the portal or the CLI command above. For the full option reference see [Get cluster credentials](how-to-connect-role-based-access-control#get-cluster-credentials).

### 2. Both quickstarts — new H3 "Choose an authentication method" under "Authenticate the client"

> Azure DocumentDB supports two data-plane authentication methods:
>
> - **Native (SCRAM-SHA-256)** — the username and password you set at cluster creation, embedded in the connection string. Use it for local development and demos. Never commit the string; read it from an environment variable such as `DOCUMENTDB_URI` and keep it in Azure Key Vault when it must live in the cloud. Prefer a least-privilege secondary user over the admin user for applications.
> - **Microsoft Entra ID (`MONGODB-OIDC`)** — the application authenticates with a managed identity or your developer sign-in and receives a short-lived token; there is no password to rotate. Use it for anything deployed to Azure. First enable it on the cluster by adding `MicrosoftEntraID` to `authConfig.allowedModes`, then register the identity on the cluster (`az documentdb mongocluster microsoft-entra-user assign`), as described in [Connect using role-based access control](how-to-connect-role-based-access-control#enable-microsoft-entra-id-authentication).
>
> The rest of this quickstart uses the native connection string. To use Microsoft Entra ID instead, replace the client construction with the snippet below.

Python pivot:

```python
# pip install "pymongo>=4.7" azure-identity
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential):
        self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        return OIDCCallbackResult(access_token=token)

client = MongoClient(
    "mongodb+srv://<your-cluster-name>.global.mongocluster.cosmos.azure.com/",
    tls=True,
    retryWrites=False,
    maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
)
```

Node.js pivot (driver), plus a Mongoose variant since many apps use it:

```javascript
// npm install mongodb@^6.7 @azure/identity
const { MongoClient } = require('mongodb');
const { DefaultAzureCredential } = require('@azure/identity');

const credential = new DefaultAzureCredential();
const oidcCallback = async () => {
  const t = await credential.getToken('https://ossrdbms-aad.database.windows.net/.default');
  // expiresOnTimestamp is in milliseconds
  return { accessToken: t.token, expiresInSeconds: Math.floor((t.expiresOnTimestamp - Date.now()) / 1000) };
};
const client = new MongoClient('mongodb+srv://<your-cluster-name>.global.mongocluster.cosmos.azure.com/', {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: 'MONGODB-OIDC',
  authMechanismProperties: { OIDC_CALLBACK: oidcCallback, ALLOWED_HOSTS: ['*.azure.com'] },
});
```

```javascript
// Mongoose 8.x passes driver options through to the MongoDB Node driver
await mongoose.connect('mongodb+srv://<your-cluster-name>.global.mongocluster.cosmos.azure.com/<database>', {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: 'MONGODB-OIDC',
  authMechanismProperties: { OIDC_CALLBACK: oidcCallback, ALLOWED_HOSTS: ['*.azure.com'] },
});
```

Closing line: "`DefaultAzureCredential` uses your `az login` session locally and the managed identity when deployed. For a user-assigned identity set `AZURE_CLIENT_ID`."

### 3. `how-to-connect-role-based-access-control.md` — "Connect using Microsoft Entra ID in code"

- Fix the existing TypeScript sample: `expiresInSeconds` should be `Math.floor(((tokenResponse?.expiresOnTimestamp ?? 0) - Date.now()) / 1000)` because `expiresOnTimestamp` is in milliseconds.
- Add the Mongoose variant above next to the TypeScript sample.
- Add a **Requirements** note: PyMongo 4.7+ (Motor 3.x when running on PyMongo 4.7+), MongoDB Node.js driver 6.7+ (Mongoose 8.x on a 6.7+ driver), `azure-identity` / `@azure/identity`. Maintainers: please confirm the exact minimums against the driver changelogs before merge.
- Add **Environment variables**: `DOCUMENTDB_URI` (host and options only, no credentials, when using OIDC), `AZURE_CLIENT_ID` (user-assigned managed identity), `AZURE_TENANT_ID` where needed.
- Add a **Troubleshooting** list: (1) OIDC authentication fails → check `MicrosoftEntraID` is in `authConfig.allowedModes`; (2) authentication succeeds at Entra but the cluster rejects the principal → the identity was not registered with `az documentdb mongocluster microsoft-entra-user assign` or has no role; (3) the token scope must be `https://ossrdbms-aad.database.windows.net/.default`; (4) write errors about retryable writes → `retrywrites=false` / `retryWrites: false` was dropped; (5) keep `ALLOWED_HOSTS: ['*.azure.com']` as in the documented Node sample.
- Link back from this heading to each language quickstart's new section so the two pages cross-reference.

## Evidence (run folders from the experiment; no connection strings)

- `runs/16-loyalty-points-ledger/20261124-184937/doc-gaps.md` — [high] "Node.js Mongoose + Microsoft Entra ID example"; `02-readiness.json` Q04/Q06/S03/S05 show the legacy 10255 string and the "no driver Entra integration" prior.
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/doc-gaps.md` — [high] "Connection-string and SRV vs legacy shapes": asks for the `list-connection-strings` paragraph.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` — Q04 and Q06 both `wrong`, confused with Cosmos DB for MongoDB RU.
- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json` — Q06 `wrong`: claims Entra ID is not supported for wire-protocol data connections.
- `runs/08-interest-rate-scenario-modeler/20261124-201113/doc-gaps.md` and `runs/01-product-catalog-with-vector-search/20261124-175429/doc-gaps.md` — PyMongo-side requests for the same side-by-side snippet.

F0135 (retry/backoff helper) was bucketed here but is a different topic and is not addressed by this PR.

Side note for the Agent Kit maintainers, not part of this PR: `skills/security/security-entra-rbac.md` hedges the mechanism ("or the current documented mechanism") and uses host suffix `mongocluster.documentdb.azure.com` (also in `skills/local-deployment/local-env-driven-config.md`); the documented host is `*.mongocluster.cosmos.azure.com`. Once the Learn snippets land, that skill should copy them and link to the quickstart section.

## Verification

### 1. Already covered? — partially_covered

- Quickstarts (fetched 2026-11-25): https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python and https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs. "Get cluster credentials" is portal-only ("select the **Connection strings** option in the resource menu"); "Authenticate the client" says only "connect to the client using a basic connection string". No mention of Entra ID, MONGODB-OIDC, the CLI command, or any option meaning; no link to the RBAC page.
- RBAC how-to: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control has "Get cluster credentials" with an option table ("The `tls` setting must also be enabled. The remaining recommended settings are best practice configuration settings."), "Enable Microsoft Entra ID authentication" (`authConfig.allowedModes` `["MicrosoftEntraID","NativeAuth"]`), `az documentdb mongocluster microsoft-entra-user assign`, and "Connect using Microsoft Entra ID in code" with Python, TypeScript and C# OIDC_CALLBACK samples. No Mongoose sample, no driver minimums, no env vars, no troubleshooting section, and it is not linked from the quickstarts. So the material exists but not where the agent looked and incomplete.
- Agent kit: `skills/azure-deployment/SKILL.md` lines 288-291 show the SCRAM string and explain `retrywrites=false`; `skills/security/security-entra-rbac.md` has only a hedged placeholder OIDC snippet. documentdb-mcp: OIDC only in its own tests (`test/context/documentdb.test.ts`). Neither covers the Learn ask.

### 2. Premise true? — confirmed (minor corrections applied)

- `az documentdb mongocluster list-connection-strings` exists: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster ("List mongo cluster connection strings. This includes the default connection string using SCRAM-SHA-256, as well as other connection strings supported by the cluster.").
- Host forms, `global` behaviour after region swap, `tls` required, `retrywrites=false`, token scope `https://ossrdbms-aad.database.windows.net/.default`, `ALLOWED_HOSTS: ['*.azure.com']`, `allowedModes`: all match the RBAC how-to page.
- Corrections applied to the body: softened the `maxIdleTimeMS` rationale (Learn calls it a recommended best-practice setting, not a gateway timeout); softened "fail on the first write"; Motor stated as "Motor 3.x running on PyMongo 4.7+" (not all Motor 3.x pull PyMongo 4.7); ALLOWED_HOSTS troubleshooting reworded (it is required only for some OIDC workflows; the doc sample sets it); the "assign a role" step now names `az documentdb mongocluster microsoft-entra-user assign`; added the fix for the existing TypeScript sample's `expiresInSeconds` unit bug (`expiresOnTimestamp` is milliseconds per @azure/identity `AccessToken`); kit side note now notes the documented host `*.mongocluster.cosmos.azure.com`. Driver minimums (PyMongo 4.7 introduced MONGODB-OIDC; Node driver 6.7 introduced `OIDC_CALLBACK`) are kept with a maintainer-confirm note.
- Nothing contradicts the fixed facts (resource type Microsoft.DocumentDB/mongoClusters, CLI group, canonical SRV string, Entra ID supported).

### 3. Maintainer skeptic — confirmed

Names three exact source files, concrete text and code to add, and a real defect in an existing sample. Squarely Azure DocumentDB specific and in the Learn docs repo (MicrosoftDocs/nosql-docs-pr). Would accept with small edits (driver-version confirmation). The agent-kit side note is explicitly out of this PR's scope.

## Finding ids

F0025, F0134, F0135, F0298, F0371, F0405, F0651, F0681, F0869, F0905, F1121, F1214, F1286, F1355, F1392, F1610, F2698, F2859, F3057, F3088, F3477
