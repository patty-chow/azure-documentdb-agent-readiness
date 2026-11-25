---
title: "security-entra-rbac: replace hedged MONGODB-OIDC stub with exact Entra URI, TOKEN_RESOURCE scope, per-driver callback samples and an explicit list of unsupported token mechanisms"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 15
findings: 15
bucket: confusion-Q06
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# security-entra-rbac: give agents the exact MONGODB-OIDC recipe instead of a hedge (and name the wrong mechanisms)

## What happens today

`skills/security/security-entra-rbac.md` is the kit's only guidance on how an application authenticates to Azure DocumentDB with Microsoft Entra ID. Its "Correct" example is a placeholder:

```javascript
// Node example — use the driver's Entra auth mechanism
// (verify current driver support/spec in the official docs)
const client = new MongoClient(uri, {
  authMechanism: "MONGODB-OIDC", // or the current documented mechanism
  // credentialProvider: Azure Managed Identity
  tls: true
});
```

- No `authMechanismProperties`: no `ENVIRONMENT:azure` / `TOKEN_RESOURCE` and no `OIDC_CALLBACK`. The snippet cannot authenticate as written.
- The comments tell the agent to "verify current driver support/spec in the official docs" and allow "the current documented mechanism", which leaves room for an invented mechanism.
- The "Incorrect" example uses host `prod-ddb.mongocluster.documentdb.azure.com`. The real suffix is `.mongocluster.cosmos.azure.com` (or `.global.mongocluster.cosmos.azure.com` for the global read-write endpoint). The same wrong suffix appears in `skills/local-deployment/local-env-driven-config.md` line 68.
- `skills/connection/SKILL.md` → "Authentication" lists only `SCRAM-SHA-256`. `skills/driver/SKILL.md` never mentions auth.

## Why it matters

In a 100-sample run of gpt-5-mini building Azure DocumentDB apps with this kit loaded, **15 samples** (02-clinical-trial-matching, 03-substitute-product-finder, 04-regulatory-reporting, 05-churn-prediction, 10-drug-formulary, 10-support-ticket-rag, 11-preference-center, 12-abandoned-cart, 13-basel-iii, 13-household-grouping, 14-customer-complaint-classifier, 17-esg-scoring, 17-stress-testing, 19-proactive-outreach, 20-store-locator) answered the cold-quiz question "how does a driver authenticate with Entra ID?" wrong in the same way: the model knew Entra exists but invented the mechanism. Observed answers:

| Wrong belief | Samples |
|---|---|
| Get a token with MSAL / `az account get-access-token` and pass it as the **password** with SCRAM | 11, 12, 13-basel, 13-household, 17-stress, 19 |
| Nonexistent `authMechanism=MONGODB-AZUREAD` | 19 |
| `authSource=$external` + `PLAIN` | 10-support, 17-esg, 20 |
| SASL `OAUTHBEARER` or GSSAPI | 02, 03, 05, 10-support |
| X.509 client certificates / mTLS | 02, 03, 04, 10-drug, 11, 13-basel, 17-esg, 17-stress, 19 |
| "Entra is management-plane only; data plane is SCRAM" | 04, 05, 14 |
| Driver OIDC support assumed without a version check | 10-drug, 14 |

Every one of these fails against Azure DocumentDB. The supported token path is the standard **MONGODB-OIDC** mechanism, either with `ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net` or with a driver `OIDC_CALLBACK` that fetches a token for scope `https://ossrdbms-aad.database.windows.net/.default`. In these 15 runs the builder fell back to SCRAM through `DOCUMENTDB_URI`, so nothing broke. But the audit stage flagged "no Entra/OIDC example in the sample" in 20-store-locator and 14-customer-complaint-classifier, and 04-regulatory-reporting logged a doc gap asking for exactly this: how to wire `Azure.Identity` into PyMongo. The first prompt that *requires* managed identity will ship one of the broken patterns above, because the skill that should correct the prior does not.

The Learn page [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control) already has the URI, the `createUser` command for Entra principals and callback samples in Python, TypeScript and C#, so no docs change is needed. The kit needs to carry them. The pattern is also already implemented in this ecosystem: `microsoft/documentdb-mcp` `src/context/documentdb.ts` builds its Entra client with `MONGODB-OIDC`, `TOKEN_RESOURCE` and an `OIDC_CALLBACK` backed by Azure Identity.

