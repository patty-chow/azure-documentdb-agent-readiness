#!/usr/bin/env python
"""Test local-gateway-parity: probe documentdb-local (container ddb-engine-test) for
feature parity with the managed Azure DocumentDB service. Database: t_parity only.

Rerun:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python run_parity.py

Reads LOCAL_URI from ../local.env. Never prints or stores the password.
Writes report.json next to this script.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback

from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(HERE), "local.env")
REPORT_PATH = os.path.join(HERE, "report.json")
CONTAINER = "ddb-engine-test"
DB_NAME = "t_parity"
COLL = "docs"
TEST_ID = "local-gateway-parity"


def load_uri():
    uri = None
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                uri = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not uri:
        raise SystemExit("LOCAL_URI not found in local.env")
    return uri


def redact(uri):
    return re.sub(r"://([^:/]+):[^@]+@", r"://\1:<redacted>@", uri)


def to_jsonable(obj):
    # bson -> plain JSON (relaxed extended JSON), then back to python so json.dump works
    return json.loads(json_util.dumps(obj, json_options=json_util.RELAXED_JSON_OPTIONS))


def err_info(e):
    info = {"exception": type(e).__name__, "message": str(e)}
    if isinstance(e, OperationFailure):
        info["code"] = e.code
        d = e.details or {}
        info["codeName"] = d.get("codeName")
        info["errmsg"] = d.get("errmsg")
        info["errorLabels"] = d.get("errorLabels", [])
        info["details"] = to_jsonable(d)
    return info


steps = []


def record(step, command, response=None, error=None, reading="", supported=None, extra=None):
    entry = {"step": step, "command": command}
    if error is not None:
        entry["error"] = error
    if response is not None:
        entry["response"] = response
    entry["supported"] = supported
    entry["reading"] = reading
    if extra:
        entry.update(extra)
    steps.append(entry)
    status = "OK" if error is None else f"ERROR code={error.get('code')} codeName={error.get('codeName')}"
    print(f"[{step}] {status}", flush=True)
    return entry


def run_cmd(step, db, command_doc, reading_ok, reading_err, **kw):
    """Run a database command; record response or error."""
    cmd_repr = f"db('{db.name}').command({json_util.dumps(command_doc)})"
    try:
        resp = db.command(command_doc, **kw)
        return record(step, cmd_repr, response=to_jsonable(resp), reading=reading_ok(resp), supported=True)
    except PyMongoError as e:
        info = err_info(e)
        return record(step, cmd_repr, error=info, reading=reading_err(info), supported=False)


def run_agg(step, coll, pipeline, reading_ok, reading_err, **kw):
    cmd_repr = f"db('{coll.database.name}').{coll.name}.aggregate({json_util.dumps(pipeline)})"
    try:
        docs = list(coll.aggregate(pipeline, **kw))
        return record(step, cmd_repr, response={"ok": 1, "documents": to_jsonable(docs)},
                      reading=reading_ok(docs), supported=True)
    except PyMongoError as e:
        info = err_info(e)
        return record(step, cmd_repr, error=info, reading=reading_err(info), supported=False)


def main():
    uri = load_uri()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    client = MongoClient(uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000,
                         socketTimeoutMS=240000)
    db = client[DB_NAME]
    admin = client.admin

    # --- 0. buildInfo and hello ---------------------------------------------------------
    bi = run_cmd("00-buildInfo", admin, {"buildInfo": 1},
                 lambda r: f"Gateway reports version {r.get('version')} (gitVersion {r.get('gitVersion')}); all later facts are about this engine/gateway build, not the managed service.",
                 lambda e: "buildInfo failed; cannot identify the engine build.")
    engine_version = (bi.get("response") or {}).get("version")
    run_cmd("00-hello", admin, {"hello": 1},
            lambda r: f"hello: maxWireVersion {r.get('maxWireVersion')}, saslSupportedMechs {r.get('saslSupportedMechs')}, isWritablePrimary {r.get('isWritablePrimary')}.",
            lambda e: "hello failed.")

    # --- 0b. extension versions via psql inside the container ---------------------------
    # The spec names role "postgres"; the image's superuser role is "documentdb" (the process
    # owner, uid 1000). Try the spec'd role first and fall back, recording both.
    ext_versions = {}

    def psql(step, role, sql, reading_ok):
        cmd = ["docker", "exec", CONTAINER, "psql", "-X", "-U", role, "-p", "9712", "-d", "postgres", "-tAc", sql]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            out = p.stdout.strip()
            ok = p.returncode == 0
            record(step, " ".join(cmd), response={"returncode": p.returncode, "stdout": out, "stderr": p.stderr.strip()},
                   reading=reading_ok(out) if ok else f"psql as role '{role}' failed: {p.stderr.strip()}", supported=ok)
            return ok, out
        except Exception as e:  # noqa
            record(step, " ".join(cmd), error={"exception": type(e).__name__, "message": str(e)},
                   reading="Could not run psql in the container.", supported=False)
            return False, ""

    ext_sql = "select extname, extversion from pg_extension where extname like 'documentdb%'"
    ok, out = psql("00-extension-version-postgres-role", "postgres", ext_sql,
                   lambda o: "pg_extension rows: " + o.replace("\n", "; "))
    if not ok:
        ok, out = psql("00-extension-version", "documentdb", ext_sql,
                       lambda o: "documentdb extension versions (role documentdb): " + o.replace("\n", "; "))
    if ok:
        ext_versions = dict(l.split("|", 1) for l in out.splitlines() if "|" in l)
    psql("00-all-extensions", "documentdb", "select extname, extversion from pg_extension order by 1",
         lambda o: "Every extension installed in the container's PostgreSQL: " + o.replace("\n", "; "))
    psql("00-pg-version", "documentdb", "select version()", lambda o: "PostgreSQL server: " + o)
    psql("00-access-methods", "documentdb", "select amname from pg_am order by 1",
         lambda o: "Index access methods available: " + o.replace("\n", ", ") + " (no diskann access method is installed).")

    # image identity
    insp = ["docker", "inspect", CONTAINER, "--format", "{{.Config.Image}} {{.Image}} {{index .Config.Labels \"org.opencontainers.image.version\"}}"]
    dig = ["docker", "image", "inspect", "ghcr.io/documentdb/documentdb/documentdb-local:latest", "--format", "{{.RepoDigests}}"]
    try:
        p1 = subprocess.run(insp, capture_output=True, text=True, timeout=60)
        p2 = subprocess.run(dig, capture_output=True, text=True, timeout=60)
        record("00-image-identity", " ; ".join([" ".join(insp), " ".join(dig)]),
               response={"inspect": p1.stdout.strip(), "repoDigests": p2.stdout.strip()},
               reading="Container image tag, image id, OCI version label and repo digest; the local ':latest' is whatever was pulled, not necessarily the current registry ':latest'.",
               supported=True)
    except Exception as e:  # noqa
        record("00-image-identity", " ".join(insp), error={"exception": type(e).__name__, "message": str(e)},
               reading="Could not inspect the image.", supported=False)

    # --- 1. fresh database with a few documents -----------------------------------------
    try:
        client.drop_database(DB_NAME)
        docs = [
            {"_id": 1, "title": "hello world", "body": "the quick brown fox", "v": [0.1, 0.2, 0.3]},
            {"_id": 2, "title": "goodbye world", "body": "lazy dogs sleep", "v": [0.3, 0.2, 0.1]},
            {"_id": 3, "title": "hello again", "body": "fox and hound", "v": [0.9, 0.1, 0.0]},
        ]
        r = db[COLL].insert_many(docs)
        record("01-seed", f"drop_database('{DB_NAME}'); db('{DB_NAME}').{COLL}.insert_many(<3 docs with title, body, v[3]>)",
               response={"inserted_ids": r.inserted_ids}, reading="Seeded three documents in t_parity.docs.", supported=True)
    except PyMongoError as e:
        record("01-seed", "insert_many", error=err_info(e), reading="Seeding failed.", supported=False)

    coll = db[COLL]

    # --- 2. createSearchIndexes (full-text) ---------------------------------------------
    csi = {"createSearchIndexes": COLL,
           "indexes": [{"name": "fts_default", "definition": {"mappings": {"dynamic": True}}}]}
    run_cmd("02-createSearchIndexes", db, csi,
            lambda r: "createSearchIndexes succeeded on the local engine.",
            lambda e: f"createSearchIndexes is refused by the local gateway: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # also the explicit-field form used by the Learn keyword page
    csi2 = {"createSearchIndexes": COLL,
            "indexes": [{"name": "fts_title", "definition": {"mappings": {"dynamic": False, "fields": {"title": {"type": "string"}}}}}]}
    run_cmd("02b-createSearchIndexes-static-mapping", db, csi2,
            lambda r: "Static-mapping createSearchIndexes succeeded.",
            lambda e: f"Static-mapping form is refused the same way: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 3. $search text query -----------------------------------------------------------
    search_pipe = [{"$search": {"index": "fts_default", "text": {"query": "hello", "path": "title"}}},
                   {"$project": {"title": 1}}]
    run_agg("03-search-text", coll, search_pipe,
            lambda d: f"$search text query returned {len(d)} documents.",
            lambda e: f"$search with a text operator is rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # $search without an index name (bare text operator)
    search_pipe2 = [{"$search": {"text": {"query": "fox", "path": "body"}}}]
    run_agg("03b-search-text-no-index", coll, search_pipe2,
            lambda d: f"$search text (no index) returned {len(d)} documents.",
            lambda e: f"$search text without index is rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 4. $listSearchIndexes -----------------------------------------------------------
    run_agg("04-listSearchIndexes", coll, [{"$listSearchIndexes": {}}],
            lambda d: f"$listSearchIndexes returned {len(d)} search indexes.",
            lambda e: f"$listSearchIndexes is rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 5. change stream: open, insert, read one event, 20 s timeout -------------------
    cs_cmd = f"db('{DB_NAME}').{COLL}.watch([]) ; then insert_one({{_id: 100, title: 'cs-probe'}}) in a thread ; stream.try_next() until one event or 20 s"
    try:
        stream = coll.watch([], max_await_time_ms=2000)
        opened = True
    except PyMongoError as e:
        opened = False
        record("05-changeStream-watch", cs_cmd, error=err_info(e),
               reading=f"collection.watch() fails at open: code {err_info(e).get('code')} {err_info(e).get('codeName')} '{err_info(e).get('errmsg')}'; no event could be read.",
               supported=False)
    if opened:
        ins_result = {}

        def do_insert():
            time.sleep(1.0)
            try:
                ins_result["inserted_id"] = coll.insert_one({"_id": 100, "title": "cs-probe"}).inserted_id
            except Exception as ex:  # noqa
                ins_result["error"] = str(ex)

        t = threading.Thread(target=do_insert, daemon=True)
        t.start()
        deadline = time.time() + 20
        event = None
        err = None
        try:
            while time.time() < deadline and event is None:
                event = stream.try_next()
        except PyMongoError as e:
            err = err_info(e)
        finally:
            try:
                stream.close()
            except Exception:
                pass
        t.join(timeout=5)
        if err:
            record("05-changeStream-watch", cs_cmd, error=err, response={"insert": to_jsonable(ins_result)},
                   reading=f"watch() opened but iterating failed: code {err.get('code')} {err.get('codeName')} '{err.get('errmsg')}'.", supported=False)
        elif event is None:
            record("05-changeStream-watch", cs_cmd, response={"event": None, "insert": to_jsonable(ins_result), "timeout_s": 20},
                   reading="watch() opened and the insert succeeded, but no change event arrived within 20 s.", supported=False)
        else:
            record("05-changeStream-watch", cs_cmd, response={"event": to_jsonable(event), "insert": to_jsonable(ins_result)},
                   reading=f"Change stream delivered an {event.get('operationType')} event.", supported=True)

    # raw aggregate with $changeStream too, so the exact server error is captured without driver wrapping
    run_agg("05b-aggregate-changeStream-raw", coll, [{"$changeStream": {}}],
            lambda d: "Raw $changeStream aggregate succeeded (cursor opened).",
            lambda e: f"Raw $changeStream aggregate rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 6. vector-diskann index ---------------------------------------------------------
    diskann = {"createIndexes": COLL, "indexes": [{"name": "v_diskann", "key": {"v": "cosmosSearch"},
               "cosmosSearchOptions": {"kind": "vector-diskann", "dimensions": 3, "similarity": "COS",
                                       "maxDegree": 32, "lBuild": 50}}]}
    run_cmd("06-vector-diskann", db, diskann,
            lambda r: "vector-diskann index created on the local engine.",
            lambda e: f"vector-diskann is rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # control: vector-hnsw, which DECISIONS says the OSS engine does register
    hnsw = {"createIndexes": COLL, "indexes": [{"name": "v_hnsw", "key": {"v": "cosmosSearch"},
            "cosmosSearchOptions": {"kind": "vector-hnsw", "dimensions": 3, "similarity": "COS", "m": 16, "efConstruction": 64}}]}
    run_cmd("06b-control-vector-hnsw", db, hnsw,
            lambda r: "Control: vector-hnsw index created, so the cosmosSearch index path itself works locally.",
            lambda e: f"Control vector-hnsw also failed: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 7. $rankFusion --------------------------------------------------------------
    rf = [{"$rankFusion": {"input": {"pipelines": {
              "byId": [{"$sort": {"_id": 1}}],
              "byTitle": [{"$sort": {"title": 1}}]}}}},
          {"$limit": 3}]
    run_agg("07-rankFusion", coll, rf,
            lambda d: f"$rankFusion returned {len(d)} documents.",
            lambda e: f"$rankFusion is rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 8. currentOp and serverStatus -------------------------------------------------
    run_cmd("08-currentOp", admin, {"currentOp": 1},
            lambda r: f"currentOp returned {len(r.get('inprog', []))} inprog entries.",
            lambda e: f"currentOp rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")
    # $currentOp must run on admin with aggregate:1; use raw command
    run_cmd("08b-aggregate-currentOp", admin, {"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
            lambda r: f"$currentOp aggregation returned {len(r.get('cursor', {}).get('firstBatch', []))} entries.",
            lambda e: f"$currentOp aggregation rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")
    run_cmd("09-serverStatus", admin, {"serverStatus": 1},
            lambda r: f"serverStatus returned top-level keys {sorted(r.keys())}.",
            lambda e: f"serverStatus rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")

    # --- 9. connectionStatus with showPrivileges ---------------------------------------
    run_cmd("10-connectionStatus-showPrivileges", admin, {"connectionStatus": 1, "showPrivileges": True},
            lambda r: f"connectionStatus returned authenticatedUsers {r.get('authInfo', {}).get('authenticatedUsers')}, roles {r.get('authInfo', {}).get('authenticatedUserRoles')}, {len(r.get('authInfo', {}).get('authenticatedUserPrivileges', []) or [])} privilege entries.",
            lambda e: f"connectionStatus showPrivileges rejected: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg')}'.")
    run_cmd("10b-connectionStatus-plain", admin, {"connectionStatus": 1},
            lambda r: f"Plain connectionStatus returned keys {sorted(r.get('authInfo', {}).keys())}.",
            lambda e: f"Plain connectionStatus rejected: code {e.get('code')} {e.get('codeName')}.")

    # --- listIndexes for the record ----------------------------------------------------
    run_cmd("11-listIndexes", db, {"listIndexes": COLL},
            lambda r: f"Indexes present at the end: {[i.get('name') for i in r.get('cursor', {}).get('firstBatch', [])]}.",
            lambda e: "listIndexes failed.")

    client.close()

    def find(step):
        return next((s for s in steps if s["step"] == step), {})

    def fmt(step):
        s = find(step)
        if s.get("supported"):
            return "supported"
        e = s.get("error", {})
        return f"not supported: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg') or e.get('message')}'"

    report = {
        "test": TEST_ID,
        "database": DB_NAME,
        "container": CONTAINER,
        "started_utc": started,
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "uri": redact(uri),
        "engine_version": engine_version,
        "extension_versions": ext_versions,
        "scope_note": ("Every fact here was observed on the documentdb-local container (open-source engine and gateway at the "
                       "buildInfo/pg_extension version above). It is evidence about the open-source engine and gateway only; "
                       "it does not prove how the managed Azure DocumentDB service behaves."),
        "summary": {
            "createSearchIndexes": fmt("02-createSearchIndexes"),
            "$search text": fmt("03-search-text"),
            "$listSearchIndexes": fmt("04-listSearchIndexes"),
            "collection.watch() change stream": fmt("05-changeStream-watch"),
            "vector-diskann index": fmt("06-vector-diskann"),
            "vector-hnsw index (control)": fmt("06b-control-vector-hnsw"),
            "$rankFusion": fmt("07-rankFusion"),
            "currentOp": fmt("08-currentOp"),
            "serverStatus": fmt("09-serverStatus"),
            "connectionStatus showPrivileges": fmt("10-connectionStatus-showPrivileges"),
        },
        "steps": steps,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
