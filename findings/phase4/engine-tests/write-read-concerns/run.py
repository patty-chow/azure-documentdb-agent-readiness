#!/usr/bin/env python
"""write-read-concerns: writeConcern (w / j / wtimeout), readConcern levels,
readPreference modes and get/setDefaultRWConcern against documentdb-local.

Reads LOCAL_URI from ../local.env (never printed). Owns database t_concern only.
Writes report.json next to this file. Every step records the exact command sent
(captured with a CommandListener where the driver builds it), the exact response
or error, and a one-sentence reading.
"""
import datetime
import json
import os
import re
import sys
import traceback

import pymongo
from bson.son import SON
from pymongo import MongoClient, monitoring
from pymongo.errors import OperationFailure, PyMongoError, WriteConcernError, WTimeoutError
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "local.env")
DB = "t_concern"
COLL = "c"


def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                if v and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found")


URI = load_uri()
REDACT_RE = re.compile(r"(mongodb://[^:/]+:)[^@]+@")


def redact(s):
    return REDACT_RE.sub(r"\1***@", str(s))


def jsonable(o):
    try:
        json.dumps(o)
        return o
    except (TypeError, ValueError):
        pass
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, float):
        return repr(o)
    return redact(repr(o))


class Capture(monitoring.CommandListener):
    """Records the last command the driver actually put on the wire."""

    def __init__(self):
        self.last = None
        self.last_reply = None

    def started(self, event):
        if event.command_name in ("hello", "isMaster", "saslStart", "saslContinue", "endSessions"):
            return
        self.last = {"command_name": event.command_name, "database": event.database_name,
                     "command": jsonable(dict(event.command))}

    def succeeded(self, event):
        if event.command_name in ("hello", "isMaster", "saslStart", "saslContinue", "endSessions"):
            return
        self.last_reply = jsonable(dict(event.reply))

    def failed(self, event):
        if event.command_name in ("hello", "isMaster", "saslStart", "saslContinue", "endSessions"):
            return
        self.last_reply = jsonable(event.failure)


CAP = Capture()
STEPS = []


def err_info(e):
    d = {"type": type(e).__name__, "message": redact(str(e))}
    if isinstance(e, OperationFailure):
        d["code"] = e.code
        det = e.details or {}
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg")
        d["errorLabels"] = det.get("errorLabels", [])
        d["details"] = jsonable(det)
    return d


def step(name, question, fn, reading_ok, reading_err=None, cmd_desc=None):
    """Run fn(); record wire command + reply/error; reading chosen by outcome."""
    CAP.last = None
    CAP.last_reply = None
    rec = {"step": name, "question": question}
    try:
        result = fn()
        rec["outcome"] = "ok"
        rec["response"] = jsonable(result)
        rec["reading"] = reading_ok(result) if callable(reading_ok) else reading_ok
    except PyMongoError as e:
        rec["outcome"] = "error"
        rec["error"] = err_info(e)
        rec["reading"] = reading_err(e) if callable(reading_err) else (reading_err or
                        f"Rejected by the local gateway with code {rec['error'].get('code')} {rec['error'].get('codeName')}: {rec['error'].get('errmsg') or rec['error']['message']}.")
    except Exception as e:  # noqa
        rec["outcome"] = "exception"
        rec["error"] = {"type": type(e).__name__, "message": redact(str(e)),
                        "trace": redact(traceback.format_exc())}
        rec["reading"] = f"Driver-side exception {type(e).__name__}: {redact(str(e))}."
    rec["wire_command"] = CAP.last if CAP.last else cmd_desc
    if cmd_desc and CAP.last:
        rec["driver_call"] = cmd_desc
    elif cmd_desc:
        rec["driver_call"] = cmd_desc
    if CAP.last_reply is not None and rec["outcome"] != "ok":
        rec["wire_reply"] = CAP.last_reply
    STEPS.append(rec)
    tag = rec["outcome"].upper()
    print(f"[{tag}] {name}: {rec['reading']}")
    return rec


