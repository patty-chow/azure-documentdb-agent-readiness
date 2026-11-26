"""m-txn-bulk part 1 (a-e): transactions on managed Azure DocumentDB.

Target: MANAGED_URI from ../managed.env (plain host). Owns database mt_txn only (collections
docs, busy, busy1s). Never prints the password. Writes txn_steps.json next to this file.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python txn.py
Mirrors findings/phase4/engine-tests/transactions-labels/run.py (open-source engine) so the
results can be compared step by step, plus with_transaction, isolation and busy-transaction steps.
"""
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB, ENV, HERE, CmdLog, Recorder, err_dict, jsonable, raw_command, redact, reply_summary, write_json  # noqa: E402

import pymongo  # noqa: E402
from bson import Int64  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from pymongo.read_concern import ReadConcern  # noqa: E402

COLL = "docs"
R = Recorder()


def txn_ids(session):
    return {"lsid": session.session_id, "txnNumber": Int64(session._server_session.transaction_id)}


def quiet_abort(s):
    try:
        s.abort_transaction()
        return {"ok": 1}
    except Exception as e:  # noqa: BLE001
        return err_dict(e)


def part0(c1):
    hello = c1.admin.command("hello")
    R.record("0a hello", "client.admin.command('hello')",
             {k: hello.get(k) for k in ("maxWireVersion", "minWireVersion", "logicalSessionTimeoutMinutes", "maxWriteBatchSize",
                                        "isWritablePrimary", "setName", "msg", "internal", "endpointName")},
             "Gateway identity and session support advertised to the driver.")
    bi = c1.admin.command("buildInfo")
    R.record("0b buildInfo", "client.admin.command('buildInfo')", {k: bi.get(k) for k in ("version", "versionArray", "ok")},
             "Server version string the gateway reports.")
    td = c1.topology_description
    R.record("0c driver + topology", "pymongo.__version__; client.topology_description",
             {"pymongo": pymongo.__version__, "topology_type": td.topology_type_name,
              "servers": [{"address": str(a), "type": d.server_type_name} for a, d in td.server_descriptions().items()]},
             "Driver and topology the driver sees (a single mongos-type endpoint).")
    return hello, bi


