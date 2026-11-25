---
title: "driver skill: add a copy-paste PyMongo \"Connect to Azure DocumentDB\" rule (SCRAM + Entra ID/OIDC, ping check) and fix retryWrites=true in kit examples"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 1
findings: 1
bucket: mcp-server
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# driver skill: add a copy-paste PyMongo "Connect to Azure DocumentDB" rule, and stop telling agents to use retryWrites=true

## What happens today

`skills/driver/SKILL.md` says the skill covers "Node.js, Python, Java, Go, and .NET", but it has one rule (`driver-singleton-client.md`) and the only code in it is JavaScript. `skills/connection/SKILL.md` says TLS is always required and that SCRAM-SHA-256 is the default mechanism, but its code blocks are JavaScript too. The only Entra ID example in the kit, `skills/security/security-entra-rbac.md`, is a JavaScript placeholder that says "verify current driver support/spec in the official docs" and has no token callback. No skill shows:

- how to pass the DocumentDB options to PyMongo's `MongoClient`,
- how to authenticate from Python with Microsoft Entra ID (`MONGODB-OIDC`, an `OIDCCallback` and the `https://ossrdbms-aad.database.windows.net/.default` scope),
- how to check the connection with `ping` before the app starts.

Learn already has both Python snippets: the Python quickstart (SCRAM plus `client.admin.command('ping')`) and the "Connect using role-based access control and Microsoft Entra ID" page (PyMongo `OIDCCallback`). The kit does not point to either one. Agents that load the kit skills therefore have nothing to copy in the place they look first.

In the `19-care-coordination-multi-agent` run (gpt-5-mini, Agent Kit + DocumentDB/Azure/Learn MCP servers), the audit stage recorded a high-priority gap. The builder did not find a single authoritative PyMongo connection example and wrote:

```python
_client = MongoClient(DOCUMENTDB_URI)   # app/app/db.py:27 — no tls/auth/retry options
```

That line works only when the operator's `DOCUMENTDB_URI` already carries `tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false`. A hand-typed or trimmed URI fails on the first query with a server-selection timeout.

The kit also contradicts itself on retryable writes:

- The portal string and Learn use `retrywrites=false`. `skills/azure-deployment/SKILL.md` gets this right: "Azure DocumentDB does not support retryable writes".
- These examples use `retryWrites=true` or `retryWrites: true` instead:
  - `skills/connection/SKILL.md`, the "Connection String Format" block,
  - `skills/security/security-tls-required.md`, the "Correct" example,
  - `skills/driver/driver-singleton-client.md`, the "Correct" example.

## Why it matters

- Only 1 of 100 samples raised this as an explicit doc gap, but the pattern shows up across the set. 57 run folders contain Python that constructs `MongoClient(...)`, with about 93 constructions in total. A single-line grep finds only about 7 that pass `tls=True` and about 5 that pass `retryWrites=False`. Without a Python reference in the kit, the agents are guessing.
- Other samples (for example `01-product-catalog-with-vector-search`, `06-collateral-management-store` and `17-esg-scoring-pipeline`) separately raised Entra ID / OIDC gaps in their `doc-gaps.md`. They fell back to the admin connection string. The OIDC variant below covers those cases too.
- Agents read and act on the `retryWrites=true` examples in three kit files. Those examples contradict the service's documented connection settings and the kit's own azure-deployment skill.

## Proposed change

### 1. New file `skills/driver/driver-python-connect.md`

````markdown
# driver-python-connect

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB (resource type `Microsoft.DocumentDB/mongoClusters`) always requires TLS. Native users authenticate with SCRAM-SHA-256, and Microsoft Entra ID principals use MONGODB-OIDC. Retryable writes are not supported, so connection strings use `retrywrites=false`. The connection string you copy from the portal (Cluster > Settings > Connection strings) already carries these query parameters. The portal string leaves out the password: replace the `<password>` placeholder yourself.

| Parameter | Value | Why |
|---|---|---|
| `tls` | `true` | TLS is mandatory |
| `authMechanism` | `SCRAM-SHA-256` (native users) or `MONGODB-OIDC` (Entra ID) | Authentication mechanism |
| `retrywrites` | `false` | Retryable writes are not supported |
| `maxIdleTimeMS` | `120000` | Recommended: closes idle pooled connections before they go stale |

