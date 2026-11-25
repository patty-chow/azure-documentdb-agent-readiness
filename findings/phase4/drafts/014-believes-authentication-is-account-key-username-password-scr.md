---
title: "documentdb-connection: add a first-class Microsoft Entra ID (MONGODB-OIDC) connection example next to SCRAM; de-hedge and fix host in security-entra-rbac"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 35
findings: 36
bucket: confusion-Q04
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# documentdb-connection: add a first-class Microsoft Entra ID (MONGODB-OIDC) connection example next to SCRAM; de-hedge and fix host in security-entra-rbac

## What happens today

The kit's connection skill tells an agent that Azure DocumentDB authenticates with a username/password in the URI, and nothing else:

- `skills/connection/SKILL.md` lines 70-74 ("Authentication"): *Default mechanism: `SCRAM-SHA-256`; credentials are managed through the Azure portal.* No mention of Microsoft Entra ID. Line 60's canonical URI also says `retryWrites=true`; the documented value for the service is `retrywrites=false` (and `skills/azure-deployment/SKILL.md:288-291` in this same kit already says so, so the kit contradicts itself).
- `skills/security/security-entra-rbac.md` is the only skill rule that shows `MONGODB-OIDC`, and it hedges: `authMechanism: "MONGODB-OIDC", // or the current documented mechanism` and `// (verify current driver support/spec in the official docs)`, with `// credentialProvider: Azure Managed Identity` as a comment instead of code. Line 15's example host is `prod-ddb.mongocluster.documentdb.azure.com`, which is not a valid Azure DocumentDB host (the suffix is `.mongocluster.cosmos.azure.com`).
- `skills/local-deployment/local-env-driven-config.md` line 68 repeats the same wrong `.mongocluster.documentdb.azure.com` suffix.
- `skills/driver/driver-singleton-client.md:26` and `skills/security/security-tls-required.md:26` also pass `retryWrites: true` in driver options.
- Only `skills/mcp-setup/SKILL.md` (`authMode: "entra"` connection profiles) and a note in `skills/high-availability/ha-cross-region-replica.md` treat Entra as a first-class path, and neither is application connection code.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), the cold-quiz question Q04 ("what does a connection string look like: scheme, host suffix, port, options") came back wrong or partly wrong on the authentication part in **35 of 100 samples** (36 findings). The model's prior is Azure Cosmos DB for MongoDB (RU): an `<account>.mongo.cosmos.azure.com:10255` URI where "the password is the account key". It did not know Entra ID is supported, or could not say how an Entra connection differs from a native one ("how to choose authMechanism (SCRAM vs MONGODB-OIDC)", "missing OIDC parameters"). Grounded answers got it right only after a Learn search landed on `how-to-connect-role-based-access-control`.

Because the connection skill never contradicts that prior, the builds in this bucket defaulted to password-in-URI SCRAM (for example the `16-subscription-billing-engine` build used `authMechanism=SCRAM-SHA-256` and no `MONGODB-OIDC`/`DefaultAzureCredential`), and the audit stage flagged "consider Microsoft Entra ID for production" as a doc gap in generated READMEs. The Learn pages already document the Entra form, so adding more Learn content is not the fix; the kit is what the agent reads before it searches.

## Proposed change

### 1. `skills/connection/SKILL.md`

Fix line 60:

```
mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

Replace the "Authentication" subsection (lines 70-74) with:

````markdown
### Authentication: two supported forms

Azure DocumentDB accepts **native users** (SCRAM-SHA-256, password in the URI) and
**Microsoft Entra ID principals** (users, service principals, managed identities;
MONGODB-OIDC, no password; the driver fetches a token from an Azure credential).
Both use the same `mongodb+srv://` scheme and the same
`<cluster>.mongocluster.cosmos.azure.com` / `<cluster>.global.mongocluster.cosmos.azure.com` host.

**Rule:** code that runs in Azure (App Service, Functions, Container Apps, AKS, VMs) or in
production should use Entra ID with a managed identity. Use a native SCRAM user for the local
DocumentDB container (`localhost:10260`) and for tools that do not support OIDC.