## Proposed change

### 1. `skills/security/security-entra-rbac.md`

Fix the host suffix in the existing Incorrect block, then **add a second Incorrect block**:

```javascript
// ❌ None of these work on Azure DocumentDB. All fail at auth.
// Token as password with SCRAM:
//   mongodb+srv://<client-id>:<access-token>@<cluster>.mongocluster.cosmos.azure.com/?authMechanism=SCRAM-SHA-256
// Invented mechanism:          authMechanism=MONGODB-AZUREAD
// LDAP/Kerberos/cert styles:   authMechanism=PLAIN | GSSAPI | MONGODB-X509 (with or without authSource=$external)
// Raw SASL:                    OAUTHBEARER
// Atlas human-flow OIDC config copied unchanged (no TOKEN_RESOURCE / callback for the ossrdbms-aad resource)
```

Note: `authSource=$external` is not wrong by itself. MONGODB-OIDC authenticates against `$external`, and drivers set it by default. It is wrong only when paired with PLAIN, GSSAPI or X.509.

**Replace the Correct block** with:

```text
Prerequisites (once per cluster; see the Learn RBAC page):
  1. Enable Entra auth (keep NativeAuth until Entra principals are verified):
       az documentdb mongocluster update --name <cluster> --resource-group <rg> \
         --auth-allowed-modes NativeAuth MicrosoftEntraID
  2. Register an Entra administrator on the cluster (portal, CLI/REST users resource, Bicep or Terraform).
  3. Signed in as that Entra admin (for example with mongosh), add the app identity by its OBJECT ID
     (not its client/application ID). readWriteAnyDatabase and clusterAdmin must be granted together:
       db.getSiblingDB("admin").runCommand({
         createUser: "<principal-object-id>",
         roles: [
           { role: "clusterAdmin", db: "admin" },
           { role: "readWriteAnyDatabase", db: "admin" }
         ],
         customData: { "IdentityProvider": { "type": "MicrosoftEntraID",
           "properties": { "principalType": "servicePrincipal" } } }   // "user" for a human identity
       })
     For read-only access use roles: [{ role: "readAnyDatabase", db: "admin" }].

Connection string (mongosh / Compass / any driver that supports ENVIRONMENT:azure):
mongodb+srv://<client-id>@<cluster>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000&authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net
(the non-global host <cluster>.mongocluster.cosmos.azure.com also works for a single cluster)
```

```javascript
// Node (mongodb >= 6.7.0): OIDC callback with DefaultAzureCredential
const { MongoClient } = require("mongodb");
const { DefaultAzureCredential } = require("@azure/identity");
const credential = new DefaultAzureCredential();
const client = new MongoClient(`mongodb+srv://${cluster}.global.mongocluster.cosmos.azure.com/`, {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const t = await credential.getToken(["https://ossrdbms-aad.database.windows.net/.default"]);
      // expiresOnTimestamp is in milliseconds
      return { accessToken: t.token, expiresInSeconds: Math.max(0, Math.floor((t.expiresOnTimestamp - Date.now()) / 1000)) };
    },
    ALLOWED_HOSTS: ["*.mongocluster.cosmos.azure.com"],
  },
});
```

```python
# PyMongo >= 4.7.0: OIDCCallback with DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult
from azure.identity import DefaultAzureCredential

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential): self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        return OIDCCallbackResult(access_token=token)

client = MongoClient(f"mongodb+srv://{cluster}.global.mongocluster.cosmos.azure.com/",
    tls=True, retryWrites=False, maxIdleTimeMS=120000, authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())})
