---
title: "connection skill: document Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode alongside SCRAM-SHA-256"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 67
findings: 71
bucket: confusion-Q06
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# connection skill: document Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode alongside SCRAM-SHA-256

## What happens today

`skills/connection/SKILL.md` is the skill an agent loads whenever it writes code that calls `connect()`. Its entire "Authentication" section is:

```
### Authentication
- Default mechanism: `SCRAM-SHA-256`
- Credentials are managed through the Azure portal (cluster's connection settings)
```

Nothing in `documentdb-connection` or `documentdb-driver` mentions Microsoft Entra ID or `MONGODB-OIDC`. `documentdb-azure-deployment` ("Entra RBAC / CMK / diagnostic settings" bullet, line 311) only says "Entra RBAC / CMK / diagnostic settings. See `documentdb-security`". The one page that does cover it, `skills/security/security-entra-rbac.md` (MEDIUM priority, loaded only if the agent opens the security skill *and* follows the sub-link), hedges with `// (verify current driver support/spec in the official docs)` and `// or the current documented mechanism`, gives no command to enable Entra on the cluster, no connection string, no token callback, and its "Incorrect" example uses a non-existent hostname (`prod-ddb.mongocluster.documentdb.azure.com`; the real suffix is `mongocluster.cosmos.azure.com`).

Meanwhile the kit's own README already tells MCP users that Entra/OIDC is the *recommended* auth mode (`authMode: "entra"`, `tokenScope: https://ossrdbms-aad.database.windows.net/.default`). The skills do not say the same thing to application code.

## Why it matters

In an agent-readiness experiment over 100 Azure DocumentDB sample prompts (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), the cold-quiz question "Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID?" was answered wrong or partly wrong in **67 of 100 samples** (71 findings; 41 fully wrong, 30 partly wrong). In almost every case the model carried over the Azure Cosmos DB for MongoDB RU mental model: "the MongoDB wire endpoint only takes username/password (SCRAM); Entra ID is not supported for the data plane / is control-plane only; there is no driver-side token flow." Representative cold answers:

- "Microsoft Entra ID (Azure AD) authentication is NOT supported for the Mongo DB wire endpoint ... There is no driver-side AAD token flow for Mongo endpoints" (04-earnings-call-rag-assistant)
- "AAD is used for control-plane / RBAC in the Azure portal ... if AAD is required you must acquire an access token ... this is a non-standard flow" (18-chargeback-dispute-multi-agent)

Downstream effect: of the 100 builds, only 8 ever emitted `MONGODB-OIDC`; the rest shipped SCRAM-only `DOCUMENTDB_URI` connection code, and the audit stage flagged "sample does not document or demonstrate Microsoft Entra ID authentication (it uses connection-string auth by default) though the service supports Entra ID" in dozens of audits (78 of 100 `05-audit.json` files mention Entra/OIDC, mostly as a gap). The Learn page `how-to-connect-role-based-access-control` already documents everything in depth; the problem is that the kit's connection path does not point there, so an agent that trusts the skill never looks.

## Proposed change

### 1. `skills/connection/SKILL.md` — replace the "Authentication" section

```markdown
### Authentication modes

Azure DocumentDB clusters accept two data-plane authentication modes. Both are
first-class; the cluster's `authConfig.allowedModes` decides which are enabled
(`NativeAuth` is on by default).

| Mode | `authMechanism` | Credential | Use when |
|------|-----------------|------------|----------|
| Native (SCRAM) | `SCRAM-SHA-256` | cluster username + password | local dev, quick samples |
| Microsoft Entra ID | `MONGODB-OIDC` | Entra token from `DefaultAzureCredential` (managed identity, workload identity, `az login`) | anything deployed to Azure; no secrets to rotate |

**Check / enable Entra ID on the cluster** (keep `NativeAuth` until the Entra
principal is verified):

```bash
az documentdb mongocluster show --name <cluster> --resource-group <rg> --query properties.authConfig
az documentdb mongocluster update --name <cluster> --resource-group <rg> \
  --auth-allowed-modes NativeAuth MicrosoftEntraID
# registers the principal as an ADMINISTRATIVE user (root on admin); the only
# role this command grants. For least-privilege app identities, register an
# admin, then create a nonadministrative Entra user with the createUser command
# (readWriteAnyDatabase + clusterAdmin, or readAnyDatabase) as the Learn page shows.
az documentdb mongocluster microsoft-entra-user assign --cluster-name <cluster> \
  --resource-group <rg> --object-id <principal-object-id> --type User \
  --role db=admin role=root