| | Native user (SCRAM) | Entra ID (OIDC) |
|---|---|---|
| `authMechanism` | `SCRAM-SHA-256` | `MONGODB-OIDC` |
| Credential in URI | `<user>:<password>@` | none (optionally `<client-id>@`) |
| Driver extra | none | `authMechanismProperties.OIDC_CALLBACK` returning an Entra token for scope `https://ossrdbms-aad.database.windows.net/.default` |
| Prereq | native user exists on the cluster | Entra ID enabled on the cluster (`az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`) and the principal registered on it (`az documentdb mongocluster microsoft-entra-user assign`, portal, or a `Microsoft.DocumentDB/mongoClusters/users` resource) |

Entra ID URI form (the `<client-id>@` part is optional):

    mongodb+srv://<client-id>@<cluster-name>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000

**Node.js (mongodb + @azure/identity):**

```javascript
const { MongoClient } = require('mongodb');
const { DefaultAzureCredential } = require('@azure/identity');

const credential = new DefaultAzureCredential();
const client = new MongoClient(
  `mongodb+srv://${process.env.DOCUMENTDB_CLUSTER}.global.mongocluster.cosmos.azure.com/`, {
    tls: true,
    retryWrites: false,
    maxIdleTimeMS: 120000,
    authMechanism: 'MONGODB-OIDC',
    authMechanismProperties: {
      OIDC_CALLBACK: async () => {
        const t = await credential.getToken('https://ossrdbms-aad.database.windows.net/.default');
        // expiresOnTimestamp is in milliseconds
        return { accessToken: t.token,
                 expiresInSeconds: Math.floor((t.expiresOnTimestamp - Date.now()) / 1000) };
      },
      ALLOWED_HOSTS: ['*.azure.com'],
    },
  });
```

**Python (pymongo + azure-identity):**

```python
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

class AzureTokenCallback(OIDCCallback):
    def __init__(self, credential): self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        return OIDCCallbackResult(access_token=token)

client = MongoClient(
    f"mongodb+srv://{CLUSTER}.global.mongocluster.cosmos.azure.com/",
    tls=True, retryWrites=False, maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureTokenCallback(DefaultAzureCredential())},
)
```

On an Azure host with a managed identity, mongosh and Compass can use
`authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net`
instead of a callback.

Source: https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control
````

### 2. `skills/security/security-entra-rbac.md`

- Line 15: change host to `prod-ddb.mongocluster.cosmos.azure.com`.
- Replace lines 20-30 ("Correct" block) with the Node.js snippet above (no `// or the current documented mechanism`, no `// (verify current driver support/spec...)` comments) and add one sentence: *MONGODB-OIDC is the mechanism; the driver calls your `OIDC_CALLBACK` to obtain an Entra token for scope `https://ossrdbms-aad.database.windows.net/.default`. Enable Microsoft Entra ID on the cluster and register the identity with `az documentdb mongocluster microsoft-entra-user assign` first.*
- Add a cross-reference: "For the SCRAM vs Entra choosing rule and the Python form, see `documentdb-connection`."

### 3. `skills/local-deployment/local-env-driven-config.md`

- Line 68: `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.documentdb.azure.com/...` -> `...@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`.

### 4. (same PR, small) `retryWrites: true` in driver options

- `skills/driver/driver-singleton-client.md:26` and `skills/security/security-tls-required.md:26`: change `retryWrites: true` to `retryWrites: false`, consistent with `skills/azure-deployment/SKILL.md:291`.

## Evidence (run folders from the readiness experiment; connection strings omitted)

- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` (confusions Q04: cold answer gave the `:10255` account-key form)
- `runs/19-insider-threat-detection-pipeline/20261124-202818/02-readiness.json` (Q04 outcome "outdated"; asks "how to choose authMechanism (SCRAM vs MONGODB-OIDC)")
- `runs/17-seasonal-trend-spotter-agent/20261124-185115/02-readiness.json` (Q04: "missing OIDC properties will fail authentication"; asks for a driver example for both auth forms)
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` (Q04 outcome "wrong")
- `runs/13-product-q-a-chatbot-rag/20261125-055422/02-readiness.json` (Q04: "wrong auth mechanism (expecting only username/password)")

