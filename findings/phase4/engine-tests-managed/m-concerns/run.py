#!/usr/bin/env python
"""m-concerns: writeConcern, readConcern, readPreference and get/setDefaultRWConcern
against the managed Azure DocumentDB cluster ddb-samples-shared (phase 1, data plane only).

Owns database mt_concern only and drops it at the end. Reads ../managed.env and never
prints or records the password or a URI. Every step records the driver call or raw command
as written, the exact commands PyMongo put on the wire (CommandListener) with the raw
replies or failures, the error fields (code, codeName, errmsg, errorLabels), follow-up
verification done on a separate unmonitored client, a verdict and a one-sentence reading.
Writes report.json next to this file.
"""
import datetime
import json
import os
import signal
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ENV, load_az_masks, redact, to_jsonable  # noqa: E402

import pymongo  # noqa: E402
from bson.son import SON  # noqa: E402
from pymongo import MongoClient, monitoring  # noqa: E402
from pymongo.errors import OperationFailure, PyMongoError  # noqa: E402
from pymongo.read_concern import ReadConcern  # noqa: E402
from pymongo.read_preferences import ReadPreference  # noqa: E402
from pymongo.write_concern import WriteConcern  # noqa: E402

DB = "mt_concern"
COLL = "c"
URI = ENV["MANAGED_URI"]
KW = dict(serverSelectionTimeoutMS=30000, connectTimeoutMS=20000, socketTimeoutMS=60000)
SKIP = {"saslStart", "saslContinue", "authenticate", "endSessions"}
STARTED = datetime.datetime.now(datetime.timezone.utc)

OSS_NOT_RUN = ("The open-source write-read-concerns test (findings/phase4/engine-tests/write-read-concerns and "
               "-rerun) was blocked before its first command (gateway InternalError on saslStart after the Docker "
               "VM disk filled), so there is no local observation to compare with.")
OSS_TXN = ("Open-source transactions-labels test (documentdb-local 0.117, wire 21): startTransaction with readConcern "
           "snapshot -> code 115 CommandNotSupported \"'Snapshot' read concern is not supported\"; majority and local "
           "-> find and commitTransaction ok:1.")


class Capture(monitoring.CommandListener):
    """Records every application command PyMongo puts on the wire, with its raw reply or failure."""

    def __init__(self):
        self.events = []
        self._open = {}

    def reset(self):
        self.events = []
        self._open = {}

    def started(self, e):
        if e.command_name in SKIP:
            return
        addr = e.connection_id
        rec = {"command_name": e.command_name, "database": e.database_name, "request_id": e.request_id,
               "server": f"{addr[0]}:{addr[1]}" if isinstance(addr, tuple) else str(addr),
               "server_connection_id": e.server_connection_id,
               "command": to_jsonable(e.command)}
        self.events.append(rec)
        self._open[e.request_id] = rec

    def succeeded(self, e):
        rec = self._open.pop(e.request_id, None)
        if rec is not None:
            rec["reply"] = to_jsonable(e.reply)
            rec["duration_ms"] = round(e.duration_micros / 1000.0, 2)

    def failed(self, e):
        rec = self._open.pop(e.request_id, None)
        if rec is not None:
            rec["failure"] = to_jsonable(e.failure)
            rec["duration_ms"] = round(e.duration_micros / 1000.0, 2)


CAP = Capture()
STEPS = []
STATE = {}


def err_info(e):
    d = {"type": type(e).__name__, "message": redact(str(e))}
    if isinstance(e, OperationFailure):
        det = e.details or {}
        d["code"] = e.code
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg")
        d["errorLabels"] = list(det["errorLabels"]) if "errorLabels" in det else None
        d["details"] = to_jsonable(det)
    labels = sorted(getattr(e, "_error_labels", set()) or [])
    d["driver_error_labels"] = labels
    return d


def step(sid, group, requested, call, fn):
    CAP.reset()
    rec = {"id": sid, "group": group, "requested_by_spec": requested, "call": call}
    t0 = time.monotonic()
    res = None
    try:
        res = fn()
        rec["outcome"] = "ok"
        rec["result"] = to_jsonable(res)
    except PyMongoError as e:
        rec["outcome"] = "error"
        rec["error"] = err_info(e)
        res = e
    except Exception as e:  # noqa: BLE001
        rec["outcome"] = "exception"
        rec["error"] = {"type": type(e).__name__, "message": redact(str(e)),
                        "trace": redact(traceback.format_exc())}
        res = e
    rec["elapsed_ms"] = round((time.monotonic() - t0) * 1000, 1)
    rec["wire"] = list(CAP.events)
    STEPS.append(rec)
    return rec, res


def finish(rec, verdict, reading, vs_open_source="not_tested_locally", vs_note=OSS_NOT_RUN,
           src=None, src_note=None):
    rec["verdict"] = verdict
    rec["reading"] = reading
    rec["vs_open_source"] = vs_open_source
    rec["vs_open_source_note"] = vs_note
    if src is not None:
        rec["vs_oss_gateway_source_prediction"] = src
        rec["vs_oss_gateway_source_note"] = src_note
    print(f"[{rec['outcome'].upper():9}] {rec['id']}: {verdict} | {reading}")


def errs(rec):
    e = rec.get("error") or {}
    if e.get("code") is not None:
        lab = e.get("errorLabels")
        return (f"code {e.get('code')} {e.get('codeName') or '(no codeName)'}: \"{e.get('errmsg')}\""
                f" (errorLabels {'absent' if lab is None else lab})")
    return f"{e.get('type')}: {e.get('message')}"


def wire_cmd(rec, name):
    for ev in rec.get("wire", []):
        if ev["command_name"] == name:
            return ev
    return None


def wce_in(rec):
    for ev in rec.get("wire", []):
        r = ev.get("reply") or {}
        if isinstance(r, dict) and r.get("writeConcernError"):
            return r["writeConcernError"]
    return None


def src_cmp(rec, expect_ok, code=None, msg_sub=None, text=""):
    """Compare with the DECISIONS.md prediction read from the open-source gateway source."""
    if expect_ok:
        ok = rec["outcome"] == "ok"
        return ("matches" if ok else "differs"), text
    e = rec.get("error") or {}
    ok = rec["outcome"] == "error" and (code is None or e.get("code") == code) and \
        (msg_sub is None or (msg_sub in (e.get("errmsg") or "")))
    return ("matches" if ok else "differs"), text


def vdoc(vcoll, _id):
    d = vcoll.find_one({"_id": _id})
    return to_jsonable(d) if d is not None else None