```

`--type` is `User` for a human identity; use the service-principal type for a
service principal or managed identity (see the Learn page's principal-type notes).

**Connect with Entra ID (Python):**

```python
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential): self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        return OIDCCallbackResult(access_token=token)

client = MongoClient(
    f"mongodb+srv://{cluster}.global.mongocluster.cosmos.azure.com/",
    tls=True, retryWrites=False, connectTimeoutMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
)
```

**Connect with Entra ID (Node.js):**

```javascript
const { DefaultAzureCredential } = require('@azure/identity');
const { MongoClient } = require('mongodb');
const credential = new DefaultAzureCredential();
const client = new MongoClient(`mongodb+srv://${cluster}.global.mongocluster.cosmos.azure.com/`, {
  tls: true, retryWrites: false, connectTimeoutMS: 120000,
  authMechanism: 'MONGODB-OIDC',
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const t = await credential.getToken(['https://ossrdbms-aad.database.windows.net/.default']);
      // expiresOnTimestamp is in milliseconds
      return { accessToken: t.token, expiresInSeconds: Math.floor((t.expiresOnTimestamp - Date.now()) / 1000) };
    },
    ALLOWED_HOSTS: ['*.azure.com'],
  },
});
```

Compass / mongosh (the host may be `<cluster>.global.mongocluster.cosmos.azure.com` or `<cluster>.mongocluster.cosmos.azure.com`): `mongodb+srv://<client-id>@<cluster>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000`

Do **not** tell users Entra ID is "control-plane only" or "not supported for the
MongoDB wire protocol" — that was true of Azure Cosmos DB for MongoDB (RU), not
Azure DocumentDB. Full walkthrough (portal / CLI / Bicep / Terraform, .NET
sample, role assignment):
https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control
```

Also append `documentdb-security` (Entra RBAC sub-page) to the skill's related-skills list, which currently has none.

### 2. `skills/security/security-entra-rbac.md` — make it concrete

- Replace the hedged "Correct" block with the Python/Node callback above (no "verify current driver support" comment; MONGODB-OIDC is the documented mechanism).
- Keep the existing least-privilege `createUser` guidance, and note that `microsoft-entra-user assign` grants only administrative `root`.
- Add an "Enable on the cluster" step with `az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID` and `az documentdb mongocluster microsoft-entra-user assign ...`.
- Fix the hostname in the "Incorrect" example to `<cluster>.mongocluster.cosmos.azure.com`.
- Consider raising priority to HIGH: the finding shows the model's default is the *wrong* answer, so this page is correcting a prior, not adding polish.

### 3. One-line cross-links

- `skills/driver/SKILL.md`: after the singleton-client guidance add "Authentication: SCRAM-SHA-256 or Microsoft Entra ID (`MONGODB-OIDC`) — see `documentdb-connection` › Authentication modes."
- `skills/azure-deployment/SKILL.md` ("Entra RBAC / CMK / diagnostic settings" bullet near line 311): change it to "**Entra ID auth** — enable with `az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID`; connection code in `documentdb-connection` › Authentication modes. CMK / diagnostics: see `documentdb-security`, `documentdb-monitoring`."

All commands and snippets above are adapted from the Learn RBAC how-to (ms.date 2026-03-11, updated 2026-11-23). One deliberate difference: the Learn TypeScript sample computes `expiresInSeconds` as `expiresOnTimestamp - Date.now()/1000`, but `@azure/identity` returns `expiresOnTimestamp` in milliseconds, so the snippet here converts it to seconds first.

## Evidence (run folders from the experiment; see `02-readiness.json` → `confusions[Q06]`, `05-audit.json`)

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` — cold answer: "AAD is not widely supported for the MongoDB API data-plane drivers"
- `runs/04-earnings-call-rag-assistant/20261124-190247/02-readiness.json` — cold answer: "Entra ID ... is NOT supported for the Mongo DB wire endpoint"; `05-audit.json` in the same folder: no Entra/OIDC path in `src/db.py`
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/02-readiness.json` — cold answer: "AAD is used for control-plane / RBAC in the Azure portal"
- `runs/01-product-catalog-with-vector-search/20261124-175429/05-audit.json` — audit gap: sample "does not document or demonstrate Microsoft Entra ID authentication ... though the service supports Entra ID"
- Aggregate: 67/100 samples wrong or partly wrong on Q06; 8/100 builds emitted `MONGODB-OIDC`.

## Verification

### 1. Already covered? partially_covered
- `skills/connection/SKILL.md` lines 70-74, the Authentication section, reads in full: "Default mechanism: `SCRAM-SHA-256`" and "Credentials are managed through the Azure portal". It does not mention Entra or OIDC.
- `skills/security/security-entra-rbac.md` (Priority MEDIUM) says Entra ID with RBAC is supported. Its Correct block hedges: "(verify current driver support/spec in the official docs)" and `authMechanism: "MONGODB-OIDC", // or the current documented mechanism`. It has no enable command and no token callback. Its Incorrect example uses the host `prod-ddb.mongocluster.documentdb.azure.com`.
- `skills/driver/SKILL.md` never mentions auth. `skills/azure-deployment/SKILL.md` line 311 only says "Entra RBAC / CMK / diagnostic settings. See `documentdb-security`".
- The kit README already has a section headed "Microsoft Entra / OIDC (recommended)", with `authMode: "entra"` and the scope `https://ossrdbms-aad.database.windows.net/.default`. That section covers MCP setup only.
- `skills/high-availability/ha-cross-region-replica.md` lines 182-183 mention that native and Entra auth modes can be switched on and off separately for each cluster.
- Learn already covers all of it in full: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control. So the gap is in the kit's connection and driver path, not in the service docs.

