# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| prompt | 2 |
| tool_result | 2 |
| operator | 1 |
| readiness_report | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:01:37+00:00

## D002 (build): I chose Python + FastAPI + Beanie as the framework and ODM.

- **Instead of:** Node.js + Express + Mongoose; Python + FastAPI + Beanie (requested)
- **Because:** The user explicitly requested Python + FastAPI + Beanie; this matches the sample requirements.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: "build a Python FastAPI service using Beanie ODM".
- **When:** 2026-11-25T06:02:14+00:00

## D003 (build): I chose Motor as the MongoDB async driver because Beanie requires Motor.

- **Instead of:** Motor (async MongoDB driver); PyMongo AsyncMongoClient (newer async API)
- **Because:** Beanie currently depends on Motor for async integration; to use Beanie as requested we must use Motor despite guidance that PyMongo's async API exists.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: "Use async stack: Motor + Beanie (Beanie requires Motor)." Also documentdb-connection notes PyMongo Async API deprecation note but Beanie depends on Motor.
- **When:** 2026-11-25T06:02:17+00:00

## D004 (build): I chose to request latest compatible releases (no strict pins) in requirements.txt.

- **Instead of:** Pin specific package versions (e.g., beanie==x, motor==y); Use latest compatible releases (no strict pins)
- **Because:** Using latest compatible releases reduces the chance of incompatibility with the runtime here; this is acceptable for a sample app. If a consumer needs strict reproducibility they can pin versions later.
- **Reason came from:** `model_default`
- **Evidence:** No exact version was mandated by the prompt; versions can cause install friction. The readiness report refers to following Beanie quickstart dependency versions but does not require exact pins.
- **When:** 2026-11-25T06:02:20+00:00

## D005 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use Microsoft Entra/OIDC auth; Use native connection string from env variable DOCUMENTDB_URI
- **Because:** The run environment already provides DOCUMENTDB_URI; reading it from env keeps secrets out of files and matches the guidance.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time."
- **When:** 2026-11-25T06:02:24+00:00

## D006 (build): I chose not to provision any Azure resources and to use the existing cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision a new DocumentDB cluster via Bicep/az/terraform; Do not provision any resources and use existing cluster
- **Because:** Policy forbids creating resources and an existing reachable cluster with DOCUMENTDB_URI is available for the sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: "Azure resource changes allowed: False." skill_md also: "A cluster is already provisioned and reachable."
- **When:** 2026-11-25T06:02:26+00:00

## D007 (build): I chose float for PurchaseOrder.total_value in this sample.

- **Instead of:** Use Decimal for monetary totals; Use float for total_value
- **Because:** Float is simpler for a small sample app and avoids additional Decimal/PyMongo type handling; note in README that production should use Decimal or specialized money types.
- **Reason came from:** `model_default`
- **Evidence:** Prompt did not mandate Decimal; simpler sample code and MongoDB stores numeric types as double by default.
- **When:** 2026-11-25T06:02:30+00:00

## D008 (build): I chose to create indexes: a single-field index on Supplier.name and a compound index on PurchaseOrder (supplier_id, status).

- **Instead of:** Do not create indexes (rely on defaults); Create indexes: Supplier.name and compound index on PurchaseOrder(supplier_id, status)
- **Because:** These indexes improve the aggregation performance and supplier lookups while keeping the sample simple.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill: 'compound index design via ESR ... prefer one compound over many singles.'
- **When:** 2026-11-25T06:02:44+00:00

## D009 (build): I chose to update config to import BaseSettings from pydantic_settings for compatibility with installed pydantic 2.x.

- **Instead of:** Keep using pydantic.BaseSettings (older API); Use pydantic_settings.BaseSettings to be compatible with pydantic v2.14
- **Because:** The installed Pydantic version requires pydantic-settings; updating the import fixes runtime error without changing dependencies.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime error: `BaseSettings has been moved to the pydantic-settings package` (traceback).
- **When:** 2026-11-25T06:03:37+00:00

## D010 (build): I chose to add pydantic-settings to requirements and install it to satisfy the pydantic v2 API.

- **Instead of:** Add pydantic-settings to requirements and install; Pin pydantic to an older version where BaseSettings is available
- **Because:** Installing pydantic-settings is the minimal change to support BaseSettings with the installed pydantic 2.x; pinning pydantic older would be heavier and unnecessary.
- **Reason came from:** `tool_result`
- **Evidence:** ModuleNotFoundError: No module named 'pydantic_settings' while running the seed script after updating config to use pydantic_settings.
- **When:** 2026-11-25T06:03:46+00:00