def part_a(c1, c2, L1, L2):
    coll1 = c1[DB][COLL]
    coll2 = c2[DB][COLL]
    c1[DB].drop_collection(COLL)
    coll1.insert_one({"_id": 1, "v": 0})
    R.record("a0 setup", "db.drop_collection('docs'); db.docs.insert_one({'_id': 1, 'v': 0})", {"inserted": 1},
             "Fresh collection with one document that both transactions will update.")

    # ---- a1..a6: two driver sessions, same document
    sA = c1.start_session()
    sB = c2.start_session()
    sA.start_transaction()
    rA = coll1.update_one({"_id": 1}, {"$set": {"v": 1, "by": "A"}}, session=sA)
    R.record("a1 session A update in txn", "sA.start_transaction(); docs.update_one({'_id': 1}, {'$set': {'v': 1, 'by': 'A'}}, session=sA)",
             {"matched": rA.matched_count, "modified": rA.modified_count, "txnNumber": sA._server_session.transaction_id})

    sB.start_transaction()
    b = {}
    mark2 = L2.mark()

    def b_update():
        t0 = time.monotonic()
        try:
            r = coll2.update_one({"_id": 1}, {"$set": {"v": 2, "by": "B"}}, session=sB)
            b["ok"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa: BLE001
            b["error"] = err_dict(e)
        b["elapsed_s"] = round(time.monotonic() - t0, 3)
        b["returned_at_monotonic"] = time.monotonic()

    tB0 = time.monotonic()
    th = threading.Thread(target=b_update, daemon=True)
    th.start()
    th.join(3.0)
    blocked = th.is_alive()
    snap = {k: v for k, v in b.items() if k != "returned_at_monotonic"}
    R.record("a2 session B update same doc in txn while A is uncommitted",
             "sB.start_transaction(); docs.update_one({'_id': 1}, {'$set': {'v': 2, 'by': 'B'}}, session=sB)  # in a thread, waited up to 3 s",
             {"still_blocked_after_3s": blocked, "result_so_far": snap or None})

    tc = time.monotonic()
    try:
        sA.commit_transaction()
        cA = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        cA = err_dict(e)
    R.record("a3 commit A", "sA.commit_transaction()",
             {"result": cA, "commit_sent_at_s_after_B_update_started": round(tc - tB0, 3), "commit_took_s": round(time.monotonic() - tc, 3)})

    th.join(120.0)
    outcome = {k: v for k, v in b.items() if k != "returned_at_monotonic"}
    if "returned_at_monotonic" in b:
        outcome["B_returned_before_A_commit_was_sent"] = b["returned_at_monotonic"] < tc
    R.record("a4 session B outcome (the second transaction's error)", "(result of B's update_one)",
             {"thread_finished": not th.is_alive(), **outcome, "client2_wire_commands": L2.since(mark2)})

    mark2 = L2.mark()
    if "ok" in b:
        try:
            sB.commit_transaction()
            r5 = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            r5 = err_dict(e)
        R.record("a5 commit B (its update had succeeded)", "sB.commit_transaction()", {"result": r5, "client2_wire_commands": L2.since(mark2)})
    else:
        r5 = quiet_abort(sB)
        R.record("a5 abort B after its error", "sB.abort_transaction()", {"result": r5, "client2_wire_commands": L2.since(mark2)},
                 "PyMongo swallows abortTransaction errors; the wire reply shows what the server said.")
    R.record("a6 final document", "docs.find_one({'_id': 1})", coll1.find_one({"_id": 1}))
    sA.end_session()
    sB.end_session()

    # ---- a7..a8: same conflict, B's write sent raw so the untouched wire reply is captured
    coll1.update_one({"_id": 1}, {"$set": {"v": 0, "by": None}})
    sA = c1.start_session()
    sB = c2.start_session()
    sA.start_transaction()
    coll1.update_one({"_id": 1}, {"$set": {"v": 11, "by": "A2"}}, session=sA)
    sB.start_transaction()
    _ = list(coll2.find({"_id": -1}, session=sB))  # opens B's transaction on the server (startTransaction: true)
    raw_b = {}

    def b_raw():
        t0 = time.monotonic()
        try:
            cmd = {"update": COLL, "updates": [{"q": {"_id": 1}, "u": {"$set": {"v": 22, "by": "B2"}}}], **txn_ids(sB), "autocommit": False}
            raw_b["reply"] = reply_summary(raw_command(c2, DB, cmd))
        except Exception as e:  # noqa: BLE001
            raw_b["error"] = err_dict(e)
        raw_b["elapsed_s"] = round(time.monotonic() - t0, 3)

    th = threading.Thread(target=b_raw, daemon=True)
    th.start()
    th.join(2.0)
    blocked2 = th.is_alive()
    try:
        sA.commit_transaction()
        cA2 = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        cA2 = err_dict(e)
    th.join(120.0)
    R.record("a7 write conflict, raw wire reply",
             "B: find in txn (startTransaction) then raw {update:'docs', updates:[{q:{_id:1}, u:{$set:{v:22,by:'B2'}}}], lsid, txnNumber, autocommit:false} on a pooled connection; A commits 2 s later",
             {"B_still_blocked_after_2s": blocked2, "commitA": cA2, **raw_b})
    ab = reply_summary(raw_command(c2, "admin", {"abortTransaction": 1, **txn_ids(sB), "autocommit": False}))
    R.record("a8 raw abortTransaction for B after the conflict", "{abortTransaction:1, lsid, txnNumber, autocommit:false} on admin", ab)
    quiet_abort(sB)
    sA.end_session()
    sB.end_session()

    # ---- a9..a10: with_transaction for B while A holds the lock; A commits after 3 s
    coll1.update_one({"_id": 1}, {"$set": {"v": 0, "by": None, "n": 0}})
    sA = c1.start_session()
    sB = c2.start_session()
    sA.start_transaction()
    coll1.update_one({"_id": 1}, {"$set": {"v": 100, "by": "A-wt"}}, session=sA)
    attempts = []
    commit_info = {}
    clock = {}

    def commit_later():
        time.sleep(3.0)
        t = time.monotonic()
        try:
            sA.commit_transaction()
            commit_info["result"] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            commit_info["result"] = err_dict(e)
        commit_info["commit_sent_at_s"] = round(t - clock["t0"], 3)

    def cb(session):
        a = {"attempt": len(attempts) + 1, "t_start_s": round(time.monotonic() - clock["t0"], 3)}
        attempts.append(a)
        try:
            r = coll2.update_one({"_id": 1}, {"$set": {"by": "B-wt"}, "$inc": {"n": 1}}, session=session)
            a["result"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa: BLE001
            a["error"] = err_dict(e)
            a["t_end_s"] = round(time.monotonic() - clock["t0"], 3)
            raise
        a["t_end_s"] = round(time.monotonic() - clock["t0"], 3)
        return "callback-returned"

    mark2 = L2.mark()
    clock["t0"] = time.monotonic()
    tc = threading.Thread(target=commit_later, daemon=True)
    tc.start()
    try:
        ret = sB.with_transaction(cb)
        wt = {"returned": ret}
    except Exception as e:  # noqa: BLE001
        wt = {"raised": err_dict(e)}
    wt_elapsed = round(time.monotonic() - clock["t0"], 3)
    tc.join(30.0)
    R.record("a9 with_transaction for B while A holds the row lock (A commits at ~3 s)",
             "sB.with_transaction(lambda s: docs.update_one({'_id': 1}, {'$set': {'by': 'B-wt'}, '$inc': {'n': 1}}, session=s))  # A committed by a timer thread after 3 s",
             {"n_callback_attempts": len(attempts), "attempts": attempts, "with_transaction_outcome": wt, "elapsed_s": wt_elapsed,
              "A_commit": commit_info, "client2_wire_commands": L2.since(mark2)})
    R.record("a10 final document after with_transaction", "docs.find_one({'_id': 1})", coll1.find_one({"_id": 1}))
    sA.end_session()
    sB.end_session()

    # ---- a11..a12 (extra): conflict with a write committed after B's transaction read the document
    coll1.update_one({"_id": 1}, {"$set": {"v": 0, "by": None}})
    sB = c2.start_session()
    sB.start_transaction()
    seq = {}
    seq["B_read_1"] = coll2.find_one({"_id": 1}, session=sB)
    r_out = coll1.update_one({"_id": 1}, {"$set": {"v": 7, "by": "outside"}})
    seq["outside_autocommit_update"] = {"matched": r_out.matched_count, "modified": r_out.modified_count}
    seq["B_read_2_after_outside_commit"] = coll2.find_one({"_id": 1}, session=sB)
    mark2 = L2.mark()
    try:
        r = coll2.update_one({"_id": 1}, {"$set": {"v": 8, "by": "B-after"}}, session=sB)
        seq["B_update"] = {"matched": r.matched_count, "modified": r.modified_count}
    except Exception as e:  # noqa: BLE001
        seq["B_update"] = err_dict(e)
    try:
        sB.commit_transaction()
        seq["B_commit"] = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        seq["B_commit"] = err_dict(e)
        seq["B_abort"] = quiet_abort(sB)
    seq["client2_wire_commands"] = L2.since(mark2)
    seq["final_document"] = coll1.find_one({"_id": 1})
    R.record("a11 (extra) B reads, an outside write commits, B reads again and updates the same document",
             "sB.start_transaction(); docs.find_one({'_id':1}, session=sB); docs.update_one({'_id':1}, {'$set': {'v': 7, 'by': 'outside'}}) [no session txn]; "
             "docs.find_one({'_id':1}, session=sB); docs.update_one({'_id':1}, {'$set': {'v': 8, 'by': 'B-after'}}, session=sB); sB.commit_transaction()",
             seq)
    sB.end_session()


def part_b(c1, L1):
    coll = c1[DB][COLL]
    for level in ("snapshot", "majority", "local"):
        s = c1.start_session()
        mark = L1.mark()
        resp = {}
        try:
            s.start_transaction(read_concern=ReadConcern(level))
            resp["find_result"] = list(coll.find({"_id": 1}, session=s))
            r = coll.update_one({"_id": 1}, {"$set": {"rc_" + level: True}}, session=s)
            resp["update_result"] = {"matched": r.matched_count, "modified": r.modified_count}
            s.commit_transaction()
            resp["commit"] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            resp["error"] = err_dict(e)
            resp["abort_after_error"] = quiet_abort(s)
        resp["wire_commands"] = L1.since(mark)
        R.record(f"b readConcern {level} in a transaction",
                 f"s.start_transaction(read_concern=ReadConcern('{level}')); docs.find({{'_id': 1}}, session=s); "
                 f"docs.update_one({{'_id': 1}}, {{'$set': {{'rc_{level}': True}}}}, session=s); s.commit_transaction()",
                 resp)
        s.end_session()
    R.record("b final document", "docs.find_one({'_id': 1})", coll.find_one({"_id": 1}),
             "Shows which readConcern transactions committed their write.")


def part_c(c1, L1):
    coll = c1[DB][COLL]
    # c1 driver path
    s = c1.start_session()
    s.start_transaction()
    coll.update_one({"_id": 1}, {"$inc": {"v": 100}}, session=s)
    mark = L1.mark()
    out = {}
    for key, fn in (("commit1", s.commit_transaction), ("commit2", s.commit_transaction), ("abort_after_commit", s.abort_transaction)):
        try:
            fn()
            out[key] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            out[key] = err_dict(e)
    out["wire_commands"] = L1.since(mark)
    R.record("c1 driver: commit, commit again, abort after commit",
             "s.start_transaction(); docs.update_one({'_id':1}, {'$inc': {'v': 100}}, session=s); s.commit_transaction(); s.commit_transaction(); s.abort_transaction()",
             out)
    s.end_session()

    # c2 raw wire
    s = c1.start_session()
    s.start_transaction()
    coll.update_one({"_id": 1}, {"$inc": {"v": 1000}}, session=s)
    ids = txn_ids(s)
    r1 = reply_summary(raw_command(c1, "admin", {"commitTransaction": 1, **ids, "autocommit": False}))
    r2 = reply_summary(raw_command(c1, "admin", {"commitTransaction": 1, **ids, "autocommit": False}))
    r2m = reply_summary(raw_command(c1, "admin", {"commitTransaction": 1, **ids, "autocommit": False, "writeConcern": {"w": "majority", "wtimeout": 10000}}))
    r3 = reply_summary(raw_command(c1, "admin", {"abortTransaction": 1, **ids, "autocommit": False}))
    R.record("c2 raw: commitTransaction twice (+ the driver's w:majority retry form), then abortTransaction",
             "{commitTransaction:1, lsid, txnNumber, autocommit:false} x2; same + writeConcern {w:'majority', wtimeout:10000}; then {abortTransaction:1, lsid, txnNumber, autocommit:false}",
             {"commit1": r1, "commit2": r2, "commit2_majority_wc": r2m, "abort_after_commit": r3})
    quiet_abort(s)
    s.end_session()

    # c3 raw: abort twice, commit after abort
    s = c1.start_session()
    s.start_transaction()
    coll.update_one({"_id": 1}, {"$inc": {"v": 1}}, session=s)
    ids = txn_ids(s)
    a1 = reply_summary(raw_command(c1, "admin", {"abortTransaction": 1, **ids, "autocommit": False}))
    a2 = reply_summary(raw_command(c1, "admin", {"abortTransaction": 1, **ids, "autocommit": False}))
    ca = reply_summary(raw_command(c1, "admin", {"commitTransaction": 1, **ids, "autocommit": False}))
    R.record("c3 raw: abortTransaction twice, then commitTransaction after abort",
             "{abortTransaction:1, lsid, txnNumber, autocommit:false} x2; then {commitTransaction:1, lsid, txnNumber, autocommit:false}",
             {"abort1": a1, "abort2": a2, "commit_after_abort": ca})
    quiet_abort(s)
    s.end_session()
    R.record("c4 document after part c", "docs.find_one({'_id': 1})", coll.find_one({"_id": 1}),
             "v should have grown by 100 + 1000 (two committed transactions) and not by 1 (aborted).")


def part_d(c1, L1):
    coll = c1[DB][COLL]
    coll.update_one({"_id": 1}, {"$set": {"v": 0}, "$unset": {"idle": "", "idle2": ""}})
    s = c1.start_session()
    s.start_transaction()
    coll.update_one({"_id": 1}, {"$set": {"idle": "start"}}, session=s)
    t0 = time.monotonic()
    time.sleep(36)
    slept = round(time.monotonic() - t0, 1)
    mark = L1.mark()
    try:
        r = coll.update_one({"_id": 1}, {"$set": {"idle": "after"}}, session=s)
        w = {"matched": r.matched_count, "modified": r.modified_count}
    except Exception as e:  # noqa: BLE001
        w = err_dict(e)
    R.record("d1 driver: write after 36 s idle in a transaction",
             f"s.start_transaction(); docs.update_one({{'_id':1}}, {{'$set': {{'idle': 'start'}}}}, session=s); time.sleep({slept}); "
             "docs.update_one({'_id':1}, {'$set': {'idle': 'after'}}, session=s)",
             {"slept_s": slept, "write_result": w, "wire_commands": L1.since(mark)})
    mark = L1.mark()
    try:
        s.commit_transaction()
        c = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        c = err_dict(e)
    R.record("d2 driver: commit after the idle timeout", "s.commit_transaction()", {"result": c, "wire_commands": L1.since(mark)})
    mark = L1.mark()
    try:
        s.abort_transaction()
        a = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        a = err_dict(e)
    R.record("d3 driver: abort after the idle timeout", "s.abort_transaction()", {"result": a, "wire_commands": L1.since(mark)})
    s.end_session()

    s = c1.start_session()
    s.start_transaction()
    coll.update_one({"_id": 1}, {"$set": {"idle2": "start"}}, session=s)
    ids = txn_ids(s)
    t0 = time.monotonic()
    time.sleep(36)
    slept = round(time.monotonic() - t0, 1)
    raw_w = reply_summary(raw_command(c1, DB, {"update": COLL, "updates": [{"q": {"_id": 1}, "u": {"$set": {"idle2": "after"}}}], **ids, "autocommit": False}))
    raw_c = reply_summary(raw_command(c1, "admin", {"commitTransaction": 1, **ids, "autocommit": False}))
    raw_a = reply_summary(raw_command(c1, "admin", {"abortTransaction": 1, **ids, "autocommit": False}))
    R.record("d4 raw: write, commit, abort after 36 s idle",
             f"s.start_transaction(); docs.update_one(... idle2:'start' ..., session=s); time.sleep({slept}); raw {{update:'docs', updates:[...], lsid, txnNumber, autocommit:false}}; "
             "raw {commitTransaction:1, lsid, txnNumber, autocommit:false}; raw {abortTransaction:1, lsid, txnNumber, autocommit:false}",
             {"slept_s": slept, "update": raw_w, "commit": raw_c, "abort": raw_a})
    quiet_abort(s)
    s.end_session()
    R.record("d5 document after the idle tests", "docs.find_one({'_id': 1})", coll.find_one({"_id": 1}),
             "Neither idle transaction should have applied its writes.")


def busy(c1, L1, step, collname, interval, until):
    db = c1[DB]
    db.drop_collection(collname)
    db.create_collection(collname)
    coll = db[collname]
    s = c1.start_session()
    s.start_transaction()
    writes = []
    mark = L1.mark()
    t0 = time.monotonic()
    i = 0
    target = 0.0
    while target <= until + 1e-9:
        now = time.monotonic() - t0
        if target > now:
            time.sleep(target - now)
        sent = time.monotonic() - t0
        w = {"i": i, "scheduled_s": target, "sent_at_s": round(sent, 3)}
        try:
            coll.insert_one({"_id": i, "t": round(sent, 3)}, session=s)
            w["result"] = "ok"
        except Exception as e:  # noqa: BLE001
            w["error"] = err_dict(e)
        w["returned_at_s"] = round(time.monotonic() - t0, 3)
        writes.append(w)
        i += 1
        target = i * interval
    wire_writes = L1.since(mark)
    mark = L1.mark()
    tcm = time.monotonic() - t0
    try:
        s.commit_transaction()
        cm = {"ok": 1}
    except Exception as e:  # noqa: BLE001
        cm = err_dict(e)
    ab = quiet_abort(s) if "exception" in cm else None
    wire_end = L1.since(mark)
    s.end_session()
    ok_writes = [w["i"] for w in writes if w.get("result") == "ok"]
    first_fail = next((w for w in writes if "error" in w), None)
    applied = sorted(d["_id"] for d in coll.find({}, {"_id": 1}))
    R.record(step,
             f"s.start_transaction(); for i in 0..: {collname}.insert_one({{'_id': i, 't': elapsed}}, session=s) every {interval} s up to t={until} s "
             "(t measured from the first write, which starts the transaction on the server); then s.commit_transaction(); "
             f"then {collname}.find() outside the transaction",
             {"writes": writes, "ok_write_ids": ok_writes,
              "first_failure": ({"i": first_fail["i"], "sent_at_s": first_fail["sent_at_s"], "returned_at_s": first_fail["returned_at_s"],
                                 "error": first_fail["error"]} if first_fail else None),
              "commit_sent_at_s": round(tcm, 3), "commit": cm, "abort_after_failed_commit": ab,
              "wire_commands_writes": wire_writes, "wire_commands_commit_abort": wire_end,
              "documents_visible_after_commit": applied})


def main():
    c1_log = CmdLog("client1")
    c2_log = CmdLog("client2")
    c1 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[c1_log])
    c2 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[c2_log])
    meta = {}
    try:
        hello, bi = part0(c1)
        meta["hello"] = {k: hello.get(k) for k in ("maxWireVersion", "maxWriteBatchSize", "logicalSessionTimeoutMinutes", "internal", "msg")}
        meta["buildInfo_version"] = bi.get("version")
        for name, fn in (("a", lambda: part_a(c1, c2, c1_log, c2_log)), ("b", lambda: part_b(c1, c1_log)),
                         ("c", lambda: part_c(c1, c1_log)), ("d", lambda: part_d(c1, c1_log)),
                         ("e", lambda: busy(c1, c1_log, "e1 busy transaction: a small write every 5 s for 40 s", "busy", 5.0, 40.0)),
                         ("e2", lambda: busy(c1, c1_log, "e2 (extra) busy transaction: a small write every 1 s for 36 s", "busy1s", 1.0, 36.0))):
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                R.record(f"{name} FATAL", f"part {name}", {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())},
                         "Script error, not a server observation.")
    finally:
        c1.close()
        c2.close()
    return meta


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    meta = main()
    write_json(os.path.join(HERE, "txn_steps.json"), {
        "part": "transactions (a-e)", "database": DB, "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(), "driver": f"pymongo {pymongo.__version__}",
        "uri_used": "MANAGED_URI (plain host, mongodb+srv, tls=true, authMechanism=SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000)",
        "meta": jsonable(meta), "steps": R.steps})
    print("\nwritten:", os.path.join(HERE, "txn_steps.json"))
