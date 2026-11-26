#!/usr/bin/env python
"""m-changestreams: change streams on the managed Azure DocumentDB cluster ddb-samples-shared
(M30, one shard, server 8.0, HA off, no cluster feature enabled). Owns database mt_cs only.

Usage:  .venv/bin/python cs_test.py <section>
Sections (run in this order): a b c d e setup_f x f cleanup
Each section writes steps_<section>.json next to this script and updates state.json
(state holds resume tokens and marker times only; never credentials).
Reads MANAGED_URI / MANAGED_GLOBAL_URI from ../managed.env and never prints or stores them.
"""
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envload import ENV, HERE, Capture, clean_cmd, err_info, j, scrub  # noqa: E402

from bson import Timestamp, json_util  # noqa: E402
from bson.int64 import Int64  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from pymongo.errors import PyMongoError  # noqa: E402

DB = "mt_cs"
STATE = os.path.join(HERE, "state.json")
CLUSTER_CREATED_UTC = "2026-11-25T20:35:33Z"  # systemData.createdAt from az documentdb mongocluster show
OSS_115 = ("documentdb-local 0.117 (findings/phase4/engine-tests/local-gateway-parity steps 05-changeStream-watch and "
           "05b-aggregate-changeStream-raw): collection.watch() and aggregate [{$changeStream: {}}] fail at open with "
           "code 115 CommandNotSupported 'Stage $changeStream is not supported yet in native pipeline'; no later "
           "change-stream behaviour could be tested on the open-source engine.")
OSS_UNTESTED = "Not testable on documentdb-local 0.117: the $changeStream stage itself is rejected there (code 115)."

cap = Capture()
steps = []
open_streams = []


def now_utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def load_state():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json_util.loads(f.read())
    return {}


def save_state(s):
    with open(STATE, "w") as f:
        f.write(json_util.dumps(s, json_options=json_util.CANONICAL_JSON_OPTIONS, indent=1))


def make_client(uri_key="MANAGED_URI", appname="m-changestreams"):
    return MongoClient(ENV[uri_key], serverSelectionTimeoutMS=30000, socketTimeoutMS=90000,
                       appname=appname, event_listeners=[cap])


def strip_raw(o):
    if isinstance(o, dict):
        return {k: strip_raw(v) for k, v in o.items() if k != "_raw"}
    if isinstance(o, list):
        return [strip_raw(v) for v in o]
    return o


def record(step, command, *, response=None, error=None, wire=None, reading="", vs_oss="not_tested_locally",
           oss_note=None, extra=None):
    e = {"step": step, "at_utc": now_utc(), "command": command}
    if response is not None:
        e["response"] = strip_raw(response)
    if error is not None:
        e["error"] = error
    if wire is not None:
        e["wire"] = wire
    e["reading"] = reading
    e["vs_open_source"] = vs_oss
    e["open_source_result"] = oss_note if oss_note else (OSS_UNTESTED if vs_oss == "not_tested_locally" else None)
    if extra:
        e.update(extra)
    steps.append(e)
    print(scrub(f"[{step}] {reading}"), flush=True)