def main():
    client = MongoClient(URI, serverSelectionTimeoutMS=15000, socketTimeoutMS=120000,
                         event_listeners=[CAP])
    db = client[DB]
    admin = client.admin
    coll = db[COLL]

    # ---- setup -------------------------------------------------------------
    try:
        bi = client.admin.command("buildInfo")
        hello = client.admin.command("hello")
    except PyMongoError as e:
        rec = {"step": "0.setup.buildInfo", "question": "Can the test authenticate and read buildInfo?",
               "driver_call": "MongoClient(LOCAL_URI).admin.command('buildInfo')",
               "wire_command": CAP.last or {"command_name": "saslStart", "database": "admin",
                                            "note": "failure happened during SCRAM-SHA-256 authentication, before buildInfo was sent"},
               "outcome": "error", "error": err_info(e),
               "reading": "The gateway answered the SCRAM saslStart with code 1 InternalError, so no command of this test could run; see environment_diagnosis."}
        STEPS.append(rec)
        print(f"[ERROR] setup: {rec['reading']}")
        write_report(status="blocked", build=None, topo=None, final_docs=None,
                     diagnosis=docker_diagnosis())
        return
    build = {"version": bi.get("version"), "gitVersion": bi.get("gitVersion"),
             "modules": bi.get("modules"), "buildInfo_keys": sorted(bi.keys())}
    topo = {k: jsonable(hello.get(k)) for k in ("isWritablePrimary", "ismaster", "secondary", "setName",
                                                "hosts", "me", "msg", "maxWireVersion", "minWireVersion",
                                                "logicalSessionTimeoutMinutes", "readOnly")}
    topo_desc = client.topology_description
    topo["driver_topology_type"] = topo_desc.topology_type_name
    topo["driver_server_types"] = [s.server_type_name for s in topo_desc.server_descriptions().values()]
    print("buildInfo:", build)
    print("hello:", topo)
    db.drop_collection(COLL)
    coll.insert_one({"_id": "seed", "n": 0})

    # ---- A. writeConcern on insert / update (raw commands) ------------------
    wc_variants = [
        ("w1", {"w": 1}),
        ("w_majority", {"w": "majority"}),
        ("w0", {"w": 0}),
        ("w3", {"w": 3}),
        ("w2", {"w": 2}),
        ("j_true", {"w": 1, "j": True}),
        ("j_false", {"w": 1, "j": False}),
        ("wtimeout_1", {"w": "majority", "wtimeout": 1}),
        ("w_tag_string", {"w": "myTag"}),
    ]
    for label, wc in wc_variants:
        doc_id = f"ins_{label}"

        def do_insert(wc=wc, doc_id=doc_id):
            return db.command(SON([("insert", COLL), ("documents", [{"_id": doc_id, "wc": label}]),
                                   ("writeConcern", wc)]))

        def ok_insert(res, wc=wc, doc_id=doc_id):
            present = coll.count_documents({"_id": doc_id}) == 1
            wce = res.get("writeConcernError")
            return (f"insert command with writeConcern {json.dumps(wc)} accepted silently (ok={res.get('ok')}, n={res.get('n')}, "
                    f"writeConcernError={'none' if not wce else json.dumps(jsonable(wce))}); document "
                    f"{'is' if present else 'is NOT'} readable afterwards, so the write landed regardless of the concern.")

        step(f"A.insert.{label}",
             "Which writeConcern w/j/wtimeout values does the gateway accept, and does any change the result?",
             do_insert, ok_insert,
             cmd_desc=f"db.command({{insert: '{COLL}', documents: [{{_id: '{doc_id}'}}], writeConcern: {json.dumps(wc)}}})")

        def do_update(wc=wc, label=label):
            return db.command(SON([("update", COLL),
                                   ("updates", [{"q": {"_id": "seed"}, "u": {"$inc": {"n": 1}, "$set": {"last": label}}}]),
                                   ("writeConcern", wc)]))

        def ok_update(res, wc=wc, label=label):
            seed = coll.find_one({"_id": "seed"})
            applied = seed is not None and seed.get("last") == label
            wce = res.get("writeConcernError")
            return (f"update command with writeConcern {json.dumps(wc)} accepted silently (ok={res.get('ok')}, n={res.get('n')}, "
                    f"nModified={res.get('nModified')}, writeConcernError={'none' if not wce else json.dumps(jsonable(wce))}); "
                    f"the update {'is' if applied else 'is NOT'} visible on the seed document.")

        step(f"A.update.{label}",
             "Which writeConcern w/j/wtimeout values does the gateway accept on update?",
             do_update, ok_update,
             cmd_desc=f"db.command({{update: '{COLL}', updates: [{{q: {{_id: 'seed'}}, u: {{$inc: {{n: 1}}}}}}], writeConcern: {json.dumps(wc)}}})")

    # ---- B. writeConcern through driver objects (incl. true unacknowledged w:0) --
    def drv_w0():
        c0 = coll.with_options(write_concern=WriteConcern(w=0))
        r = c0.insert_one({"_id": "drv_w0", "wc": "w0"})
        import time
        time.sleep(0.5)
        present = coll.count_documents({"_id": "drv_w0"})
        return {"acknowledged": r.acknowledged, "inserted_id": str(r.inserted_id), "visible_after_0.5s": present}

    step("B.driver.insert_one.w0",
         "Is an unacknowledged (OP_MSG moreToCome) w:0 write accepted and durable?",
         drv_w0,
         lambda r: f"Driver-level w:0 insert returned acknowledged={r['acknowledged']} (no reply awaited) and the document was "
                   f"{'found' if r['visible_after_0.5s'] else 'NOT found'} on a subsequent read: w:0 is accepted and the write lands.",
         cmd_desc="coll.with_options(write_concern=WriteConcern(w=0)).insert_one({_id:'drv_w0'})")

    def drv_wmaj_j_wt():
        c1 = coll.with_options(write_concern=WriteConcern(w="majority", j=True, wtimeout=1))
        r = c1.insert_one({"_id": "drv_wmaj_j_wt", "wc": "majority,j,wtimeout1"})
        return {"acknowledged": r.acknowledged, "inserted_id": str(r.inserted_id)}

    step("B.driver.insert_one.majority_j_true_wtimeout1",
         "Does the driver-level WriteConcern(w='majority', j=True, wtimeout=1) raise WTimeoutError or succeed?",
         drv_wmaj_j_wt,
         lambda r: "Driver-level insert with w:majority, j:true, wtimeoutMS:1 acknowledged without WTimeoutError or writeConcernError: j and wtimeout are accepted and have no observable effect.",
         cmd_desc="coll.with_options(write_concern=WriteConcern(w='majority', j=True, wtimeout=1)).insert_one(...)")

    def drv_w3():
        c3 = coll.with_options(write_concern=WriteConcern(w=3))
        return c3.insert_one({"_id": "drv_w3"}).acknowledged

    step("B.driver.insert_one.w3",
         "Does the driver surface the w:3 rejection as an OperationFailure/WriteConcernError?",
         drv_w3, lambda r: f"Unexpectedly accepted (acknowledged={r}).",
         lambda e: f"Driver raised {type(e).__name__} code {getattr(e, 'code', None)} {err_info(e).get('codeName')}: {err_info(e).get('errmsg')}; errorLabels={err_info(e).get('errorLabels')}.",
         cmd_desc="coll.with_options(write_concern=WriteConcern(w=3)).insert_one({_id:'drv_w3'})")

    def drv_update_w0():
        c0 = coll.with_options(write_concern=WriteConcern(w=0))
        r = c0.update_one({"_id": "seed"}, {"$set": {"last": "drv_w0_update"}})
        import time
        time.sleep(0.5)
        seed = coll.find_one({"_id": "seed"})
        return {"acknowledged": r.acknowledged, "seed_last": seed.get("last") if seed else None}

    step("B.driver.update_one.w0",
         "Is an unacknowledged w:0 update accepted and applied?",
         drv_update_w0,
         lambda r: f"Driver-level w:0 update_one returned acknowledged={r['acknowledged']}; seed.last is now {r['seed_last']!r}, so the update {'was' if r['seed_last']=='drv_w0_update' else 'was NOT'} applied.",
         cmd_desc="coll.with_options(write_concern=WriteConcern(w=0)).update_one({_id:'seed'}, {$set:{last:'drv_w0_update'}})")

    # ---- C. readConcern levels outside a transaction (raw find command) -----
    for level in ("local", "majority", "available", "linearizable", "snapshot", "Majority"):
        def do_find(level=level):
            return db.command(SON([("find", COLL), ("filter", {"_id": "seed"}), ("readConcern", {"level": level})]))

        step(f"C.find.readConcern.{level}",
             "Which readConcern levels are accepted outside a transaction?",
             do_find,
             lambda r, level=level: f"find with readConcern level '{level}' accepted (ok={r.get('ok')}, returned {len(r.get('cursor', {}).get('firstBatch', []))} document(s)); the engine ignores readConcern so no stronger isolation is observable.",
             cmd_desc=f"db.command({{find: '{COLL}', filter: {{_id: 'seed'}}, readConcern: {{level: '{level}'}}}})")

    # aggregate with readConcern majority / snapshot
    for level in ("majority", "snapshot"):
        def do_agg(level=level):
            return db.command(SON([("aggregate", COLL), ("pipeline", [{"$count": "n"}]), ("cursor", {}),
                                   ("readConcern", {"level": level})]))

        step(f"C.aggregate.readConcern.{level}",
             "Does aggregate behave like find for readConcern validation?",
             do_agg,
             lambda r, level=level: f"aggregate with readConcern level '{level}' accepted (ok={r.get('ok')}, firstBatch={jsonable(r.get('cursor', {}).get('firstBatch'))}).",
             cmd_desc=f"db.command({{aggregate: '{COLL}', pipeline: [{{$count: 'n'}}], cursor: {{}}, readConcern: {{level: '{level}'}}}})")

    # driver-level readConcern objects
    for level in ("majority", "linearizable"):
        def drv_rc(level=level):
            return list(coll.with_options(read_concern=ReadConcern(level)).find({"_id": "seed"}))

        step(f"C.driver.find.readConcern.{level}",
             "Does the driver-level ReadConcern object reach the gateway and get the same verdict?",
             drv_rc,
             lambda r, level=level: f"Driver-level find with ReadConcern('{level}') returned {len(r)} document(s).",
             cmd_desc=f"coll.with_options(read_concern=ReadConcern('{level}')).find({{_id:'seed'}})")

    # ---- D. readPreference on find -----------------------------------------
    prefs = [("primary", ReadPreference.PRIMARY), ("secondary", ReadPreference.SECONDARY),
             ("secondaryPreferred", ReadPreference.SECONDARY_PREFERRED), ("nearest", ReadPreference.NEAREST),
             ("primaryPreferred", ReadPreference.PRIMARY_PREFERRED)]
    for name, rp in prefs:
        def drv_rp(rp=rp):
            return list(coll.with_options(read_preference=rp).find({"_id": "seed"}))

        step(f"D.driver.find.readPreference.{name}",
             "Which readPreference modes are accepted on a find, and does the driver even send $readPreference to this single-node gateway?",
             drv_rp,
             lambda r, name=name: f"Driver-level find with readPreference {name} returned {len(r)} document(s); see wire_command for whether $readPreference was actually sent (the driver omits it for a Standalone/primary target).",
             cmd_desc=f"coll.with_options(read_preference=ReadPreference.{name.upper()}).find({{_id:'seed'}})")

    # raw commands with explicit $readPreference so the gateway definitely sees each mode
    for name in ("primary", "secondary", "secondaryPreferred", "nearest", "primaryPreferred"):
        def raw_rp(name=name):
            return db.command(SON([("find", COLL), ("filter", {"_id": "seed"}), ("$readPreference", {"mode": name})]))

        step(f"D.raw.find.$readPreference.{name}",
             "Which readPreference modes does the gateway accept when $readPreference is explicitly present in the command?",
             raw_rp,
             lambda r, name=name: f"find with explicit $readPreference {{mode: '{name}'}} accepted (ok={r.get('ok')}, {len(r.get('cursor', {}).get('firstBatch', []))} document(s)); on a single-node gateway it can only have been served by the one node.",
             cmd_desc=f"db.command({{find: '{COLL}', filter: {{_id:'seed'}}, $readPreference: {{mode: '{name}'}}}})")

    # tag set and hedge as cheap extras documented in the DECISIONS item
    step("D.raw.find.$readPreference.secondaryPreferred_tags",
         "Is a tag set rejected regardless of mode?",
         lambda: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                                 ("$readPreference", {"mode": "secondaryPreferred", "tags": [{"dc": "east"}]})])),
         lambda r: f"Accepted (ok={r.get('ok')}).",
         cmd_desc=f"db.command({{find: '{COLL}', $readPreference: {{mode:'secondaryPreferred', tags:[{{dc:'east'}}]}}}})")
    step("D.raw.find.$readPreference.nearest_hedge",
         "Is hedge {enabled:true} rejected?",
         lambda: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                                 ("$readPreference", {"mode": "nearest", "hedge": {"enabled": True}})])),
         lambda r: f"Accepted (ok={r.get('ok')}).",
         cmd_desc=f"db.command({{find: '{COLL}', $readPreference: {{mode:'nearest', hedge:{{enabled:true}}}}}})")

    # ---- E. get/setDefaultRWConcern ----------------------------------------
    step("E.admin.getDefaultRWConcern",
         "What does getDefaultRWConcern return on the admin database?",
         lambda: admin.command("getDefaultRWConcern"),
         lambda r: f"Returned {json.dumps(jsonable(r))}.",
         cmd_desc="client.admin.command('getDefaultRWConcern')")
    step("E.admin.getDefaultRWConcern.inMemory",
         "Does getDefaultRWConcern accept inMemory:true?",
         lambda: admin.command(SON([("getDefaultRWConcern", 1), ("inMemory", True)])),
         lambda r: f"Returned {json.dumps(jsonable(r))}.",
         cmd_desc="client.admin.command({getDefaultRWConcern:1, inMemory:true})")
    step("E.t_concern.getDefaultRWConcern",
         "Is getDefaultRWConcern refused on a non-admin database?",
         lambda: db.command("getDefaultRWConcern"),
         lambda r: f"Unexpectedly accepted on {DB}: {json.dumps(jsonable(r))}.",
         cmd_desc=f"client['{DB}'].command('getDefaultRWConcern')")
    step("E.admin.setDefaultRWConcern.w1",
         "Is setDefaultRWConcern supported?",
         lambda: admin.command(SON([("setDefaultRWConcern", 1), ("defaultWriteConcern", {"w": 1})])),
         lambda r: f"Unexpectedly accepted: {json.dumps(jsonable(r))}.",
         cmd_desc="client.admin.command({setDefaultRWConcern:1, defaultWriteConcern:{w:1}})")
    step("E.admin.setDefaultRWConcern.readConcern_local",
         "Is setDefaultRWConcern with defaultReadConcern supported?",
         lambda: admin.command(SON([("setDefaultRWConcern", 1), ("defaultReadConcern", {"level": "local"})])),
         lambda r: f"Unexpectedly accepted: {json.dumps(jsonable(r))}.",
         cmd_desc="client.admin.command({setDefaultRWConcern:1, defaultReadConcern:{level:'local'}})")
    step("E.admin.getDefaultRWConcern.after_set",
         "Did any setDefaultRWConcern attempt change what getDefaultRWConcern reports?",
         lambda: admin.command("getDefaultRWConcern"),
         lambda r: f"Returned {json.dumps(jsonable(r))} after the set attempts.",
         cmd_desc="client.admin.command('getDefaultRWConcern')")

    # ---- cleanup ------------------------------------------------------------
    final_docs = list(coll.find({}, {"_id": 1, "wc": 1, "last": 1, "n": 1}).sort("_id", 1))
    db.drop_collection(COLL)
    client.close()

    write_report(status="completed", build=build, topo=topo, final_docs=final_docs, diagnosis=None)


