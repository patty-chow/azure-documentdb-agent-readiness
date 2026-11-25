#!/usr/bin/env python
"""Extra probes for the write-read-concerns reproduce stage, beyond the tester's run.py, against the
documentdb-local container ddb-engine-test (open-source DocumentDB engine + gateway, image pg17-1.2.0).

Rerun: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I extra_probes.py

Owns database t_concern_rerun only: it is recreated here and dropped at the end (transaction control
commands commitTransaction/abortTransaction go to admin by protocol; getDefaultRWConcern is admin-only by
definition and is read-only). Container inspection is read-only: grep over the gateway binary and the
extension .so, and one SELECT on pg_settings / pg_file_settings inside a read-only transaction.
LOCAL_URI is read from ../../engine-tests/local.env and is never printed or written.

"main_branch_expectation" quotes the local copies of the main-branch gateway source that the DECISIONS.md
research saved (scratchpad/phase4/sme/engine-src/{write_concern,read_concern,read_preference,validation}.rs,
fetched 2026-11-25). Those files are data and are never executed. Writes extra.json.
"""
import datetime, json, os, re, subprocess, sys, time, traceback

from bson import Timestamp, json_util
from bson.son import SON
from pymongo import MongoClient, monitoring
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.uri_parser import parse_uri
from pymongo.write_concern import WriteConcern

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.normpath(os.path.join(HERE, "..", "..", "engine-tests", "local.env"))
OUT = os.path.join(HERE, "extra.json")
DB = "t_concern_rerun"
COLL = "c"
CONTAINER = "ddb-engine-test"
GW_BIN = "/home/documentdb/gateway/pg_documentdb_gw/target/release-with-symbols/documentdb_gateway"
PSQL = "/usr/lib/postgresql/17/bin/psql"