### 2. Is the premise true? confirmed
I checked the draft against the Learn RBAC how-to (ms.date 2026-03-11, updated_at 2026-11-23):
- The CLI enable command matches the page: `az documentdb mongocluster update --name <cluster-name> --resource-group <resource-group> --auth-allowed-modes NativeAuth MicrosoftEntraID`. The page also says "Keep `NativeAuth` in the list until you verify..." and checks the `authConfig.allowedModes` array.
- `az documentdb mongocluster microsoft-entra-user assign ... --type User --role db=admin role=root` is on the page. The page says these registrations grant **administrative** access. Nonadministrative access is created with `createUser` (`readWriteAnyDatabase` + `clusterAdmin`, or `readAnyDatabase`).
- The scope `https://ossrdbms-aad.database.windows.net/.default`, `authMechanism` `MONGODB-OIDC`, `retrywrites=false`, `ALLOWED_HOSTS: ['*.azure.com']` and the Python and TypeScript OIDC callbacks all match. The host can be `<cluster-name>.global.mongocluster.cosmos.azure.com` or `<cluster-name>.mongocluster.cosmos.azure.com`.
- The mongosh string format `mongodb+srv://<client-id>@<cluster-name>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000` matches.
- The supported principals are users, service principals, and user- or system-assigned managed identities. So the model's belief that Entra is "control-plane only" is wrong, and the draft's correction holds.

I made these edits to the draft body:
1. The draft's `assign` example used `--type ServicePrincipal` for an app principal and gave it `root`. I changed the example to the documented `--type User`. I added a note that `assign` grants only administrative root and that least-privilege app identities go through `createUser`. This also keeps the kit's existing least-privilege advice.
2. I added the missing `MongoClient` import to the Node snippet.
3. I rewrote `expiresInSeconds` as `Math.floor((expiresOnTimestamp - Date.now())/1000)`, because `@azure/identity` returns `expiresOnTimestamp` in milliseconds. The Learn TypeScript sample mixes ms and seconds here. That may be worth a separate Learn issue.
4. I noted both host forms.
5. The draft said "step 9" of the azure-deployment skill. I replaced that with the actual bullet near line 311.

### 3. Maintainer skeptic: confirmed
The PR names exact files (`skills/connection/SKILL.md`, `skills/security/security-entra-rbac.md`, `skills/driver/SKILL.md`, `skills/azure-deployment/SKILL.md`). It proposes concrete replacement text, and every snippet traces back to the Learn how-to. It is specific to Azure DocumentDB: it fixes a real factual gap and a hedge in the kit's own skill, and it removes a wrong hostname. The kit README already calls Entra/OIDC the recommended mode, so the change is consistent with the kit itself. I would accept it after the small edits above.

## Finding ids

- F0005
- F0041
- F0073
- F0109
- F0149
- F0180
- F0259
- F0288
- F0316
- F0350
- F0422
- F0457
- F0526
- F0558
- F0598
- F0629
- F0696
- F0727
- F0794
- F0825
- F0848
- F0918
- F0944
- F0970
- F1001
- F1041
- F1075
- F1103
- F1132
- F1161
- F1199
- F1225
- F1260
- F1339
- F1370
- F1402
- F1435
- F1488
- F1523
- F1625
- F1718
- F1754
- F1827
- F1891
- F2018
- F2053
- F2084
- F2122
- F2244
- F2289
- F2389
- F2487
- F2518
- F2552
- F2591
- F2621
- F2649
- F2909
- F2976
- F3042
- F3073
- F3111
- F3145
- F3177
- F3227
- F3258
- F3298
- F3361
- F3394
- F3426
- F3459
