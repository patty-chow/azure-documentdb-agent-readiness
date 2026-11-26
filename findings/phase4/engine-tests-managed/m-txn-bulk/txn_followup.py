"""m-txn-bulk follow-up: characterise the 30 s transaction limit and isolation on managed Azure DocumentDB.

Why: in txn.py a busy transaction writing every 5 s committed at 40 s, while one writing every 1 s
was ended at ~34 s with 251; and two 36 s idle trials returned different first errors (code 1 vs 251).
This script runs staggered concurrent trials with absolute timestamps so the kill times can be compared,
and repeats the read-visibility check (a11) under readConcern none / snapshot / majority.
Owns database mt_txn only (collections iso, fbusy, fidle). Writes txn_followup_steps.json.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python txn_followup.py
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

R = Recorder()
T0 = None


def now_s():
    return round(time.monotonic() - T0, 3)


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sleep_until(t_abs):
    d = t_abs - time.monotonic()
    if d > 0:
        time.sleep(d)


def txn_ids(session):
    return {"lsid": session.session_id, "txnNumber": Int64(session._server_session.transaction_id)}


def iso_check(c1, c2, L2, level):
    coll1 = c1[DB]["iso"]
    coll2 = c2[DB]["iso"]
    coll1.delete_many({})
    coll1.insert_one({"_id": 1, "v": 0})
    s = c2.start_session()
    s.start_transaction(read_concern=ReadConcern(level) if level else None)
    mark = L2.mark()
    out = {}
    try:
        out["txn_read_1"] = coll2.find_one({"_id": 1}, session=s)
        r = coll1.update_one({"_id": 1}, {"$set": {"v": 7, "by": "outside"}})
        out["outside_autocommit_update"] = {"matched": r.matched_count, "modified": r.modified_count}
        out["txn_read_2_after_outside_commit"] = coll2.find_one({"_id": 1}, session=s)
        try:
            r = coll2.update_one({"_id": 1}, {"$set": {"v": 8, "by": "txn"}}, session=s)
            out["txn_update"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa: BLE001
            out["txn_update"] = err_dict(e)
        try:
            s.commit_transaction()
            out["txn_commit"] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            out["txn_commit"] = err_dict(e)
    except Exception as e:  # noqa: BLE001
        out["error"] = err_dict(e)
        try:
            s.abort_transaction()
        except Exception:  # noqa: BLE001
            pass
    out["client2_wire_commands"] = L2.since(mark)
    out["final_document"] = coll1.find_one({"_id": 1})
    s.end_session()
    lv = repr(level) if level else "None (driver default, no readConcern sent)"
    R.record(f"f-iso readConcern {level or 'default'}: read, outside write commits, read again, update, commit",
             f"s.start_transaction(read_concern={'ReadConcern(' + repr(level) + ')' if level else 'None'}); iso.find_one({{'_id':1}}, session=s); "
             "iso.update_one({'_id':1}, {'$set': {'v': 7, 'by': 'outside'}}) [autocommit, other client]; iso.find_one({'_id':1}, session=s); "
             "iso.update_one({'_id':1}, {'$set': {'v': 8, 'by': 'txn'}}, session=s); s.commit_transaction()",
             out, f"readConcern {lv}")


def busy_trial(client, k, start_at, interval, max_age, res):
    sleep_until(T0 + start_at)
    coll = client[DB]["fbusy"]
    s = client.start_session()
    s.start_transaction()
    res.update({"trial": f"busy-{k}", "kind": "busy", "interval_s": interval, "planned_start_s": start_at, "writes": []})
    t_start = None
    i = 0
    try:
        while True:
            if t_start is not None:
                sleep_until(t_start + i * interval)
            tsent = time.monotonic()
            if t_start is None:
                t_start = tsent
                res["txn_start_abs_s"] = now_s()
                res["txn_start_utc"] = utc()
            age = tsent - t_start
            if age > max_age:
                res["stopped"] = f"reached max age {max_age} s without a failure"
                break
            w = {"i": i, "age_s": round(age, 3), "abs_s": round(tsent - T0, 3)}
            try:
                coll.insert_one({"_id": f"b{k}-{i}", "k": k, "i": i}, session=s)
                w["ok"] = True
                res["last_ok_age_s"] = round(age, 3)
                res["last_ok_abs_s"] = round(tsent - T0, 3)
            except Exception as e:  # noqa: BLE001
                w["ok"] = False
                w["utc"] = utc()
                w["error"] = err_dict(e)
                res["first_failure"] = w
                res["writes"].append({"i": i, "age_s": w["age_s"], "ok": False})
                # one confirming write
                time.sleep(0.5)
                try:
                    coll.insert_one({"_id": f"b{k}-{i}-confirm", "k": k, "i": i}, session=s)
                    res["confirm_write"] = {"ok": True}
                except Exception as e2:  # noqa: BLE001
                    res["confirm_write"] = err_dict(e2)
                break
            res["writes"].append({"i": i, "age_s": w["age_s"], "ok": True})
            i += 1
        tc = time.monotonic()
        try:
            s.commit_transaction()
            res["commit"] = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            res["commit"] = err_dict(e)
        res["commit_age_s"] = round(tc - t_start, 3)
        res["commit_abs_s"] = round(tc - T0, 3)
    except Exception as e:  # noqa: BLE001
        res["script_error"] = {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())}
    finally:
        s.end_session()
    res["n_writes_ok"] = sum(1 for w in res["writes"] if w["ok"])
    res["docs_visible_after"] = coll.count_documents({"k": k})


def idle_trial(client, k, start_at, idle_s, raw, res):
    sleep_until(T0 + start_at)
    coll = client[DB]["fidle"]
    s = client.start_session()
    s.start_transaction()
    res.update({"trial": f"idle-{k}", "kind": "idle", "path": "raw wire" if raw else "driver", "idle_s": idle_s, "planned_start_s": start_at})
    try:
        coll.insert_one({"_id": f"i{k}-start", "k": k}, session=s)
        t_start = time.monotonic()
        res["txn_start_abs_s"] = now_s()
        res["txn_start_utc"] = utc()
        sleep_until(t_start + idle_s)
        tw = time.monotonic()
        res["write_age_s"] = round(tw - t_start, 3)
        res["write_abs_s"] = round(tw - T0, 3)
        res["write_utc"] = utc()
        if raw:
            ids = txn_ids(s)
            res["write"] = reply_summary(raw_command(client, DB, {"insert": "fidle", "documents": [{"_id": f"i{k}-after", "k": k}], **ids, "autocommit": False}))
            res["commit"] = reply_summary(raw_command(client, "admin", {"commitTransaction": 1, **ids, "autocommit": False}))
            res["abort"] = reply_summary(raw_command(client, "admin", {"abortTransaction": 1, **ids, "autocommit": False}))
            try:
                s.abort_transaction()
            except Exception:  # noqa: BLE001
                pass
        else:
            try:
                coll.insert_one({"_id": f"i{k}-after", "k": k}, session=s)
                res["write"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                res["write"] = err_dict(e)
            try:
                s.commit_transaction()
                res["commit"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                res["commit"] = err_dict(e)
    except Exception as e:  # noqa: BLE001
        res["script_error"] = {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())}
    finally:
        s.end_session()
    res["docs_visible_after"] = coll.count_documents({"k": k})


def brief(err):
    if not isinstance(err, dict):
        return err
    if err.get("ok") == 1 and "code" not in err:
        return "ok"
    if "exception" in err:
        return {"exception": err["exception"], "code": err.get("code"), "codeName": err.get("codeName"), "errmsg": err.get("errmsg"),
                "server_errorLabels": err.get("errorLabels_in_server_reply"), "driver_labels": err.get("driver_exception_labels")}
    return {"code": err.get("code"), "codeName": err.get("codeName"), "errmsg": err.get("errmsg"),
            "errorLabels_field_present": err.get("_errorLabels_field_present")}


def main():
    global T0
    L1 = CmdLog("client1")
    L2 = CmdLog("client2")
    c1 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[L1])
    c2 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[L2])
    cb = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, maxPoolSize=50)
    ci = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, maxPoolSize=50)
    try:
        for level in (None, "snapshot", "majority"):
            iso_check(c1, c2, L2, level)

        db = c1[DB]
        for name in ("fbusy", "fidle"):
            db.drop_collection(name)
            db.create_collection(name)
        # warm both pools so the first timed operation does not include a TLS handshake
        for cl in (cb, ci):
            threads = [threading.Thread(target=lambda cl=cl: cl[DB]["fbusy"].find_one({"_id": "none"})) for _ in range(12)]
            [t.start() for t in threads]
            [t.join() for t in threads]

        T0 = time.monotonic()
        R.record("g0 timing origin", "T0 = time.monotonic() before starting the concurrent trials", {"T0_utc": utc()},
                 "All abs_s values below are seconds after this instant.")
        plan = []
        for k, st in enumerate((0.0, 5.0, 10.0, 15.0, 20.0, 25.0)):
            plan.append(("busy", dict(client=cb, k=k, start_at=st, interval=1.0, max_age=100.0)))
        for k, st in ((6, 0.0), (7, 2.5)):
            plan.append(("busy", dict(client=cb, k=k, start_at=st, interval=5.0, max_age=100.0)))
        idle_specs = [(0, 0.0, 25, False), (1, 0.0, 31, False), (2, 0.0, 36, False), (3, 10.0, 36, False), (4, 20.0, 36, False),
                      (5, 0.0, 45, False), (6, 0.0, 60, False), (7, 0.0, 75, False),
                      (8, 0.0, 36, True), (9, 10.0, 36, True), (10, 20.0, 36, True)]
        for k, st, idle, raw in idle_specs:
            plan.append(("idle", dict(client=ci, k=k, start_at=st, idle_s=idle, raw=raw)))
        results = []
        threads = []
        for kind, kw in plan:
            res = {}
            results.append(res)
            fn = busy_trial if kind == "busy" else idle_trial
            t = threading.Thread(target=fn, kwargs={**kw, "res": res}, daemon=True)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(400)

        for res in results:
            if res.get("kind") == "busy":
                cmd = (f"busy trial {res['trial']}: s.start_transaction(); fbusy.insert_one({{'_id': ..., 'k': {res['trial'].split('-')[1]}}}, session=s) "
                       f"every {res['interval_s']} s from planned start {res['planned_start_s']} s until the first failure (+1 confirming write) or age 100 s; s.commit_transaction(); "
                       "fbusy.count_documents({'k': k}) outside the transaction")
                R.record(f"g-{res['trial']}", cmd, res)
            else:
                path = res.get("path")
                if path == "raw wire":
                    cmd = (f"idle trial {res['trial']}: s.start_transaction(); fidle.insert_one(start doc, session=s); sleep {res['idle_s']} s; "
                           "raw {insert:'fidle', documents:[...], lsid, txnNumber, autocommit:false}; raw {commitTransaction:1, ...}; raw {abortTransaction:1, ...}")
                else:
                    cmd = (f"idle trial {res['trial']}: s.start_transaction(); fidle.insert_one(start doc, session=s); sleep {res['idle_s']} s; "
                           "fidle.insert_one(after doc, session=s); s.commit_transaction()")
                R.record(f"g-{res['trial']}", cmd, res)

        summary = {"busy": [], "idle": []}
        for res in results:
            if res.get("kind") == "busy":
                ff = res.get("first_failure")
                summary["busy"].append({
                    "trial": res["trial"], "interval_s": res["interval_s"], "txn_start_abs_s": res.get("txn_start_abs_s"),
                    "last_ok_age_s": res.get("last_ok_age_s"), "last_ok_abs_s": res.get("last_ok_abs_s"),
                    "first_failure_age_s": ff["age_s"] if ff else None, "first_failure_abs_s": ff["abs_s"] if ff else None,
                    "first_failure": brief(ff["error"]) if ff else None, "commit": brief(res.get("commit")),
                    "commit_age_s": res.get("commit_age_s"), "n_writes_ok": res.get("n_writes_ok"), "docs_visible_after": res.get("docs_visible_after")})
            else:
                summary["idle"].append({
                    "trial": res["trial"], "path": res.get("path"), "idle_s": res.get("idle_s"), "txn_start_abs_s": res.get("txn_start_abs_s"),
                    "write_abs_s": res.get("write_abs_s"), "write_age_s": res.get("write_age_s"), "write": brief(res.get("write")),
                    "commit": brief(res.get("commit")), "abort": brief(res.get("abort")) if "abort" in res else None,
                    "docs_visible_after": res.get("docs_visible_after")})
        R.record("g-summary concurrent busy and idle trials", "summary of the g-* trials above", summary)
    finally:
        for cl in (c1, c2, cb, ci):
            cl.close()


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    try:
        main()
    except Exception as e:  # noqa: BLE001
        R.record("FATAL", "txn_followup.py", {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())},
                 "Script error, not a server observation.")
    write_json(os.path.join(HERE, "txn_followup_steps.json"), {
        "part": "transactions follow-up (isolation; 30 s limit characterisation)", "database": DB, "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(), "driver": f"pymongo {pymongo.__version__}",
        "uri_used": "MANAGED_URI (plain host)", "steps": R.steps})
    print("\nwritten:", os.path.join(HERE, "txn_followup_steps.json"))