def main():
    load_az_masks()
    client = MongoClient(URI, event_listeners=[CAP], **KW)
    vc = MongoClient(URI, **KW)  # unmonitored client for verification reads
    db = client[DB]
    coll = db[COLL]
    vcoll = vc[DB][COLL]
    STATE["client"] = client

    # ------------------------------------------------------------------ setup
    rec, res = step("S0.buildInfo", "setup", False, "client.admin.command('buildInfo')",
                    lambda: client.admin.command("buildInfo"))
    STATE["buildInfo"] = rec.get("result")
    finish(rec, "info", f"buildInfo version {rec.get('result', {}).get('version') if rec['outcome'] == 'ok' else errs(rec)}.",
           "n/a", "Context only.")

    rec, res = step("S1.hello", "setup", False, "client.admin.command('hello')",
                    lambda: client.admin.command("hello"))
    hello = res if rec["outcome"] == "ok" else {}
    STATE["hello"] = rec.get("result")
    td = client.topology_description
    STATE["driver_topology"] = {"topology_type": td.topology_type_name,
                                "servers": [{"address": f"{a[0]}:{a[1]}", "server_type": s.server_type_name}
                                            for a, s in td.server_descriptions().items()]}
    finish(rec, "info",
           (f"hello reports msg {hello.get('msg')!r}, maxWireVersion {hello.get('maxWireVersion')}, "
            f"maxWriteBatchSize {hello.get('maxWriteBatchSize')}, no setName/hosts, an operationTime "
            f"{'present' if 'operationTime' in hello else 'absent'} and $clusterTime "
            f"{'present' if '$clusterTime' in hello else 'absent'}; PyMongo classifies the deployment as "
            f"{td.topology_type_name} with server types {[s['server_type'] for s in STATE['driver_topology']['servers']]}."),
           "different",
           "documentdb-local 0.117 advertised wire version 21 (MongoDB 7.0); this cluster advertises 25 (8.0). "
           "maxWriteBatchSize 25,000 is the same value the open-source bulkwrite-forms test observed.")

    def setup():
        r = db.command("dropDatabase")
        coll.insert_one({"_id": "seed", "n": 0, "last": "setup"})
        return {"dropDatabase_reply": r, "seed_inserted": True}

    rec, res = step("S2.setup", "setup", False,
                    "client['mt_concern'].command('dropDatabase'); coll.insert_one({_id:'seed', n:0, last:'setup'})", setup)
    finish(rec, "info", "Fresh mt_concern database with one seed document." if rec["outcome"] == "ok" else errs(rec),
           "n/a", "Setup only.")
    if rec["outcome"] != "ok":
        raise RuntimeError("setup failed")

    # ------------------------------------------------------- A. raw writeConcern
    raw_wc = [
        ("w1", {"w": 1}, True, True, None, None),
        ("w_majority", {"w": "majority"}, True, True, None, None),
        ("w0", {"w": 0}, True, True, None, None),
        ("w2", {"w": 2}, True, False, 2, "exceeds the number of data-bearing voting members"),
        ("w3", {"w": 3}, True, False, 2, "exceeds the number of data-bearing voting members"),
        ("w1_j_true", {"w": 1, "j": True}, True, True, None, None),
        ("w1_j_false", {"w": 1, "j": False}, True, True, None, None),
        ("w_majority_wtimeout_1", {"w": "majority", "wtimeout": 1}, True, True, None, None),
        ("w_custom_tag", {"w": "myTag"}, False, False, 2, None),
    ]
    src_text = {
        True: "DECISIONS (gateway write_concern.rs): w:0, w:1 and 'majority' are validated and ignored; j and wtimeout are accepted and ignored.",
        False: "DECISIONS (gateway write_concern.rs): numeric w 2..50 -> BadValue 'w value {n} exceeds the number of data-bearing voting members'; any string tag other than 'majority' -> BadValue.",
    }
    for label, wc, requested, expect_ok, ecode, emsg in raw_wc:
        doc_id = f"raw_ins_{label}"
        cmd_text = f"db.command(SON([('insert','c'),('documents',[{{'_id':'{doc_id}','label':'{label}'}}]),('writeConcern',{json.dumps(wc)})]))"

        def do_ins(wc=wc, doc_id=doc_id, label=label):
            return db.command(SON([("insert", COLL), ("documents", [{"_id": doc_id, "label": label}]),
                                   ("writeConcern", wc)]))

        rec, res = step(f"A.raw.insert.{label}", "A.writeConcern.raw", requested, cmd_text, do_ins)
        if label == "w0":
            time.sleep(0.5)
        landed = vdoc(vcoll, doc_id)
        rec["verification"] = {"query": f"unmonitored client: c.find_one({{_id:'{doc_id}'}})", "document": landed}
        s, n = src_cmp(rec, expect_ok, ecode, emsg, src_text[expect_ok])
        if rec["outcome"] == "ok":
            w = wce_in(rec)
            verdict = "accepted_with_writeConcernError" if w else "accepted_silently"
            extra = ""
            if label == "w0":
                extra = (" PyMongo's db.command does not set the OP_MSG moreToCome bit, so the gateway replied in full "
                         f"({json.dumps(rec.get('result'))}).")
            reading = (f"Raw insert with writeConcern {json.dumps(wc)} returned ok:{rec['result'].get('ok')} n:{rec['result'].get('n')} "
                       f"with {'writeConcernError ' + json.dumps(w) if w else 'no writeConcernError'}, and the document "
                       f"{'is' if landed else 'is NOT'} readable afterwards, so the concern changed nothing observable.{extra}")
        else:
            verdict = "rejected_but_applied" if landed else "rejected"
            reading = (f"Raw insert with writeConcern {json.dumps(wc)} was rejected with {errs(rec)}, and the document "
                       f"{'WAS written anyway' if landed else 'was not written'}.")
        finish(rec, verdict, reading, src=s, src_note=n)

        upd_val = f"raw_upd_{label}"
        cmd_text = (f"db.command(SON([('update','c'),('updates',[{{'q':{{'_id':'seed'}},'u':{{'$set':{{'last':'{upd_val}'}},"
                    f"'$inc':{{'n':1}}}}}}]),('writeConcern',{json.dumps(wc)})]))")

        def do_upd(wc=wc, upd_val=upd_val):
            return db.command(SON([("update", COLL),
                                   ("updates", [{"q": {"_id": "seed"}, "u": {"$set": {"last": upd_val}, "$inc": {"n": 1}}}]),
                                   ("writeConcern", wc)]))

        rec, res = step(f"A.raw.update.{label}", "A.writeConcern.raw", requested, cmd_text, do_upd)
        if label == "w0":
            time.sleep(0.5)
        seed = vdoc(vcoll, "seed")
        applied = bool(seed and seed.get("last") == upd_val)
        rec["verification"] = {"query": "unmonitored client: c.find_one({_id:'seed'})", "document": seed,
                               "update_applied": applied}
        s, n = src_cmp(rec, expect_ok, ecode, emsg, src_text[expect_ok])
        if rec["outcome"] == "ok":
            w = wce_in(rec)
            verdict = "accepted_with_writeConcernError" if w else "accepted_silently"
            reading = (f"Raw update with writeConcern {json.dumps(wc)} returned ok:{rec['result'].get('ok')} "
                       f"n:{rec['result'].get('n')} nModified:{rec['result'].get('nModified')} with "
                       f"{'writeConcernError ' + json.dumps(w) if w else 'no writeConcernError'}, and the update "
                       f"{'is' if applied else 'is NOT'} visible on the seed document.")
        else:
            verdict = "rejected_but_applied" if applied else "rejected"
            reading = (f"Raw update with writeConcern {json.dumps(wc)} was rejected with {errs(rec)}, and the update "
                       f"{'WAS applied anyway' if applied else 'was not applied'}.")
        finish(rec, verdict, reading, src=s, src_note=n)

    # raw w:0 duplicate key (extra): does a full reply still carry the write error?
    def raw_w0_dup():
        return db.command(SON([("insert", COLL), ("documents", [{"_id": "seed", "dup": True}]),
                               ("writeConcern", {"w": 0})]))

    rec, res = step("A.raw.insert.w0_duplicate_key", "A.writeConcern.raw", False,
                    "db.command(SON([('insert','c'),('documents',[{'_id':'seed','dup':True}]),('writeConcern',{'w':0})]))",
                    raw_w0_dup)
    seed = vdoc(vcoll, "seed")
    rec["verification"] = {"query": "unmonitored client: c.find_one({_id:'seed'})", "document": seed}
    if rec["outcome"] == "ok":
        we = rec["result"].get("writeErrors")
        finish(rec, "accepted_silently" if not we else "accepted_with_writeErrors",
               (f"A raw (acknowledged-transport) insert of a duplicate _id with writeConcern {{w:0}} returned "
                f"ok:{rec['result'].get('ok')} n:{rec['result'].get('n')} and "
                f"{'writeErrors ' + json.dumps(we) if we else 'no writeErrors'}: with a full reply the gateway "
                f"{'still reports' if we else 'does not report'} the duplicate-key error under w:0."))
    else:
        finish(rec, "rejected", f"A raw insert of a duplicate _id with writeConcern {{w:0}} raised {errs(rec)}.")

    # --------------------------------------------------- B. driver writeConcern
    drv_wc = [
        ("w1", WriteConcern(w=1), "WriteConcern(w=1)", True, True),
        ("w_majority", WriteConcern(w="majority"), "WriteConcern(w='majority')", True, True),
        ("w0", WriteConcern(w=0), "WriteConcern(w=0)", True, True),
        ("w2", WriteConcern(w=2), "WriteConcern(w=2)", True, False),
        ("w3", WriteConcern(w=3), "WriteConcern(w=3)", True, False),
        ("j_true", WriteConcern(j=True), "WriteConcern(j=True)", True, True),
        ("j_false", WriteConcern(j=False), "WriteConcern(j=False)", True, True),
        ("w_majority_wtimeout_1", WriteConcern(w="majority", wtimeout=1), "WriteConcern(w='majority', wtimeout=1)", True, True),
    ]
    for label, wc, wc_text, requested, expect_ok in drv_wc:
        doc_id = f"drv_ins_{label}"

        def d_ins(wc=wc, doc_id=doc_id, label=label):
            r = coll.with_options(write_concern=wc).insert_one({"_id": doc_id, "label": label})
            return {"acknowledged": r.acknowledged, "inserted_id": r.inserted_id}

        rec, res = step(f"B.driver.insert_one.{label}", "B.writeConcern.driver", requested,
                        f"coll.with_options(write_concern={wc_text}).insert_one({{'_id':'{doc_id}','label':'{label}'}})", d_ins)
        if label == "w0":
            time.sleep(1.0)
        landed = vdoc(vcoll, doc_id)
        rec["verification"] = {"query": f"unmonitored client: c.find_one({{_id:'{doc_id}'}})", "document": landed}
        s, n = src_cmp(rec, expect_ok, 2 if not expect_ok else None, None, src_text[expect_ok])
        wire = wire_cmd(rec, "insert")
        sent_wc = (wire or {}).get("command", {}).get("writeConcern")
        if rec["outcome"] == "ok":
            ack = rec["result"].get("acknowledged")
            if label == "w0":
                verdict = "accepted_and_honoured" if (not ack and landed) else "accepted_silently"
                reading = (f"insert_one with {wc_text} was sent as an unacknowledged OP_MSG (writeConcern on the wire "
                           f"{json.dumps(sent_wc)}, acknowledged={ack}, the {{ok:1}} reply is synthesized by PyMongo) and "
                           f"the document {'was' if landed else 'was NOT'} readable 1 s later, so w:0 behaves as fire-and-forget.")
            else:
                reading = (f"insert_one with {wc_text} (wire writeConcern {json.dumps(sent_wc)}) returned acknowledged={ack} "
                           f"without WriteConcernError or WTimeoutError and the document {'is' if landed else 'is NOT'} "
                           f"readable, so the concern had no observable effect.")
                verdict = "accepted_silently"
        else:
            verdict = "rejected_but_applied" if landed else "rejected"
            reading = (f"insert_one with {wc_text} (wire writeConcern {json.dumps(sent_wc)}) raised "
                       f"{rec['error']['type']} {errs(rec)}, and the document {'WAS written anyway' if landed else 'was not written'}.")
        finish(rec, verdict, reading, src=s, src_note=n)

        upd_val = f"drv_upd_{label}"

        def d_upd(wc=wc, upd_val=upd_val):
            r = coll.with_options(write_concern=wc).update_one({"_id": "seed"},
                                                                {"$set": {"last": upd_val}, "$inc": {"n": 1}})
            out = {"acknowledged": r.acknowledged}
            if r.acknowledged:
                out.update({"matched_count": r.matched_count, "modified_count": r.modified_count})
            return out

        rec, res = step(f"B.driver.update_one.{label}", "B.writeConcern.driver", requested,
                        f"coll.with_options(write_concern={wc_text}).update_one({{'_id':'seed'}}, "
                        f"{{'$set':{{'last':'{upd_val}'}},'$inc':{{'n':1}}}})", d_upd)
        if label == "w0":
            time.sleep(1.0)
        seed = vdoc(vcoll, "seed")
        applied = bool(seed and seed.get("last") == upd_val)
        rec["verification"] = {"query": "unmonitored client: c.find_one({_id:'seed'})", "document": seed,
                               "update_applied": applied}
        s, n = src_cmp(rec, expect_ok, 2 if not expect_ok else None, None, src_text[expect_ok])
        wire = wire_cmd(rec, "update")
        sent_wc = (wire or {}).get("command", {}).get("writeConcern")
        if rec["outcome"] == "ok":
            ack = rec["result"].get("acknowledged")
            if label == "w0":
                verdict = "accepted_and_honoured" if (not ack and applied) else "accepted_silently"
                reading = (f"update_one with {wc_text} went out unacknowledged (wire writeConcern {json.dumps(sent_wc)}, "
                           f"acknowledged={ack}) and the update {'was' if applied else 'was NOT'} visible 1 s later.")
            else:
                verdict = "accepted_silently"
                reading = (f"update_one with {wc_text} (wire writeConcern {json.dumps(sent_wc)}) returned acknowledged={ack} "
                           f"matched={rec['result'].get('matched_count')} modified={rec['result'].get('modified_count')} "
                           f"with no write concern error, and the update {'is' if applied else 'is NOT'} visible.")
        else:
            verdict = "rejected_but_applied" if applied else "rejected"
            reading = (f"update_one with {wc_text} (wire writeConcern {json.dumps(sent_wc)}) raised "
                       f"{rec['error']['type']} {errs(rec)}, and the update {'WAS applied anyway' if applied else 'was not applied'}.")
        finish(rec, verdict, reading, src=s, src_note=n)

    # w:0 honoured at the protocol level: one pooled connection, unacknowledged insert, then an acknowledged read
    def w0_protocol():
        p1 = MongoClient(URI, maxPoolSize=1, event_listeners=[CAP], **KW)
        try:
            p1.admin.command("ping")
            c0 = p1[DB][COLL].with_options(write_concern=WriteConcern(w=0))
            r1 = c0.insert_one({"_id": "drv_w0_proto_1", "label": "w0_proto"})
            r2 = c0.insert_one({"_id": "drv_w0_proto_2", "label": "w0_proto"})
            time.sleep(1.0)
            d = p1[DB][COLL].find_one({"_id": "drv_w0_proto_2"})
            n = p1[DB][COLL].count_documents({"label": "w0_proto"})
            return {"insert_1_acknowledged": r1.acknowledged, "insert_2_acknowledged": r2.acknowledged,
                    "same_connection_find_one": d, "same_connection_count": n}
        finally:
            p1.close()

    rec, res = step("B.driver.w0.same_connection_followup", "B.writeConcern.driver", False,
                    "p1 = MongoClient(URI, maxPoolSize=1); two WriteConcern(w=0) insert_one calls, sleep 1 s, then "
                    "find_one and count_documents on the same pooled connection", w0_protocol)
    conn_ids = sorted({ev.get("server_connection_id") for ev in rec["wire"] if ev.get("server_connection_id") is not None})
    rec["verification"] = {"server_connection_ids_seen": conn_ids}
    if rec["outcome"] == "ok":
        finish(rec, "accepted_and_honoured",
               (f"Two unacknowledged inserts followed by an acknowledged find_one and count_documents on the same "
                f"connection (server connection ids {conn_ids}) succeeded with count {rec['result'].get('same_connection_count')}, "
                f"so the gateway sent no reply to the moreToCome messages and the stream stayed in sync."))
    else:
        finish(rec, "error",
               f"The acknowledged read after unacknowledged writes on the same connection failed with {errs(rec)}; "
               f"a ProtocolError here would mean the gateway answered a moreToCome message.")

    def w0_dup():
        r = coll.with_options(write_concern=WriteConcern(w=0)).insert_one({"_id": "seed", "dup": True})
        time.sleep(0.5)
        return {"acknowledged": r.acknowledged}

    rec, res = step("B.driver.insert_one.w0_duplicate_key", "B.writeConcern.driver", False,
                    "coll.with_options(write_concern=WriteConcern(w=0)).insert_one({'_id':'seed','dup':True})", w0_dup)
    seed = vdoc(vcoll, "seed")
    rec["verification"] = {"query": "unmonitored client: c.find_one({_id:'seed'})", "document": seed}
    if rec["outcome"] == "ok":
        finish(rec, "accepted_and_honoured",
               (f"An unacknowledged insert of a duplicate _id returned acknowledged={rec['result'].get('acknowledged')} "
                f"and raised nothing, and the seed document {'is unchanged' if seed and not seed.get('dup') else 'CHANGED'}: "
                f"under w:0 the server-side duplicate-key error is invisible to the application, as w:0 specifies."))
    else:
        finish(rec, "error", f"Unexpected error {errs(rec)}.")

    def w1_dup():
        r = coll.insert_one({"_id": "seed", "dup": True})
        return {"acknowledged": r.acknowledged}

    rec, res = step("B.driver.insert_one.default_wc_duplicate_key", "B.writeConcern.driver", False,
                    "coll.insert_one({'_id':'seed','dup':True})  # client default write concern", w1_dup)
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"The same duplicate insert with the default (acknowledged) write concern raised {rec.get('error', {}).get('type')} "
            f"{errs(rec)}, the contrast that shows w:0 really suppresses error reporting.")
           if rec["outcome"] != "ok" else "Unexpectedly accepted a duplicate _id.")

    # client-level (connection-string style) options
    def client_opts(kwargs, doc_id, also_update):
        c = MongoClient(URI, event_listeners=[CAP], **kwargs, **KW)
        try:
            cc = c[DB][COLL]
            out = {"client_write_concern": cc.write_concern.document}
            r = cc.insert_one({"_id": doc_id, "label": doc_id})
            out["insert_acknowledged"] = r.acknowledged
            if also_update:
                u = cc.update_one({"_id": "seed"}, {"$set": {"last": doc_id}})
                out["update"] = {"acknowledged": u.acknowledged, "matched_count": u.matched_count,
                                 "modified_count": u.modified_count}
            return out
        finally:
            c.close()

    for sid, kwargs, txt, expect_ok in [
        ("B.client.w_majority", {"w": "majority"}, "MongoClient(URI, w='majority')", True),
        ("B.client.w_majority_wTimeoutMS_1_journal_true", {"w": "majority", "wTimeoutMS": 1, "journal": True},
         "MongoClient(URI, w='majority', wTimeoutMS=1, journal=True)", True),
        ("B.client.w2", {"w": 2}, "MongoClient(URI, w=2)", False),
    ]:
        doc_id = sid.replace(".", "_")
        rec, res = step(sid, "B.writeConcern.client_options", sid != "B.client.w2" and "wTimeoutMS" in sid,
                        f"{txt}; c['mt_concern']['c'].insert_one({{'_id':'{doc_id}'}}); update_one({{'_id':'seed'}}, "
                        f"{{'$set':{{'last':'{doc_id}'}}}})", lambda kwargs=kwargs, doc_id=doc_id: client_opts(kwargs, doc_id, True))
        landed = vdoc(vcoll, doc_id)
        rec["verification"] = {"query": f"unmonitored client: c.find_one({{_id:'{doc_id}'}})", "document": landed}
        wire = wire_cmd(rec, "insert")
        sent_wc = (wire or {}).get("command", {}).get("writeConcern")
        s, n = src_cmp(rec, expect_ok, 2 if not expect_ok else None, None, src_text[expect_ok])
        if rec["outcome"] == "ok":
            finish(rec, "accepted_silently",
                   (f"{txt} put writeConcern {json.dumps(sent_wc)} on the wire; insert and update were acknowledged "
                    f"without a write concern error and the document {'is' if landed else 'is NOT'} readable."),
                   src=s, src_note=n)
        else:
            finish(rec, "rejected_but_applied" if landed else "rejected",
                   (f"{txt} put writeConcern {json.dumps(sent_wc)} on the wire and the insert raised {rec['error']['type']} "
                    f"{errs(rec)}; the document {'WAS written anyway' if landed else 'was not written'}."),
                   src=s, src_note=n)

    # ----------------------------------------- C. readConcern outside a transaction
    rc_src = {
        "local": (True, None, None, "DECISIONS (gateway validation.rs): local is accepted and ignored."),
        "majority": (True, None, None, "DECISIONS (gateway validation.rs): majority is accepted and ignored."),
        "available": (False, 115, "'Available' read concern is not supported",
                      "DECISIONS (gateway validation.rs:126-136): available -> CommandNotSupported \"'Available' read concern is not supported\"."),
        "linearizable": (False, 115, "'Linearizable' read concern is not supported",
                         "DECISIONS (gateway validation.rs:126-136): linearizable -> CommandNotSupported \"'Linearizable' read concern is not supported\"."),
        "snapshot": (False, 115, "'Snapshot' read concern is not supported",
                     "DECISIONS (gateway validation.rs:111-124): snapshot -> CommandNotSupported \"'Snapshot' read concern is not supported\" unless allow_transaction_snapshot is on (open item 3)."),
    }

    def judge_read(rec, desc, level):
        exp_ok, code, msg, text = rc_src[level]
        s, n = src_cmp(rec, exp_ok, code, msg, text)
        if rec["outcome"] == "ok":
            r = rec.get("result") or {}
            cur = r.get("cursor", {}) if isinstance(r, dict) else {}
            atct = None
            for ev in rec["wire"]:
                rep = ev.get("reply") or {}
                if isinstance(rep, dict):
                    atct = atct or (rep.get("cursor") or {}).get("atClusterTime") or rep.get("atClusterTime")
            if level == "snapshot":
                verdict = "accepted_and_honoured" if atct else "accepted_silently"
                reading = (f"{desc} was accepted; the reply {'carries cursor.atClusterTime ' + json.dumps(atct) if atct else 'carries no atClusterTime'}"
                           f"{', so a snapshot point was established' if atct else ', so no snapshot point is observable'}.")
            else:
                verdict = "accepted_silently"
                reading = (f"{desc} was accepted and returned the seed document; on a single-node cluster with HA off "
                           f"there is no replica whose state could differ, so '{level}' has no observable effect.")
        else:
            verdict = "rejected"
            reading = f"{desc} was rejected with {errs(rec)}."
        finish(rec, verdict, reading, src=s, src_note=n)

    for level in ("local", "majority", "available", "linearizable", "snapshot"):
        rec, res = step(f"C.raw.find.readConcern.{level}", "C.readConcern.raw", True,
                        f"db.command(SON([('find','c'),('filter',{{'_id':'seed'}}),('readConcern',{{'level':'{level}'}})]))",
                        lambda level=level: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                                                            ("readConcern", {"level": level})])))
        judge_read(rec, f"Raw find with readConcern {{level:'{level}'}}", level)

    for level in ("local", "majority", "available", "linearizable", "snapshot"):
        rec, res = step(f"C.driver.find.readConcern.{level}", "C.readConcern.driver", True,
                        f"coll.with_options(read_concern=ReadConcern('{level}')).find_one({{'_id':'seed'}})",
                        lambda level=level: coll.with_options(read_concern=ReadConcern(level)).find_one({"_id": "seed"}))
        judge_read(rec, f"find_one with ReadConcern('{level}') (wire readConcern "
                        f"{json.dumps((wire_cmd(rec, 'find') or {}).get('command', {}).get('readConcern'))})", level)

    # extras: case sensitivity, aggregate, afterClusterTime / atClusterTime
    rec, res = step("C.raw.find.readConcern.Majority_mixed_case", "C.readConcern.raw", False,
                    "db.command(SON([('find','c'),('filter',{'_id':'seed'}),('readConcern',{'level':'Majority'})]))",
                    lambda: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}), ("readConcern", {"level": "Majority"})])))
    s, n = src_cmp(rec, False, 2, "Invalid readConcern level", "DECISIONS (gateway read_concern.rs): level parsing is case-sensitive; anything else -> BadValue 'Invalid readConcern level'.")
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"readConcern level 'Majority' was rejected with {errs(rec)}, so level parsing is case-sensitive."
            if rec["outcome"] != "ok" else "readConcern level 'Majority' was accepted, so level parsing is case-insensitive."),
           src=s, src_note=n)

    for level in ("majority", "snapshot"):
        rec, res = step(f"C.raw.aggregate.readConcern.{level}", "C.readConcern.raw", False,
                        f"db.command(SON([('aggregate','c'),('pipeline',[{{'$match':{{'_id':'seed'}}}}]),('cursor',{{}}),('readConcern',{{'level':'{level}'}})]))",
                        lambda level=level: db.command(SON([("aggregate", COLL), ("pipeline", [{"$match": {"_id": "seed"}}]),
                                                            ("cursor", {}), ("readConcern", {"level": level})])))
        judge_read(rec, f"Raw aggregate with readConcern {{level:'{level}'}}", level)

    def after_ct():
        ts = client.admin.command("hello").get("operationTime")
        STATE["ts_for_after"] = ts
        r = db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                            ("readConcern", {"level": "majority", "afterClusterTime": ts})]))
        return {"afterClusterTime_used": ts, "reply": r}

    rec, res = step("C.raw.find.readConcern.majority_afterClusterTime", "C.readConcern.raw", False,
                    "ts = client.admin.command('hello')['operationTime']; db.command(SON([('find','c'),('filter',{'_id':'seed'}),"
                    "('readConcern',{'level':'majority','afterClusterTime':ts})]))", after_ct)
    s, n = src_cmp(rec, False, 20, None,
                   "DECISIONS: gateway read_concern.rs on main documents afterClusterTime -> IllegalOperation; issue #770 reports release/1.0-RC2 silently accepts it.")
    if rec["outcome"] == "ok":
        finish(rec, "accepted_silently",
               (f"readConcern majority with afterClusterTime (the hello operationTime) was accepted and returned "
                f"{len(rec['result']['reply'].get('cursor', {}).get('firstBatch', []))} document(s), the RC2 behaviour in issue #770 rather than main's IllegalOperation."),
               src=s, src_note=n)
    else:
        finish(rec, "rejected", f"readConcern majority with afterClusterTime was rejected with {errs(rec)}.", src=s, src_note=n)

    def at_ct():
        vcoll.insert_one({"_id": "atct_before", "grp": "atct"})
        time.sleep(1.2)
        ts = client.admin.command("hello").get("operationTime")
        time.sleep(1.2)
        vcoll.insert_one({"_id": "atct_after", "grp": "atct"})
        r = db.command(SON([("find", COLL), ("filter", {"grp": "atct"}),
                            ("readConcern", {"level": "snapshot", "atClusterTime": ts})]))
        return {"atClusterTime_used": ts, "reply": r,
                "ids": [d["_id"] for d in r.get("cursor", {}).get("firstBatch", [])]}

    rec, res = step("C.raw.find.readConcern.snapshot_atClusterTime", "C.readConcern.raw", False,
                    "unmonitored insert {_id:'atct_before',grp:'atct'}; ts = hello.operationTime; unmonitored insert "
                    "{_id:'atct_after',grp:'atct'}; db.command(SON([('find','c'),('filter',{'grp':'atct'}),"
                    "('readConcern',{'level':'snapshot','atClusterTime':ts})]))", at_ct)
    s, n = src_cmp(rec, False, None, None,
                   "DECISIONS: snapshot is rejected unless allow_transaction_snapshot is on; read_concern.rs on main says atClusterTime -> InvalidOptions; issue #770 reports RC2 silently accepts it.")
    if rec["outcome"] == "ok":
        ids = rec["result"].get("ids")
        honoured = ids == ["atct_before"]
        finish(rec, "accepted_and_honoured" if honoured else "accepted_not_honoured",
               f"snapshot read at atClusterTime returned {ids}: the document written after the timestamp "
               f"{'is excluded, so the point-in-time read is honoured' if honoured else 'is included, so atClusterTime is not honoured'}.",
               src=s, src_note=n)
    else:
        finish(rec, "rejected", f"readConcern snapshot with atClusterTime was rejected with {errs(rec)}.", src=s, src_note=n)

    def snap_session():
        vcoll.insert_one({"_id": "snap_before", "grp": "snap"})
        out = {}
        with client.start_session(snapshot=True) as s:
            first = list(coll.find({"grp": "snap"}, session=s))
            out["first_ids"] = [d["_id"] for d in first]
            out["session_snapshot_time_after_first"] = s._snapshot_time
            vcoll.insert_one({"_id": "snap_after", "grp": "snap"})
            time.sleep(0.5)
            second = list(coll.find({"grp": "snap"}, session=s))
            out["second_ids"] = [d["_id"] for d in second]
        return out

    rec, res = step("C.driver.snapshot_session.find", "C.readConcern.driver", False,
                    "unmonitored insert {_id:'snap_before',grp:'snap'}; with client.start_session(snapshot=True) as s: "
                    "list(coll.find({'grp':'snap'}, session=s)); unmonitored insert {_id:'snap_after',grp:'snap'}; "
                    "list(coll.find({'grp':'snap'}, session=s))", snap_session)
    s, n = src_cmp(rec, False, 115, "'Snapshot' read concern is not supported", rc_src["snapshot"][3])
    if rec["outcome"] == "ok":
        r = rec["result"]
        honoured = r.get("second_ids") == r.get("first_ids") and "snap_after" not in (r.get("second_ids") or [])
        finish(rec, "accepted_and_honoured" if honoured else "accepted_not_honoured",
               (f"A PyMongo snapshot session read {r.get('first_ids')} then {r.get('second_ids')} after a concurrent insert "
                f"(session snapshot time {json.dumps(r.get('session_snapshot_time_after_first'))}), so the snapshot "
                f"{'is' if honoured else 'is NOT'} held across reads."), src=s, src_note=n)
    else:
        finish(rec, "rejected", f"The first read of a PyMongo snapshot session (start_session(snapshot=True)) failed with {errs(rec)}.",
               src=s, src_note=n)

    def causal():
        out = {"ops": []}
        with client.start_session(causal_consistency=True) as s:
            for name, fn in [
                ("insert_one cc_1", lambda: coll.insert_one({"_id": "cc_1", "grp": "cc"}, session=s).acknowledged),
                ("insert_one cc_2", lambda: coll.insert_one({"_id": "cc_2", "grp": "cc"}, session=s).acknowledged),
                ("find_one cc_1", lambda: coll.find_one({"_id": "cc_1"}, session=s)),
                ("update_one cc_1", lambda: coll.update_one({"_id": "cc_1"}, {"$set": {"u": 1}}, session=s).modified_count),
            ]:
                before = s.operation_time
                try:
                    v = fn()
                    out["ops"].append({"op": name, "operation_time_before": before, "ok": True, "value": v,
                                       "operation_time_after": s.operation_time})
                except PyMongoError as e:
                    out["ops"].append({"op": name, "operation_time_before": before, "ok": False, "error": err_info(e)})
        return out

    rec, res = step("C.driver.causal_session.afterClusterTime", "C.readConcern.driver", False,
                    "with client.start_session(causal_consistency=True) as s: insert_one cc_1, insert_one cc_2, "
                    "find_one cc_1, update_one cc_1 (each with session=s)", causal)
    s, n = src_cmp(rec, True, None, None,
                   "DECISIONS: read_concern.rs on main documents afterClusterTime -> IllegalOperation; RC2 silently accepts it (#770). PyMongo adds afterClusterTime to reads and writes in a causal session once a reply carried operationTime.")
    if rec["outcome"] == "ok":
        ops = rec["result"]["ops"]
        sent = [((ev.get("command") or {}).get("readConcern")) for ev in rec["wire"]]
        all_ok = all(o.get("ok") for o in ops)
        failed = [o for o in ops if not o.get("ok")]
        rec["verification"] = {"readConcern_on_wire_per_command": sent}
        if all_ok:
            s = "matches" if not any(x and "afterClusterTime" in x for x in sent) else "differs"
            n = ("Prediction from main-branch source: afterClusterTime -> IllegalOperation. "
                 + ("No afterClusterTime was sent, so the prediction was not exercised." if s == "matches" else
                    "afterClusterTime was sent and accepted, which differs from main (matches RC2)."))
            op_time_in_replies = any(isinstance(ev.get("reply"), dict) and "operationTime" in ev["reply"] for ev in rec["wire"])
            rec["verification"]["any_reply_has_operationTime"] = op_time_in_replies
            finish(rec, "accepted_silently",
                   (f"All four operations in a causally consistent session succeeded; readConcern on the wire per command was "
                    f"{json.dumps(sent)} because {'some' if op_time_in_replies else 'no'} insert/find/update reply carried operationTime, "
                    f"so afterClusterTime {'is accepted' if any(x and 'afterClusterTime' in x for x in sent) else 'was never sent'} and the "
                    f"session gives no causal guarantee beyond the single node's own ordering."), src=s, src_note=n)
        else:
            finish(rec, "rejected",
                   (f"In a causally consistent session {[o['op'] for o in failed]} failed "
                    f"({'; '.join(o['op'] + ': ' + str(o['error'].get('code')) + ' ' + str(o['error'].get('codeName')) + ' ' + str(o['error'].get('errmsg')) for o in failed)}); "
                    f"readConcern on the wire per command was {json.dumps(sent)}."), src="differs" if failed else s, src_note=n)
    else:
        finish(rec, "error", f"Causal session sequence raised {errs(rec)}.", src=s, src_note=n)

    # causal session once the session HAS an operationTime (hello is the only reply that carries one)
    def causal_after_hello():
        out = {"ops": []}
        with client.start_session(causal_consistency=True) as s:
            h = client.admin.command("hello", session=s)
            out["hello_operationTime"] = h.get("operationTime")
            out["session_operation_time_after_hello"] = s.operation_time
            for name, fn in [("find_one seed", lambda: coll.find_one({"_id": "seed"}, session=s)),
                             ("insert_one cc_h", lambda: coll.insert_one({"_id": "cc_h", "grp": "cc"}, session=s).acknowledged)]:
                try:
                    out["ops"].append({"op": name, "ok": True, "value": fn()})
                except PyMongoError as e:
                    out["ops"].append({"op": name, "ok": False, "error": err_info(e)})
        return out

    rec, res = step("C.driver.causal_session.after_hello_in_session", "C.readConcern.driver", False,
                    "with client.start_session(causal_consistency=True) as s: client.admin.command('hello', session=s); "
                    "coll.find_one({'_id':'seed'}, session=s); coll.insert_one({'_id':'cc_h'}, session=s)", causal_after_hello)
    landed = vdoc(vcoll, "cc_h")
    sent = [((ev.get("command") or {}).get("readConcern")) for ev in rec["wire"] if ev["command_name"] in ("find", "insert")]
    rec["verification"] = {"readConcern_on_wire_find_insert": sent, "cc_h_document": landed}
    if rec["outcome"] == "ok":
        ops = rec["result"]["ops"]
        bad = [o for o in ops if not o["ok"]]
        finish(rec, "rejected" if bad else "accepted_silently",
               (f"After a hello run inside the causal session set its operationTime, PyMongo sent readConcern {json.dumps(sent)} on "
                f"the next find and insert; " +
                ("; ".join(f"{o['op']} failed with code {o['error'].get('code')} {o['error'].get('codeName')}: \"{o['error'].get('errmsg')}\"" for o in bad)
                 if bad else "both succeeded") +
                f" (cc_h {'was' if landed else 'was not'} written)."),
               src="matches" if bad and all(o["error"].get("code") == 20 for o in bad) else "differs",
               src_note="DECISIONS: read_concern.rs on main documents afterClusterTime -> IllegalOperation.")
    else:
        finish(rec, "error", f"Sequence raised {errs(rec)}.")

    def causal_advance():
        ts = client.admin.command("hello").get("operationTime")
        STATE["advance_ts"] = ts
        with client.start_session(causal_consistency=True) as s:
            s.advance_operation_time(ts)
            return {"advanced_to": ts, "find_one": coll.find_one({"_id": "seed"}, session=s)}

    rec, res = step("C.driver.causal_session.advance_operation_time", "C.readConcern.driver", False,
                    "ts = client.admin.command('hello')['operationTime']; with client.start_session(causal_consistency=True) as s: "
                    "s.advance_operation_time(ts); coll.find_one({'_id':'seed'}, session=s)", causal_advance)
    ev = wire_cmd(rec, "find")
    rec["verification"] = {"find_readConcern_on_wire": (ev or {}).get("command", {}).get("readConcern")}
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"A causal session advanced to the hello operationTime (MongoDB's documented way to chain causal consistency across "
            f"sessions) sent readConcern {json.dumps(rec['verification']['find_readConcern_on_wire'])} and the find was rejected with {errs(rec)}."
            if rec["outcome"] != "ok" else
            f"A causal session advanced to the hello operationTime sent readConcern {json.dumps(rec['verification']['find_readConcern_on_wire'])} and the find succeeded."),
           src="matches" if (rec.get("error") or {}).get("code") == 20 else "differs",
           src_note="DECISIONS: read_concern.rs on main documents afterClusterTime -> IllegalOperation.")

    # snapshot vs local cursor consistency across getMore (unsorted, batchSize 2, concurrent insert between batches)
    for level in ("snapshot", "local"):
        def gm(level=level):
            grp = f"gm_{level}"
            vcoll.insert_many([{"_id": f"{grp}_{i:02d}", "grp": grp} for i in range(6)])
            cur = coll.with_options(read_concern=ReadConcern(level)).find({"grp": grp}).batch_size(2)
            first = [next(cur)["_id"], next(cur)["_id"]]
            vcoll.insert_one({"_id": f"{grp}_99", "grp": grp})
            time.sleep(0.3)
            rest = [d["_id"] for d in cur]
            return {"first_batch": first, "rest": rest, "inserted_between_batches": f"{grp}_99",
                    "inserted_doc_seen": f"{grp}_99" in rest, "total": len(first) + len(rest)}

        rec, res = step(f"C.driver.find.readConcern.{level}.getMore_consistency", "C.readConcern.driver", False,
                        f"unmonitored insert_many 6 docs grp gm_{level}; cur = coll.with_options(read_concern=ReadConcern('{level}'))"
                        f".find({{'grp':'gm_{level}'}}).batch_size(2); read first batch; unmonitored insert gm_{level}_99; exhaust cursor",
                        gm)
        gms = [e for e in rec["wire"] if e["command_name"] == "getMore"]
        rec["verification"] = {"getMore_count": len(gms),
                               "getMore_readConcern_on_wire": [(e.get("command") or {}).get("readConcern") for e in gms]}
        if rec["outcome"] == "ok":
            seen = rec["result"]["inserted_doc_seen"]
            if level == "snapshot":
                verdict = "accepted_not_honoured" if seen else "accepted_and_honoured"
                reading = (f"A readConcern snapshot cursor read 2 documents, then a concurrent insert, then {len(gms)} getMore call(s) "
                           f"{'DID' if seen else 'did not'} return the new document, so the cursor "
                           f"{'is not' if seen else 'is'} pinned to one point in time across batches.")
            else:
                verdict = "accepted_silently"
                reading = (f"Control: a readConcern local cursor under the same sequence {'did' if seen else 'did not'} return the "
                           f"document inserted between batches ({len(gms)} getMore call(s)).")
            finish(rec, verdict, reading)
        else:
            finish(rec, "error", f"The cursor sequence failed with {errs(rec)}.")

    # -------------------------------------------------- D. readPreference on find
    rp_src = {
        "primary": (True, None, None, "DECISIONS (gateway read_preference.rs): primary accepted and discarded."),
        "secondary": (False, 133, "no server available for query with ReadPreference secondary",
                      "DECISIONS (gateway read_preference.rs:160-165): secondary -> FailedToSatisfyReadPreference 'no server available for query with ReadPreference secondary'."),
        "secondaryPreferred": (True, None, None, "DECISIONS (gateway read_preference.rs): secondaryPreferred accepted and discarded."),
        "nearest": (True, None, None, "DECISIONS (gateway read_preference.rs): nearest accepted and discarded."),
        "primaryPreferred": (True, None, None, "DECISIONS (gateway read_preference.rs): primaryPreferred accepted and discarded."),
    }
    servers_seen = set()

    def judge_rp(rec, desc, mode):
        exp_ok, code, msg, text = rp_src[mode]
        s, n = src_cmp(rec, exp_ok, code, msg, text)
        ev = wire_cmd(rec, "find")
        sent = (ev or {}).get("command", {}).get("$readPreference")
        srv = (ev or {}).get("server")
        if srv:
            servers_seen.add(srv)
        rec["verification"] = {"$readPreference_on_wire": sent, "served_by": srv}
        if rec["outcome"] == "ok":
            finish(rec, "accepted_silently",
                   (f"{desc} sent $readPreference {json.dumps(sent) if sent else '(none: PyMongo omits it for primary)'} to "
                    f"{srv} and returned the seed document; the deployment exposes a single endpoint, so no routing is observable."),
                   src=s, src_note=n)
        else:
            finish(rec, "rejected",
                   f"{desc} sent $readPreference {json.dumps(sent)} and was rejected with {errs(rec)}.", src=s, src_note=n)

    rps = [("primary", ReadPreference.PRIMARY, True), ("secondary", ReadPreference.SECONDARY, True),
           ("secondaryPreferred", ReadPreference.SECONDARY_PREFERRED, True), ("nearest", ReadPreference.NEAREST, True),
           ("primaryPreferred", ReadPreference.PRIMARY_PREFERRED, False)]
    enum_name = {"primary": "PRIMARY", "secondary": "SECONDARY", "secondaryPreferred": "SECONDARY_PREFERRED",
                 "nearest": "NEAREST", "primaryPreferred": "PRIMARY_PREFERRED"}
    for mode, rp, requested in rps:
        rec, res = step(f"D.driver.find.readPreference.{mode}", "D.readPreference.driver", requested,
                        f"coll.with_options(read_preference=ReadPreference.{enum_name[mode]}).find_one({{'_id':'seed'}})",
                        lambda rp=rp: coll.with_options(read_preference=rp).find_one({"_id": "seed"}))
        judge_rp(rec, f"find_one with read_preference {mode}", mode)

    for mode, _, requested in rps:
        rec, res = step(f"D.raw.find.$readPreference.{mode}", "D.readPreference.raw", requested,
                        f"db.command(SON([('find','c'),('filter',{{'_id':'seed'}}),('$readPreference',{{'mode':'{mode}'}})]))",
                        lambda mode=mode: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                                                          ("$readPreference", {"mode": mode})])))
        judge_rp(rec, f"Raw find with $readPreference {{mode:'{mode}'}}", mode)

    extras = [
        ("D.raw.find.$readPreference.secondaryPreferred_tags", {"mode": "secondaryPreferred", "tags": [{"dc": "east"}]},
         False, 133, "tag set", "DECISIONS (read_preference.rs:125-131): any tags field -> FailedToSatisfyReadPreference 'no server available for query with specified tag set list'."),
        ("D.raw.find.$readPreference.nearest_hedge_enabled", {"mode": "nearest", "hedge": {"enabled": True}},
         False, 2, "hedged reads are not supported", "DECISIONS (read_preference.rs:167-172): hedge {enabled:true} -> BadValue 'hedged reads are not supported'."),
        ("D.raw.find.$readPreference.secondaryPreferred_maxStalenessSeconds_90", {"mode": "secondaryPreferred", "maxStalenessSeconds": 90},
         True, None, None, "DECISIONS (read_preference.rs): non-negative integer maxStalenessSeconds with a non-primary mode is accepted and discarded."),
        ("D.raw.find.$readPreference.primary_maxStalenessSeconds_90", {"mode": "primary", "maxStalenessSeconds": 90},
         False, 9, None, "DECISIONS (read_preference.rs): mode primary combined with maxStalenessSeconds -> FailedToParse."),
    ]
    for sid, rpdoc, exp_ok, code, msg, text in extras:
        rec, res = step(sid, "D.readPreference.raw", False,
                        f"db.command(SON([('find','c'),('filter',{{'_id':'seed'}}),('$readPreference',{json.dumps(rpdoc)})]))",
                        lambda rpdoc=rpdoc: db.command(SON([("find", COLL), ("filter", {"_id": "seed"}),
                                                            ("$readPreference", rpdoc)])))
        s, n = src_cmp(rec, exp_ok, code, msg, text)
        ev = wire_cmd(rec, "find")
        rec["verification"] = {"$readPreference_on_wire": (ev or {}).get("command", {}).get("$readPreference"),
                               "served_by": (ev or {}).get("server")}
        if rec["outcome"] == "ok":
            finish(rec, "accepted_silently", f"Raw find with $readPreference {json.dumps(rpdoc)} was accepted and returned the seed document.",
                   src=s, src_note=n)
        else:
            finish(rec, "rejected", f"Raw find with $readPreference {json.dumps(rpdoc)} was rejected with {errs(rec)}.",
                   src=s, src_note=n)

    for mode in ("secondary", "nearest"):
        def cl_rp(mode=mode):
            c = MongoClient(URI, readPreference=mode, event_listeners=[CAP], **KW)
            try:
                return {"client_read_preference": c.read_preference.document,
                        "find_one": c[DB][COLL].find_one({"_id": "seed"})}
            finally:
                c.close()

        rec, res = step(f"D.client.readPreference.{mode}", "D.readPreference.client_options", False,
                        f"MongoClient(URI, readPreference='{mode}')['mt_concern']['c'].find_one({{'_id':'seed'}})", cl_rp)
        judge_rp(rec, f"find_one on a client created with readPreference='{mode}'", mode)

    # ---------------------------------------------- E. get/setDefaultRWConcern
    get_src = ("DECISIONS (gateway processor/constant.rs:63-93): constant {defaultReadConcern:{level:'majority'}, "
               "defaultWriteConcern:{w:'majority', wtimeout:0}, defaultReadConcernSource:'implicit', "
               "defaultWriteConcernSource:'implicit', ok:1}; admin database only.")
    rec, res = step("E.admin.getDefaultRWConcern", "E.defaultRWConcern", True, "client.admin.command('getDefaultRWConcern')",
                    lambda: client.admin.command("getDefaultRWConcern"))
    first_get = rec.get("result") if rec["outcome"] == "ok" else None
    STATE["getDefaultRWConcern_before"] = first_get
    if rec["outcome"] == "ok":
        r = rec["result"]
        match = (r.get("defaultReadConcern") == {"level": "majority"} and
                 r.get("defaultWriteConcern") == {"w": "majority", "wtimeout": 0} and
                 r.get("defaultReadConcernSource") == "implicit" and r.get("defaultWriteConcernSource") == "implicit")
        finish(rec, "accepted_silently",
               (f"getDefaultRWConcern returned {json.dumps(r)}; the reported majority/majority defaults cannot be honoured "
                f"as replication guarantees on this single-node cluster and the writeConcern tests show w is validated, not applied."),
               src="matches" if match else "differs", src_note=get_src)
    else:
        finish(rec, "rejected", f"getDefaultRWConcern was rejected with {errs(rec)}.", src="differs", src_note=get_src)

    rec, res = step("E.admin.getDefaultRWConcern.inMemory_true", "E.defaultRWConcern", False,
                    "client.admin.command(SON([('getDefaultRWConcern',1),('inMemory',True)]))",
                    lambda: client.admin.command(SON([("getDefaultRWConcern", 1), ("inMemory", True)])))
    s, n = src_cmp(rec, True, None, None, "DECISIONS: inMemory is one of the allowed top-level fields.")
    finish(rec, "accepted_silently" if rec["outcome"] == "ok" else "rejected",
           (f"getDefaultRWConcern with inMemory:true returned {json.dumps(rec.get('result'))}." if rec["outcome"] == "ok"
            else f"getDefaultRWConcern with inMemory:true was rejected with {errs(rec)}."), src=s, src_note=n)

    rec, res = step("E.mt_concern.getDefaultRWConcern", "E.defaultRWConcern", False,
                    "client['mt_concern'].command('getDefaultRWConcern')",
                    lambda: db.command("getDefaultRWConcern"))
    s, n = src_cmp(rec, False, 13, "Only the admin database can process getDefaultRWConcern",
                   "DECISIONS: non-admin database -> Unauthorized 'Only the admin database can process getDefaultRWConcern.'")
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"getDefaultRWConcern on mt_concern was rejected with {errs(rec)}." if rec["outcome"] != "ok"
            else f"getDefaultRWConcern on mt_concern was accepted: {json.dumps(rec.get('result'))}."), src=s, src_note=n)

    rec, res = step("E.admin.getDefaultRWConcern.unknown_field", "E.defaultRWConcern", False,
                    "client.admin.command(SON([('getDefaultRWConcern',1),('foo',1)]))",
                    lambda: client.admin.command(SON([("getDefaultRWConcern", 1), ("foo", 1)])))
    s, n = src_cmp(rec, False, None, "Not a valid value for getDefaultRWConcern",
                   "DECISIONS: any other top-level field -> UnknownBsonField 'Not a valid value for getDefaultRWConcern: {field}'.")
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"getDefaultRWConcern with an unknown field was rejected with {errs(rec)}." if rec["outcome"] != "ok"
            else f"getDefaultRWConcern with an unknown field was accepted: {json.dumps(rec.get('result'))}."), src=s, src_note=n)

    # setDefaultRWConcern: probe first with no fields (can never change state under MongoDB semantics);
    # send value-bearing forms only if the probe proves the command itself is not implemented.
    rec, res = step("E.admin.setDefaultRWConcern.probe_no_fields", "E.defaultRWConcern", True,
                    "client.admin.command('setDefaultRWConcern')  # no defaultReadConcern/defaultWriteConcern",
                    lambda: client.admin.command("setDefaultRWConcern"))
    probe = rec
    unsupported = probe["outcome"] == "error" and (probe["error"].get("code") in (59, 115) or
                                                   "not supported" in (probe["error"].get("errmsg") or "").lower() or
                                                   "no such command" in (probe["error"].get("errmsg") or "").lower())
    finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
           (f"setDefaultRWConcern with no fields was rejected with {errs(rec)}"
            f"{', which identifies the command itself as unimplemented' if unsupported else ', a value-level rejection, so the command may exist'}."
            if rec["outcome"] != "ok" else f"setDefaultRWConcern with no fields was accepted: {json.dumps(rec.get('result'))}."),
           src="matches" if unsupported else "differs",
           src_note="Compatibility page: setDefaultRWConcern No; DECISIONS gives no gateway-source detail for it.")
    STATE["setDefaultRWConcern_unsupported"] = unsupported

    if unsupported:
        for sid, extra, txt in [
            ("E.admin.setDefaultRWConcern.defaultWriteConcern_w1", ("defaultWriteConcern", {"w": 1}),
             "client.admin.command(SON([('setDefaultRWConcern',1),('defaultWriteConcern',{'w':1})]))"),
            ("E.admin.setDefaultRWConcern.defaultReadConcern_local", ("defaultReadConcern", {"level": "local"}),
             "client.admin.command(SON([('setDefaultRWConcern',1),('defaultReadConcern',{'level':'local'})]))"),
        ]:
            rec, res = step(sid, "E.defaultRWConcern", True, txt,
                            lambda extra=extra: client.admin.command(SON([("setDefaultRWConcern", 1), extra])))
            finish(rec, "rejected" if rec["outcome"] != "ok" else "accepted_silently",
                   (f"setDefaultRWConcern with {json.dumps({extra[0]: extra[1]})} was rejected with {errs(rec)}."
                    if rec["outcome"] != "ok" else f"setDefaultRWConcern with {json.dumps({extra[0]: extra[1]})} was ACCEPTED: {json.dumps(rec.get('result'))}."),
                   src="matches" if rec["outcome"] != "ok" else "differs",
                   src_note="Compatibility page: setDefaultRWConcern No.")
            if rec["outcome"] == "ok":
                STATE.setdefault("config_changes", []).append(
                    f"setDefaultRWConcern {json.dumps({extra[0]: extra[1]})} accepted on admin (step {sid}).")
    else:
        rec = {"id": "E.admin.setDefaultRWConcern.value_forms", "group": "E.defaultRWConcern", "requested_by_spec": True,
               "call": "not sent", "outcome": "not_run", "wire": []}
        STEPS.append(rec)
        finish(rec, "not_run",
               "The no-field probe did not prove setDefaultRWConcern unimplemented, so value-bearing forms were not sent, "
               "to avoid changing the cluster-wide default.", "n/a", "Not run.")

    rec, res = step("E.admin.getDefaultRWConcern.after_set_attempts", "E.defaultRWConcern", True,
                    "client.admin.command('getDefaultRWConcern')", lambda: client.admin.command("getDefaultRWConcern"))
    same = rec["outcome"] == "ok" and first_get is not None and \
        {k: v for k, v in rec["result"].items() if k not in ("operationTime", "localUpdateTime", "updateOpTime")} == \
        {k: v for k, v in first_get.items() if k not in ("operationTime", "localUpdateTime", "updateOpTime")}
    finish(rec, "info",
           (f"getDefaultRWConcern after the set attempts returned {json.dumps(rec.get('result'))}, "
            f"{'identical to the first call (ignoring operationTime), so nothing changed' if same else 'DIFFERENT from the first call'}."
            if rec["outcome"] == "ok" else f"getDefaultRWConcern failed with {errs(rec)}."),
           src="matches" if same else "differs", src_note=get_src)

    # --------------------------- X. readConcern inside a transaction (comparison with open source)
    def txn(level):
        with client.start_session() as s:
            s.start_transaction(read_concern=ReadConcern(level))
            try:
                d = coll.find_one({"_id": "seed"}, session=s)
                s.commit_transaction()
                return {"find_one": d, "committed": True}
            except Exception:
                if s.in_transaction:
                    try:
                        s.abort_transaction()
                    except Exception:  # noqa: BLE001
                        pass
                raise

    txn_results = {}
    for level in ("snapshot", "majority", "local", "available", "linearizable"):
        rec, res = step(f"X.txn.readConcern.{level}", "X.readConcern.in_transaction", False,
                        f"with client.start_session() as s: s.start_transaction(read_concern=ReadConcern('{level}')); "
                        f"coll.find_one({{'_id':'seed'}}, session=s); s.commit_transaction()",
                        lambda level=level: txn(level))
        txn_results[level] = rec["outcome"]
        first = rec["wire"][0] if rec["wire"] else {}
        rc_sent = (first.get("command") or {}).get("readConcern")
        rec["verification"] = {"first_command_readConcern_on_wire": rc_sent}
        ours_ok = rec["outcome"] == "ok"
        if level in ("snapshot", "majority", "local"):
            oss_ok = level != "snapshot"
            same = (oss_ok == ours_ok)
            if not oss_ok and not ours_ok:
                e = rec.get("error") or {}
                same = e.get("code") == 115 and e.get("errmsg") == "'Snapshot' read concern is not supported"
            vs, vs_note = ("same" if same else "different"), OSS_TXN
        else:
            vs, vs_note = "not_tested_locally", "The open-source transactions test tried only snapshot, majority and local."
        exp_ok, code, msg, text = rc_src[level]
        if ours_ok:
            reading = (f"A transaction started with readConcern {json.dumps(rc_sent)} ran find_one and committed (ok:1).")
            verdict = "accepted_silently"
        else:
            reading = f"A transaction started with readConcern {json.dumps(rc_sent)} failed with {errs(rec)}."
            verdict = "rejected"
        s, n = src_cmp(rec, exp_ok, code, msg, text)
        finish(rec, verdict, reading, vs, vs_note, src=s, src_note=n)

    if txn_results.get("snapshot") == "ok":
        def canonical():
            with client.start_session() as s:
                s.start_transaction(read_concern=ReadConcern("snapshot"), write_concern=WriteConcern(w="majority"))
                coll.update_one({"_id": "seed"}, {"$set": {"last": "txn_snapshot_majority"}}, session=s)
                s.commit_transaction()
            return {"committed": True}

        rec, res = step("X.txn.snapshot_plus_w_majority_update", "X.readConcern.in_transaction", False,
                        "start_transaction(read_concern=ReadConcern('snapshot'), write_concern=WriteConcern(w='majority')); "
                        "update_one seed; commit_transaction()", canonical)
        seed = vdoc(vcoll, "seed")
        rec["verification"] = {"seed": seed}
        finish(rec, "accepted_silently" if rec["outcome"] == "ok" else "rejected",
               (f"The canonical snapshot + w:majority transaction committed and the update "
                f"{'is' if seed and seed.get('last') == 'txn_snapshot_majority' else 'is NOT'} visible."
                if rec["outcome"] == "ok" else f"The canonical snapshot + w:majority transaction failed with {errs(rec)}."),
               "not_tested_locally", "The open-source test stopped at the snapshot rejection.")

    # isolation inside a transaction per readConcern level: read, outside insert + update, read again
    for level in ("snapshot", "majority", "local"):
        def iso(level=level):
            grp = f"iso_{level}"
            vcoll.insert_one({"_id": f"{grp}_a", "grp": grp})
            with client.start_session() as s:
                s.start_transaction(read_concern=ReadConcern(level))
                try:
                    first = [d["_id"] for d in coll.find({"grp": grp}, session=s)]
                    vcoll.insert_one({"_id": f"{grp}_b", "grp": grp})
                    vcoll.update_one({"_id": f"{grp}_a"}, {"$set": {"changed_outside": True}})
                    time.sleep(0.3)
                    second_docs = list(coll.find({"grp": grp}, session=s))
                    s.commit_transaction()
                except Exception:
                    if s.in_transaction:
                        try:
                            s.abort_transaction()
                        except Exception:  # noqa: BLE001
                            pass
                    raise
            second = [d["_id"] for d in second_docs]
            return {"first_read": first, "second_read": second, "outside_insert_seen": f"{grp}_b" in second,
                    "outside_update_seen": any(d.get("changed_outside") for d in second_docs), "committed": True}

        rec, res = step(f"X.txn.readConcern.{level}.isolation", "X.readConcern.in_transaction", False,
                        f"unmonitored insert iso_{level}_a; start_transaction(read_concern=ReadConcern('{level}')); find grp; "
                        f"unmonitored insert iso_{level}_b and update iso_{level}_a; find grp again in the transaction; commit",
                        iso)
        if rec["outcome"] == "ok":
            r = rec["result"]
            stable = not r["outside_insert_seen"] and not r["outside_update_seen"]
            finish(rec, ("accepted_and_honoured" if stable else "accepted_not_honoured") if level == "snapshot"
                   else ("accepted_stable_snapshot" if stable else "accepted_read_committed"),
                   (f"Inside a readConcern {level} transaction the second read returned {r['second_read']} after the first returned "
                    f"{r['first_read']}; the concurrent committed insert {'was' if r['outside_insert_seen'] else 'was not'} visible and the "
                    f"concurrent update {'was' if r['outside_update_seen'] else 'was not'}, so the transaction "
                    f"{'reads one stable snapshot' if stable else 'does not hold a stable snapshot (read-committed behaviour)'}."),
                   "not_tested_locally", "The open-source transactions test did not check isolation.")
        else:
            finish(rec, "error", f"The isolation sequence failed with {errs(rec)}.", "not_tested_locally",
                   "The open-source transactions test did not check isolation.")

    def causal_then_txn():
        out = {}
        with client.start_session(causal_consistency=True) as s:
            out["pre_find"] = coll.find_one({"_id": "seed"}, session=s)
            out["operation_time_before_txn"] = s.operation_time
            s.start_transaction()
            try:
                out["txn_find"] = coll.find_one({"_id": "seed"}, session=s)
                s.commit_transaction()
                out["committed"] = True
            except Exception:
                if s.in_transaction:
                    try:
                        s.abort_transaction()
                    except Exception:  # noqa: BLE001
                        pass
                raise
        return out

    rec, res = step("X.txn.causal_session_afterClusterTime_at_start", "X.readConcern.in_transaction", False,
                    "with client.start_session(causal_consistency=True) as s: find_one seed; s.start_transaction(); "
                    "find_one seed; s.commit_transaction()", causal_then_txn)
    starts = [ev for ev in rec["wire"] if (ev.get("command") or {}).get("startTransaction")]
    rc_sent = (starts[0].get("command") or {}).get("readConcern") if starts else None
    rec["verification"] = {"startTransaction_command_readConcern_on_wire": rc_sent}
    finish(rec, "accepted_silently" if rec["outcome"] == "ok" else "rejected",
           (f"A transaction started in a causal session after a read carried readConcern {json.dumps(rc_sent)} on its first "
            f"command and committed." if rec["outcome"] == "ok" else
            f"A transaction started in a causal session (first-command readConcern {json.dumps(rc_sent)}) failed with {errs(rec)}."),
           "not_tested_locally", "The open-source transactions test used fresh sessions without afterClusterTime.")

    # ------------------------------------------------------------- Z. cleanup
    final_docs = [to_jsonable(d) for d in vcoll.find({}, {"_id": 1, "label": 1, "last": 1, "n": 1, "grp": 1, "dup": 1}).sort("_id", 1)]
    STATE["final_documents_before_drop"] = final_docs
    rec, res = step("Z.dropDatabase", "cleanup", True, "client['mt_concern'].command('dropDatabase')",
                    lambda: db.command("dropDatabase"))

    def verify_drop():
        names = vc[DB].list_collection_names()
        ld = vc.admin.command(SON([("listDatabases", 1), ("nameOnly", True), ("filter", {"name": DB})]))
        present = any(d.get("name") == DB for d in ld.get("databases", []))
        return {"mt_concern_collections": names, "listDatabases_filter_returned_count": len(ld.get("databases", [])),
                "mt_concern_listed": present}

    v = verify_drop()
    rec["verification"] = v
    finish(rec, "info",
           (f"dropDatabase returned {json.dumps(rec.get('result'))}; afterwards mt_concern has collections "
            f"{v['mt_concern_collections']} and is {'still' if v['mt_concern_listed'] else 'not'} listed."
            if rec["outcome"] == "ok" else f"dropDatabase failed with {errs(rec)}."), "n/a", "Cleanup.")
    STATE["servers_seen_for_reads"] = sorted(servers_seen)
    vc.close()
    client.close()