```

```csharp
// .NET driver: IOidcCallback + MongoCredential.CreateOidcCredential (from the Learn page)
settings.Credential = MongoCredential.CreateOidcCredential(new AzureIdentityTokenHandler(new DefaultAzureCredential(), tenantId));
// AzureIdentityTokenHandler : IOidcCallback returns new OidcAccessToken(token.Token, token.ExpiresOn - DateTimeOffset.UtcNow)
// for scope "https://ossrdbms-aad.database.windows.net/.default"
```

```java
// Java driver: not on the Learn page. Verify before merging.
// MongoCredential.createOidcCredential(null)
//   .withMechanismProperty(MongoCredential.OIDC_CALLBACK_KEY, (MongoCredential.OidcCallback) ctx ->
//       new MongoCredential.OidcCallbackResult(credential.getToken(new TokenRequestContext()
//           .addScopes("https://ossrdbms-aad.database.windows.net/.default")).block().getToken()))
```

Add a short table:

| Client | Minimum for MONGODB-OIDC with callback / ENVIRONMENT:azure |
|---|---|
| Node `mongodb` | 6.7.0 (release notes: MONGODB-OIDC supported, `OIDC_CALLBACK`, `ENVIRONMENT:azure`) |
| PyMongo | 4.7.0 (changelog: "Added support for MONGODB-OIDC authentication") |
| .NET | current 3.x ships `IOidcCallback` / `CreateOidcCredential`; maintainer to confirm the first 2.x version from release notes |
| Java | current 5.x ships `OIDC_CALLBACK_KEY`; maintainer to confirm the minimum from release notes |
| mongosh / Compass / VS Code DocumentDB extension | use the URI above; the Learn page also shows the VS Code extension prompting for Entra sign-in |

(The Python, TypeScript and C# bodies follow the Learn page's code samples. The Java snippet and the .NET/Java version minimums are not on Learn and need a check against the driver release notes before merging.)

### 2. `skills/connection/SKILL.md` → "Authentication"

Add after the SCRAM bullet:

```
- Microsoft Entra ID (managed identity / service principal / user): `authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net` on the same mongodb+srv host, or a driver OIDC_CALLBACK that gets a token for scope `https://ossrdbms-aad.database.windows.net/.default` (PyMongo >= 4.7, Node >= 6.7). The token is never the password. PLAIN, GSSAPI, MONGODB-X509, OAUTHBEARER and "MONGODB-AZUREAD" are not supported. The principal must first be added with createUser by object ID. See security-entra-rbac.md.
```

### 3. `skills/local-deployment/local-env-driven-config.md` line 68

`.mongocluster.documentdb.azure.com` → `.mongocluster.cosmos.azure.com`.

## Evidence (run folders from the 100-sample experiment)

- `runs/19-proactive-outreach-orchestration/20261124-205844/02-readiness.json`: confusions[Q06], `MONGODB-AZUREAD`, token as password; outcome `wrong`
- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json` and `05-audit.json`: `authSource=$external` + PLAIN/X.509; audit says the sample never shows MONGODB-OIDC
- `runs/14-customer-complaint-classifier/20261124-201931/02-readiness.json` and `05-audit.json`: "Entra is not the data-plane path"; asks for driver-version minimums; builder chose SCRAM (D005/D011)
- `runs/04-regulatory-reporting-orchestration/20261124-200545/doc-gaps.md` line 47: "Entra ID authentication patterns for application code"
- `runs/10-support-ticket-rag-assistant/20261124-204529/02-readiness.json`: SASL/OAUTHBEARER or PLAIN/$external

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? partially_covered

The kit has a stub but not the recipe. `skills/security/security-entra-rbac.md` contains only `authMechanism: "MONGODB-OIDC", // or the current documented mechanism` with `// credentialProvider: Azure Managed Identity` commented out and the hedge "(verify current driver support/spec in the official docs)". It has no `authMechanismProperties`, no TOKEN_RESOURCE or scope, and no `createUser` for Entra principals. Its Incorrect example uses the wrong host suffix `.mongocluster.documentdb.azure.com`, and so does `skills/local-deployment/local-env-driven-config.md:68`. `skills/connection/SKILL.md:70-74` says "Default mechanism: `SCRAM-SHA-256`" and nothing about Entra. A grep of `skills/` and `knowledge-base/` for `ossrdbms`, `TOKEN_RESOURCE` and `OIDC_CALLBACK` finds nothing. The kit's other Entra mentions (`skills/mcp-setup/SKILL.md`, `ha-cross-region-replica.md`) cover MCP transport auth and replica auth modes, not driver code.