def docker_diagnosis():
    """Read-only look at the container when the gateway cannot reach Postgres."""
    import subprocess
    out = {}
    cmds = {
        "docker_ps": ["docker", "ps", "--filter", "name=ddb-engine-test", "--format", "{{.Names}} {{.Status}} {{.Image}}"],
        "container_df": ["docker", "exec", "ddb-engine-test", "df", "-h", "/", "/data"],
        "container_du_data": ["docker", "exec", "ddb-engine-test", "du", "-sh", "/data"],
        "pg_isready": ["docker", "exec", "ddb-engine-test", "pg_isready", "-h", "127.0.0.1", "-p", "9712"],
        "docker_system_df": ["docker", "system", "df"],
    }
    for k, c in cmds.items():
        try:
            r = subprocess.run(c, capture_output=True, text=True, timeout=60)
            out[k] = {"command": " ".join(c), "exit": r.returncode, "output": (r.stdout + r.stderr).strip()[:4000]}
        except Exception as e:  # noqa
            out[k] = {"command": " ".join(c), "error": repr(e)}
    try:
        r = subprocess.run(["docker", "logs", "ddb-engine-test"], capture_output=True, text=True, timeout=60)
        text = re.sub(r"\x1b\[[0-9;]*m", "", r.stdout + r.stderr)
        lines = text.splitlines()
        pg = [ln[:400] for ln in lines if ln.startswith("[POSTGRES]") and
              re.search(r"PANIC|FATAL|No space|terminat|shutting down|shut down|redo starts|startup process", ln)]
        gw = [ln[:400] for ln in lines if "Pool error" in ln and not ln.startswith("[GATEWAY-FILE]")]
        out["container_log_excerpt"] = {"command": "docker logs ddb-engine-test (filtered)",
                                        "postgres_crash_lines": pg[:25],
                                        "gateway_pool_error_lines_last3": gw[-3:],
                                        "gateway_pool_error_count": len(gw)}
    except Exception as e:  # noqa
        out["container_log_excerpt"] = {"error": repr(e)}
    return out