def write_report(status, fatal=None):
    verdicts = {}
    for s in STEPS:
        verdicts[s["id"]] = {"verdict": s.get("verdict"), "requested_by_spec": s.get("requested_by_spec"),
                             "code": (s.get("error") or {}).get("code"), "codeName": (s.get("error") or {}).get("codeName"),
                             "vs_open_source": s.get("vs_open_source"),
                             "vs_oss_gateway_source_prediction": s.get("vs_oss_gateway_source_prediction")}
    hello = STATE.get("hello") or {}
    bi = STATE.get("buildInfo") or {}
    report = {
        "test": "m-concerns",
        "status": status,
        "fatal": fatal,
        "database": DB,
        "started_utc": STARTED.isoformat(),
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": {
            "resource": "Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus",
            "tier": "M30, one shard, server version 8.0, Premium SSD v2, high availability disabled, public access",
            "connection": "MANAGED_URI (mongodb+srv, plain host, tls=true, authMechanism=SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000); credentials redacted",
            "hello_subset": {k: hello.get(k) for k in ("msg", "isWritablePrimary", "maxWireVersion", "minWireVersion",
                                                       "maxWriteBatchSize", "maxBsonObjectSize", "maxMessageSizeBytes",
                                                       "logicalSessionTimeoutMinutes", "readOnly", "internal",
                                                       "operationTime", "setName", "hosts", "endpointName")
                             if k in hello or k in ("setName", "hosts")},
            "hello_keys": sorted(hello.keys()) if isinstance(hello, dict) else None,
            "buildInfo_subset": {k: bi.get(k) for k in ("version", "gitVersion", "versionArray", "maxBsonObjectSize")},
            "driver_topology": STATE.get("driver_topology"),
            "servers_seen_for_reads": STATE.get("servers_seen_for_reads"),
        },
        "driver": {"pymongo": pymongo.version, "python": sys.version.split()[0]},
        "evidence_scope": ("Observations of the managed Azure DocumentDB service on 2026-11-25 at engine versions "
                           "hello.internal.documentdb_versions ['2.2-1','2.3.0','12.1-1'], maxWireVersion 25, single node "
                           "(HA disabled). Behaviour with HA enabled or with a replica cluster was not tested (phase 1 forbids "
                           "configuration changes)."),
        "decisions_topic": ("findings/phase4/DECISIONS.md, topic 'Transactions, write semantics and bulk operations' (SME topic 9): "
                            "settled items on writeConcern w, j, wtimeout, readConcern levels, readPreference and "
                            "getDefaultRWConcern (all engine_source, read from the open-source gateway) and open items 3 "
                            "(snapshot on Azure) and 8 (Azure gateway parity)."),
        "open_source_comparison_basis": (OSS_NOT_RUN + " The only concern behaviour observed on documentdb-local is readConcern "
                                         "inside a transaction (transactions-labels test), compared in the X steps. Every other "
                                         "step instead carries vs_oss_gateway_source_prediction: whether the managed reply "
                                         "matches what DECISIONS.md predicted from the open-source gateway source."),
        "config_changes": STATE.get("config_changes", []),
        "getDefaultRWConcern_before": STATE.get("getDefaultRWConcern_before"),
        "final_documents_before_drop": STATE.get("final_documents_before_drop"),
        "verdict_index": verdicts,
        "steps": STEPS,
    }
    text = json.dumps(report, indent=2, default=str)
    text = redact(text)
    pw = ENV.get("MANAGED_PASS")
    assert not pw or pw not in text, "password leaked into report"
    with open(os.path.join(HERE, "report.json"), "w") as f:
        f.write(text)
    print(f"report written: status={status}, steps={len(STEPS)}")


def _alarm(signum, frame):
    raise TimeoutError("m-concerns watchdog: 540 s elapsed")


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(540)
    try:
        main()
        write_report("completed")
    except BaseException as e:  # noqa: BLE001
        print("FATAL:", redact(repr(e)))
        print(redact(traceback.format_exc()))
        # best-effort cleanup of the owned database only
        try:
            c = STATE.get("client")
            if c is not None:
                r = c[DB].command("dropDatabase")
                STEPS.append({"id": "Z.dropDatabase.after_fatal", "group": "cleanup", "outcome": "ok",
                              "result": to_jsonable(r), "call": "client['mt_concern'].command('dropDatabase')"})
        except Exception as e2:  # noqa: BLE001
            STEPS.append({"id": "Z.dropDatabase.after_fatal", "group": "cleanup", "outcome": "error",
                          "error": {"type": type(e2).__name__, "message": redact(str(e2))}})
        write_report("partial", fatal=redact(repr(e)))
