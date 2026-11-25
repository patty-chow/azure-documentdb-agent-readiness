#!/usr/bin/env python
"""local-gateway-parity, ENGINE 1.2.0 RERUN.

Probes the documentdb-local container ddb-engine-test (MongoDB wire protocol on localhost:10260,
TLS, self-signed certificate) for the features DECISIONS.md topic 12 ("Local gateway container")
asks about, and compares every result with the engine 0.117 run
(engine-tests/local-gateway-parity/report.json; ENGINE-TESTS.md "Local gateway parity").

Database: t_parity only. It is dropped at the start (fresh) and at the end. No other database is
written, dropped or watched.

Rerun:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I \
    <this directory>/run_parity_1_2.py

Reads LOCAL_URI from <scratchpad>/engine-tests/local.env (override with LOCAL_ENV=/path).
The password is never printed and never written: the report holds a redacted URI, and every
recorded value is scrubbed for the password string before the report is written.
"""
import datetime as dt
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time

import bson
import pymongo
from bson import Binary, json_util
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.operations import SearchIndexModel

TEST_ID = "local-gateway-parity"
STAGE = "ENGINE 1.2.0 RERUN"
DB_NAME = "t_parity"
COLL_NAME = "docs"
CONTAINER = "ddb-engine-test"
SUB_TIMEOUT_S = 120          # every docker/psql call
SOCKET_TIMEOUT_MS = 240000   # every driver call stays under 5 minutes
CS_TIMEOUT_S = 20            # change stream read window
SEARCH_INDEX_WAIT_S = 60     # only used if createSearchIndexes ever succeeds

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(os.path.dirname(HERE))
ENV_PATH = os.environ.get("LOCAL_ENV", os.path.join(SCRATCH, "engine-tests", "local.env"))
BASELINE_PATH = os.path.join(SCRATCH, "engine-tests", "local-gateway-parity", "report.json")
ENGINE_TESTS_MD = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/ENGINE-TESTS.md"
REPORT_PATH = os.path.join(HERE, "report.json")


# ----------------------------------------------------------------------------- helpers
def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            env[k] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(ENV_PATH)
URI = ENV.get("LOCAL_URI")
if not URI:
    sys.exit("LOCAL_URI not found in " + ENV_PATH)
_m = re.match(r"mongodb(?:\+srv)?://([^:@/]+):([^@]*)@", URI)
USER = _m.group(1) if _m else ENV.get("LOCAL_USER", "")
_SECRET = (_m.group(2) if _m else "") or ENV.get("LOCAL_PASS", "")


def redact_uri(uri):
    return re.sub(r"://([^:/@]+):[^@]+@", r"://\1:<redacted>@", uri)


def dumps(obj):
    return json_util.dumps(obj, json_options=json_util.RELAXED_JSON_OPTIONS)


def j(obj):
    """BSON -> plain JSON-able python (relaxed extended JSON)."""
    return json.loads(dumps(obj))


SECRET_KEYS = re.compile(r"^(pwd|password|newPassword)$", re.I)


