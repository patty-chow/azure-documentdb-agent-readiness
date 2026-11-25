---
id: K16
title: "driver skill: add a copy-paste PyMongo 'Connect to Azure DocumentDB' rule"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 1
member_drafts:
  - 120-documentdb-driver-skill-lacks-an-authoritative-copy-paste-py.md
open_questions: 2
---

# driver skill: add a copy-paste PyMongo "Connect to Azure DocumentDB" rule

## What happens today

`skills/driver/SKILL.md` says it covers "Node.js, Python, Java, Go, and .NET". It has one rule, `driver-singleton-client.md`, and all of its code is JavaScript. `skills/connection/SKILL.md` says TLS is always required and SCRAM-SHA-256 is the default mechanism, but its code is JavaScript too. The only Python connection code in the kit is in `skills/local-deployment/*`. That code targets the local emulator, and the `tlsAllowInvalidCertificates` setting it shows (sometimes as an anti-pattern) must never be used against the managed service.

So no kit skill shows a Python agent how to:

- pass the Azure DocumentDB connection options to PyMongo's `MongoClient`,
- check the connection with `ping` before the app starts serving.

Learn already has a PyMongo snippet in the Python quickstart, but the kit does not link to it. An agent that loads the kit looks there first and finds nothing to copy.

In one sample (`19-care-coordination-multi-agent`, gpt-5-mini with the Agent Kit and the DocumentDB, Azure and Learn MCP servers), the audit stage logged a high-priority gap: there was no authoritative PyMongo connection example. The builder wrote this:

```python
_client = MongoClient(DOCUMENTDB_URI)   # app/app/db.py:27, no tls/auth/retry options
```

That works only if the operator's URI already carries every required option. A URI that was typed by hand or trimmed fails at the first query with a server-selection timeout.

## Why it matters

- One of the 100 samples named this as an explicit documentation gap. The underlying pattern is wider. In the same run, 57 run folders contain Python that builds a `MongoClient(...)`, about 93 calls in total. A single-line grep finds about 7 that pass `tls=True` and about 5 that pass `retryWrites=False`. Without a Python reference, agents guess the options or leave them out.
- These counts come from one experiment run and from grep, not from per-sample review, so treat them as indicative.

## Scope and related PRs

- **K01** fixes the `retryWrites=true` examples in `skills/connection/SKILL.md`, `skills/driver/driver-singleton-client.md` and `skills/security/security-tls-required.md`, along with the `.documentdb.azure.com` host suffix. Those fixes are left out of this PR.
- **K03** adds Microsoft Entra ID (MONGODB-OIDC) guidance and per-driver examples, Python included, to the connection and security skills, and rewrites `security-entra-rbac.md`. This PR only links to that guidance. The source draft also proposed a cross-link line in `skills/connection/SKILL.md` ("Python example: see `documentdb-driver` → `driver-python-connect`"); because K03 rewrites that section, add the line there. The draft's PyMongo MONGODB-OIDC example (`OIDCCallback`, `https://ossrdbms-aad.database.windows.net/.default` scope) and its Entra ID evidence (`01-product-catalog-with-vector-search`, `06-collateral-management-store`, `17-esg-scoring-pipeline` doc-gaps) also move to K03.
- This PR adds one new rule file and one index line, and edits no other file.

## Proposed change

### 1. New file `skills/driver/driver-python-connect.md`

````markdown
# driver-python-connect

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB (resource type `Microsoft.DocumentDB/mongoClusters`) always requires TLS. Native users authenticate with SCRAM-SHA-256. The connection string from the portal (Cluster > Settings > Connection strings) uses the `mongodb+srv` scheme, a host ending in `.mongocluster.cosmos.azure.com`, and these query options:

| Option | Value |
|---|---|
| `tls` | `true` |
| `authMechanism` | `SCRAM-SHA-256` (native users; for Microsoft Entra ID see the `documentdb-connection` skill, Authentication section) |
| `retrywrites` | `false` |
| `maxIdleTimeMS` | `120000` |

The portal string leaves out the password, so fill in the placeholder yourself. Legacy Azure Cosmos DB for MongoDB (RU) strings (`*.mongo.cosmos.azure.com`, port 10255, `replicaSet=globaldb`) belong to a different service and will not connect.

If an option is set in both the URI and a PyMongo keyword argument, the keyword argument wins. Keep the two consistent.

## Correct

```python
import os
from pymongo import MongoClient

# Portal connection string with the password filled in, read from the
# environment or a secret store. Never commit it.
uri = os.environ["DOCUMENTDB_URI"]

client = MongoClient(
    uri,
    tls=True,                       # TLS is always required
    retryWrites=False,              # matches the published connection string
    maxIdleTimeMS=120000,           # matches the published connection string
    serverSelectionTimeoutMS=5000,  # fail fast instead of waiting 30 s
)
client.admin.command("ping")        # raises on a bad host, bad credentials, a firewall block or a TLS error
```

Create this client once per process (see `driver-singleton-client`). `AsyncMongoClient` takes the same keyword arguments.

## Incorrect

```python
client = MongoClient(os.environ["DOCUMENTDB_URI"])           # works only if the URI carries every option
client = MongoClient(uri, retryWrites=True)                  # contradicts the published connection string
client = MongoClient(uri, tlsAllowInvalidCertificates=True)  # local emulator only, never the managed service
```

## References

- [Quickstart: Python driver — Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python)
- [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)
````

### 2. Add the rule to `skills/driver/SKILL.md`

Add this line under `## Rules`:

```markdown
- [driver-python-connect](driver-python-connect.md) — Connect from PyMongo with explicit `tls=True`, `retryWrites=False` and `maxIdleTimeMS`, and verify the connection with `ping` at startup.
```

## Evidence

Run folders under `azure-documentdb-agent-readiness/runs/`:

- `19-care-coordination-multi-agent/20261124-195730/doc-gaps.md`: "[high] Explicit PyMongo connection examples for mongoClusters"
- `19-care-coordination-multi-agent/20261124-195730/05-audit.json`: `doc_gaps[0]`
- `19-care-coordination-multi-agent/20261124-195730/app/app/db.py`: line 27, a bare `MongoClient(DOCUMENTDB_URI)`
- `19-care-coordination-multi-agent/20261124-195730/05a-practice-discovery.md`: practice P02 (enforce TLS) was found only in the Learn quickstart, not in the kit

## Open questions

1. **Why `retrywrites=false`?** [needs SME confirmation] The portal string, the Learn quickstart and `skills/azure-deployment/SKILL.md` all use `retrywrites=false`. The sources give different reasons. One view is that the service does not support retryable writes and that enabling them causes write errors. The other is that Learn lists `retrywrites=false` only as a recommended setting (TLS is the only "must") and never says retryable writes are unsupported. The rule above sets `retryWrites=False` only to match the published string and gives no reason. Please give the engineering answer so this rule, K01 and Learn can all state the same reason.
2. **Should every client set `maxIdleTimeMS=120000`?** [needs SME confirmation] Is 120000 the recommended value for every workload, or only the portal default?

## Source drafts

- `120-documentdb-driver-skill-lacks-an-authoritative-copy-paste-py.md`