The host is `<cluster>.global.mongocluster.cosmos.azure.com` (global read-write endpoint) or `<cluster>.mongocluster.cosmos.azure.com`, always with the `mongodb+srv` scheme. Legacy Azure Cosmos DB for MongoDB (RU) strings (`*.mongo.cosmos.azure.com`, `replicaSet=globaldb`, port 10255) belong to a different service and will not connect.

When an option appears both in the URI and as a PyMongo keyword argument, the keyword argument wins. Keep the two consistent.

## Correct — SCRAM-SHA-256 (connection string from the portal)

```python
import os
from pymongo import MongoClient

# Read the portal connection string (password filled in) from the environment
# or a secret store. Never commit it.
uri = os.environ["DOCUMENTDB_URI"]

client = MongoClient(
    uri,
    tls=True,                       # DocumentDB always requires TLS
    retryWrites=False,              # retryable writes are not supported
    serverSelectionTimeoutMS=5000,  # fail fast instead of waiting 30 s
)
client.admin.command("ping")        # raises on bad host, credentials, firewall or TLS
```

Create this client once per process (see `driver-singleton-client`).

## Correct — Microsoft Entra ID (MONGODB-OIDC)

Before this works:

- Entra ID authentication must be enabled on the cluster, alongside native authentication.
- The principal (user, service principal or managed identity) must be added as a cluster user.
- You need PyMongo 4.7 or later and `azure-identity`.

```python
import os
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential):
        self.credential = credential

    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token
        return OIDCCallbackResult(access_token=token)

cluster = os.environ["DOCUMENTDB_CLUSTER_NAME"]
client = MongoClient(
    f"mongodb+srv://{cluster}.global.mongocluster.cosmos.azure.com/",
    tls=True,
    retryWrites=False,
    maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
    serverSelectionTimeoutMS=5000,
)
client.admin.command("ping")
```

## Incorrect

```python
client = MongoClient(os.environ["DOCUMENTDB_URI"])          # relies on the URI carrying tls/auth/retry
client = MongoClient(uri, retryWrites=True)                 # retryable writes are not supported
client = MongoClient(uri, tlsAllowInvalidCertificates=True) # never against the managed service
```

## References

- [Quickstart: Python driver — Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python)
- [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)
- [PyMongo: MONGODB-OIDC authentication](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/security/authentication/oidc/)
````

### 2. Register the rule in `skills/driver/SKILL.md`

Under `## Rules`, add:

```markdown
- [driver-python-connect](driver-python-connect.md) — Connect from PyMongo with explicit `tls=True`, `retryWrites=False`, SCRAM-SHA-256 or Entra ID (MONGODB-OIDC), and verify with `ping`.
```

### 3. Fix the `retryWrites=true` examples elsewhere in the kit

- `skills/connection/SKILL.md`, "Connection String Format": change the string to `mongodb+srv://<username>:<password>@<cluster-name>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`. Under "### Authentication", add `MONGODB-OIDC` (Microsoft Entra ID) as a supported mechanism, plus the line "Python example: see `documentdb-driver` → `driver-python-connect`."
- `skills/security/security-tls-required.md` and `skills/driver/driver-singleton-client.md`: in the "Correct" examples, change `retryWrites: true` to `retryWrites: false`.
- `skills/security/security-entra-rbac.md`: replace the "verify current driver support" placeholder with a link to `driver-python-connect`. In the "Incorrect" example, the host `mongocluster.documentdb.azure.com` is not a real DocumentDB host; change it to `mongocluster.cosmos.azure.com`.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `19-care-coordination-multi-agent/20261124-195730/doc-gaps.md`: "[high] Explicit PyMongo connection examples for mongoClusters".
- `19-care-coordination-multi-agent/20261124-195730/05-audit.json`: `doc_gaps[0]`, proposed_fix_type `mcp_tool_or_description`.
- `19-care-coordination-multi-agent/20261124-195730/app/app/db.py`: line 27, bare `MongoClient(DOCUMENTDB_URI)`.
- `19-care-coordination-multi-agent/20261124-195730/05a-practice-discovery.md`: practice P02 (enforce TLS) was found only in the Learn quickstart, not in the kit.
- `01-product-catalog-with-vector-search/20261124-175429/doc-gaps.md`, `06-collateral-management-store/20261124-200922/doc-gaps.md` and `17-esg-scoring-pipeline/20261124-192259/doc-gaps.md`: Entra ID / OIDC connection gaps.