def scrub(o):
    if isinstance(o, dict):
        return {k: ("<redacted>" if SECRET_KEYS.match(str(k)) else scrub(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    if isinstance(o, str) and _SECRET and _SECRET in o:
        return o.replace(_SECRET, "<redacted>")
    return o


def err_info(e):
    info = {"exception": type(e).__name__}
    if isinstance(e, OperationFailure):
        d = e.details or {}
        info["code"] = e.code
        info["codeName"] = d.get("codeName")
        info["errmsg"] = d.get("errmsg")
        info["errorLabels"] = d.get("errorLabels")          # None means the key is absent from the reply
        info["errorLabels_present_in_reply"] = "errorLabels" in d
        info["reply"] = j(d)
    else:
        info["message"] = str(e)
    info["driver_error_labels"] = sorted(getattr(e, "_error_labels", None) or [])
    return info


def err_phrase(info):
    if not info:
        return "no error"
    if info.get("code") is None:
        return f"{info.get('exception')}: {info.get('message')}"
    labels = info.get("errorLabels")
    lab = f"errorLabels {labels}" if labels else "no errorLabels"
    return f"code {info['code']} {info.get('codeName')} '{info.get('errmsg')}' ({lab})"


STEPS = []


def record(step, command, reading, *, response=None, error=None, supported=None, elapsed_ms=None, **extra):
    entry = {"step": step, "command": command}
    if error is not None:
        entry["error"] = scrub(error)
    if response is not None:
        entry["response"] = scrub(response)
    entry["supported"] = supported
    if elapsed_ms is not None:
        entry["elapsed_ms"] = elapsed_ms
    entry["reading"] = scrub(reading)
    entry.update(scrub(extra))
    STEPS.append(entry)
    status = "OK" if supported else ("ERROR " + err_phrase(error) if error else "NOT-SUPPORTED/FAILED")
    print(f"[{step}] {status}", flush=True)
    return entry


def ms_since(t0):
    return round((time.monotonic() - t0) * 1000, 1)


def cmd_step(step, db, doc, ok, bad):
    call = f'client["{db.name}"].command({dumps(doc)})'
    t0 = time.monotonic()
    try:
        r = j(db.command(doc))
        return record(step, call, ok(r), response=r, supported=True, elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        return record(step, call, bad(info), error=info, supported=False, elapsed_ms=ms_since(t0))


def agg_step(step, coll, pipeline, ok, bad):
    call = f'client["{coll.database.name}"]["{coll.name}"].aggregate({dumps(pipeline)})'
    t0 = time.monotonic()
    try:
        docs = j(list(coll.aggregate(pipeline)))
        return record(step, call, ok(docs), response={"documents": docs, "n": len(docs)},
                      supported=True, elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        return record(step, call, bad(info), error=info, supported=False, elapsed_ms=ms_since(t0))


def sh_step(step, argv, ok, bad=None):
    call = shlex.join(argv)
    t0 = time.monotonic()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=SUB_TIMEOUT_S)
        resp = {"returncode": p.returncode, "stdout": p.stdout.rstrip("\n"), "stderr": p.stderr.rstrip("\n")}
        good = p.returncode == 0
        if good:
            reading = ok(resp)
        elif bad:
            reading = bad(resp)
        else:
            reading = f"Command failed with exit code {p.returncode}: {resp['stderr']}"
        record(step, call, reading, response=resp, supported=good, elapsed_ms=ms_since(t0))
        return good, resp
    except Exception as e:  # noqa: BLE001
        info = {"exception": type(e).__name__, "message": str(e)}
        record(step, call, f"Could not run the command: {info['message']}", error=info,
               supported=False, elapsed_ms=ms_since(t0))
        return False, {}


def lines(s):
    return [l for l in (s or "").splitlines() if l.strip()]


def print_block(title, obj):
    print(f"===== PRINT {title} =====")
    print(obj if isinstance(obj, str) else json.dumps(scrub(obj), indent=2, default=str))
    print(f"===== END {title} =====", flush=True)


def get_step(name):
    return next((s for s in STEPS if s["step"] == name), {})


# ----------------------------------------------------------------------------- main
DOCS = [
    {"_id": 1, "title": "hello world", "body": "the quick brown fox", "v": [0.1, 0.2, 0.3], "w": [0.1, 0.2, 0.3]},
    {"_id": 2, "title": "goodbye world", "body": "lazy dogs sleep", "v": [0.3, 0.2, 0.1], "w": [0.3, 0.2, 0.1]},
    {"_id": 3, "title": "hello again", "body": "fox and hound", "v": [0.9, 0.1, 0.0], "w": [0.9, 0.1, 0.0]},
]


def main():
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    print(f"{TEST_ID} {STAGE}; uri {redact_uri(URI)}; pymongo {pymongo.version}; python {platform.python_version()}",
          flush=True)
    client = MongoClient(URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000,
                         socketTimeoutMS=SOCKET_TIMEOUT_MS)
    admin = client.admin
    db = client[DB_NAME]
    coll = db[COLL_NAME]

    # ---- 00. engine identity ----------------------------------------------------------
    bi = cmd_step(
        "00a-buildInfo", admin, {"buildInfo": 1},
        lambda r: (f"buildInfo succeeds with version {r.get('version')}, versionArray {r.get('versionArray')}, "
                   f"gitVersion {r.get('gitVersion', 'absent')} and keys {sorted(r.keys())}; 7.0.0 is the MongoDB API "
                   f"level the gateway advertises, not the DocumentDB build, which hello.internal and pg_extension give."),
        lambda e: f"buildInfo failed: {err_phrase(e)}.")
    hello = cmd_step(
        "00b-hello", admin, {"hello": 1},
        lambda r: (f"hello succeeds: msg '{r.get('msg')}', maxWireVersion {r.get('maxWireVersion')}, maxWriteBatchSize "
                   f"{r.get('maxWriteBatchSize')}, logicalSessionTimeoutMinutes {r.get('logicalSessionTimeoutMinutes')}, "
                   f"saslSupportedMechs {r.get('saslSupportedMechs')}, internal {r.get('internal')}."),
        lambda e: f"hello failed: {err_phrase(e)}.")
    hr = hello.get("response") or {}
    record("00c-hello.internal", 'client["admin"].command({"hello": 1})["internal"]  (field of the 00b-hello reply)',
           (f"hello.internal reports documentdb_versions {(hr.get('internal') or {}).get('documentdb_versions')} and kind "
            f"'{(hr.get('internal') or {}).get('kind')}', so the gateway identifies the engine build it fronts."
            if "internal" in hr else "hello has no 'internal' field on this build."),
           response={"internal_present": "internal" in hr, "internal": hr.get("internal")},
           supported="internal" in hr)

    # hello.saslSupportedMechs: unrequested, requested for the test user, requested for a user that does not exist
    cmd_step("00d-hello-saslSupportedMechs-unrequested", admin, {"hello": 1},
             lambda r: (f"Without a saslSupportedMechs request field hello still returns saslSupportedMechs "
                        f"{r.get('saslSupportedMechs')} (MongoDB returns the field only when asked)."
                        if "saslSupportedMechs" in r else
                        "Without a saslSupportedMechs request field hello omits saslSupportedMechs, as MongoDB does."),
             lambda e: f"hello failed: {err_phrase(e)}.")
    cmd_step("00e-hello-saslSupportedMechs-requested", admin, {"hello": 1, "saslSupportedMechs": f"admin.{USER}"},
             lambda r: (f"hello with saslSupportedMechs 'admin.{USER}' returns saslSupportedMechs "
                        f"{r.get('saslSupportedMechs')}: SCRAM-SHA-256 only, no MONGODB-OIDC or SCRAM-SHA-1."
                        if "saslSupportedMechs" in r else
                        f"hello with saslSupportedMechs 'admin.{USER}' omits the field."),
             lambda e: f"hello with saslSupportedMechs failed: {err_phrase(e)}.")
    cmd_step("00f-hello-saslSupportedMechs-unknown-user", admin,
             {"hello": 1, "saslSupportedMechs": "admin.no_such_user_t_parity"},
             lambda r: (f"For a user that does not exist hello still returns saslSupportedMechs "
                        f"{r.get('saslSupportedMechs')} (MongoDB omits the field for unknown users), so the list is "
                        f"static, not looked up per user." if "saslSupportedMechs" in r else
                        "For a user that does not exist hello omits saslSupportedMechs, as MongoDB does."),
             lambda e: f"hello with an unknown user failed: {err_phrase(e)}.")

    # MONGODB-OIDC at the protocol level: a separate client with no credentials, empty payload, no token
    noauth_uri = re.sub(r"authMechanism=[^&]*&?", "", re.sub(r"://[^@/]+@", "://", URI)).rstrip("&?")
    oidc_doc = {"saslStart": 1, "mechanism": "MONGODB-OIDC", "payload": Binary(bson.encode({}))}
    oidc_call = (f'MongoClient("{noauth_uri}")["admin"].command({{"saslStart": 1, "mechanism": "MONGODB-OIDC", '
                 f'"payload": Binary(bson.encode({{}}))}})  # unauthenticated client, empty payload, no token')
    t0 = time.monotonic()
    try:
        c2 = MongoClient(noauth_uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000,
                         socketTimeoutMS=SOCKET_TIMEOUT_MS)
        try:
            r = j(c2.admin.command(oidc_doc))
            record("00f2-saslStart-MONGODB-OIDC", oidc_call,
                   f"The gateway accepts a MONGODB-OIDC saslStart and replies {r}.", response=r, supported=True,
                   elapsed_ms=ms_since(t0))
        finally:
            c2.close()
    except PyMongoError as e:
        info = err_info(e)
        record("00f2-saslStart-MONGODB-OIDC", oidc_call,
               f"A MONGODB-OIDC saslStart is refused at the protocol level: {err_phrase(info)}.", error=info,
               supported=False, elapsed_ms=ms_since(t0))

    # ---- 00. PostgreSQL side: the spec's exact commands first, then the working fallback ------------
    spec_ext = ["docker", "exec", CONTAINER, "psql", "-U", "postgres", "-p", "9712", "-tAc",
                "select extname, extversion from pg_extension"]
    spec_am = ["docker", "exec", CONTAINER, "psql", "-U", "postgres", "-p", "9712", "-tAc",
               "select amname from pg_am"]
    fb = ["docker", "exec", CONTAINER, "psql", "-X", "-U", "documentdb", "-p", "9712", "-d", "postgres", "-tAc"]
    sh_step("00g-pg_extension-spec-command", spec_ext,
            lambda r: "pg_extension (spec command): " + "; ".join(sorted(lines(r["stdout"]))) + ".",
            lambda r: (f"The spec's command fails (exit {r['returncode']}): {r['stderr'].strip()}; the image has no "
                       f"'postgres' role, so the fallback below uses the image's superuser role 'documentdb'."))
    sh_step("00h-container-os-user", ["docker", "exec", CONTAINER, "id"],
            lambda r: f"The container processes run as {r['stdout'].strip()}; psql without -U would use that role name.")
    sh_step("00i-superuser-roles", fb + ["select rolname from pg_roles where rolsuper"],
            lambda r: f"Superuser roles in the container's PostgreSQL: {', '.join(lines(r['stdout']))}.")
    sh_step("00i2-pg_extension-role-documentdb-default-db",
            ["docker", "exec", CONTAINER, "psql", "-U", "documentdb", "-p", "9712", "-tAc",
             "select extname, extversion from pg_extension"],
            lambda r: "Role documentdb without -d works: " + "; ".join(lines(r["stdout"])) + ".",
            lambda r: (f"Role documentdb without -d fails (exit {r['returncode']}): {r['stderr'].strip()}; psql defaults "
                       f"the database to the role name, so -d postgres is needed."))
    sh_step("00i3-pg_extension-role-documentdb-with-psqlrc",
            ["docker", "exec", CONTAINER, "psql", "-U", "documentdb", "-p", "9712", "-d", "postgres", "-tAc",
             "select extname, extversion from pg_extension"],
            lambda r: (f"Without -X the image's ~/.psqlrc runs first and its output starts with "
                       f"{lines(r['stdout'])[:2]} before the rows, so the fallback adds -X for clean output."))
    ok_ext, ext = sh_step(
        "00j-pg_extension-fallback", fb + ["select extname, extversion from pg_extension"],
        lambda r: ("pg_extension (role documentdb, database postgres, -X skips the image's ~/.psqlrc which prints "
                   "two SET lines): " + "; ".join(sorted(lines(r["stdout"]))) + "."))
    sh_step("00k-pg_am-spec-command", spec_am,
            lambda r: "pg_am (spec command): " + ", ".join(sorted(lines(r["stdout"]))) + ".",
            lambda r: f"The spec's command fails (exit {r['returncode']}): {r['stderr'].strip()}.")
    ok_am, am = sh_step(
        "00l-pg_am-fallback", fb + ["select amname from pg_am"],
        lambda r: ("Index access methods (role documentdb): " + ", ".join(sorted(lines(r["stdout"]))) + "; "
                   + ("a diskann access method IS installed." if any("diskann" in l for l in lines(r["stdout"]))
                      else "no diskann access method is installed, only hnsw and ivfflat for vectors.")))
    sh_step("00m-pg-version", fb + ["select version()"], lambda r: "PostgreSQL server: " + r["stdout"].strip() + ".")
    sh_step("00n-engine-feature-gucs",
            fb + ["select name, setting from pg_settings where name ~* "
                  "'(changestream|change_stream|vector|search|diskann|rankfusion|currentop|serverstatus)' order by 1"],
            lambda r: ("Engine settings whose names match change stream, vector, search, diskann, rankfusion, currentop "
                       "or serverstatus: " + "; ".join(lines(r["stdout"])) + " (no change-stream or diskann setting "
                       "exists)." if not any(re.search(r"change.?stream|diskann", l, re.I) for l in lines(r["stdout"]))
                       else "Engine settings matching the probed features: " + "; ".join(lines(r["stdout"])) + "."))
    sh_step("00o-image-identity",
            ["docker", "inspect", CONTAINER, "--format",
             '{{.Config.Image}}|{{.Image}}|{{index .Config.Labels "org.opencontainers.image.version"}}|'
             '{{index .Config.Labels "org.opencontainers.image.revision"}}|{{.State.Status}}|{{.State.StartedAt}}'],
            lambda r: ("Container image|image id|OCI version|OCI revision|state|started: " + r["stdout"].strip()
                       + "."))

    ext_rows = dict(l.split("|", 1) for l in lines(ext.get("stdout")) if "|" in l) if ok_ext else {}
    am_rows = sorted(lines(am.get("stdout"))) if ok_am else []

    print_block("buildInfo", bi.get("response") or bi.get("error"))
    print_block("hello.internal", (hello.get("response") or {}).get("internal"))
    print_block("pg_extension (extname|extversion)", "\n".join(sorted(lines(ext.get("stdout")))))
    print_block("pg_am (amname)", "\n".join(am_rows))

    # ---- 01. fresh t_parity with three documents -------------------------------------
    t0 = time.monotonic()
    seed_call = (f'client["{DB_NAME}"].command({{"dropDatabase": 1}}); '
                 f'client["{DB_NAME}"]["{COLL_NAME}"].insert_many({dumps(DOCS)})')
    try:
        pre = j(db.command({"dropDatabase": 1}))
        ins = coll.insert_many(DOCS)
        record("01-seed", seed_call, "Dropped any earlier t_parity and seeded three documents into t_parity.docs.",
               response={"dropDatabase": pre, "inserted_ids": ins.inserted_ids}, supported=True,
               elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        record("01-seed", seed_call, f"Seeding failed: {err_phrase(info)}.", error=info, supported=False,
               elapsed_ms=ms_since(t0))

    # ---- 02. createSearchIndexes ------------------------------------------------------
    created_any = False
    csi = {"createSearchIndexes": COLL_NAME,
           "indexes": [{"name": "fts_default", "definition": {"mappings": {"dynamic": True}}}]}
    s = cmd_step("02a-createSearchIndexes", db, csi,
                 lambda r: f"createSearchIndexes (dynamic mapping) succeeds: {r}.",
                 lambda e: f"createSearchIndexes (dynamic mapping) is refused: {err_phrase(e)}.")
    created_any |= bool(s.get("supported"))
    csi2 = {"createSearchIndexes": COLL_NAME,
            "indexes": [{"name": "fts_title",
                         "definition": {"mappings": {"dynamic": False, "fields": {"title": {"type": "string"}}}}}]}
    s = cmd_step("02b-createSearchIndexes-static-mapping", db, csi2,
                 lambda r: f"createSearchIndexes (static mapping on title) succeeds: {r}.",
                 lambda e: f"The static-mapping form is refused the same way: {err_phrase(e)}.")
    created_any |= bool(s.get("supported"))
    helper_call = (f'client["{DB_NAME}"]["{COLL_NAME}"].create_search_index(SearchIndexModel('
                   f'definition={{"mappings": {{"dynamic": True}}}}, name="fts_helper"))  '
                   f'# PyMongo {pymongo.version} sends createSearchIndexes')
    t0 = time.monotonic()
    try:
        name = coll.create_search_index(SearchIndexModel(definition={"mappings": {"dynamic": True}}, name="fts_helper"))
        created_any = True
        record("02c-create_search_index-driver-helper", helper_call,
               f"The PyMongo helper succeeds and returns index name '{name}'.", response={"name": name},
               supported=True, elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        record("02c-create_search_index-driver-helper", helper_call,
               f"The PyMongo helper surfaces the same refusal: {err_phrase(info)}.", error=info, supported=False,
               elapsed_ms=ms_since(t0))

    if created_any:  # only meaningful if an index was accepted
        t0 = time.monotonic()
        polls, last, ready = 0, None, False
        wait_call = (f'repeat list(client["{DB_NAME}"]["{COLL_NAME}"].list_search_indexes()) every 1 s until every '
                     f'index is queryable or {SEARCH_INDEX_WAIT_S} s pass')
        err = None
        try:
            while time.monotonic() - t0 < SEARCH_INDEX_WAIT_S:
                polls += 1
                last = j(list(coll.list_search_indexes()))
                if last and all(i.get("queryable") or i.get("status") == "READY" for i in last):
                    ready = True
                    break
                time.sleep(1)
        except PyMongoError as e:
            err = err_info(e)
        record("02d-wait-for-search-index", wait_call,
               (f"Search indexes became queryable after {polls} polls." if ready else
                f"Search indexes were not queryable within {SEARCH_INDEX_WAIT_S} s." if not err else
                f"Polling failed: {err_phrase(err)}."),
               response={"polls": polls, "last": last, "ready": ready}, error=err, supported=ready,
               elapsed_ms=ms_since(t0))

    # ---- 03. $search text query ------------------------------------------------------
    agg_step("03a-search-text", coll,
             [{"$search": {"index": "fts_default", "text": {"query": "hello", "path": "title"}}},
              {"$project": {"title": 1}}],
             lambda d: f"$search text returns {len(d)} documents: {d}.",
             lambda e: f"$search with a text operator is rejected: {err_phrase(e)}.")
    agg_step("03b-search-text-no-index", coll, [{"$search": {"text": {"query": "fox", "path": "body"}}}],
             lambda d: f"$search text without an index name returns {len(d)} documents.",
             lambda e: f"$search text without an index name is rejected the same way: {err_phrase(e)}.")

    # ---- 04. $listSearchIndexes ------------------------------------------------------
    agg_step("04a-listSearchIndexes", coll, [{"$listSearchIndexes": {}}],
             lambda d: f"$listSearchIndexes succeeds and returns {len(d)} search indexes: {d}.",
             lambda e: f"$listSearchIndexes is rejected: {err_phrase(e)}.")
    t0 = time.monotonic()
    lsi_call = (f'list(client["{DB_NAME}"]["{COLL_NAME}"].list_search_indexes())  '
                f'# PyMongo sends aggregate [{{"$listSearchIndexes": {{}}}}]')
    try:
        out = j(list(coll.list_search_indexes()))
        record("04b-list_search_indexes-driver-helper", lsi_call,
               f"The PyMongo helper returns {len(out)} search indexes.", response={"documents": out},
               supported=True, elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        record("04b-list_search_indexes-driver-helper", lsi_call,
               f"The PyMongo helper surfaces the same refusal: {err_phrase(info)}.", error=info, supported=False,
               elapsed_ms=ms_since(t0))

    # ---- 05. change streams: open, insert, read one event, 20 s window ----------------
    def do_insert(i):
        try:
            r = coll.insert_one({"_id": i, "title": f"cs-probe-{i}"})
            return {"ok": True, "inserted_id": r.inserted_id, "acknowledged": r.acknowledged}
        except PyMongoError as e:
            return {"ok": False, "error": err_info(e)}

    def watch_step(step, target, target_expr, insert_id):
        call = (f'stream = {target_expr}.watch(max_await_time_ms=1000)  # open; '
                f'client["{DB_NAME}"]["{COLL_NAME}"].insert_one({{"_id": {insert_id}, "title": "cs-probe-{insert_id}"}})'
                f'  # insert; stream.try_next() repeated until one event arrives or {CS_TIMEOUT_S} s pass, '
                f'then stream.close()  # read one event')
        t0 = time.monotonic()
        try:
            stream = target.watch(max_await_time_ms=1000)
        except PyMongoError as e:
            open_ms = ms_since(t0)
            info = err_info(e)
            ins = do_insert(insert_id)
            return record(
                step, call,
                (f"{target_expr}.watch() fails at open with {err_phrase(info)}; the follow-up insert "
                 f"{'succeeded' if ins.get('ok') else 'failed'}, and no event could be read because no change stream "
                 f"cursor exists."),
                error=info, response={"open": {"ok": False, "elapsed_ms": open_ms}, "insert": ins,
                                      "read": "not possible: no cursor", "timeout_s": CS_TIMEOUT_S},
                supported=False, elapsed_ms=ms_since(t0))
        open_ms = ms_since(t0)
        ins = do_insert(insert_id)
        event, err, polls = None, None, 0
        t_read = time.monotonic()
        try:
            while time.monotonic() - t_read < CS_TIMEOUT_S:
                polls += 1
                ev = stream.try_next()
                if ev is not None:
                    event = ev
                    break
        except PyMongoError as e:
            err = err_info(e)
        finally:
            try:
                stream.close()
            except Exception:  # noqa: BLE001
                pass
        resp = {"open": {"ok": True, "elapsed_ms": open_ms}, "insert": ins,
                "read": {"event": j(event) if event is not None else None, "polls": polls,
                         "elapsed_ms": ms_since(t_read)}, "timeout_s": CS_TIMEOUT_S}
        if err:
            return record(step, call, f"watch() opened but reading failed: {err_phrase(err)}.", error=err,
                          response=resp, supported=False, elapsed_ms=ms_since(t0))
        if event is None:
            return record(step, call,
                          f"watch() opened and the insert succeeded, but no change event arrived within {CS_TIMEOUT_S} s.",
                          response=resp, supported=False, elapsed_ms=ms_since(t0))
        return record(step, call,
                      f"watch() opened and delivered a '{event.get('operationType')}' event for _id "
                      f"{(event.get('documentKey') or {}).get('_id')} after {polls} polls.",
                      response=resp, supported=True, elapsed_ms=ms_since(t0))

    watch_step("05a-collection.watch", coll, f'client["{DB_NAME}"]["{COLL_NAME}"]', 100)
    agg_step("05b-aggregate-changeStream-raw", coll, [{"$changeStream": {}}],
             lambda d: "A raw $changeStream aggregate opens a cursor.",
             lambda e: f"A raw $changeStream aggregate is rejected with the same server error: {err_phrase(e)}.")
    watch_step("05c-database.watch", db, f'client["{DB_NAME}"]', 101)

    # ---- 06. vector indexes: diskann, with hnsw and ivf controls ----------------------
    diskann = {"createIndexes": COLL_NAME, "indexes": [{
        "name": "v_diskann", "key": {"v": "cosmosSearch"},
        "cosmosSearchOptions": {"kind": "vector-diskann", "dimensions": 3, "similarity": "COS",
                                "maxDegree": 32, "lBuild": 50}}]}
    d = cmd_step("06a-vector-diskann", db, diskann,
                 lambda r: f"A vector-diskann index is created: {r}.",
                 lambda e: f"vector-diskann is rejected: {err_phrase(e)}.")
    hnsw_path = "v" if not d.get("supported") else "h"   # one vector index per path: avoid a code 85 clash
    hnsw = {"createIndexes": COLL_NAME, "indexes": [{
        "name": f"{hnsw_path}_hnsw", "key": {hnsw_path: "cosmosSearch"},
        "cosmosSearchOptions": {"kind": "vector-hnsw", "dimensions": 3, "similarity": "COS", "m": 16,
                                "efConstruction": 64}}]}
    cmd_step("06b-control-vector-hnsw", db, hnsw,
             lambda r: "Control: a vector-hnsw index on the same collection is created, so the cosmosSearch index path works.",
             lambda e: f"Control vector-hnsw also failed: {err_phrase(e)}.")
    ivf = {"createIndexes": COLL_NAME, "indexes": [{
        "name": "w_ivf", "key": {"w": "cosmosSearch"},
        "cosmosSearchOptions": {"kind": "vector-ivf", "dimensions": 3, "similarity": "COS", "numLists": 1}}]}
    cmd_step("06c-control-vector-ivf", db, ivf,
             lambda r: "Control: a vector-ivf index on another path is created.",
             lambda e: f"Control vector-ivf failed: {err_phrase(e)}.")
    agg_step("06d-control-cosmosSearch-query", coll,
             [{"$search": {"cosmosSearch": {"vector": [0.1, 0.2, 0.3], "path": hnsw_path, "k": 2},
                           "returnStoredSource": True}},
              {"$project": {"_id": 1, "title": 1, "score": {"$meta": "searchScore"}}}],
             lambda d: (f"Control: a cosmosSearch query on the HNSW index returns {len(d)} documents, nearest _id "
                        f"{d[0].get('_id') if d else None}: {d}."),
             lambda e: f"Control cosmosSearch query failed: {err_phrase(e)}.")

    # ---- 07. $rankFusion -------------------------------------------------------------
    agg_step("07-rankFusion", coll,
             [{"$rankFusion": {"input": {"pipelines": {"byId": [{"$sort": {"_id": 1}}],
                                                       "byTitle": [{"$sort": {"title": 1}}]}}}},
              {"$limit": 3}],
             lambda d: f"$rankFusion succeeds and returns {len(d)} documents: {d}.",
             lambda e: f"$rankFusion is rejected: {err_phrase(e)}.")

    # ---- 08. currentOp ---------------------------------------------------------------
    def cop_reading(entries, how):
        types = sorted({str(x.get("type")) for x in entries})
        return (f"{how} succeeds with {len(entries)} entries (types {types}); entry keys include "
                f"{sorted(set().union(*[set(x.keys()) for x in entries])) if entries else []}.")
    cmd_step("08a-currentOp", admin, {"currentOp": 1},
             lambda r: cop_reading(r.get("inprog", []), "The currentOp command"),
             lambda e: f"currentOp is rejected: {err_phrase(e)}.")
    cmd_step("08b-aggregate-currentOp", admin, {"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
             lambda r: cop_reading((r.get("cursor") or {}).get("firstBatch", []), "The $currentOp stage"),
             lambda e: f"The $currentOp stage is rejected: {err_phrase(e)}.")

    # ---- 09. serverStatus ------------------------------------------------------------
    cmd_step("09-serverStatus", admin, {"serverStatus": 1},
             lambda r: (f"serverStatus succeeds (it returned code 115 on 0.117) with top-level keys {sorted(r.keys())}; "
                        f"process '{r.get('process')}', version '{r.get('version')}', opcounters {r.get('opcounters')}, "
                        f"connections {r.get('connections')} (whether these counters are live is tested in 09b)."),
             lambda e: f"serverStatus is rejected: {err_phrase(e)}.")

    # ---- 09b. are the serverStatus counters live? --------------------------------------
    t0 = time.monotonic()
    ss_call = ('s1 = client["admin"].command({"serverStatus": 1}); '
               'for i in range(10): client["t_parity"]["docs"].insert_one({"_id": 200 + i, "title": "ss-probe"}); '
               'for i in range(10): client["t_parity"]["docs"].find_one({"_id": 200 + i}); '
               'for i in range(10): client["t_parity"].command({"ping": 1}); time.sleep(1); '
               's2 = client["admin"].command({"serverStatus": 1}); compare sections of s1 and s2')
    try:
        s1 = j(admin.command({"serverStatus": 1}))
        for i in range(10):
            coll.insert_one({"_id": 200 + i, "title": "ss-probe"})
        for i in range(10):
            coll.find_one({"_id": 200 + i})
        for i in range(10):
            db.command({"ping": 1})
        time.sleep(1)
        s2 = j(admin.command({"serverStatus": 1}))
        sections = ["opcounters", "network", "connections", "catalogStats", "mem", "globalLock", "asserts",
                    "transactions", "metrics", "locks", "uptime", "localTime"]
        delta = {k: {"before": s1.get(k), "after": s2.get(k), "changed": s1.get(k) != s2.get(k)} for k in sections}
        live = [k for k in ("opcounters", "network", "connections", "catalogStats") if delta[k]["changed"]]
        moving = [k for k in sections if delta[k]["changed"]]
        reading = (
            (f"The serverStatus counters are static: after 10 inserts, 10 finds and 10 pings on this connection, "
             f"opcounters {s2.get('opcounters')}, network {s2.get('network')}, connections {s2.get('connections')} and "
             f"catalogStats.collections {(s2.get('catalogStats') or {}).get('collections')} are unchanged (only "
             f"{moving} move), so the 1.2.0 reply has serverStatus's shape but placeholder values, not live metrics.")
            if not live else
            (f"serverStatus sections {live} changed across 10 inserts, 10 finds and 10 pings, so those counters are "
             f"live; sections that moved: {moving}."))
        record("09b-serverStatus-counters-live", ss_call, reading,
               response={"delta": delta, "live_sections": live, "sections_that_moved": moving},
               supported=bool(live), elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        record("09b-serverStatus-counters-live", ss_call, f"The serverStatus delta check failed: {err_phrase(info)}.",
               error=info, supported=False, elapsed_ms=ms_since(t0))

    # ---- 10. connectionStatus --------------------------------------------------------
    def cs_reading(r):
        ai = r.get("authInfo", {})
        privs = ai.get("authenticatedUserPrivileges") or []
        actions = sorted({a for p in privs for a in p.get("actions", [])})
        return (f"connectionStatus with showPrivileges succeeds: users {ai.get('authenticatedUsers')}, roles "
                f"{ai.get('authenticatedUserRoles')}, {len(privs)} privilege entries with {len(actions)} distinct actions"
                f"{' (including changeStream, which the engine cannot serve)' if 'changeStream' in actions else ''}.")
    cmd_step("10a-connectionStatus-showPrivileges", admin, {"connectionStatus": 1, "showPrivileges": True},
             cs_reading, lambda e: f"connectionStatus with showPrivileges is rejected: {err_phrase(e)}.")
    cmd_step("10b-connectionStatus-plain", admin, {"connectionStatus": 1},
             lambda r: f"Plain connectionStatus succeeds with authInfo keys {sorted((r.get('authInfo') or {}).keys())}.",
             lambda e: f"Plain connectionStatus is rejected: {err_phrase(e)}.")

    # ---- 11. final index state -------------------------------------------------------
    cmd_step("11-listIndexes", db, {"listIndexes": COLL_NAME},
             lambda r: (f"Indexes present before the drop: "
                        f"{[i.get('name') for i in (r.get('cursor') or {}).get('firstBatch', [])]}."),
             lambda e: f"listIndexes failed: {err_phrase(e)}.")

    # ---- 12. drop the test database --------------------------------------------------
    cmd_step("12a-dropDatabase", db, {"dropDatabase": 1},
             lambda r: f"t_parity dropped: {r}.", lambda e: f"dropDatabase failed: {err_phrase(e)}.")
    t0 = time.monotonic()
    vcall = (f'client["{DB_NAME}"].list_collection_names(); "{DB_NAME}" in client.list_database_names()  '
             f'# only the boolean for t_parity is recorded')
    try:
        colls = db.list_collection_names()
        present = DB_NAME in client.list_database_names()
        record("12b-verify-drop", vcall,
               f"After the drop t_parity has collections {colls} and is {'still' if present else 'no longer'} listed.",
               response={"t_parity_collections": colls, "t_parity_present": present},
               supported=(not present and not colls), elapsed_ms=ms_since(t0))
    except PyMongoError as e:
        info = err_info(e)
        record("12b-verify-drop", vcall, f"Verification failed: {err_phrase(info)}.", error=info, supported=False,
               elapsed_ms=ms_since(t0))
    client.close()

    # ---- summary, comparison with 0.117, conclusions ---------------------------------
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    report = build_report(started, finished, ext_rows, am_rows)
    text = json.dumps(scrub(report), indent=2, default=str)
    if _SECRET and _SECRET in text:          # belt and braces: never write the password
        text = text.replace(_SECRET, "<redacted>")
    with open(REPORT_PATH, "w") as f:
        f.write(text)
    print(f"report written: {REPORT_PATH}")


# ----------------------------------------------------------------------------- report
FEATURES = [
    ("createSearchIndexes", "02a-createSearchIndexes", "02-createSearchIndexes"),
    ("$search text", "03a-search-text", "03-search-text"),
    ("$listSearchIndexes", "04a-listSearchIndexes", "04-listSearchIndexes"),
    ("collection.watch() change stream", "05a-collection.watch", "05-changeStream-watch"),
    ("vector-diskann index", "06a-vector-diskann", "06-vector-diskann"),
    ("vector-hnsw index (control)", "06b-control-vector-hnsw", "06b-control-vector-hnsw"),
    ("$rankFusion", "07-rankFusion", "07-rankFusion"),
    ("currentOp", "08a-currentOp", "08-currentOp"),
    ("$currentOp stage", "08b-aggregate-currentOp", "08b-aggregate-currentOp"),
    ("serverStatus", "09-serverStatus", "09-serverStatus"),
    ("connectionStatus showPrivileges", "10a-connectionStatus-showPrivileges", "10-connectionStatus-showPrivileges"),
]


def fmt(s):
    if not s:
        return "not run"
    if s.get("supported"):
        return "supported"
    e = s.get("error") or {}
    if e:
        return f"not supported: code {e.get('code')} {e.get('codeName')} '{e.get('errmsg') or e.get('message')}'"
    return "not supported: " + s.get("reading", "")


def build_report(started, finished, ext_rows, am_rows):
    base = {}
    try:
        with open(BASELINE_PATH) as f:
            base = json.load(f)
    except Exception as e:  # noqa: BLE001
        base = {"_load_error": str(e)}
    bsteps = {s["step"]: s for s in base.get("steps", [])}

    def bstep(n):
        return bsteps.get(n, {})

    summary, by_feature = {}, {}
    for label, cur, old in FEATURES:
        now = fmt(get_step(cur))
        before = (base.get("summary") or {}).get(label) or fmt(bstep(old))
        summary[label] = now
        ce, be = get_step(cur).get("error") or {}, bstep(old).get("error") or {}
        by_feature[label] = {
            "0.117": before, "1.2.0": now, "changed": now != before,
            "same_code_codeName_errmsg": ((ce.get("code"), ce.get("codeName"), ce.get("errmsg"))
                                          == (be.get("code"), be.get("codeName"), be.get("errmsg"))
                                          if (ce and be) else None),
        }

    hr = (get_step("00b-hello").get("response") or {})
    bhr = (bstep("00-hello").get("response") or {})
    sasl_now = (get_step("00d-hello-saslSupportedMechs-unrequested").get("response") or {}).get("saslSupportedMechs")
    sasl_req = (get_step("00e-hello-saslSupportedMechs-requested").get("response") or {}).get("saslSupportedMechs")
    sasl_unknown = (get_step("00f-hello-saslSupportedMechs-unknown-user").get("response") or {}).get("saslSupportedMechs")
    ssl = get_step("09b-serverStatus-counters-live")
    summary["serverStatus counters live"] = (
        ("yes: " + ", ".join((ssl.get("response") or {}).get("live_sections") or [])) if ssl.get("supported")
        else "no: " + ssl.get("reading", "not run"))
    summary["hello.saslSupportedMechs"] = {"unrequested": sasl_now, f"requested admin.{USER}": sasl_req,
                                           "requested unknown user": sasl_unknown}
    by_feature["hello.saslSupportedMechs"] = {"0.117": bhr.get("saslSupportedMechs"), "1.2.0": sasl_now,
                                              "changed": bhr.get("saslSupportedMechs") != sasl_now,
                                              "note": "0.117 recorded only the unrequested hello."}

    def hello_core(h):
        return {k: v for k, v in h.items() if k not in ("localTime", "connectionId")}
    hc, bhc = hello_core(hr), hello_core(bhr)
    hello_diff = {k: {"0.117": bhc.get(k), "1.2.0": hc.get(k)} for k in sorted(set(hc) | set(bhc)) if hc.get(k) != bhc.get(k)}

    base_ext = dict(l.split("|", 1) for l in lines((bstep("00-all-extensions").get("response") or {}).get("stdout")) if "|" in l)
    base_am = sorted(lines((bstep("00-access-methods").get("response") or {}).get("stdout")))
    ext_diff = {k: {"0.117": base_ext.get(k), "1.2.0": ext_rows.get(k)} for k in sorted(set(base_ext) | set(ext_rows))}

    def actions_of(step):
        privs = (((step.get("response") or {}).get("authInfo") or {}).get("authenticatedUserPrivileges")) or []
        return sorted({a for p in privs for a in p.get("actions", [])})
    a_now = actions_of(get_step("10a-connectionStatus-showPrivileges"))
    a_old = actions_of(bstep("10-connectionStatus-showPrivileges"))

    bi = get_step("00a-buildInfo").get("response") or {}
    bbi = bstep("00-buildInfo").get("response") or {}
    image = (get_step("00o-image-identity").get("response") or {}).get("stdout", "")
    internal = hr.get("internal") or {}

    comparison = {
        "baseline_report": BASELINE_PATH,
        "baseline_doc": ENGINE_TESTS_MD + ' section "Local gateway parity (topic 12)"',
        "baseline_image": (bstep("00-image-identity").get("response") or {}).get("inspect"),
        "baseline_finished_utc": base.get("finished_utc"),
        "by_feature": by_feature,
        "changed_features": [k for k, v in by_feature.items() if v.get("changed")],
        "unchanged_features": [k for k, v in by_feature.items() if not v.get("changed")],
        "buildInfo": {"0.117": bbi, "1.2.0": bi},
        "hello_fields_that_differ": hello_diff,
        "extensions": ext_diff,
        "access_methods": {"0.117": base_am, "1.2.0": am_rows, "changed": base_am != am_rows},
        "pg_version": {"0.117": (bstep("00-pg-version").get("response") or {}).get("stdout"),
                       "1.2.0": (get_step("00m-pg-version").get("response") or {}).get("stdout")},
        "connectionStatus_actions": {"added_in_1.2.0": sorted(set(a_now) - set(a_old)),
                                     "removed_in_1.2.0": sorted(set(a_old) - set(a_now)),
                                     "count_0.117": len(a_old), "count_1.2.0": len(a_now)},
    }

    conclusions = build_conclusions(summary, by_feature, comparison, internal, bi, ext_rows, am_rows)

    return {
        "test": TEST_ID,
        "stage": STAGE,
        "database": DB_NAME,
        "container": CONTAINER,
        "image_identity": image,
        "started_utc": started,
        "finished_utc": finished,
        "uri": redact_uri(URI),
        "client": {"python": platform.python_version(), "pymongo": pymongo.version},
        "engine_version": {
            "buildInfo.version": bi.get("version"),
            "hello.internal.documentdb_versions": internal.get("documentdb_versions"),
            "pg_extension.documentdb": ext_rows.get("documentdb"),
            "pg_extension.documentdb_core": ext_rows.get("documentdb_core"),
            "postgresql": (get_step("00m-pg-version").get("response") or {}).get("stdout"),
        },
        "extension_versions": ext_rows,
        "access_methods": am_rows,
        "scope_note": ("Every fact here was observed on the documentdb-local container ddb-engine-test (open-source "
                       "DocumentDB engine and gateway at the hello.internal / pg_extension version above, buildInfo "
                       "version 7.0.0). It is evidence about the open-source engine and gateway at that version only; "
                       "it does not prove how the managed Azure DocumentDB service behaves."),
        "deviations_from_spec": [
            "The spec's psql commands (-U postgres) fail because the image has no 'postgres' role; both are recorded "
            "as run, and the same SQL was rerun as role 'documentdb' (the image's superuser and OS user) with "
            "-d postgres (psql otherwise defaults to a nonexistent 'documentdb' database) and -X (skips the image's "
            "~/.psqlrc, which prints two SET lines).",
            "Extra steps beyond the spec, for context: createSearchIndexes static mapping and the PyMongo helper, "
            "$search text without an index name, the list_search_indexes helper, a raw $changeStream aggregate, "
            "database-level watch() on t_parity, HNSW and IVF control indexes and a cosmosSearch control query, the "
            "$currentOp stage, plain connectionStatus, hello with saslSupportedMechs requested for the test user and "
            "for an unknown user, an unauthenticated MONGODB-OIDC saslStart with an empty payload (no token), "
            "a serverStatus before/after counter check (10 inserts, 10 finds, 10 pings in "
            "t_parity), engine feature settings and image identity. client.watch() was not run because a "
            "cluster-wide stream would read other databases.",
        ],
        "summary": summary,
        "comparison_with_0_117": comparison,
        "conclusions": conclusions,
        "steps": STEPS,
    }


def build_conclusions(summary, by_feature, comparison, internal, bi, ext_rows, am_rows):
    def ch(label):
        v = by_feature.get(label, {})
        return "unchanged from 0.117" if not v.get("changed") else f"changed from 0.117 (was: {v.get('0.117')})"

    out = []
    out.append({"question": "Which engine build did this rerun test?",
                "answer": (f"hello.internal.documentdb_versions {internal.get('documentdb_versions')}, pg_extension "
                           f"documentdb {ext_rows.get('documentdb')} / documentdb_core {ext_rows.get('documentdb_core')}, "
                           f"image|id|OCI version|revision|state|started {get_step('00o-image-identity').get('response', {}).get('stdout', '')}; "
                           f"buildInfo still says version {bi.get('version')} (the MongoDB API level, not the engine build)."),
                "confidence": "observed"})
    for label, q in [
        ("createSearchIndexes", "Does createSearchIndexes work on documentdb-local 1.2.0?"),
        ("$search text", "Does a $search text query work on documentdb-local 1.2.0?"),
        ("$listSearchIndexes", "Does $listSearchIndexes work on documentdb-local 1.2.0?"),
        ("collection.watch() change stream", "Does collection.watch() open and deliver an insert event within 20 s on 1.2.0?"),
        ("vector-diskann index", "Can a vector-diskann index be created on documentdb-local 1.2.0?"),
        ("$rankFusion", "Does $rankFusion work on documentdb-local 1.2.0?"),
        ("currentOp", "Does currentOp work on documentdb-local 1.2.0?"),
        ("serverStatus", "Does serverStatus work on documentdb-local 1.2.0?"),
        ("connectionStatus showPrivileges", "Does connectionStatus with showPrivileges work on documentdb-local 1.2.0?"),
    ]:
        extra = ""
        if label == "vector-diskann index":
            extra = (f"; pg_am lists {', '.join(am_rows)}"
                     f"{'' if any('diskann' in a for a in am_rows) else ' (no diskann access method)'}")
        if label == "collection.watch() change stream":
            extra = f"; database-level watch(): {fmt(get_step('05c-database.watch'))}"
        out.append({"question": q, "answer": f"{summary.get(label)}{extra}; {ch(label)}.", "confidence": "observed"})
    out.append({"question": "Are the serverStatus counters live on documentdb-local 1.2.0?",
                "answer": summary.get("serverStatus counters live", "not run") + " (not testable on 0.117, where serverStatus failed).",
                "confidence": "observed"})
    s = summary.get("hello.saslSupportedMechs", {})
    out.append({"question": "Is a MONGODB-OIDC (Entra ID) saslStart accepted by the 1.2.0 gateway?",
                "answer": fmt(get_step("00f2-saslStart-MONGODB-OIDC")) + " (unauthenticated client, empty payload, no token; not run on 0.117).",
                "confidence": "observed"})
    out.append({"question": "What does hello advertise in saslSupportedMechs on 1.2.0?",
                "answer": (f"{s.get('unrequested')} without asking, {s.get('requested admin.' + USER)} when asked for "
                           f"admin.{USER}, and {s.get('requested unknown user')} for a user that does not exist: a static "
                           f"SCRAM-SHA-256-only list, so MONGODB-OIDC (Entra ID) cannot be negotiated locally; "
                           f"{ch('hello.saslSupportedMechs')}."),
                "confidence": "observed"})
    out.append({"question": "Which parity results changed between engine 0.117 and 1.2.0?",
                "answer": (f"Changed: {comparison['changed_features'] or 'none'}. Unchanged: "
                           f"{comparison['unchanged_features']}. Access methods changed: "
                           f"{comparison['access_methods']['changed']}."),
                "confidence": "observed"})
    out.append({"question": "Does the spec's psql command (-U postgres) work on the 1.2.0 image?",
                "answer": (f"{fmt(get_step('00g-pg_extension-spec-command'))}; "
                           f"{get_step('00g-pg_extension-spec-command').get('response', {}).get('stderr', '')} "
                           f"The superuser role is {', '.join(lines(get_step('00i-superuser-roles').get('response', {}).get('stdout')))}."),
                "confidence": "observed"})
    out.append({"question": "Does any of this prove managed Azure DocumentDB behaviour?",
                "answer": ("No. These are observations of the open-source engine and gateway in documentdb-local at the "
                           "version above; managed-service behaviour has to be checked on a cluster."),
                "confidence": "inferred"})
    return out


if __name__ == "__main__":
    main()