def summarize_wire(evts):
    pairs = {}
    order = []
    for e in evts:
        rid = e["request_id"]
        if rid not in pairs:
            pairs[rid] = {}
            order.append(rid)
        pairs[rid][e["kind"]] = e
    calls, empty_gm = [], []
    for rid in order:
        p = pairs[rid]
        st = p.get("started")
        fin = p.get("succeeded") or p.get("failed")
        name = (st or fin)["command_name"]
        entry = {"command_name": name}
        if st:
            cmd = dict(st["command"])
            cmd.pop("lsid", None)
            entry["command"] = cmd
        if fin:
            entry["duration_ms"] = fin["duration_ms"]
            if "reply" in fin:
                entry["reply"] = fin["reply"]
            if "failure" in fin:
                entry["failure"] = fin["failure"]
        if name == "getMore" and fin and "reply" in fin:
            nb = (fin["reply"].get("cursor") or {}).get("nextBatch")
            if nb == []:
                empty_gm.append(entry)
                continue
        calls.append(entry)
    out = {"calls": calls}
    if empty_gm:
        durs = sorted(x["duration_ms"] for x in empty_gm)
        out["empty_getMore"] = {"count": len(empty_gm), "duration_ms_min": durs[0], "duration_ms_median": durs[len(durs) // 2],
                                "duration_ms_max": durs[-1], "first_sample": empty_gm[0]}
    return out


def token_info(tok):
    if tok is None:
        return None
    if not isinstance(tok, dict):
        return {"type": type(tok).__name__}
    info = {"keys": list(tok.keys())}
    d = tok.get("_data")
    info["_data_type"] = type(d).__name__
    if isinstance(d, str):
        info["_data_len"] = len(d)
        info["_data_is_hex"] = bool(re.fullmatch(r"[0-9A-Fa-f]+", d))
        try:
            b = base64.b64decode(d + "=" * (-len(d) % 4), validate=True)
            info["_data_base64_bytes_hex"] = b.hex()
        except Exception as ex:  # noqa
            info["_data_base64_error"] = str(ex)[:120]
    elif isinstance(d, bytes):
        info["_data_bytes_hex"] = bytes(d).hex()
    return info


def ev_shape(ev):
    sh = {"operationType": ev.get("operationType"), "keys": list(ev.keys()),
          "types": {k: type(v).__name__ for k, v in ev.items()},
          "updateDescription": "present" if "updateDescription" in ev else "absent",
          "fullDocument": ("absent" if "fullDocument" not in ev else ("null" if ev["fullDocument"] is None else "document"))}
    if "fullDocumentBeforeChange" in ev:
        sh["fullDocumentBeforeChange"] = "null" if ev["fullDocumentBeforeChange"] is None else "document"
    ct = ev.get("clusterTime")
    if isinstance(ct, Timestamp):
        sh["clusterTime_t_utc"] = dt.datetime.fromtimestamp(ct.time, dt.timezone.utc).isoformat()
        sh["clusterTime_inc"] = ct.inc
    wt = ev.get("wallTime")
    if isinstance(wt, dt.datetime):
        sh["wallTime_utc"] = wt.isoformat()
    sh["token"] = token_info(ev.get("_id"))
    return sh


def open_stream(target, **kw):
    try:
        s = target.watch(**kw)
        open_streams.append(s)
        return s, None
    except PyMongoError as ex:
        return None, err_info(ex)
    except Exception as ex:  # noqa  (client-side validation errors)
        return None, {"exception": type(ex).__name__, "message": scrub(str(ex))}


def close_stream(s):
    if s is None:
        return
    try:
        s.close()
    except Exception:  # noqa
        pass
    if s in open_streams:
        open_streams.remove(s)


def read_events(stream, want, timeout=30.0, extra_wait=0.0, filter_db=None, t_ref=None):
    t0 = time.monotonic()
    t_ref = t_ref if t_ref is not None else t0
    got, foreign = [], {}
    raw = []
    err = None
    polls = 0

    def handle(ev, phase):
        ns = ev.get("ns") if isinstance(ev.get("ns"), dict) else {}
        if filter_db and ns.get("db") != filter_db:
            key = f"{ns.get('db')}.{ns.get('coll')}:{ev.get('operationType')}"
            foreign[key] = foreign.get(key, 0) + 1
            return
        got.append({"phase": phase, "t_rel_s": round(time.monotonic() - t_ref, 3), "shape": ev_shape(ev), "event": j(ev)})
        raw.append(ev)

    try:
        deadline = t0 + timeout
        while time.monotonic() < deadline and len([g for g in got if g["phase"] == "wanted"]) < want:
            polls += 1
            ev = stream.try_next()
            if ev is None:
                if not stream.alive:
                    break
                time.sleep(0.2)
                continue
            handle(ev, "wanted")
        if extra_wait and stream.alive:
            end2 = time.monotonic() + extra_wait
            while time.monotonic() < end2:
                polls += 1
                ev = stream.try_next()
                if ev is None:
                    if not stream.alive:
                        break
                    time.sleep(0.2)
                    continue
                handle(ev, "extra")
    except PyMongoError as ex:
        err = err_info(ex)
    except Exception as ex:  # noqa
        err = {"exception": type(ex).__name__, "message": scrub(str(ex))}
    try:
        rt = j(stream.resume_token)
    except Exception:  # noqa
        rt = None
    out = {"want": want, "timeout_s": timeout, "extra_wait_s": extra_wait, "got": len(got),
           "elapsed_s": round(time.monotonic() - t0, 2), "try_next_calls": polls, "stream_alive_after": stream.alive,
           "resume_token_after": rt, "error": err, "events": got, "_raw": raw}
    if filter_db:
        out["foreign_events_by_ns_op"] = foreign
    return out


def ops_of(r):
    out = []
    for g in r["events"]:
        ev = g["event"]
        dk = ev.get("documentKey") or {}
        out.append((ev.get("operationType"), dk.get("_id") if isinstance(dk, dict) else None))
    return out


def raw_cs_probe(client, coll_name, cs_opts, getmore_tries=2, max_time_ms=2000, agg_target=None):
    """Raw aggregate + getMore + killCursors in one explicit session, so the exact server reply or error is kept."""
    db = client[DB]
    out = {}
    target = agg_target if agg_target is not None else coll_name
    cmd = {"aggregate": target, "pipeline": [{"$changeStream": cs_opts}], "cursor": {}}
    out["command"] = j(cmd)
    with client.start_session() as s:
        try:
            r = db.command(cmd, session=s)
            out["aggregate_reply"] = clean_cmd(r)
            cid = r["cursor"]["id"]
            gms = []
            for _ in range(getmore_tries):
                if not cid:
                    break
                try:
                    g = db.command({"getMore": Int64(cid), "collection": coll_name, "maxTimeMS": max_time_ms}, session=s)
                    gms.append({"reply": clean_cmd(g)})
                    cid = g["cursor"]["id"]
                except PyMongoError as ex:
                    gms.append({"error": err_info(ex)})
                    cid = 0
            out["getMore"] = gms
            if cid:
                try:
                    k = db.command({"killCursors": coll_name, "cursors": [Int64(cid)]}, session=s)
                    out["killCursors_reply"] = clean_cmd(k)
                except PyMongoError as ex:
                    out["killCursors_error"] = err_info(ex)
        except PyMongoError as ex:
            out["aggregate_error"] = err_info(ex)
    return out


def ensure_coll(db, name):
    try:
        db.create_collection(name)
        return {"created": name}
    except PyMongoError as ex:
        return {"create_error": err_info(ex)}


def fmt_err(e):
    if not e:
        return ""
    return f"code {e.get('code')} {e.get('codeName')} '{e.get('errmsg') or e.get('message')}'"


# ----------------------------------------------------------------------------------------------
def section_a(client, st):
    db = client[DB]
    coll = db["cs_a"]
    m = cap.mark()
    res = ensure_coll(db, "cs_a")
    record("a0-create-collection", "db['mt_cs'].create_collection('cs_a')", response=res,
           wire=summarize_wire(cap.since(m)),
           reading="Collection mt_cs.cs_a created for the baseline stream." if "created" in res else f"create_collection failed: {res}",
           vs_oss="n/a")

    # a1 open
    m = cap.mark()
    s, err = open_stream(coll, max_await_time_ms=1000)
    rt_open = None
    if s is not None:
        try:
            rt_open = j(s.resume_token)
        except Exception:  # noqa
            rt_open = None
    record("a1-collection-watch-open", "stream = db['mt_cs']['cs_a'].watch(max_await_time_ms=1000)",
           response={"opened": s is not None, "stream.resume_token_at_open": rt_open,
                     "resume_token_at_open_info": token_info(rt_open) if isinstance(rt_open, dict) else None},
           error=err, wire=summarize_wire(cap.since(m)),
           reading=("collection.watch() opens on the managed service with no feature enabled (aggregate with $changeStream accepted)."
                    if s is not None else f"collection.watch() fails at open: {fmt_err(err)}."),
           vs_oss="different" if s is not None else "same", oss_note=OSS_115)
    if s is None:
        return

    # a2 writes immediately after open (no getMore issued yet), then read with 30 s timeout
    m = cap.mark()
    t0 = time.monotonic()
    writes = []
    try:
        w = coll.insert_one({"_id": 1, "name": "alpha", "qty": 1})
        writes.append({"op": "insert_one({_id: 1, name: 'alpha', qty: 1})", "t_rel_s": round(time.monotonic() - t0, 3),
                       "result": {"inserted_id": w.inserted_id}})
        w = coll.update_one({"_id": 1}, {"$set": {"qty": 2, "status": "updated"}})
        writes.append({"op": "update_one({_id: 1}, {$set: {qty: 2, status: 'updated'}})", "t_rel_s": round(time.monotonic() - t0, 3),
                       "result": {"matched": w.matched_count, "modified": w.modified_count}})
        w = coll.delete_one({"_id": 1})
        writes.append({"op": "delete_one({_id: 1})", "t_rel_s": round(time.monotonic() - t0, 3),
                       "result": {"deleted": w.deleted_count}})
    except PyMongoError as ex:
        writes.append({"error": err_info(ex)})
    r = read_events(s, 3, timeout=30, extra_wait=3, t_ref=t0)
    types = [g["shape"]["operationType"] for g in r["events"]]
    upd = [g for g in r["events"] if g["shape"]["operationType"] == "update"]
    ud = upd[0]["shape"]["updateDescription"] if upd else "no update event"
    fd_upd = upd[0]["shape"]["fullDocument"] if upd else "n/a"
    ins = [g for g in r["events"] if g["shape"]["operationType"] == "insert"]
    fd_ins = ins[0]["shape"]["fullDocument"] if ins else "n/a"
    reading = (f"After insert, $set update and delete issued right after watch() returned, the stream delivered {r['got']} "
               f"event(s) {types} in {r['elapsed_s']} s (error: {fmt_err(r['error']) or 'none'}); update event updateDescription: {ud}; "
               f"update fullDocument without updateLookup: {fd_upd}; insert fullDocument: {fd_ins}.")
    record("a2-insert-update-delete-read",
           "insert_one / update_one($set) / delete_one on mt_cs.cs_a immediately after watch(); then stream.try_next() loop until 3 events or 30 s (+3 s to catch extras)",
           response={"writes": j(writes), "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
    st["a_events_ops"] = types
    m = cap.mark()
    close_stream(s)
    record("a3-close", "stream.close()", response={"alive_after_close": s.alive}, wire=summarize_wire(cap.since(m)),
           reading="Stream closed; the driver's killCursors reply is in wire.", vs_oss="n/a")

    # a4 raw aggregate (mirrors OSS step 05b) to capture the exact server cursor reply
    m = cap.mark()
    raw = raw_cs_probe(client, "cs_a", {}, getmore_tries=1, max_time_ms=1000)
    ar = raw.get("aggregate_reply") or {}
    cur = ar.get("cursor") or {}
    reading = (f"Raw aggregate [{{$changeStream: {{}}}}] on mt_cs.cs_a succeeds: cursor id non-zero={bool(cur.get('id'))}, "
               f"firstBatch length {len(cur.get('firstBatch') or [])}, postBatchResumeToken {'present' if 'postBatchResumeToken' in cur else 'absent'}, "
               f"operationTime {'present' if 'operationTime' in ar else 'absent'}, $clusterTime {'present' if '$clusterTime' in ar else 'absent'}."
               if "aggregate_reply" in raw else f"Raw $changeStream aggregate rejected: {fmt_err(raw.get('aggregate_error'))}.")
    record("a4-raw-aggregate-changeStream", "db['mt_cs'].command({aggregate: 'cs_a', pipeline: [{$changeStream: {}}], cursor: {}}) then one getMore (maxTimeMS 1000) and killCursors, one explicit session",
           response=raw, reading=reading, vs_oss="different" if "aggregate_reply" in raw else "same", oss_note=OSS_115)


def section_b(client, st):
    db = client[DB]
    coll = db["cs_b"]
    ensure_coll(db, "cs_b")
    m = cap.mark()
    s, err = open_stream(coll, full_document="updateLookup", max_await_time_ms=1000)
    if s is None:
        record("b1-updateLookup-open", "db['mt_cs']['cs_b'].watch(full_document='updateLookup', max_await_time_ms=1000)",
               error=err, wire=summarize_wire(cap.since(m)), reading=f"watch(full_document='updateLookup') fails at open: {fmt_err(err)}.")
        return
    t0 = time.monotonic()
    writes = []
    try:
        coll.insert_one({"_id": 10, "name": "beta", "qty": 1})
        writes.append("insert_one({_id: 10, name: 'beta', qty: 1})")
        coll.update_one({"_id": 10}, {"$set": {"qty": 2}})
        writes.append("update_one({_id: 10}, {$set: {qty: 2}})")
        coll.update_one({"_id": 10}, {"$set": {"qty": 3, "status": "second"}})
        writes.append("update_one({_id: 10}, {$set: {qty: 3, status: 'second'}})")
    except PyMongoError as ex:
        writes.append({"error": err_info(ex)})
    r = read_events(s, 3, timeout=30, t_ref=t0)
    upd = [g["event"] for g in r["events"] if g["event"].get("operationType") == "update"]
    fds = [u.get("fullDocument") for u in upd]
    uds = ["present" if "updateDescription" in u else "absent" for u in upd]
    reading = (f"With full_document='updateLookup' the stream delivered {r['got']} event(s) {[g['shape']['operationType'] for g in r['events']]}; "
               f"the two update events carry fullDocument {json.dumps(fds, default=str)} (both updates were written before the first read) and updateDescription {uds}.")
    record("b1-updateLookup-insert-update-update",
           "stream = db['mt_cs']['cs_b'].watch(full_document='updateLookup', max_await_time_ms=1000); insert_one, update_one($set qty 2), update_one($set qty 3) written before reading; read 3 events, 30 s timeout",
           response={"writes": j(writes), "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
    # b2 update then delete before reading: does updateLookup return null for the update?
    m = cap.mark()
    t0 = time.monotonic()
    writes = []
    try:
        coll.update_one({"_id": 10}, {"$set": {"qty": 4}})
        writes.append("update_one({_id: 10}, {$set: {qty: 4}})")
        coll.delete_one({"_id": 10})
        writes.append("delete_one({_id: 10})")
    except PyMongoError as ex:
        writes.append({"error": err_info(ex)})
    r = read_events(s, 2, timeout=30, extra_wait=3, t_ref=t0)
    upd = [g["event"] for g in r["events"] if g["event"].get("operationType") == "update"]
    dele = [g["event"] for g in r["events"] if g["event"].get("operationType") == "delete"]
    reading = (f"Update then delete written before reading: {r['got']} event(s) {[g['shape']['operationType'] for g in r['events']]}; "
               f"update fullDocument = {json.dumps([u.get('fullDocument', '<absent>') for u in upd], default=str)}; "
               f"delete fullDocument = {json.dumps([d.get('fullDocument', '<absent>') for d in dele], default=str)}.")
    record("b2-updateLookup-update-then-delete",
           "same stream: update_one({_id: 10}, {$set: {qty: 4}}) then delete_one({_id: 10}) before reading; read 2 events, 30 s timeout (+3 s)",
           response={"writes": writes, "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
    close_stream(s)


def section_c(client, st):
    db = client[DB]
    ensure_coll(db, "cs_c1")
    ensure_coll(db, "cs_c2")
    # c1 database-level
    m = cap.mark()
    s, err = open_stream(db, max_await_time_ms=1000)
    if s is None:
        record("c1-db-watch", "db['mt_cs'].watch(max_await_time_ms=1000)", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"Database-level watch() fails at open: {fmt_err(err)}.")
    else:
        t0 = time.monotonic()
        writes = []
        try:
            db["cs_c1"].insert_one({"_id": "c1-1"})
            writes.append("db['mt_cs']['cs_c1'].insert_one({_id: 'c1-1'})")
            db["cs_c2"].insert_one({"_id": "c2-1"})
            writes.append("db['mt_cs']['cs_c2'].insert_one({_id: 'c2-1'})")
        except PyMongoError as ex:
            writes.append({"error": err_info(ex)})
        r = read_events(s, 2, timeout=30, extra_wait=2, t_ref=t0)
        nss = [g["event"].get("ns") for g in r["events"]]
        reading = (f"Database-level watch() opened and delivered {r['got']} event(s) from {json.dumps(nss)} in {r['elapsed_s']} s "
                   f"(error: {fmt_err(r['error']) or 'none'}).")
        record("c1-db-watch", "stream = db['mt_cs'].watch(max_await_time_ms=1000); insert one doc into cs_c1 and one into cs_c2; read 2 events, 30 s timeout (+2 s)",
               response={"writes": writes, "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
        close_stream(s)
    # c2 client (cluster) level, no filter
    m = cap.mark()
    s, err = open_stream(client, max_await_time_ms=1000)
    if s is None:
        record("c2-client-watch", "client.watch(max_await_time_ms=1000)", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"Cluster-level client.watch() fails at open: {fmt_err(err)}.")
    else:
        t0 = time.monotonic()
        try:
            db["cs_c1"].insert_one({"_id": "c1-2"})
            writes = ["db['mt_cs']['cs_c1'].insert_one({_id: 'c1-2'})"]
        except PyMongoError as ex:
            writes = [{"error": err_info(ex)}]
        r = read_events(s, 1, timeout=30, extra_wait=2, filter_db=DB, t_ref=t0)
        reading = (f"Cluster-level client.watch() opened and delivered {r['got']} mt_cs event(s) {ops_of(r)} in {r['elapsed_s']} s; "
                   f"events from other databases seen meanwhile (ns:op counts, contents not recorded): {json.dumps(r.get('foreign_events_by_ns_op'))}; "
                   f"error: {fmt_err(r['error']) or 'none'}.")
        record("c2-client-watch", "stream = client.watch(max_await_time_ms=1000); insert one doc into mt_cs.cs_c1; read until 1 mt_cs event or 30 s (+2 s); events of other databases only counted by ns and operationType",
               response={"writes": writes, "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
        close_stream(s)
    # c3 client level with server-side $match on ns.db
    m = cap.mark()
    s, err = open_stream(client, pipeline=[{"$match": {"ns.db": DB}}], max_await_time_ms=1000)
    if s is None:
        record("c3-client-watch-match-ns", "client.watch([{$match: {'ns.db': 'mt_cs'}}], max_await_time_ms=1000)", error=err,
               wire=summarize_wire(cap.since(m)), reading=f"Cluster-level watch with $match on ns.db fails at open: {fmt_err(err)}.")
    else:
        t0 = time.monotonic()
        try:
            db["cs_c2"].insert_one({"_id": "c2-2"})
            writes = ["db['mt_cs']['cs_c2'].insert_one({_id: 'c2-2'})"]
        except PyMongoError as ex:
            writes = [{"error": err_info(ex)}]
        r = read_events(s, 1, timeout=30, extra_wait=2, filter_db=DB, t_ref=t0)
        reading = (f"Cluster-level watch with server-side $match on ns.db delivered {r['got']} mt_cs event(s) {ops_of(r)} and "
                   f"{sum((r.get('foreign_events_by_ns_op') or {}).values())} event(s) from other databases (error: {fmt_err(r['error']) or 'none'}).")
        record("c3-client-watch-match-ns", "stream = client.watch([{$match: {'ns.db': 'mt_cs'}}], max_await_time_ms=1000); insert one doc into mt_cs.cs_c2; read 1 event, 30 s (+2 s)",
               response={"writes": writes, "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
        close_stream(s)


def section_d(client, st):
    db = client[DB]
    coll = db["cs_d"]
    ensure_coll(db, "cs_d")
    # d1 capture token
    m = cap.mark()
    s, err = open_stream(coll, max_await_time_ms=1000)
    if s is None:
        record("d1-capture-token", "db['mt_cs']['cs_d'].watch()", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() fails at open: {fmt_err(err)}.")
        return
    t0 = time.monotonic()
    coll.insert_one({"_id": "d-1", "v": 1})
    coll.insert_one({"_id": "d-2", "v": 2})
    r = read_events(s, 2, timeout=30, t_ref=t0)
    tok = None
    raw_tok_obj = None
    if r["_raw"]:
        raw_tok_obj = r["_raw"][-1]["_id"]  # exact BSON form from the driver
        tok = j(raw_tok_obj)
    stream_rt = s.resume_token
    close_stream(s)
    st["d_event_token"] = raw_tok_obj
    st["d_stream_resume_token"] = stream_rt
    same = (j(stream_rt) == tok) if tok is not None else None
    reading = (f"Captured resume token after 2 inserts: last event _id {json.dumps(tok)}; stream.resume_token after the batch "
               f"{'equals' if same else 'differs from'} the last event _id ({json.dumps(j(stream_rt))}); stream closed.")
    record("d1-capture-token", "stream = db['mt_cs']['cs_d'].watch(max_await_time_ms=1000); insert d-1, d-2; read 2 events (30 s); token = last event['_id']; also stream.resume_token; stream.close()",
           response={"read": r, "event_token": tok, "event_token_info": token_info(raw_tok_obj), "stream.resume_token": j(stream_rt),
                     "stream_resume_token_info": token_info(stream_rt)},
           wire=summarize_wire(cap.since(m)), reading=reading)
    if raw_tok_obj is None:
        return
    # d2 missed writes
    m = cap.mark()
    coll.insert_one({"_id": "d-3", "v": 3})
    coll.update_one({"_id": "d-3"}, {"$set": {"v": 33}})
    coll.delete_one({"_id": "d-1"})
    record("d2-missed-writes", "with no stream open: insert_one({_id: 'd-3', v: 3}); update_one({_id: 'd-3'}, {$set: {v: 33}}); delete_one({_id: 'd-1'})",
           response={"writes": ["insert d-3", "update d-3 $set v 33", "delete d-1"]}, wire=summarize_wire(cap.since(m)),
           reading="Three writes made while no stream was open.")
    expected = [("insert", "d-3"), ("update", "d-3"), ("delete", "d-1")]
    # d3 resume_after
    m = cap.mark()
    s, err = open_stream(coll, resume_after=raw_tok_obj, max_await_time_ms=1000)
    if s is None:
        record("d3-resume-after", "db['mt_cs']['cs_d'].watch(resume_after=token)", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch(resume_after=token) fails at open: {fmt_err(err)}.")
    else:
        r = read_events(s, 3, timeout=30, extra_wait=3)
        got = ops_of(r)
        ok = got[:3] == expected and len(got) == 3
        reading = (f"resume_after=token delivered {got} (expected {expected}); "
                   f"{'exactly the three missed events in order, no replay of d-2 and nothing extra' if ok else 'NOT exactly the missed events'}; error: {fmt_err(r['error']) or 'none'}.")
        record("d3-resume-after", "stream = db['mt_cs']['cs_d'].watch(resume_after=token, max_await_time_ms=1000); read 3 events, 30 s (+3 s)",
               response={"read": r, "expected": expected, "match": ok}, wire=summarize_wire(cap.since(m)), reading=reading)
        close_stream(s)
    # d4 start_after with the same token
    m = cap.mark()
    s, err = open_stream(coll, start_after=raw_tok_obj, max_await_time_ms=1000)
    if s is None:
        record("d4-start-after", "db['mt_cs']['cs_d'].watch(start_after=token)", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch(start_after=token) fails at open: {fmt_err(err)}.")
    else:
        r = read_events(s, 3, timeout=30, extra_wait=2)
        got = ops_of(r)
        ok = got[:3] == expected and len(got) == 3
        record("d4-start-after", "stream = db['mt_cs']['cs_d'].watch(start_after=token, max_await_time_ms=1000); read 3 events, 30 s (+2 s)",
               response={"read": r, "expected": expected, "match": ok}, wire=summarize_wire(cap.since(m)),
               reading=f"start_after=token delivered {got}; {'same three missed events as resume_after' if ok else 'differs from resume_after'}; error: {fmt_err(r['error']) or 'none'}.")
        close_stream(s)
    # d5 idle stream token (postBatchResumeToken) checkpoint
    m = cap.mark()
    s, err = open_stream(coll, max_await_time_ms=1000)
    pbrt = None
    if s is not None:
        e1 = s.try_next()
        e2 = s.try_next()
        pbrt = s.resume_token
        close_stream(s)
        idle_events = [j(e) for e in (e1, e2) if e is not None]
    else:
        idle_events = []
    wire_idle = summarize_wire(cap.since(m))
    if pbrt is None:
        record("d5-idle-token", "stream = db['mt_cs']['cs_d'].watch(); stream.try_next() x2 with no writes; stream.resume_token",
               response={"idle_events": idle_events, "stream.resume_token": None}, error=err, wire=wire_idle,
               reading="An idle stream exposes no resume token (stream.resume_token is None): the server sent no postBatchResumeToken, so an idle consumer cannot checkpoint.")
        return
    m = cap.mark()
    coll.insert_one({"_id": "d-4"})
    coll.insert_one({"_id": "d-5"})
    s, err = open_stream(coll, resume_after=pbrt, max_await_time_ms=1000)
    if s is None:
        record("d5-idle-token", "watch(resume_after=idle stream.resume_token)", error=err, wire=summarize_wire(cap.since(m)),
               response={"idle_events": idle_events, "idle_resume_token": j(pbrt), "idle_token_info": token_info(pbrt), "wire_idle": wire_idle},
               reading=f"Resuming from the idle stream's token fails at open: {fmt_err(err)}.")
        return
    r = read_events(s, 2, timeout=30, extra_wait=2)
    got = ops_of(r)
    ok = got == [("insert", "d-4"), ("insert", "d-5")]
    record("d5-idle-token",
           "stream = watch(); try_next() x2 with no writes; tok = stream.resume_token (postBatchResumeToken); close; insert d-4, d-5; watch(resume_after=tok); read 2 events, 30 s (+2 s)",
           response={"idle_events": idle_events, "idle_resume_token": j(pbrt), "idle_token_info": token_info(pbrt), "wire_idle": wire_idle, "read": r, "match": ok},
           wire=summarize_wire(cap.since(m)),
           reading=(f"An idle stream exposes a resume token ({json.dumps(j(pbrt))}) and resuming from it delivered {got}: "
                    f"{'exactly the two later inserts' if ok else 'not exactly the two later inserts'}; error: {fmt_err(r['error']) or 'none'}."))
    close_stream(s)


def fabricate(real):
    d = real.get("_data") if isinstance(real, dict) else None
    fakes = [
        ("garbage-string", {"_data": "garbage-not-a-resume-token"}),
        ("empty-string", {"_data": ""}),
        ("int-data", {"_data": 12345}),
        ("empty-document", {}),
        ("wrong-field", {"foo": "bar"}),
        ("mongodb-style-hex-token", {"_data": "8267A1B2C3000000012B022C0100296E5A1004A1B2C3D4E5F60718293A4B5C6D7E8F90463C5F6964003C6162630004"}),
    ]
    if isinstance(d, str) and d:
        fakes.append(("real-truncated-to-half", {"_data": d[: max(1, len(d) // 2)]}))
        fakes.append(("real-plus-AAAA-suffix", {"_data": d + "AAAA"}))
        b = None
        try:
            b = base64.b64decode(d + "=" * (-len(d) % 4), validate=True)
        except Exception:  # noqa
            b = None
        if re.fullmatch(r"[0-9A-Fa-f]+", d):
            fakes.append(("real-last-hex-byte-changed", {"_data": d[:-2] + ("00" if d[-2:].upper() != "00" else "FF")}))
            fakes.append(("all-F-same-length-hex", {"_data": "F" * len(d)}))
            fakes.append(("all-0-same-length-hex", {"_data": "0" * len(d)}))
        elif b:
            fl = bytearray(b)
            fl[-1] ^= 0xFF
            fakes.append(("real-last-byte-flipped-valid-base64", {"_data": base64.b64encode(bytes(fl)).decode()}))
            fakes.append(("all-0xFF-same-length-valid-base64", {"_data": base64.b64encode(b"\xff" * len(b)).decode()}))
            fakes.append(("all-zero-same-length-valid-base64", {"_data": base64.b64encode(b"\x00" * len(b)).decode()}))
            txt = None
            try:
                txt = b.decode("ascii")
            except Exception:  # noqa
                txt = None
            if txt and re.fullmatch(r"\d+(:\d+)+", txt):
                parts = txt.split(":")
                enc = lambda t: {"_data": base64.b64encode(t.encode()).decode()}  # noqa: E731
                lsn = int(parts[2]) if len(parts) > 2 else 0
                def with_lsn(v):
                    q = list(parts)
                    if len(q) > 2:
                        q[2] = str(v)
                    if len(q) > 4 and q[4] != "0":
                        q[4] = str(v)
                    return ":".join(q)
                fakes.append(("structured-future-position (x100 third field)", enc(with_lsn(lsn * 100))))
                fakes.append(("structured-ancient-position (third field 1)", enc(with_lsn(1))))
                fakes.append(("structured-position-minus-1", enc(with_lsn(max(1, lsn - 1)))))
                q = list(parts); q[0] = "9"
                fakes.append(("structured-version-9", enc(":".join(q))))
                fakes.append(("structured-three-fields-only", enc(":".join(parts[:3]))))
                q = list(parts); q[2] = "abc"
                fakes.append(("structured-non-numeric-field", enc(":".join(q))))
                fakes.append(("base64-of-plain-text", enc("hello world")))
    fakes.append(("non-document-string", "not-a-document"))
    return fakes


def section_e(client, st):
    db = client[DB]
    coll = db["cs_e"]
    ensure_coll(db, "cs_e")
    # real token from cs_e
    m = cap.mark()
    s, err = open_stream(coll, max_await_time_ms=1000)
    real = None
    if s is not None:
        coll.insert_one({"_id": "e-1"})
        r = read_events(s, 1, timeout=30)
        if r["_raw"]:
            real = r["_raw"][0]["_id"]
        close_stream(s)
    else:
        r = None
    record("e0-real-token", "stream = db['mt_cs']['cs_e'].watch(); insert_one({_id: 'e-1'}); read 1 event; token = event['_id']; close",
           response={"read": r, "real_token": j(real), "real_token_info": token_info(real)}, error=err, wire=summarize_wire(cap.since(m)),
           reading=f"Real token captured on cs_e for comparison: {json.dumps(j(real))}." if real else "No real token could be captured.")
    st["e_real_token"] = real
    # e1 fabricated / malformed tokens via raw aggregate
    for name, fake in fabricate(real or {}):
        raw = raw_cs_probe(client, "cs_e", {"resumeAfter": fake}, getmore_tries=1, max_time_ms=2000)
        if "aggregate_error" in raw:
            reading = f"resumeAfter {name}: rejected at aggregate with {fmt_err(raw['aggregate_error'])}; labels {raw['aggregate_error'].get('errorLabels_server')}."
        else:
            gm = raw.get("getMore") or []
            gerr = next((g["error"] for g in gm if "error" in g), None)
            nb = [len(((g.get("reply") or {}).get("cursor") or {}).get("nextBatch") or []) for g in gm if "reply" in g]
            reading = (f"resumeAfter {name}: aggregate accepted (cursor opened); first getMore "
                       + (f"failed with {fmt_err(gerr)}." if gerr else f"returned nextBatch sizes {nb} with no error."))
        record(f"e1-fabricated-{name}", f"raw: db['mt_cs'].command({{aggregate: 'cs_e', pipeline: [{{$changeStream: {{resumeAfter: {json.dumps(j(fake))}}}}}], cursor: {{}}}}) then one getMore (maxTimeMS 2000), one explicit session",
               response=raw, reading=reading)
    # e1-driver: what the driver surfaces for one malformed and one well-formed fabricated token
    for name, fake in [f for f in fabricate(real or {}) if f[0] in ("garbage-string", "real-last-byte-flipped-valid-base64", "structured-future-position (x100 third field)", "structured-ancient-position (third field 1)", "real-last-hex-byte-changed")]:
        m = cap.mark()
        s, err = open_stream(coll, resume_after=fake, max_await_time_ms=1000)
        r = None
        if s is not None:
            r = read_events(s, 1, timeout=8)
            close_stream(s)
        reading = (f"Driver watch(resume_after={name}) raises at open: {fmt_err(err)}; driver labels {err.get('errorLabels_driver') if err else None}."
                   if s is None else f"Driver watch(resume_after={name}) opened; reading 8 s gave {r['got']} event(s), error {fmt_err(r['error']) or 'none'}.")
        record(f"e1-driver-{name}", f"db['mt_cs']['cs_e'].watch(resume_after={json.dumps(j(fake))}, max_await_time_ms=1000); try_next up to 8 s",
               response={"read": r}, error=err, wire=summarize_wire(cap.since(m)), reading=reading)
    # e2 token from another collection (cs_d) used on cs_e
    dtok = st.get("d_event_token")
    if dtok:
        raw = raw_cs_probe(client, "cs_e", {"resumeAfter": dtok}, getmore_tries=2, max_time_ms=2000)
        if "aggregate_error" in raw:
            reading = f"A valid token from mt_cs.cs_d used on mt_cs.cs_e is rejected at aggregate with {fmt_err(raw['aggregate_error'])}."
        else:
            gm = raw.get("getMore") or []
            gerr = next((g["error"] for g in gm if "error" in g), None)
            batches = [((g.get("reply") or {}).get("cursor") or {}).get("nextBatch") for g in gm if "reply" in g]
            fb = ((raw.get("aggregate_reply") or {}).get("cursor") or {}).get("firstBatch")
            reading = (f"A valid token from mt_cs.cs_d used on mt_cs.cs_e is accepted at aggregate; firstBatch {len(fb or [])} event(s), getMore "
                       + (f"error {fmt_err(gerr)}." if gerr else f"batches sizes {[len(b or []) for b in batches]} with no error."))
        record("e2-token-from-other-collection", "raw: aggregate on cs_e with $changeStream {resumeAfter: <token captured on cs_d in d1>} then up to 2 getMores",
               response=raw, reading=reading)
    # e3 dropped and recreated collection
    ensure_coll(db, "cs_e2")
    c2 = db["cs_e2"]
    m = cap.mark()
    s, err = open_stream(c2, max_await_time_ms=1000)
    if s is None:
        record("e3a-token-before-drop", "db['mt_cs']['cs_e2'].watch()", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() fails at open: {fmt_err(err)}.")
        return
    c2.insert_one({"_id": "before-drop-1"})
    r = read_events(s, 1, timeout=30)
    t_before = r["_raw"][0]["_id"] if r["_raw"] else None
    record("e3a-token-before-drop", "stream = db['mt_cs']['cs_e2'].watch(max_await_time_ms=1000); insert_one({_id: 'before-drop-1'}); read 1 event; T_before = event['_id']",
           response={"read": r, "T_before": j(t_before)}, wire=summarize_wire(cap.since(m)),
           reading=f"Token before drop captured: {json.dumps(j(t_before))}.")
    # drop while the stream is open
    m = cap.mark()
    drop_reply = None
    try:
        drop_reply = db.command({"drop": "cs_e2"})
    except PyMongoError as ex:
        drop_reply = {"error": err_info(ex)}
    r = read_events(s, 5, timeout=20)
    evts = [g["event"] for g in r["events"]]
    t_drop = next((e["_id"] for e in r["_raw"] if e.get("operationType") == "drop"), None)
    t_inval = next((e["_id"] for e in r["_raw"] if e.get("operationType") == "invalidate"), None)
    record("e3b-drop-with-stream-open", "db['mt_cs'].command({drop: 'cs_e2'}) while the cs_e2 stream is open; read up to 5 events or 20 s (stops early if the stream dies)",
           response={"drop_reply": j(drop_reply), "read": r}, wire=summarize_wire(cap.since(m)),
           reading=(f"Dropping the watched collection produced {[e.get('operationType') for e in evts]} on the open stream within {r['elapsed_s']} s; "
                    f"stream alive afterwards: {r['stream_alive_after']}; error: {fmt_err(r['error']) or 'none'}."))
    close_stream(s)
    # recreate
    m = cap.mark()
    ensure_coll(db, "cs_e2")
    c2.insert_one({"_id": "after-recreate-1"})
    record("e3c-recreate", "db['mt_cs'].create_collection('cs_e2'); insert_one({_id: 'after-recreate-1'})",
           response={"recreated": True}, wire=summarize_wire(cap.since(m)), reading="cs_e2 recreated and one document inserted.", vs_oss="n/a")
    trials = [("e3d-resume-after-T_before", "resume_after", t_before), ("e3e-start-after-T_before", "start_after", t_before)]
    if t_drop is not None:
        trials.append(("e3f-resume-after-T_drop", "resume_after", t_drop))
    if t_inval is not None:
        trials.append(("e3g-resume-after-T_invalidate", "resume_after", t_inval))
        trials.append(("e3h-start-after-T_invalidate", "start_after", t_inval))
    for i, (sid, opt, tok) in enumerate(trials):
        if tok is None:
            continue
        m = cap.mark()
        s, err = open_stream(c2, max_await_time_ms=1000, **{opt: tok})
        r = None
        if s is not None:
            c2.insert_one({"_id": f"after-recreate-probe-{i}"})
            r = read_events(s, 5, timeout=15)
            close_stream(s)
        reading = (f"watch({opt}=<{sid.split('-', 3)[-1]}>) on the recreated collection raises at open: {fmt_err(err)}; server labels {err.get('errorLabels_server') if err else None}."
                   if s is None else f"watch({opt}=<{sid.split('-', 3)[-1]}>) on the recreated collection opened; after a probe insert it delivered {ops_of(r)} in 15 s; error: {fmt_err(r['error']) or 'none'}.")
        record(sid, f"db['mt_cs']['cs_e2'].watch({opt}={json.dumps(j(tok))}, max_await_time_ms=1000); insert_one({{_id: 'after-recreate-probe-{i}'}}); read up to 5 events, 15 s",
               response={"read": r}, error=err, wire=summarize_wire(cap.since(m)), reading=reading)
    # raw form of the most interesting case for the exact server reply
    raw = raw_cs_probe(client, "cs_e2", {"resumeAfter": t_before}, getmore_tries=2, max_time_ms=2000)
    if "aggregate_error" in raw:
        reading = f"Raw resumeAfter T_before on the recreated collection: aggregate rejected with {fmt_err(raw['aggregate_error'])}."
    else:
        gm = raw.get("getMore") or []
        gerr = next((g["error"] for g in gm if "error" in g), None)
        fb = ((raw.get("aggregate_reply") or {}).get("cursor") or {}).get("firstBatch") or []
        nbs = [[(e.get("operationType"), (e.get("documentKey") or {}).get("_id")) for e in (((g.get("reply") or {}).get("cursor") or {}).get("nextBatch") or [])] for g in gm if "reply" in g]
        reading = (f"Raw resumeAfter T_before on the recreated collection: aggregate accepted, firstBatch {[(e.get('operationType'), (e.get('documentKey') or {}).get('_id')) for e in fb]}, getMore "
                   + (f"error {fmt_err(gerr)}." if gerr else f"batches {nbs}."))
    record("e3i-raw-resume-after-T_before", "raw: aggregate on cs_e2 with $changeStream {resumeAfter: T_before} then up to 2 getMores (maxTimeMS 2000)",
           response=raw, reading=reading)


def section_setup_f(client, st):
    db = client[DB]
    coll = db["cs_f"]
    ensure_coll(db, "cs_f")
    m = cap.mark()
    hello = client.admin.command("hello")
    ops = []
    with client.start_session() as s:
        t_wall = time.time()
        coll.insert_one({"_id": "f-1", "marker": "f", "written_utc": now_utc()}, session=s)
        ops.append(s.operation_time)
        coll.update_one({"_id": "f-1"}, {"$set": {"marker": "f-updated"}}, session=s)
        ops.append(s.operation_time)
        coll.delete_one({"_id": "f-1"}, session=s)
        ops.append(s.operation_time)
    st["f_marker_wall"] = t_wall
    st["f_marker_ops"] = ops
    hop = hello.get("operationTime")
    record("f0-markers", "hello; then with client.start_session() as s: insert_one f-1, update_one f-1 $set, delete_one f-1 on mt_cs.cs_f (session=s), reading s.operation_time after each",
           response={"marker_wall_utc": dt.datetime.fromtimestamp(t_wall, dt.timezone.utc).isoformat(),
                     "session_operation_times": j(ops), "hello_operationTime": j(hop),
                     "hello_operationTime_utc": dt.datetime.fromtimestamp(hop.time, dt.timezone.utc).isoformat() if isinstance(hop, Timestamp) else None},
           wire=summarize_wire(cap.since(m)),
           reading=(f"Marker writes done at {dt.datetime.fromtimestamp(t_wall, dt.timezone.utc).isoformat()}; the server returned operationTime "
                    f"{j(ops)} (session.operation_time) for them."), vs_oss="n/a")


def section_x(client, st):
    db = client[DB]
    # x0 watch a collection that does not exist yet
    m = cap.mark()
    cx = db["cs_x0_absent"]
    s, err = open_stream(cx, max_await_time_ms=1000)
    r = None
    if s is not None:
        cx.insert_one({"_id": "x0-1"})
        r = read_events(s, 1, timeout=20, extra_wait=2)
        close_stream(s)
    record("x0-watch-nonexistent-collection", "db['mt_cs']['cs_x0_absent'].watch() before the collection exists; insert_one({_id: 'x0-1'}) (creates it); read 1 event, 20 s (+2 s)",
           response={"read": r}, error=err, wire=summarize_wire(cap.since(m)),
           reading=(f"watch() on a not-yet-existing collection fails at open: {fmt_err(err)}." if s is None else
                    f"watch() on a not-yet-existing collection opens; the insert that creates it delivered {ops_of(r)} (error: {fmt_err(r['error']) or 'none'})."))
    # x1 updateDescription opt-in
    ensure_coll(db, "cs_x1")
    m = cap.mark()
    coll_mod = {}
    try:
        coll_mod["reply"] = j(db.command({"collMod": "cs_x1", "enableUpdateDescription": {"enabled": True}}))
    except PyMongoError as ex:
        coll_mod["error"] = err_info(ex)
    try:
        info = list(db.list_collections(filter={"name": "cs_x1"}))
        coll_mod["listCollections_options"] = j(info[0].get("options") if info else None)
    except PyMongoError as ex:
        coll_mod["listCollections_error"] = err_info(ex)
    record("x1a-collMod-enableUpdateDescription", "db['mt_cs'].command({collMod: 'cs_x1', enableUpdateDescription: {enabled: true}}); list_collections(filter={name: 'cs_x1'}) options",
           response=coll_mod, wire=summarize_wire(cap.since(m)),
           reading=(f"collMod enableUpdateDescription accepted ({json.dumps(coll_mod.get('reply'))}); collection options now {json.dumps(coll_mod.get('listCollections_options'))}."
                    if "reply" in coll_mod else f"collMod enableUpdateDescription rejected: {fmt_err(coll_mod.get('error'))}."))
    c1 = db["cs_x1"]
    m = cap.mark()
    s, err = open_stream(c1, max_await_time_ms=1000)
    if s is not None:
        t0 = time.monotonic()
        ops = []
        try:
            c1.insert_one({"_id": "x1-1", "a": 1, "b": 2, "arr": [1, 2, 3]}); ops.append("insert {_id:'x1-1', a:1, b:2, arr:[1,2,3]}")
            c1.update_one({"_id": "x1-1"}, {"$set": {"a": 10}, "$unset": {"b": ""}}); ops.append("update {$set:{a:10}, $unset:{b:''}}")
            c1.update_one({"_id": "x1-1"}, {"$inc": {"a": 1}}); ops.append("update {$inc:{a:1}}")
            c1.update_one({"_id": "x1-1"}, {"$push": {"arr": 4}}); ops.append("update {$push:{arr:4}}")
            c1.update_one({"_id": "x1-1"}, [{"$set": {"c": {"$add": ["$a", 1]}}}]); ops.append("update pipeline [{$set:{c:{$add:['$a',1]}}}]")
            c1.replace_one({"_id": "x1-1"}, {"z": 1}); ops.append("replace_one {_id:'x1-1'} -> {z:1}")
        except PyMongoError as ex:
            ops.append({"error": err_info(ex)})
        r = read_events(s, 6, timeout=30, extra_wait=2, t_ref=t0)
        summ = [(g["shape"]["operationType"], g["shape"]["updateDescription"], g["event"].get("updateDescription")) for g in r["events"]]
        reading = (f"After collMod, update events carry updateDescription as follows (op, presence, value): {json.dumps(summ, default=str)}; "
                   f"error: {fmt_err(r['error']) or 'none'}.")
        record("x1b-updateDescription-after-collMod", "stream = db['mt_cs']['cs_x1'].watch(); insert; update $set+$unset; update $inc; update $push; pipeline-style update; replace_one; read 6 events, 30 s (+2 s)",
               response={"writes": j(ops), "read": r}, wire=summarize_wire(cap.since(m)), reading=reading)
        close_stream(s)
    else:
        record("x1b-updateDescription-after-collMod", "db['mt_cs']['cs_x1'].watch()", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() fails at open: {fmt_err(err)}.")
    # x2 pre-images
    ensure_coll(db, "cs_x2")
    m = cap.mark()
    pm = {}
    try:
        pm["reply"] = j(db.command({"collMod": "cs_x2", "changeStreamPreAndPostImages": {"enabled": True}}))
    except PyMongoError as ex:
        pm["error"] = err_info(ex)
    record("x2a-collMod-changeStreamPreAndPostImages", "db['mt_cs'].command({collMod: 'cs_x2', changeStreamPreAndPostImages: {enabled: true}})",
           response=pm, wire=summarize_wire(cap.since(m)),
           reading=(f"collMod changeStreamPreAndPostImages accepted ({json.dumps(pm.get('reply'))})." if "reply" in pm
                    else f"collMod changeStreamPreAndPostImages rejected: {fmt_err(pm.get('error'))}."))
    c2 = db["cs_x2"]
    c2.insert_one({"_id": "x2-1", "v": 1})
    m = cap.mark()
    s, err = open_stream(c2, full_document_before_change="whenAvailable", full_document="whenAvailable", max_await_time_ms=1000)
    if s is not None:
        c2.update_one({"_id": "x2-1"}, {"$set": {"v": 2}})
        c2.delete_one({"_id": "x2-1"})
        r = read_events(s, 2, timeout=30, extra_wait=2)
        summ = [(g["shape"]["operationType"], g["event"].get("fullDocumentBeforeChange", "<absent>"), g["event"].get("fullDocument", "<absent>")) for g in r["events"]]
        record("x2b-preimages-whenAvailable", "stream = db['mt_cs']['cs_x2'].watch(full_document_before_change='whenAvailable', full_document='whenAvailable'); update_one $set v 2; delete_one; read 2 events, 30 s (+2 s)",
               response={"read": r}, wire=summarize_wire(cap.since(m)),
               reading=f"With pre/post images enabled: (op, fullDocumentBeforeChange, fullDocument) = {json.dumps(summ, default=str)}; error: {fmt_err(r['error']) or 'none'}.")
        close_stream(s)
    else:
        record("x2b-preimages-whenAvailable", "db['mt_cs']['cs_x2'].watch(full_document_before_change='whenAvailable', full_document='whenAvailable')",
               error=err, wire=summarize_wire(cap.since(m)), reading=f"watch() with pre/post-image options fails at open: {fmt_err(err)}.")
    ensure_coll(db, "cs_x2b")
    c3 = db["cs_x2b"]
    c3.insert_one({"_id": "x2b-1", "v": 1})
    m = cap.mark()
    s, err = open_stream(c3, full_document_before_change="required", max_await_time_ms=1000)
    if s is not None:
        c3.update_one({"_id": "x2b-1"}, {"$set": {"v": 2}})
        r = read_events(s, 1, timeout=15)
        record("x2c-preimage-required-not-enabled", "stream = db['mt_cs']['cs_x2b'].watch(full_document_before_change='required') on a collection without pre-images; update_one; read 1 event, 15 s",
               response={"read": r}, wire=summarize_wire(cap.since(m)),
               reading=(f"fullDocumentBeforeChange 'required' without pre-images enabled: {r['got']} event(s) "
                        f"{[(g['shape']['operationType'], g['event'].get('fullDocumentBeforeChange', '<absent>')) for g in r['events']]}, error {fmt_err(r['error']) or 'none'}."))
        close_stream(s)
    else:
        record("x2c-preimage-required-not-enabled", "db['mt_cs']['cs_x2b'].watch(full_document_before_change='required')", error=err,
               wire=summarize_wire(cap.since(m)), reading=f"'required' pre-image option without enablement fails at open: {fmt_err(err)}.")
    # x3 showExpandedEvents
    ensure_coll(db, "cs_x3")
    c4 = db["cs_x3"]
    m = cap.mark()
    s, err = open_stream(c4, show_expanded_events=True, max_await_time_ms=1000)
    if s is not None:
        try:
            c4.create_index("k", name="k_1")
        except PyMongoError as ex:
            pass
        c4.insert_one({"_id": "x3-1", "k": 1})
        r = read_events(s, 3, timeout=15)
        record("x3-showExpandedEvents", "stream = db['mt_cs']['cs_x3'].watch(show_expanded_events=True); create_index('k'); insert_one; read up to 3 events, 15 s",
               response={"read": r}, wire=summarize_wire(cap.since(m)),
               reading=f"show_expanded_events=True opened; events seen: {[g['shape']['operationType'] for g in r['events']]}; error {fmt_err(r['error']) or 'none'}.")
        close_stream(s)
    else:
        record("x3-showExpandedEvents", "db['mt_cs']['cs_x3'].watch(show_expanded_events=True)", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"show_expanded_events=True fails at open: {fmt_err(err)}.")
    # x4 global host
    gclient = make_client("MANAGED_GLOBAL_URI", appname="m-changestreams-global")
    try:
        gc = gclient[DB]["cs_x4"]
        ensure_coll(gclient[DB], "cs_x4")
        m = cap.mark()
        s, err = open_stream(gc, max_await_time_ms=1000)
        if s is not None:
            gc.insert_one({"_id": "x4-1"})
            r = read_events(s, 1, timeout=30)
            record("x4-watch-via-global-host", "client on MANAGED_GLOBAL_URI (.global. host): db['mt_cs']['cs_x4'].watch(); insert_one; read 1 event, 30 s",
                   response={"read": r}, wire=summarize_wire(cap.since(m)),
                   reading=f"Through the .global. host the stream delivered {ops_of(r)} in {r['elapsed_s']} s; error {fmt_err(r['error']) or 'none'}.")
            close_stream(s)
        else:
            record("x4-watch-via-global-host", "global host: db['mt_cs']['cs_x4'].watch()", error=err, wire=summarize_wire(cap.since(m)),
                   reading=f"watch() through the .global. host fails at open: {fmt_err(err)}.")
    finally:
        gclient.close()
    # x5 server-side $match / $project
    ensure_coll(db, "cs_x5")
    c5 = db["cs_x5"]
    m = cap.mark()
    pipe = [{"$match": {"operationType": {"$in": ["insert", "delete"]}}}, {"$project": {"fullDocument": 0}}]
    s, err = open_stream(c5, pipeline=pipe, max_await_time_ms=1000)
    if s is not None:
        c5.insert_one({"_id": "x5-1", "v": 1})
        c5.update_one({"_id": "x5-1"}, {"$set": {"v": 2}})
        c5.delete_one({"_id": "x5-1"})
        r = read_events(s, 2, timeout=30, extra_wait=3)
        record("x5-pipeline-match-project", "stream = db['mt_cs']['cs_x5'].watch([{$match: {operationType: {$in: ['insert','delete']}}}, {$project: {fullDocument: 0}}]); insert, update, delete; read 2 events, 30 s (+3 s)",
               response={"read": r}, wire=summarize_wire(cap.since(m)),
               reading=(f"With $match on operationType and $project, the stream delivered {ops_of(r)} (fullDocument on insert: "
                        f"{[g['shape']['fullDocument'] for g in r['events'] if g['shape']['operationType'] == 'insert']}); error {fmt_err(r['error']) or 'none'}."))
        close_stream(s)
    else:
        record("x5-pipeline-match-project", "watch with $match/$project pipeline", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() with a $match/$project pipeline fails at open: {fmt_err(err)}.")


def section_f(client, st):
    coll = client[DB]["cs_f"]
    marker_wall = st["f_marker_wall"]
    ops = st.get("f_marker_ops") or []
    waited = 0
    elapsed = time.time() - marker_wall
    if elapsed < 180:
        waited = 180 - elapsed
        time.sleep(waited)
    now = time.time()
    trials = []
    t1 = Timestamp(int(marker_wall) - 30, 0)
    trials.append(("f1-start-at-wallclock-minus-30s", t1, 3, 30,
                   f"Timestamp({t1.time}, 0) = 30 s before the marker writes = {round((now - t1.time) / 60, 1)} minutes before this call"))
    if ops and isinstance(ops[0], Timestamp):
        trials.append(("f2-start-at-insert-operationTime", ops[0], 3, 30, f"session.operation_time returned by the marker insert {j(ops[0])}"))
    if len(ops) > 1 and isinstance(ops[1], Timestamp):
        trials.append(("f2b-start-at-update-operationTime", ops[1], 2, 30, f"session.operation_time returned by the marker update {j(ops[1])}"))
    if not (ops and isinstance(ops[0], Timestamp)):
        try:
            sf = json.load(open(os.path.join(HERE, "steps_setup_f.json")))
            hop = sf["steps"][0]["response"]["hello_operationTime"]["$timestamp"]
            hts = Timestamp(int(hop["t"]), int(hop["i"]))
            trials.append(("f2-start-at-hello-operationTime-before-markers", hts, 3, 30,
                           f"the operationTime {j(hts)} that hello returned just before the marker writes (the writes' own replies carry no operationTime)"))
        except Exception as ex:  # noqa
            print("no hello operationTime available:", ex)
    t3 = Timestamp(int(now) - 3600, 0)
    trials.append(("f3-start-at-1h-ago-before-cluster-creation", t3, 3, 30,
                   f"Timestamp({t3.time}, 0) = 1 hour ago = {dt.datetime.fromtimestamp(t3.time, dt.timezone.utc).isoformat()}, before the cluster's createdAt {CLUSTER_CREATED_UTC}"))
    t4 = Timestamp(int(now) - 40 * 86400, 0)
    trials.append(("f4-start-at-40-days-ago", t4, 3, 30,
                   f"Timestamp({t4.time}, 0) = 40 days ago = {dt.datetime.fromtimestamp(t4.time, dt.timezone.utc).isoformat()}, beyond the documented 35-day window"))
    for sid, ts, want, tmo, desc in trials:
        m = cap.mark()
        s, err = open_stream(coll, start_at_operation_time=ts, max_await_time_ms=1000)
        r = None
        if s is not None:
            r = read_events(s, want, timeout=tmo, extra_wait=2)
            close_stream(s)
        reading = (f"start_at_operation_time {desc}: fails at open with {fmt_err(err)}; server labels {err.get('errorLabels_server') if err else None}."
                   if s is None else f"start_at_operation_time {desc}: delivered {ops_of(r)} in {r['elapsed_s']} s; error {fmt_err(r['error']) or 'none'}.")
        record(sid, f"db['mt_cs']['cs_f'].watch(start_at_operation_time={j(ts)}, max_await_time_ms=1000); read up to {want} events, {tmo} s (+2 s)",
               response={"start_at_operation_time": j(ts), "description": desc, "read": r,
                         "marker_writes_were_utc": dt.datetime.fromtimestamp(marker_wall, dt.timezone.utc).isoformat(), "waited_s": round(waited, 1)},
               error=err, wire=summarize_wire(cap.since(m)), reading=reading)
    # f5 future start time
    t5 = Timestamp(int(time.time()) + 120, 0)
    m = cap.mark()
    s, err = open_stream(coll, start_at_operation_time=t5, max_await_time_ms=1000)
    r = None
    if s is not None:
        coll.insert_one({"_id": "f-future-probe"})
        r = read_events(s, 1, timeout=10)
        close_stream(s)
    record("f5-start-at-2-minutes-in-future", f"db['mt_cs']['cs_f'].watch(start_at_operation_time={j(t5)} (now + 120 s)); insert_one({{_id: 'f-future-probe'}}) now; read 1 event, 10 s",
           response={"start_at_operation_time": j(t5), "read": r}, error=err, wire=summarize_wire(cap.since(m)),
           reading=(f"A start time 2 minutes in the future fails at open: {fmt_err(err)}." if s is None else
                    f"A start time 2 minutes in the future is accepted; an insert made now produced {ops_of(r)} within 10 s (error {fmt_err(r['error']) or 'none'})."))


def section_cleanup(client, st):
    db = client[DB]
    m = cap.mark()
    s_db, err1 = open_stream(db, max_await_time_ms=1000)
    s_coll, err2 = open_stream(db["cs_a"], max_await_time_ms=1000)
    drop = {}
    try:
        client.drop_database(DB)
        drop["dropped"] = True
    except PyMongoError as ex:
        drop["error"] = err_info(ex)
    r1 = read_events(s_db, 50, timeout=15) if s_db is not None else None
    r2 = read_events(s_coll, 10, timeout=10) if s_coll is not None else None
    close_stream(s_db)
    close_stream(s_coll)
    leftover = len(open_streams)
    for s in list(open_streams):
        close_stream(s)
    exists = DB in client.list_database_names()
    def opsum(r):
        if r is None:
            return None
        return [(g["event"].get("operationType"), (g["event"].get("ns") or {}).get("coll")) for g in r["events"]]
    record("z1-dropDatabase-with-streams-open", "open db['mt_cs'].watch() and db['mt_cs']['cs_a'].watch(); client.drop_database('mt_cs'); read db stream up to 15 s and cs_a stream up to 10 s; close both; list_database_names()",
           response={"drop": drop, "db_stream_open_error": err1, "coll_stream_open_error": err2, "db_stream_read": r1, "coll_stream_read": r2,
                     "streams_left_open_before_cleanup": leftover, "mt_cs_exists_after": exists},
           wire=summarize_wire(cap.since(m)),
           reading=(f"dropDatabase with streams open: the database stream saw {opsum(r1)} (alive after: {r1['stream_alive_after'] if r1 else None}), the cs_a stream saw {opsum(r2)} "
                    f"(alive after: {r2['stream_alive_after'] if r2 else None}); all streams closed; mt_cs exists afterwards: {exists}."))


def section_cr(client, st):
    """Re-test of the database-level stream (c1 delivered nothing): controlled comparisons."""
    db = client[DB]
    # c4 same write seen by a collection-level and a database-level stream opened side by side
    m = cap.mark()
    s_coll, e1 = open_stream(db["cs_c1"], max_await_time_ms=1000)
    s_db, e2 = open_stream(db, max_await_time_ms=1000)
    t0 = time.monotonic()
    db["cs_c1"].insert_one({"_id": "c1-3"})
    r_coll = read_events(s_coll, 1, timeout=30, t_ref=t0) if s_coll is not None else None
    r_db = read_events(s_db, 1, timeout=45, t_ref=t0) if s_db is not None else None
    close_stream(s_coll)
    close_stream(s_db)
    record("c4-db-vs-collection-same-write",
           "s_coll = db['mt_cs']['cs_c1'].watch(); s_db = db['mt_cs'].watch(); insert_one({_id: 'c1-3'}) into cs_c1; read s_coll up to 30 s, then s_db up to 45 s",
           response={"coll_open_error": e1, "db_open_error": e2, "coll_read": r_coll, "db_read": r_db}, wire=summarize_wire(cap.since(m)),
           reading=(f"Same insert into mt_cs.cs_c1: the collection-level stream delivered {ops_of(r_coll) if r_coll else e1} in {r_coll['elapsed_s'] if r_coll else '-'} s, "
                    f"the database-level stream delivered {ops_of(r_db) if r_db else e2} in {r_db['elapsed_s'] if r_db else '-'} s (alive {r_db['stream_alive_after'] if r_db else '-'}, error {fmt_err(r_db['error']) if r_db and r_db['error'] else 'none'})."))
    # c5 db-level stream, then a brand-new collection with insert/update/delete
    m = cap.mark()
    s_db, err = open_stream(db, max_await_time_ms=1000)
    r = None
    if s_db is not None:
        t0 = time.monotonic()
        c3 = db["cs_c3"]
        c3.insert_one({"_id": "c3-1", "v": 1})
        c3.update_one({"_id": "c3-1"}, {"$set": {"v": 2}})
        c3.delete_one({"_id": "c3-1"})
        r = read_events(s_db, 3, timeout=45, t_ref=t0)
        close_stream(s_db)
    record("c5-db-watch-new-collection", "s_db = db['mt_cs'].watch(); insert/update/delete on new collection cs_c3 (created by the insert); read 3 events, 45 s",
           response={"read": r}, error=err, wire=summarize_wire(cap.since(m)),
           reading=(f"Database-level stream with insert/update/delete on a new collection delivered {ops_of(r)} in {r['elapsed_s']} s (error {fmt_err(r['error']) or 'none'})."
                    if r is not None else f"Database-level watch fails at open: {fmt_err(err)}."))
    # c6 raw database-level aggregate + getMores
    m = cap.mark()
    out = {"command": {"aggregate": 1, "pipeline": [{"$changeStream": {}}], "cursor": {}}}
    with client.start_session() as sess:
        try:
            rr = db.command({"aggregate": 1, "pipeline": [{"$changeStream": {}}], "cursor": {}}, session=sess)
            out["aggregate_reply"] = clean_cmd(rr)
            cid = rr["cursor"]["id"]
            db["cs_c1"].insert_one({"_id": "c1-4"})
            gms = []
            for _ in range(3):
                if not cid:
                    break
                try:
                    g = db.command({"getMore": Int64(cid), "collection": "$cmd.aggregate", "maxTimeMS": 3000}, session=sess)
                    gms.append({"reply": clean_cmd(g)})
                    cid = g["cursor"]["id"]
                except PyMongoError as ex:
                    gms.append({"error": err_info(ex)})
                    cid = 0
            out["getMore"] = gms
            if cid:
                out["killCursors_reply"] = clean_cmd(db.command({"killCursors": "$cmd.aggregate", "cursors": [Int64(cid)]}, session=sess))
        except PyMongoError as ex:
            out["error"] = err_info(ex)
    sizes = [len(((g.get("reply") or {}).get("cursor") or {}).get("nextBatch") or []) for g in out.get("getMore", [])]
    record("c6-raw-db-level-aggregate", "raw: db['mt_cs'].command({aggregate: 1, pipeline: [{$changeStream: {}}], cursor: {}}); insert_one({_id: 'c1-4'}) into cs_c1; 3 x getMore {collection: '$cmd.aggregate', maxTimeMS: 3000}; killCursors",
           response=out, wire=summarize_wire(cap.since(m)),
           reading=(f"Raw database-level $changeStream: cursor opened on {((out.get('aggregate_reply') or {}).get('cursor') or {}).get('ns')}; after an insert the three getMores returned nextBatch sizes {sizes}."
                    if "error" not in out else f"Raw database-level $changeStream failed: {fmt_err(out['error'])}."))
    # c7 database-level stream resumed from a collection event token captured in d1 (before d-3..d-5 and later writes)
    tok = st.get("d_event_token")
    if tok:
        m = cap.mark()
        s_db, err = open_stream(db, resume_after=tok, max_await_time_ms=1000)
        r = None
        if s_db is not None:
            r = read_events(s_db, 10, timeout=30)
            close_stream(s_db)
        record("c7-db-watch-resume-after-collection-token", f"db['mt_cs'].watch(resume_after={json.dumps(j(tok))} (cs_d event token from d1)); read up to 10 events, 30 s",
               response={"read": r}, error=err, wire=summarize_wire(cap.since(m)),
               reading=(f"Database-level stream resumed from a cs_d event token delivered {ops_of(r)} (error {fmt_err(r['error']) or 'none'})."
                        if r is not None else f"Database-level watch(resume_after=cs_d token) fails at open: {fmt_err(err)}."))


def section_er(client, st):
    """Follow-ups to e: one stream kept open across drop + recreate; a future-position token with a write; older positions."""
    db = client[DB]
    ensure_coll(db, "cs_e3")
    c = db["cs_e3"]
    m = cap.mark()
    s, err = open_stream(c, max_await_time_ms=1000)
    r1 = r2 = None
    drop_reply = None
    if s is not None:
        t0 = time.monotonic()
        c.insert_one({"_id": "e3-before-drop"})
        r1 = read_events(s, 1, timeout=30, t_ref=t0)
        try:
            drop_reply = j(db.command({"drop": "cs_e3"}))
        except PyMongoError as ex:
            drop_reply = {"error": err_info(ex)}
        time.sleep(2)
        db.create_collection("cs_e3")
        c.insert_one({"_id": "e3-after-recreate"})
        r2 = read_events(s, 3, timeout=20, t_ref=t0)
        close_stream(s)
    w = summarize_wire(cap.since(m))
    failed = [x for x in w["calls"] if "failure" in x]
    aggs = [x for x in w["calls"] if x["command_name"] == "aggregate"]
    record("e4-one-stream-across-drop-and-recreate",
           "stream = db['mt_cs']['cs_e3'].watch(max_await_time_ms=1000); insert e3-before-drop; read 1; drop cs_e3; sleep 2 s; create_collection cs_e3; insert e3-after-recreate; read up to 3 events, 20 s, same stream",
           response={"read_before_drop": r1, "drop_reply": drop_reply, "read_after_recreate": r2,
                     "server_failures_seen_by_driver": [x["failure"] for x in failed],
                     "aggregate_commands_sent": [x.get("command") for x in aggs]},
           error=err, wire=w,
           reading=(f"Across drop and recreate the same stream delivered {ops_of(r1) if r1 else None} then {ops_of(r2) if r2 else None} "
                    f"(no drop/invalidate events); the server failed {len(failed)} getMore(s) with {[(x['failure'].get('code'), x['failure'].get('codeName')) for x in failed]} "
                    f"and the driver sent {len(aggs)} aggregate(s) in total, i.e. {len(aggs) - 1} automatic resume(s)."))
    # e5 future-position token, then a write
    real = st.get("e_real_token")
    fut = None
    for name, fake in fabricate(real or {}):
        if name.startswith("structured-future-position"):
            fut = fake
    if fut is not None:
        m = cap.mark()
        s, err = open_stream(db["cs_e"], resume_after=fut, max_await_time_ms=1000)
        r = None
        if s is not None:
            t0 = time.monotonic()
            db["cs_e"].insert_one({"_id": "e-future-probe"})
            r = read_events(s, 1, timeout=15, t_ref=t0)
            close_stream(s)
        record("e5-future-position-token-then-write", f"db['mt_cs']['cs_e'].watch(resume_after={json.dumps(j(fut))}) (third field x100); insert_one({{_id: 'e-future-probe'}}); read 1 event, 15 s",
               response={"read": r}, error=err, wire=summarize_wire(cap.since(m)),
               reading=(f"A fabricated token pointing far ahead is accepted and the stream then delivered {ops_of(r)} for a new insert within 15 s "
                        f"(error {fmt_err(r['error']) or 'none'}): a corrupted future token yields a silently idle stream." if r is not None and not r['events'] else
                        (f"Future-position token: delivered {ops_of(r)}; error {fmt_err(r['error']) if r else fmt_err(err)}.")))
    # e6 older positions inside or before the retained log
    if isinstance(real, dict) and isinstance(real.get("_data"), str):
        txt = base64.b64decode(real["_data"]).decode()
        parts = txt.split(":")
        for pos in (10000000, 100000000, 170000000):
            q = list(parts)
            q[2] = str(pos)
            q[4] = str(pos)
            tok = {"_data": base64.b64encode(":".join(q).encode()).decode()}
            raw = raw_cs_probe(client, "cs_e", {"resumeAfter": tok}, getmore_tries=1, max_time_ms=2000)
            if "aggregate_error" in raw:
                rd = f"Position {pos}: rejected at aggregate with {fmt_err(raw['aggregate_error'])}."
            else:
                fb = ((raw.get("aggregate_reply") or {}).get("cursor") or {}).get("firstBatch") or []
                rd = f"Position {pos}: accepted; firstBatch {[(e.get('operationType'), (e.get('documentKey') or {}).get('_id')) for e in fb]}."
            record(f"e6-older-position-{pos}", f"raw: aggregate on cs_e with $changeStream {{resumeAfter: {json.dumps(tok)}}} (decoded '{':'.join(q)}'), one getMore",
                   response=raw, reading=rd)


def section_x1c(client, st):
    """x1a showed the documented {enabled: true} form is rejected with TypeMismatch; try the boolean form the error asks for."""
    db = client[DB]
    ensure_coll(db, "cs_x1b")
    m = cap.mark()
    cm = {}
    try:
        cm["reply"] = j(db.command({"collMod": "cs_x1b", "enableUpdateDescription": True}))
    except PyMongoError as ex:
        cm["error"] = err_info(ex)
    try:
        info = list(db.list_collections(filter={"name": "cs_x1b"}))
        cm["listCollections_options"] = j(info[0].get("options") if info else None)
    except PyMongoError as ex:
        cm["listCollections_error"] = err_info(ex)
    record("x1c-collMod-enableUpdateDescription-bool", "db['mt_cs'].command({collMod: 'cs_x1b', enableUpdateDescription: true}); list_collections(filter={name: 'cs_x1b'}) options",
           response=cm, wire=summarize_wire(cap.since(m)),
           reading=(f"collMod with enableUpdateDescription: true (boolean) accepted ({json.dumps(cm.get('reply'))}); collection options {json.dumps(cm.get('listCollections_options'))}."
                    if "reply" in cm else f"collMod enableUpdateDescription: true rejected: {fmt_err(cm.get('error'))}."))
    c1 = db["cs_x1b"]
    m = cap.mark()
    s, err = open_stream(c1, max_await_time_ms=1000)
    if s is None:
        record("x1d-updateDescription-after-bool-collMod", "db['mt_cs']['cs_x1b'].watch()", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() fails at open: {fmt_err(err)}.")
        return
    t0 = time.monotonic()
    ops = []
    try:
        c1.insert_one({"_id": "x1b-1", "a": 1, "b": 2, "arr": [1, 2, 3]}); ops.append("insert {_id:'x1b-1', a:1, b:2, arr:[1,2,3]}")
        c1.update_one({"_id": "x1b-1"}, {"$set": {"a": 10}, "$unset": {"b": ""}}); ops.append("update {$set:{a:10}, $unset:{b:''}}")
        c1.update_one({"_id": "x1b-1"}, {"$inc": {"a": 1}}); ops.append("update {$inc:{a:1}}")
        c1.update_one({"_id": "x1b-1"}, {"$push": {"arr": 4}}); ops.append("update {$push:{arr:4}}")
        c1.update_one({"_id": "x1b-1"}, [{"$set": {"c": {"$add": ["$a", 1]}}}]); ops.append("update pipeline [{$set:{c:{$add:['$a',1]}}}]")
        c1.replace_one({"_id": "x1b-1"}, {"z": 1}); ops.append("replace_one {_id:'x1b-1'} -> {z:1}")
    except PyMongoError as ex:
        ops.append({"error": err_info(ex)})
    r = read_events(s, 6, timeout=30, extra_wait=2, t_ref=t0)
    summ = [(g["shape"]["operationType"], g["shape"]["updateDescription"], g["event"].get("updateDescription")) for g in r["events"]]
    record("x1d-updateDescription-after-bool-collMod",
           "stream = db['mt_cs']['cs_x1b'].watch(); insert; update $set+$unset; update $inc; update $push; pipeline-style update; replace_one; read 6 events, 30 s (+2 s)",
           response={"writes": j(ops), "read": r}, wire=summarize_wire(cap.since(m)),
           reading=f"After collMod enableUpdateDescription: true, (op, updateDescription presence, value) = {json.dumps(summ, default=str)}; error {fmt_err(r['error']) or 'none'}.")
    close_stream(s)


def section_x1e(client, st):
    """Re-check updateDescription on cs_x1b about a minute after the boolean collMod, with a fresh client and stream."""
    db = client[DB]
    time.sleep(60)
    c1 = db["cs_x1b"]
    m = cap.mark()
    s, err = open_stream(c1, max_await_time_ms=1000)
    if s is None:
        record("x1e-updateDescription-recheck", "db['mt_cs']['cs_x1b'].watch()", error=err, wire=summarize_wire(cap.since(m)),
               reading=f"watch() fails at open: {fmt_err(err)}.")
        return
    t0 = time.monotonic()
    c1.insert_one({"_id": "x1b-2", "a": 1, "b": 2})
    c1.update_one({"_id": "x1b-2"}, {"$set": {"a": 5}, "$unset": {"b": ""}})
    r = read_events(s, 2, timeout=30, extra_wait=2, t_ref=t0)
    close_stream(s)
    summ = [(g["shape"]["operationType"], g["shape"]["updateDescription"], g["event"].get("updateDescription")) for g in r["events"]]
    record("x1e-updateDescription-recheck", "60 s after x1c, new client: stream = db['mt_cs']['cs_x1b'].watch(); insert x1b-2; update_one {$set: {a: 5}, $unset: {b: ''}}; read 2 events, 30 s (+2 s)",
           response={"read": r}, wire=summarize_wire(cap.since(m)),
           reading=f"About a minute after enabling, (op, updateDescription presence, value) = {json.dumps(summ, default=str)}; error {fmt_err(r['error']) or 'none'}.")


def section_fr(client, st):
    """Follow-up to f3/f4: on cs_a, whose only events are ~13 minutes old, does a start time before the cluster existed replay them,
    and does a start time 3.5 minutes ago skip them (control that the timestamp is honoured, not ignored)?"""
    coll = client[DB]["cs_a"]
    now = time.time()
    trials = [
        ("f6-cs_a-start-at-40-days-ago", Timestamp(int(now) - 40 * 86400, 0), "40 days ago (before the cluster existed, beyond 35 days)"),
        ("f7-cs_a-start-at-210s-ago-control", Timestamp(int(now) - 210, 0), "210 s ago (after the cs_a events of a2, so none should replay)"),
        ("f8-cs_a-start-at-1h-ago", Timestamp(int(now) - 3600, 0), "1 hour ago (before the cluster's createdAt 2026-11-25T20:35:33Z)"),
    ]
    for sid, ts, desc in trials:
        m = cap.mark()
        s, err = open_stream(coll, start_at_operation_time=ts, max_await_time_ms=1000)
        r = None
        if s is not None:
            r = read_events(s, 3, timeout=15, extra_wait=2)
            close_stream(s)
        record(sid, f"db['mt_cs']['cs_a'].watch(start_at_operation_time={j(ts)}, max_await_time_ms=1000); read up to 3 events, 15 s (+2 s)",
               response={"start_at_operation_time": j(ts), "description": desc, "read": r}, error=err, wire=summarize_wire(cap.since(m)),
               reading=(f"cs_a with start_at_operation_time {desc}: fails at open with {fmt_err(err)}." if s is None else
                        f"cs_a with start_at_operation_time {desc}: delivered {ops_of(r)} (the a2 events were written at about 21:00:39Z); error {fmt_err(r['error']) or 'none'}."))


SECTIONS = {"a": section_a, "b": section_b, "c": section_c, "d": section_d, "e": section_e, "setup_f": section_setup_f,
            "x": section_x, "f": section_f, "cleanup": section_cleanup, "cr": section_cr, "er": section_er, "x1c": section_x1c, "x1e": section_x1e, "fr": section_fr}


def main():
    sec = sys.argv[1]
    st = load_state()
    client = make_client()
    t0 = time.time()
    try:
        SECTIONS[sec](client, st)
    except Exception as ex:  # noqa
        steps.append({"step": f"{sec}-UNHANDLED", "at_utc": now_utc(), "command": f"section {sec}",
                      "error": {"exception": type(ex).__name__, "message": scrub(str(ex)), "traceback": scrub(traceback.format_exc())},
                      "reading": "Unhandled exception in the test script (not a service observation).", "vs_open_source": "n/a"})
        print(scrub(traceback.format_exc()), flush=True)
    finally:
        for s in list(open_streams):
            close_stream(s)
        save_state(st)
        out = {"section": sec, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(), "finished_utc": now_utc(),
               "duration_s": round(time.time() - t0, 1), "steps": steps}
        text = scrub(json.dumps(out, indent=1, default=str))
        with open(os.path.join(HERE, f"steps_{sec}.json"), "w") as f:
            f.write(text)
        client.close()
        print(f"section {sec}: {len(steps)} steps, {out['duration_s']} s", flush=True)


if __name__ == "__main__":
    main()