def load_uri():
    for line in open(ENV):
        line = line.strip()
        if line.startswith("LOCAL_URI="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("LOCAL_URI not found")


URI = load_uri()
_PW = parse_uri(URI).get("password") or ""


def scrub(s):
    s = re.sub(r"(mongodb(?:\+srv)?://[^:/@]+:)[^@]+@", r"\1***@", str(s))
    if _PW and len(_PW) >= 4:
        s = s.replace(_PW, "***")
    return s


def ej(o):
    try:
        return json.loads(scrub(json_util.dumps(o, json_options=json_util.RELAXED_JSON_OPTIONS)))
    except Exception:  # noqa: BLE001
        return scrub(repr(o))


IGNORED = {"hello", "ismaster", "isMaster", "saslStart", "saslContinue", "authenticate", "endSessions"}


class Capture(monitoring.CommandListener):
    def __init__(self):
        self.armed, self.events, self.tag = False, [], "probe_client"

    def start(self):
        self.events, self.armed = [], True

    def stop(self):
        self.armed = False
        ev, self.events = self.events, []
        return ev

    def _w(self, n):
        return self.armed and n not in IGNORED

    def started(self, e):
        if self._w(e.command_name):
            self.events.append({"event": "CommandStarted", "command_name": e.command_name, "database": e.database_name,
                                "server_connection_id": e.server_connection_id, "command": ej(dict(e.command))})

    def succeeded(self, e):
        if self._w(e.command_name):
            self.events.append({"event": "CommandSucceeded", "command_name": e.command_name,
                                "server_connection_id": e.server_connection_id, "reply": ej(dict(e.reply))})

    def failed(self, e):
        if self._w(e.command_name):
            self.events.append({"event": "CommandFailed", "command_name": e.command_name,
                                "server_connection_id": e.server_connection_id, "failure": ej(dict(e.failure))})


class PoolEvents(monitoring.ConnectionPoolListener):
    def __init__(self):
        self.reset()

    def reset(self):
        self.created, self.closed, self.reasons = 0, 0, []

    def snapshot(self):
        return {"connections_created": self.created, "connections_closed": self.closed, "closed_reasons": list(self.reasons)}

    def pool_created(self, e): pass
    def pool_ready(self, e): pass
    def pool_cleared(self, e): pass
    def pool_closed(self, e): pass
    def connection_created(self, e): self.created += 1
    def connection_ready(self, e): pass
    def connection_closed(self, e): self.closed += 1; self.reasons.append(str(e.reason))
    def connection_check_out_started(self, e): pass
    def connection_check_out_failed(self, e): pass
    def connection_checked_out(self, e): pass
    def connection_checked_in(self, e): pass


CAP = Capture()
STEPS = []
CODES = {"BadValue": 2, "FailedToParse": 9, "TypeMismatch": 14, "IllegalOperation": 20, "InvalidOptions": 72,
         "CommandNotSupported": 115, "FailedToSatisfyReadPreference": 133, "UnknownBsonField": 40415}


def err_info(e):
    d = {"type": type(e).__name__, "message": scrub(str(e))}
    if isinstance(e, OperationFailure):
        det = e.details or {}
        d.update({"code": e.code, "codeName": det.get("codeName"), "errmsg": det.get("errmsg"),
                  "errorLabels": det.get("errorLabels"), "details": ej(det)})
    return d


def ACC(src):
    return {"outcome": "accepted", "source": src}


def REJ(code_name, contains=None, src=None):
    d = {"outcome": "rejected", "codeName": code_name, "source": src}
    if contains:
        d["errmsg_contains"] = contains
    return d


NOCLAIM = {"outcome": None}


def compare(rec, exp):
    if not exp or exp.get("outcome") is None:
        return "no main-branch claim"
    if rec["outcome"] == "exception":
        return "not comparable (exception)"
    if exp["outcome"] == "accepted":
        return "same as main" if rec["outcome"] == "ok" else "differs from main (rejected; main accepts)"
    if rec["outcome"] != "error":
        return "differs from main (accepted; main rejects)"
    e, probs = rec["error"], []
    if exp.get("codeName") and e.get("codeName") != exp["codeName"] and e.get("code") != CODES.get(exp["codeName"]):
        probs.append(f"got {e.get('code')} {e.get('codeName')}, main gives {exp['codeName']}")
    if exp.get("errmsg_contains") and exp["errmsg_contains"] not in (e.get("errmsg") or ""):
        probs.append(f"errmsg lacks {exp['errmsg_contains']!r}")
    return "same as main" if not probs else "differs from main: " + "; ".join(probs)


def fmt_err(rec):
    e = rec["error"]
    if e.get("code") is None:
        return f"{e['type']}: {e['message']}"
    lab = "no errorLabels field" if e.get("errorLabels") is None else f"errorLabels {json.dumps(e['errorLabels'])}"
    return f"code {e['code']} {e.get('codeName')} \"{e.get('errmsg')}\" ({lab})"


def run_step(sid, *, group, question, call, fn, expect=None, post=None, read=None):
    CAP.start()
    rec = {"id": sid, "group": group, "question": question, "driver_call": call}
    res = None
    try:
        res = fn()
        rec["outcome"], rec["response"] = "ok", ej(res)
    except PyMongoError as e:
        rec["outcome"], rec["error"] = "error", err_info(e)
    except Exception as e:  # noqa: BLE001
        rec["outcome"] = "exception"
        rec["error"] = {"type": type(e).__name__, "message": scrub(str(e)), "trace": scrub(traceback.format_exc())}
    rec["wire"] = CAP.stop()
    if post:
        try:
            rec["observed_after"] = ej(post(rec, res))
        except Exception as e:  # noqa: BLE001
            rec["observed_after"] = {"post_check_exception": scrub(f"{type(e).__name__}: {e}")}
    if expect is not None:
        rec["main_branch_expectation"] = expect
        rec["vs_main_branch_source"] = compare(rec, expect)
    try:
        rec["reading"] = read(rec) if read else default_read(rec)
    except Exception as e:  # noqa: BLE001
        rec["reading"] = f"reading generator failed: {type(e).__name__}: {e}"
    STEPS.append(rec)
    print(f"[{rec['outcome']:>9}] {sid}: {rec['reading']}", flush=True)
    return rec


def first_reply(rec, name=None):
    for ev in rec["wire"]:
        if ev["event"] in ("CommandSucceeded", "CommandFailed") and (name is None or ev["command_name"] == name):
            return ev.get("reply") or ev.get("failure")
    return None


def default_read(rec):
    vs = rec.get("vs_main_branch_source")
    tail = f" ({vs})" if vs else ""
    if rec["outcome"] == "ok":
        return f"Accepted with reply {json.dumps(first_reply(rec))}{tail}."
    return f"Rejected with {fmt_err(rec)}{tail}."


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    client = MongoClient(URI, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000, event_listeners=[CAP])
    other = MongoClient(URI, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000)  # concurrent writer, not captured
    db, coll = client[DB], client[DB][COLL]
    hello = client.admin.command("hello")
    engine = {"hello.internal.documentdb_versions": ej((hello.get("internal") or {}).get("documentdb_versions")),
              "hello.maxWriteBatchSize": hello.get("maxWriteBatchSize"),
              "hello.has_operationTime": "operationTime" in hello, "hello.has_$clusterTime": "$clusterTime" in hello}
    pre = DB in client.list_database_names()
    if pre:
        client.drop_database(DB)
    seed = ([{"_id": "read_target", "v": 1}, {"_id": "fam_target", "n": 0}, {"_id": "snap_doc", "v": 1}]
            + [{"_id": f"del_target_{i}"} for i in range(1, 4)]
            + [{"_id": f"cur_{i}", "grp": "cur", "v": 1} for i in range(6)])
    run_step("XS.seed", group="setup", question="Recreate t_concern_rerun.c with the probe targets.",
             call=f"client['{DB}']['{COLL}'].insert_many(<{len(seed)} seed documents>)",
             fn=lambda: {"inserted": len(coll.insert_many([dict(d) for d in seed]).inserted_ids)},
             read=lambda r: f"Seeded {len(seed)} documents (outcome {r['outcome']}); database existed before: {pre}.")

    def present(i):
        return other[DB][COLL].count_documents({"_id": i}) == 1

    # ------------------------------------------------------------ XW: writeConcern validation depth (raw insert)
    WSRC = "main-branch write_concern.rs validate() doc comment (local copy, fetched 2026-11-25)"
    OMIT = object()
    xw = [
        ("wc_string", "notADocument", REJ("TypeMismatch", "writeConcern must be a document", WSRC)),
        ("wc_int", 1, REJ("TypeMismatch", "writeConcern must be a document", WSRC)),
        ("wc_empty_doc", {}, ACC(WSRC)),
        ("wc_null", None, ACC(WSRC)),
        ("w_minus1", {"w": -1}, REJ("FailedToParse", None, WSRC)),
        ("w_51", {"w": 51}, REJ("FailedToParse", None, WSRC)),
        ("w_50", {"w": 50}, REJ("BadValue", None, WSRC)),
        ("w_nan", {"w": float("nan")}, REJ("FailedToParse", None, WSRC)),
        ("w_bool", {"w": True}, REJ("FailedToParse", None, WSRC)),
        ("w_array", {"w": [1]}, REJ("FailedToParse", None, WSRC)),
        ("w_null", {"w": None}, REJ("BadValue", None, WSRC)),
        ("w_empty_tag_set", {"w": {}}, REJ("FailedToParse", None, WSRC)),
        ("w_tag_set_string_value", {"w": {"dc": "east"}}, REJ("FailedToParse", None, WSRC)),
        ("j_string", {"j": "yes"}, REJ("TypeMismatch", None, WSRC)),
        ("fsync_string", {"fsync": "yes"}, REJ("TypeMismatch", None, WSRC)),
        ("provenance_bogus", {"w": 1, "provenance": "bogus"}, REJ("BadValue", None, WSRC)),
        ("provenance_int", {"w": 1, "provenance": 5}, REJ("TypeMismatch", None, WSRC)),
        ("wtimeout_negative", {"w": 1, "wtimeout": -5}, ACC(WSRC)),
        ("wtimeout_string", {"w": 1, "wtimeout": "abc"}, ACC(WSRC)),
        ("unknown_subfield_foo", {"w": 1, "foo": 1}, REJ("UnknownBsonField", "is an unknown field", WSRC)),
    ]
    for label, wc, exp in xw:
        doc_id = f"xw_ins_{label}"

        def ins(wc=wc, doc_id=doc_id):
            return db.command(SON([("insert", COLL), ("documents", [{"_id": doc_id}]), ("writeConcern", wc)]))

        def rd(rec, label=label):
            landed = (rec.get("observed_after") or {}).get("document_present")
            base = default_read(rec).rstrip(".")
            return f"{base}; the document {'was' if landed else 'was NOT'} written."

        run_step(f"XW.raw.insert.{label}", group="XW writeConcern validation depth (raw insert command body)",
                 question=f"Is writeConcern {json.dumps(ej(wc))} accepted on insert, and does the write land?",
                 call=(f"client['{DB}'].command(SON([('insert', '{COLL}'), ('documents', [{{'_id': '{doc_id}'}}]), "
                       f"('writeConcern', {wc!r})]))"),
                 fn=ins, expect=exp, post=lambda rec, res, doc_id=doc_id: {"document_present": present(doc_id)}, read=rd)

    # ------------------------------------------------------------ XW2: other write commands
    for label, wc, target in (("w2", {"w": 2}, "del_target_1"), ("w_tag", {"w": "myTag"}, "del_target_2")):
        run_step(f"XW2.raw.delete.{label}", group="XW2 writeConcern on delete and findAndModify",
                 question=f"Is a delete with writeConcern {json.dumps(wc)} accepted and applied?",
                 call=(f"client['{DB}'].command(SON([('delete', '{COLL}'), ('deletes', [{{'q': {{'_id': '{target}'}}, 'limit': 1}}]), "
                       f"('writeConcern', {wc!r})]))"),
                 fn=lambda wc=wc, target=target: db.command(SON([("delete", COLL), ("deletes", [{"q": {"_id": target}, "limit": 1}]),
                                                                ("writeConcern", wc)])),
                 expect=REJ("BadValue", None, WSRC),
                 post=lambda rec, res, target=target: {"document_still_present": present(target)},
                 read=lambda rec: default_read(rec).rstrip(".") + (
                     "; the document was deleted." if not (rec.get("observed_after") or {}).get("document_still_present")
                     else "; the document is still present."))
    for label, wc in (("w2", {"w": 2}), ("w_tag", {"w": "myTag"})):
        run_step(f"XW2.raw.findAndModify.{label}", group="XW2 writeConcern on delete and findAndModify",
                 question=f"Is findAndModify with writeConcern {json.dumps(wc)} accepted and applied?",
                 call=(f"client['{DB}'].command(SON([('findAndModify', '{COLL}'), ('query', {{'_id': 'fam_target'}}), "
                       f"('update', {{'$inc': {{'n': 1}}}}), ('new', True), ('writeConcern', {wc!r})]))"),
                 fn=lambda wc=wc: db.command(SON([("findAndModify", COLL), ("query", {"_id": "fam_target"}),
                                                  ("update", {"$inc": {"n": 1}}), ("new", True), ("writeConcern", wc)])),
                 expect=REJ("BadValue", None, WSRC),
                 post=lambda rec, res: {"fam_target_after": other[DB][COLL].find_one({"_id": "fam_target"})})

    # ------------------------------------------------------------ XR: readConcern validation depth (raw find)
    RSRC = "main-branch read_concern.rs validate_and_extract_level() doc comment (local copy, fetched 2026-11-25)"
    xr = [
        ("level_int", {"level": 1}, REJ("TypeMismatch", "readConcern.level must be a string", RSRC)),
        ("level_null", {"level": None}, ACC(RSRC)),
        ("level_empty_string", {"level": ""}, REJ("BadValue", "Invalid readConcern level", RSRC)),
        ("unknown_subfield_foo", {"level": "local", "foo": 1}, REJ("UnknownBsonField", "is an unknown field", RSRC)),
        ("provenance_bogus", {"level": "local", "provenance": "bogus"}, REJ("BadValue", "Invalid readConcern provenance", RSRC)),
        ("provenance_clientSupplied", {"level": "local", "provenance": "clientSupplied"}, ACC(RSRC)),
        ("afterClusterTime_zero", {"level": "majority", "afterClusterTime": Timestamp(0, 0)},
         REJ("InvalidOptions", "readConcern.afterClusterTime is not supported", RSRC)),
        ("afterClusterTime_int", {"level": "majority", "afterClusterTime": 5}, REJ("TypeMismatch", "must be a timestamp", RSRC)),
        ("atClusterTime_null", {"level": "snapshot", "atClusterTime": None}, REJ("TypeMismatch", "must be a timestamp", RSRC)),
        ("not_a_document", "local", NOCLAIM),
    ]
    for label, rc, exp in xr:
        run_step(f"XR.raw.find.{label}", group="XR readConcern validation depth (raw find, outside a transaction)",
                 question=f"How is readConcern {json.dumps(ej(rc))} treated on find?",
                 call=(f"client['{DB}'].command(SON([('find', '{COLL}'), ('filter', {{'_id': 'read_target'}}), "
                       f"('readConcern', {rc!r})]))"),
                 fn=lambda rc=rc: db.command(SON([("find", COLL), ("filter", {"_id": "read_target"}), ("readConcern", rc)])),
                 expect=exp)
    PSRC = "main-branch process.rs test read_concern_flag_controls_request_parsing (ping with level UNKNOWN -> BadValue)"
    for label, rc, exp in (("bogus", {"level": "bogus"}, REJ("BadValue", "Invalid readConcern level", PSRC)),
                           ("linearizable", {"level": "linearizable"}, ACC("main-branch validation.rs: level checks run only for multi-document transaction requests"))):
        run_step(f"XR.raw.ping.{label}", group="XR readConcern validation depth (raw find, outside a transaction)",
                 question=f"Is readConcern {json.dumps(rc)} validated on a non-read command (ping on {DB})?",
                 call=f"client['{DB}'].command(SON([('ping', 1), ('readConcern', {rc!r})]))",
                 fn=lambda rc=rc: db.command(SON([("ping", 1), ("readConcern", rc)])), expect=exp)

    # ------------------------------------------------------------ XR2: readConcern levels on count / distinct
    VSRC = ("main-branch validation.rs validate_request(): returns Ok(()) when the request carries no transaction_info "
            "or autocommit is true, so the Available/Linearizable/Snapshot checks run only inside multi-document transactions")
    for level in ("available", "linearizable", "snapshot"):
        run_step(f"XR2.raw.count.{level}", group="XR2 readConcern levels on count and distinct (outside a transaction)",
                 question=f"Is count with readConcern {{level: '{level}'}} accepted outside a transaction?",
                 call=(f"client['{DB}'].command(SON([('count', '{COLL}'), ('query', {{'_id': 'read_target'}}), "
                       f"('readConcern', {{'level': '{level}'}})]))"),
                 fn=lambda level=level: db.command(SON([("count", COLL), ("query", {"_id": "read_target"}),
                                                        ("readConcern", {"level": level})])), expect=ACC(VSRC))
        run_step(f"XR2.raw.distinct.{level}", group="XR2 readConcern levels on count and distinct (outside a transaction)",
                 question=f"Is distinct with readConcern {{level: '{level}'}} accepted outside a transaction?",
                 call=(f"client['{DB}'].command(SON([('distinct', '{COLL}'), ('key', 'v'), ('query', {{'_id': 'read_target'}}), "
                       f"('readConcern', {{'level': '{level}'}})]))"),
                 fn=lambda level=level: db.command(SON([("distinct", COLL), ("key", "v"), ("query", {"_id": "read_target"}),
                                                        ("readConcern", {"level": level})])), expect=ACC(VSRC))

    # ------------------------------------------------------------ XS: is snapshot honoured outside a transaction?
    def snap_two_reads():
        other[DB][COLL].update_one({"_id": "snap_doc"}, {"$set": {"v": 1}})
        with client.start_session(snapshot=True) as s:
            r1 = coll.find_one({"_id": "snap_doc"}, session=s)
            t1 = getattr(s, "_snapshot_time", None)
            other[DB][COLL].update_one({"_id": "snap_doc"}, {"$set": {"v": 2}})
            r2 = coll.find_one({"_id": "snap_doc"}, session=s)
            return {"first_read": r1, "second_read": r2, "snapshot_time_after_first_read": t1,
                    "snapshot_time_after_second_read": getattr(s, "_snapshot_time", None)}

    def snap_read(rec):
        if rec["outcome"] != "ok":
            return f"Failed with {fmt_err(rec)}."
        r = rec["response"]
        finds = [ev["command"].get("readConcern") for ev in rec["wire"] if ev["event"] == "CommandStarted" and ev["command_name"] == "find"]
        v1, v2 = (r.get("first_read") or {}).get("v"), (r.get("second_read") or {}).get("v")
        return (f"In one pymongo snapshot session the first find (readConcern {json.dumps(finds[0] if finds else None)}) saw v={v1}; "
                f"after a separate client set v=2 the second find (readConcern {json.dumps(finds[1] if len(finds) > 1 else None)}) "
                f"saw v={v2}, so the session's reads {'were NOT' if v2 == 2 else 'WERE'} pinned to one snapshot "
                f"(MongoDB would return v=1 both times).")

    run_step("XS.snapshot_session.two_reads_with_concurrent_update", group="XS snapshot behaviour outside a transaction",
             question="Does a snapshot session pin its second read to the first read's snapshot when another client updates in between?",
             call=(f"with client.start_session(snapshot=True) as s: coll.find_one({{'_id': 'snap_doc'}}, session=s); "
                   f"other_client['{DB}']['{COLL}'].update_one({{'_id': 'snap_doc'}}, {{'$set': {{'v': 2}}}}); "
                   "coll.find_one({'_id': 'snap_doc'}, session=s)"),
             fn=snap_two_reads, expect=NOCLAIM, read=snap_read)

    def cursor_probe(level):
        def f():
            other[DB][COLL].update_many({"grp": "cur"}, {"$set": {"v": 1}})
            c = coll if level is None else coll.with_options(read_concern=ReadConcern(level))
            cur = c.find({"grp": "cur"}).batch_size(2)
            first = [next(cur), next(cur)]
            other[DB][COLL].update_many({"grp": "cur"}, {"$set": {"v": 2}})
            rest = list(cur)
            return {"first_batch_v": [d["v"] for d in first], "later_batches_v": [d["v"] for d in rest],
                    "ids": [d["_id"] for d in first + rest]}
        return f

    def cursor_read(rec):
        if rec["outcome"] != "ok":
            return f"Failed with {fmt_err(rec)}."
        r = rec["response"]
        n_get = sum(1 for ev in rec["wire"] if ev["event"] == "CommandStarted" and ev["command_name"] == "getMore")
        rc = next((ev["command"].get("readConcern") for ev in rec["wire"] if ev["event"] == "CommandStarted"
                   and ev["command_name"] == "find"), None)
        later = r.get("later_batches_v") or []
        seen_new = any(v == 2 for v in later)
        return (f"find with readConcern {json.dumps(rc)} and batchSize 2 returned v={r.get('first_batch_v')} in the first "
                f"batch; after a separate client set every v to 2, {n_get} getMore(s) returned v={later}, so later batches "
                f"{'DID' if seen_new else 'did NOT'} see the concurrent update.")

    for level in ("snapshot", None):
        lab = level or "none"
        run_step(f"XS.cursor.{lab}.getMore_after_concurrent_update", group="XS snapshot behaviour outside a transaction",
                 question=f"Does one find cursor (readConcern {lab}) keep a single snapshot across getMore when another client updates?",
                 call=(f"cur = client['{DB}']['{COLL}']" + ("" if level is None else f".with_options(read_concern=ReadConcern('{level}'))")
                       + ".find({'grp': 'cur'}).batch_size(2); read 2 docs; other_client update_many({'grp': 'cur'}, {'$set': {'v': 2}}); list(cur)"),
                 fn=cursor_probe(level), expect=NOCLAIM, read=cursor_read)

    # ------------------------------------------------------------ XT: transaction-side claims the tester did not test
    def txn_local():
        with client.start_session() as s:
            s.start_transaction(read_concern=ReadConcern("local"))
            docs = list(coll.find({"_id": "read_target"}, session=s))
            s.commit_transaction()
            return {"docs": docs, "committed": True}

    run_step("XT.transaction.readConcern_local", group="XT transactions",
             question="Is readConcern local accepted as a transaction readConcern?",
             call=(f"with client.start_session() as s: s.start_transaction(read_concern=ReadConcern('local')); "
                   f"list(client['{DB}']['{COLL}'].find({{'_id': 'read_target'}}, session=s)); s.commit_transaction()"),
             fn=txn_local, expect=ACC("DECISIONS.md topic 9 readConcern item / main-branch validation.rs (local is not refused)"))

    def txn_rc_after_start():
        with client.start_session() as s:
            s.start_transaction()
            try:
                first = db.command(SON([("find", COLL), ("filter", {"_id": "read_target"})]), session=s)
                second = db.command(SON([("find", COLL), ("filter", {"_id": "read_target"}),
                                         ("readConcern", {"level": "local"})]), session=s)
                s.commit_transaction()
                return {"first": first, "second": second, "committed": True}
            except Exception:
                if s.in_transaction:
                    s.abort_transaction()
                raise

    def after_start_read(rec):
        abort = first_reply(rec, "abortTransaction")
        base = default_read(rec).rstrip(".")
        if abort is not None:
            base += (f"; the abortTransaction that followed returned {json.dumps({k: abort.get(k) for k in ('ok', 'code', 'codeName', 'errmsg', 'errorLabels') if k in abort})}"
                     f" ({'errorLabels present' if 'errorLabels' in abort else 'no errorLabels field'})")
        return base + "."

    run_step("XT.transaction.readConcern_on_second_statement", group="XT transactions",
             question="Is a readConcern on the second statement of a transaction refused (DECISIONS: InvalidOptions)?",
             call=(f"with client.start_session() as s: s.start_transaction(); client['{DB}'].command(SON([('find', '{COLL}'), "
                   f"('filter', {{'_id': 'read_target'}})]), session=s); client['{DB}'].command(SON([('find', '{COLL}'), "
                   "('filter', {'_id': 'read_target'}), ('readConcern', {'level': 'local'})]), session=s)  # abort on failure"),
             fn=txn_rc_after_start,
             expect=REJ("InvalidOptions", "Read concern cannot be defined after transaction has started",
                        "DECISIONS.md topic 9 readConcern item (validation.rs:99-106)"),
             read=after_start_read)

    def txn_commit_w2():
        with client.start_session() as s:
            s.start_transaction(write_concern=WriteConcern(w=2))
            coll.insert_one({"_id": "txn_w2_doc"}, session=s)
            s.commit_transaction()
            return {"committed": True}

    run_step("XT.transaction.commit_writeConcern_w2", group="XT transactions",
             question="Is commitTransaction with writeConcern {w: 2} accepted, and does the transaction's insert land?",
             call=(f"with client.start_session() as s: s.start_transaction(write_concern=WriteConcern(w=2)); "
                   f"client['{DB}']['{COLL}'].insert_one({{'_id': 'txn_w2_doc'}}, session=s); s.commit_transaction()"),
             fn=txn_commit_w2, expect=REJ("BadValue", None, WSRC + " (if commitTransaction's writeConcern is validated)"),
             post=lambda rec, res: {"document_present": present("txn_w2_doc"),
                                    "commit_wire_writeConcern": next((ev["command"].get("writeConcern") for ev in rec["wire"]
                                                                      if ev["event"] == "CommandStarted" and ev["command_name"] == "commitTransaction"), None)})

    # ------------------------------------------------------------ XP: readPreference claims the tester did not test
    RPSRC = "main-branch read_preference.rs ReadPreference::parse (local copy, fetched 2026-11-25)"
    xp = [
        ("empty_document", {}, REJ("FailedToParse", "'mode' field is required", RPSRC)),
        ("mode_int", {"mode": 1}, REJ("FailedToParse", "'mode' field must be a string", RPSRC)),
        ("not_a_document", "primary", REJ("FailedToParse", "'$readPreference' must be a document", RPSRC)),
        ("primary_hedge_disabled", {"mode": "primary", "hedge": {"enabled": False}},
         REJ("FailedToParse", "mode 'primary' does not allow for 'hedge'", RPSRC)),
        ("nearest_hedge_disabled", {"mode": "nearest", "hedge": {"enabled": False}}, ACC(RPSRC)),
        ("nearest_maxStaleness_negative", {"mode": "nearest", "maxStalenessSeconds": -1},
         REJ("FailedToParse", "must be non-negative", RPSRC)),
        ("nearest_maxStaleness_double", {"mode": "nearest", "maxStalenessSeconds": 1.5},
         REJ("FailedToParse", "must be an integer", RPSRC)),
        ("nearest_maxStaleness_5", {"mode": "nearest", "maxStalenessSeconds": 5}, ACC(RPSRC + " (no lower bound)")),
        ("primary_tags_empty", {"mode": "primary", "tags": [{}]},
         REJ("FailedToSatisfyReadPreference", "specified tag set list", RPSRC)),
    ]
    for label, rp, exp in xp:
        run_step(f"XP.raw.find.{label}", group="XP $readPreference parsing claims not exercised by the tester",
                 question=f"How is $readPreference {json.dumps(rp)} treated on find?",
                 call=(f"client['{DB}'].command(SON([('find', '{COLL}'), ('filter', {{'_id': 'read_target'}}), "
                       f"('$readPreference', {rp!r})]))"),
                 fn=lambda rp=rp: db.command(SON([("find", COLL), ("filter", {"_id": "read_target"}), ("$readPreference", rp)])),
                 expect=exp)

    # ------------------------------------------------------------ XU: unacknowledged (w:0, moreToCome) writes that fail
    pool = PoolEvents()
    c_w0 = MongoClient(URI, maxPoolSize=1, minPoolSize=0, retryReads=False, retryWrites=False,
                       serverSelectionTimeoutMS=15000, socketTimeoutMS=60000, event_listeners=[CAP, pool])
    c_w0[DB][COLL].find_one({"_id": "read_target"})  # warm and authenticate the single connection
    w0 = c_w0[DB][COLL].with_options(write_concern=WriteConcern(w=0))

    def w0_fail(op):
        def f():
            pool.reset()
            r = op()
            follow = c_w0[DB][COLL].find_one({"_id": "read_target"})
            return {"acknowledged": r.acknowledged, "same_connection_follow_up_find": follow, "pool_during_step": pool.snapshot()}
        return f

    def w0_read(rec):
        if rec["outcome"] != "ok":
            return (f"The same-connection follow-up after the failing unacknowledged write raised {fmt_err(rec)}, so the "
                    "gateway answered (or broke) the moreToCome message.")
        r = rec["response"]
        ids = sorted({ev.get("server_connection_id") for ev in rec["wire"] if ev["event"] == "CommandStarted"})
        return (f"The failing w:0 write returned acknowledged={r.get('acknowledged')}; the follow-up find on server connection(s) "
                f"{ids} returned {json.dumps(r.get('same_connection_follow_up_find'))} with "
                f"{r['pool_during_step']['connections_created']} connection(s) created and "
                f"{r['pool_during_step']['connections_closed']} closed, so the gateway sent no reply (not even an error) to the "
                f"moreToCome message and kept the connection; observed state after: {json.dumps(rec.get('observed_after'))}.")

    run_step("XU.driver.insert_one.w0_duplicate_key", group="XU unacknowledged writes that fail",
             question="Does a w:0 insert that hits a duplicate key leave the connection usable with no stray reply?",
             call=(f"c_w0 = MongoClient(LOCAL_URI, maxPoolSize=1, retryReads=False, retryWrites=False); "
                   f"c_w0['{DB}']['{COLL}'].with_options(write_concern=WriteConcern(w=0)).insert_one({{'_id': 'read_target', 'dup': True}}); "
                   f"then c_w0['{DB}']['{COLL}'].find_one({{'_id': 'read_target'}}) on the same single pooled connection"),
             fn=w0_fail(lambda: w0.insert_one({"_id": "read_target", "dup": True})), expect=NOCLAIM,
             post=lambda rec, res: {"read_target_after": other[DB][COLL].find_one({"_id": "read_target"})}, read=w0_read)
    run_step("XU.driver.update_one.w0_invalid_operator", group="XU unacknowledged writes that fail",
             question="Does a w:0 update with an unknown update operator leave the connection usable with no stray reply?",
             call=(f"c_w0['{DB}']['{COLL}'].with_options(write_concern=WriteConcern(w=0)).update_one({{'_id': 'read_target'}}, "
                   "{'$bogusOp': {'v': 9}}); then the same-connection find_one"),
             fn=w0_fail(lambda: w0.update_one({"_id": "read_target"}, {"$bogusOp": {"v": 9}})), expect=NOCLAIM,
             post=lambda rec, res: {"read_target_after": other[DB][COLL].find_one({"_id": "read_target"})}, read=w0_read)
    c_w0.close()

    # ------------------------------------------------------------ XE: getDefaultRWConcern with comment
    run_step("XE.admin.getDefaultRWConcern.comment", group="XE getDefaultRWConcern",
             question="Is the comment field accepted by getDefaultRWConcern (DECISIONS lists it as allowed)?",
             call="client.admin.command(SON([('getDefaultRWConcern', 1), ('comment', 'reproduce-stage')]))",
             fn=lambda: client.admin.command(SON([("getDefaultRWConcern", 1), ("comment", "reproduce-stage")])),
             expect=ACC("DECISIONS.md topic 9 getDefaultRWConcern item (constant.rs allowed fields)"))

    # ------------------------------------------------------------ cleanup
    final_docs = list(other[DB][COLL].find({}).sort("_id", 1))
    run_step("XZ.drop_database", group="cleanup", question=f"Drop {DB} and confirm it is gone.",
             call=f"client.drop_database('{DB}'); '{DB}' in client.list_database_names()",
             fn=lambda: client.drop_database(DB),
             post=lambda rec, res: {"listed_after_drop": DB in client.list_database_names()},
             read=lambda rec: f"dropDatabase returned {json.dumps(first_reply(rec))}; {DB} listed afterwards: "
                              f"{(rec.get('observed_after') or {}).get('listed_after_drop')}.")
    client.close()
    other.close()
    inspect = container_inspection()
    report = {"test": "write-read-concerns", "stage": "reproduce: extra probes beyond the tester's script",
              "database": DB, "database_existed_before": pre, "started_at": started,
              "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "engine": engine,
              "evidence_scope": ("Observed on documentdb-local (open-source DocumentDB engine + gateway 1.2.0, single node, "
                                 "seen by pymongo as a mongos). Evidence about that build only, not about managed Azure DocumentDB."),
              "steps": STEPS, "container_inspection": inspect, "final_documents_before_drop": ej(final_docs)}
    text = scrub(json.dumps(report, indent=2, default=lambda o: ej(o)))
    if _PW and len(_PW) >= 4:
        assert _PW not in text
    open(OUT, "w").write(text)
    print(f"written {OUT}: {len(STEPS)} steps")


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {"command": " ".join(cmd), "exit": r.returncode, "output": scrub((r.stdout + r.stderr).strip())[:20000]}


def container_inspection():
    strings = ["operationTime", "$clusterTime", "clusterTime", "afterClusterTime", "atClusterTime",
               "mongoAllowTransactionSnapshot", "TransientTransactionError", "writeConcernError", "readConcern",
               "enable_read_concern_validation", "Unknown writeConcern w tag", "writeConcern must be a document",
               "BSON field 'readConcern.", "readConcern.level must be a string", "Invalid readConcern provenance",
               "'mode' field is required", "does not allow for 'hedge'", "must be non-negative", "maxWriteBatchSize",
               "Cannot continue transaction", "errorLabels", "RetryableWriteError", "UnknownTransactionCommitResult",
               "NoWritesPerformed"]
    rows = []
    for s in strings:
        gw = sh(["docker", "exec", CONTAINER, "sh", "-c", 'grep -a -o -F -e "$1" "$2" | wc -l', "sh", s, GW_BIN])
        so = sh(["docker", "exec", CONTAINER, "sh", "-c", 'cat /usr/lib/postgresql/17/lib/pg_documentdb*.so | grep -a -o -F -e "$1" | wc -l', "sh", s])
        rows.append({"string": s, "gateway_binary_count": int(gw["output"]) if gw["output"].isdigit() else gw["output"],
                     "extension_so_count": int(so["output"]) if so["output"].isdigit() else so["output"]})
    q1 = ("select name, setting, boot_val, source from pg_settings where name ilike any (array['%snapshot%','%concern%',"
          "'%validation%','documentdb.mongo%','documentdb.maxWriteBatchSize']) order by name")
    q2 = "select sourcefile, name, setting, applied from pg_file_settings where name ilike 'documentdb.%' order by name"
    pg = [sh(["docker", "exec", "-e", "PGOPTIONS=-c default_transaction_read_only=on", CONTAINER, PSQL, "-p", "9712",
              "-d", "postgres", "-AtX", "-c", q]) for q in (q1, q2)]
    host_cfg = sh(["docker", "exec", CONTAINER, "sh", "-c", "cat /tmp/documentdb_host_config_*.json"])
    setup = sh(["docker", "exec", CONTAINER, "sh", "-c", "cat /tmp/SetupConfiguration_*.json"])
    try:
        sd = json.loads(setup["output"])
        setup_summary = {"keys": sorted(sd.keys()), "DynamicConfigurationFile": sd.get("DynamicConfigurationFile")}
    except ValueError:
        setup_summary = {"unparsed": True}
    return {"binary_strings": {"command": "docker exec ddb-engine-test sh -c 'grep -a -o -F -e \"$1\" \"$2\" | wc -l' sh S " + GW_BIN
                               + " (and the same over cat /usr/lib/postgresql/17/lib/pg_documentdb*.so)", "rows": rows},
            "pg_settings": pg[0], "pg_file_settings": pg[1], "host_config_file": host_cfg,
            "setup_configuration_keys_only": {"command": "docker exec ddb-engine-test sh -c 'cat /tmp/SetupConfiguration_*.json' (keys only; values withheld)",
                                              "summary": setup_summary}}


if __name__ == "__main__":
    main()