Learn already covers it fully: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control has the URI with `authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net`, `AzureIdentityTokenCallback(OIDCCallback)` in Python, `OIDC_CALLBACK` in TypeScript, `IOidcCallback` / `MongoCredential.CreateOidcCredential` in C#, and the `createUser` command. So the gap is in the kit, which is the target. `microsoft/documentdb-mcp` `src/context/documentdb.ts:33-47` implements the same pattern (MONGODB-OIDC, TOKEN_RESOURCE, OIDC_CALLBACK via Azure Identity), but agents building samples do not read it.

### 2. Premise true? confirmed (with detail corrections applied)

The core claim is correct: MONGODB-OIDC with `ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net`, or an `OIDC_CALLBACK` for scope `https://ossrdbms-aad.database.windows.net/.default`, is the supported Entra path. The token-as-password, MONGODB-AZUREAD, PLAIN, GSSAPI, X.509 and OAUTHBEARER variants are not offered (Learn lists only `MONGODB-OIDC` as the Entra authMechanism). The CLI line `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID` matches Learn verbatim. Detail errors in the draft, all now corrected in the body:

- **createUser was wrong.** The draft granted only `readWriteAnyDatabase` with no `customData`. Learn says `readWriteAnyDatabase` and `clusterAdmin` "must be granted together". It requires `customData: { "IdentityProvider": { "type": "MicrosoftEntraID", "properties": { "principalType": "<principal-type>" } } }` with `servicePrincipal` for managed identities, uses the object ID rather than the client ID, and needs an Entra administrator registered first. All of this was added.
- **Node minimum** was given as "6.x". The node-mongodb-native v6.7.0 release notes introduce MONGODB-OIDC with `OIDC_CALLBACK` and `ENVIRONMENT:azure`, so it is now 6.7.0. PyMongo 4.7.0 is confirmed by the PyMongo changelog ("Added support for MONGODB-OIDC authentication").
- **.NET "3.x (OIDC introduced in 2.27)", mongosh "2.x" and Compass "1.40+"** could not be verified (the MongoDB C# OIDC docs state no minimum), so they were replaced with "maintainer to confirm". The same applies to Java 5.1: its release notes only say "Enhanced OIDC support".
- **Attribution.** The draft said the C#/Java bodies were copied from Learn. Learn has Python, TypeScript and C# only, with no Java, so the Java snippet is now marked as needing verification.
- **authSource=$external.** It was listed as a wrong mechanism, but MONGODB-OIDC itself authenticates against `$external`, and documentdb-mcp sets `authSource: '$external'` alongside MONGODB-OIDC. The text now says it is wrong only when paired with PLAIN/GSSAPI/X.509.
- **ALLOWED_HOSTS** was narrowed to `*.mongocluster.cosmos.azure.com`, matching documentdb-mcp's README. The Node `expiresInSeconds` uses the millisecond timestamp correctly. Note that Learn's TypeScript sample subtracts seconds from the millisecond `expiresOnTimestamp`.

Sources: Learn RBAC page above (updated 2026-11-23); https://github.com/mongodb/node-mongodb-native/releases/tag/v6.7.0; https://pymongo.readthedocs.io/en/stable/changelog.html; https://www.mongodb.com/docs/drivers/csharp/current/security/authentication/oidc/; https://github.com/mongodb/mongo-java-driver/releases/tag/r5.1.0; documentdb-mcp `src/context/documentdb.ts`, `README.md:213-216`.

### 3. Maintainer skeptic: confirmed

The change names exact files and lines (`skills/security/security-entra-rbac.md`, `skills/connection/SKILL.md` "Authentication", `skills/local-deployment/local-env-driven-config.md:68`). It is specific to Azure DocumentDB (ossrdbms-aad token resource, mongocluster.cosmos.azure.com host, the `customData` IdentityProvider shape), fixes a real factual error (the host suffix) and a non-running snippet, and copies content from the official Learn page. As maintainer I would accept it once the Java snippet and the .NET/Java version minimums are verified, which the body now flags. It belongs in Azure/documentdb-agent-kit. Learn needs no change.

## Finding ids

F0215, F0496, F0661, F0765, F1590, F1684, F1861, F1922, F2154, F2217, F2326, F2842, F2941, F3324, F3499