Full list: 36 findings across 35 distinct samples, all `confusions[Q04]` in `02-readiness.json`.

## Verification

### 1. Already covered? partially_covered

The kit does mention Entra, but not where the agent looks for connection guidance, and not in usable form.
- `skills/connection/SKILL.md:70-74`: "Default mechanism: `SCRAM-SHA-256`" / "Credentials are managed through the Azure portal". No Entra, no OIDC. Line 60 carries `retryWrites=true`.
- `skills/security/security-entra-rbac.md:23-29`: "`authMechanism: "MONGODB-OIDC", // or the current documented mechanism`", "`// (verify current driver support/spec in the official docs)`", "`// credentialProvider: Azure Managed Identity`" (comment only, no callback code). Line 15 uses host `prod-ddb.mongocluster.documentdb.azure.com`.
- `skills/local-deployment/local-env-driven-config.md:68`: `...@<cluster>.mongocluster.documentdb.azure.com/...`.
- `skills/mcp-setup/SKILL.md:114-115`: Entra-to-cluster tokens via `authMode: "entra"` profiles (MCP server only).
- `skills/azure-deployment/SKILL.md:288-291` already has the correct `retrywrites=false` SCRAM string, confirming the kit is internally inconsistent.
- Learn (https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control) fully documents the Entra form, so the gap is the kit, as the draft says.

### 2. Premise true? confirmed (with small corrections applied)

Checked against the Learn page above (updated 2026-11-23):
- Entra ID is supported and "implemented using OpenID Connect (OIDC)"; parameters table lists `authMechanism` `MONGODB-OIDC` and `retrywrites` `false`; host `<cluster-name>.global.mongocluster.cosmos.azure.com` or `<cluster-name>.mongocluster.cosmos.azure.com`.
- URI form with optional `<client-id>@`, and the mongosh/Compass `ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net` form, match the page.
- Python `OIDCCallback` and Node `OIDC_CALLBACK` + `ALLOWED_HOSTS: ['*.azure.com']` with scope `https://ossrdbms-aad.database.windows.net/.default` match the page's samples.
- Corrections applied to the body: (a) the draft's grant command `az documentdb mongocluster user create` does not exist on Learn; the documented command is `az documentdb mongocluster microsoft-entra-user assign` (or a `Microsoft.DocumentDB/mongoClusters/users` resource), and enabling Entra is `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`; (b) "every built sample shipped SCRAM" softened to what was observed; (c) the Node `expiresInSeconds` keeps the millisecond-correct form (`expiresOnTimestamp` from `@azure/identity` is in ms; the Learn sample subtracts seconds from ms, which a maintainer may want to report to Learn separately); (d) "local gateway" renamed to the local DocumentDB container on port 10260; (e) added the two other `retryWrites: true` occurrences in the kit.

### 3. Maintainer skeptic: confirmed

As maintainer of Azure/documentdb-agent-kit I would accept this: it names exact files and lines, fixes two factual defects (invalid host suffix `mongocluster.documentdb.azure.com` in two files; `retryWrites=true` contradicting the kit's own azure-deployment skill), removes hedging the kit should not ship, and replaces a placeholder with code copied from the official Learn how-to. It is specific to Azure DocumentDB (OIDC token scope, host form, auth modes), not generic hygiene, and belongs in this repository.

## Finding ids

F0003, F0147, F0178, F0695, F0823, F0887, F0968, F1130, F1159, F1258, F1297, F1400, F1433, F1589, F1682, F1825, F1859, F2152, F2184, F2216, F2242, F2287, F2485, F2516, F2589, F2619, F2647, F2682, F2711, F2777, F2907, F2940, F3012, F3256, F3392, F3424