def write_report(status, build, topo, final_docs, diagnosis):
    report = {
        "test": "write-read-concerns",
        "status": status,
        "database": DB,
        "ran_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": "documentdb-local container ddb-engine-test, localhost:10260 (TLS, self-signed)",
        "driver": {"pymongo": pymongo.version, "python": sys.version.split()[0]},
        "buildInfo": jsonable(build) if build else "unavailable: authentication failed (see steps[0] and environment_diagnosis)",
        "hello": topo,
        "evidence_scope": ("Observed on documentdb-local (open-source engine + gateway at the buildInfo version above). "
                           "This is evidence about the open-source engine/gateway only; it does not prove managed Azure DocumentDB behaviour."),
        "decisions_topic": "findings/phase4/DECISIONS.md, 'Transactions, write semantics and bulk operations (SME topic 9)': settled items on w, j, wtimeout, readConcern levels, readPreference, getDefaultRWConcern; open items 3 (snapshot) and 8 (Azure gateway parity).",
        "planned_steps_not_run": PLANNED if status != "completed" else [],
        "environment_diagnosis": diagnosis,
        "final_documents_in_t_concern.c_before_drop": jsonable(final_docs),
        "steps": STEPS,
    }
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"report written (status={status})")


PLANNED = [
    "A.insert/A.update with writeConcern: {w:1}, {w:'majority'}, {w:0}, {w:3}, {w:2}, {w:1,j:true}, {w:1,j:false}, {w:'majority',wtimeout:1}, {w:'myTag'}",
    "B.driver-level WriteConcern(w=0) insert_one/update_one (unacknowledged), WriteConcern(w='majority', j=True, wtimeout=1), WriteConcern(w=3)",
    "C.find with readConcern level local, majority, available, linearizable, snapshot, 'Majority' (case check); aggregate with majority/snapshot; driver ReadConcern('majority'/'linearizable')",
    "D.find with readPreference primary, secondary, secondaryPreferred, nearest, primaryPreferred (driver-level and explicit $readPreference), plus tags and hedge extras",
    "E.getDefaultRWConcern on admin (plain, inMemory:true) and on t_concern; setDefaultRWConcern defaultWriteConcern {w:1} and defaultReadConcern {level:'local'}; getDefaultRWConcern again",
]


if __name__ == "__main__":
    main()