## Verification

### 1. Already covered? — partially_covered

- **Kit:** `skills/driver/` contains only `SKILL.md` and `driver-singleton-client.md`, and there is no Python in either. `skills/connection/SKILL.md` mentions PyMongo `MongoClient` / `AsyncMongoClient` only in prose, with JavaScript code. `skills/security/security-entra-rbac.md` has a JavaScript OIDC placeholder ("verify current driver support/spec in the official docs") and no callback or scope. Python connection code appears only in `skills/local-deployment/*`, for the local emulator, with `tlsAllowInvalidCertificates`. The kit does not cover the ask.
- **Learn:** https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python has a PyMongo SCRAM snippet with the portal-style URI (`...?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`) and `client.admin.command('ping')`. https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control has a PyMongo `AzureIdentityTokenCallback(OIDCCallback)` sample using the `https://ossrdbms-aad.database.windows.net/.default` scope, `tls=True`, `retryWrites=False` and `authMechanism="MONGODB-OIDC"`. The content exists, but not in the place the agent looked first (the kit skill).
- **Correction applied:** the draft said that neither the Learn quickstarts nor the kit had a concrete PyMongo snippet. That was wrong for Learn. The body now says the Learn snippets exist, and the new rule links to them.

### 2. Premise true? — confirmed (with corrections)

The core claim holds: the kit's driver skill has no Python connection guidance. These details were corrected or tightened:

- **retrywrites:** Learn's Entra page lists `retrywrites=false` among "recommended" settings, and only TLS as a "must". The kit's `skills/azure-deployment/SKILL.md` says retryable writes are not supported. The body now gives that reason ("retryable writes are not supported") instead of "required by the service".
- **maxIdleTimeMS:** reworded as recommended, not required.
- **`.global.` host:** added the `.global.mongocluster.cosmos.azure.com` form, which the Learn pages use.
- **Entra prerequisite:** added that native authentication must stay enabled alongside Entra ID (Learn Entra page).
- **OIDC sample:** now builds `DefaultAzureCredential` once and passes it to the callback, matching the Learn sample, instead of creating a new credential on every `fetch`.
- **Extra kit defect:** found and added that `retryWrites=true` appears in `skills/connection/SKILL.md` (connection-string block), `skills/security/security-tls-required.md` and `skills/driver/driver-singleton-client.md`.
- **Wrong host in kit:** `security-entra-rbac.md` uses `mongocluster.documentdb.azure.com`.
- **Sample counts:** checked with grep. 57 run folders have Python `MongoClient(` calls, about 93 constructions; a single-line grep finds about 7 with `tls=True` and 5 with `retryWrites=False`. The count was corrected from ~65 to ~93.
- **Facts confirmed unchanged:**
  - PyMongo keyword arguments take precedence over URI options.
  - PyMongo added MONGODB-OIDC support in 4.7.
  - Legacy RU endpoints (`*.mongo.cosmos.azure.com:10255`, `replicaSet=globaldb`) are a different service.

### 3. Maintainer skeptic — confirmed

As a kit maintainer, I would accept this. It names exact files (a new `skills/driver/driver-python-connect.md`, a registration line in `skills/driver/SKILL.md`, one-line fixes in three existing files) and the code follows the official Learn samples. The guidance is specific to Azure DocumentDB: mongocluster hosts, the ossrdbms-aad token scope, and retrywrites=false. The fix belongs in Azure/documentdb-agent-kit even though the theme was bucketed under "mcp-server": no MCP server change is needed, and Learn already has the content.

## Finding ids

- F3159
