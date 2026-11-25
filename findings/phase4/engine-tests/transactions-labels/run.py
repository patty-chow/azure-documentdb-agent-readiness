"""Test transactions-labels: transaction error shapes on documentdb-local.

Owns database t_txn only. Rerun with:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python run.py
Reads LOCAL_URI from ../local.env; never prints credentials.
"""
import json, os, re, sys, time, threading, traceback
from datetime import datetime, timezone

import pymongo
from bson import Int64
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure, InvalidOperation
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "local.env")
DB = "t_txn"
COLL = "docs"


def load_uri():
    with open(ENV) as f:
        for line in f:
            m = re.match(r'^LOCAL_URI=(.*)$', line.strip())
            if m:
                v = m.group(1).strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found")


def redact(s):
    return re.sub(r'//[^@/]*@', '//***@', str(s))


def jsonable(o):
    """Make a server response JSON-serialisable (Int64, Timestamp, ObjectId, datetime...)."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (str, int, float, bool)) or o is None:
        return o
    return repr(o)


def err_dict(exc):
    d = {"exception": type(exc).__name__, "message": redact(str(exc))}
    if isinstance(exc, OperationFailure):
        det = exc.details or {}
        d.update({
            "code": det.get("code", exc.code),
            "codeName": det.get("codeName"),
            "errmsg": det.get("errmsg"),
            "errorLabels": det.get("errorLabels"),
            "raw": jsonable(det),
        })
    elif isinstance(exc, PyMongoError):
        d["errorLabels"] = sorted(getattr(exc, "_error_labels", set()) or [])
    return d


steps = []


def record(step, command, response, reading):
    entry = {"step": step, "command": command, "response": jsonable(response), "reading": reading}
    steps.append(entry)
    print(f"\n### {step}\n  cmd: {command}\n  resp: {json.dumps(entry['response'], default=str)[:1500]}\n  read: {reading}")
    return entry


def raw_admin(client, doc):
    """Send a command on admin verbatim (pymongo adds only $db), return the raw reply document."""
    with client._conn_for_writes(None, "raw_admin") as conn:
        return conn.command("admin", dict(doc), check=False)


def txn_ids(session):
    return {"lsid": session.session_id, "txnNumber": Int64(session._server_session.transaction_id)}


def summarize_err_reply(reply):
    return {k: reply.get(k) for k in ("ok", "code", "codeName", "errmsg", "errorLabels") if k in reply}


def main():
    uri = load_uri()
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    # Second client so the two sessions use separate connections.
    client2 = MongoClient(uri, serverSelectionTimeoutMS=10000)

    bi = client.admin.command("buildInfo")
    record("0a buildInfo", "db.adminCommand({buildInfo: 1})",
           {k: bi.get(k) for k in ("version", "versionArray", "gitVersion", "modules", "ok")},
           "Version reported by the documentdb-local gateway; all facts below are about this engine/gateway build, not the managed service.")
    hello = client.admin.command("hello")
    record("0b hello", "db.adminCommand({hello: 1})",
           {k: hello.get(k) for k in ("maxWireVersion", "minWireVersion", "logicalSessionTimeoutMinutes", "maxWriteBatchSize", "isWritablePrimary", "setName", "msg")},
           "Wire version, session timeout and batch size advertised by the gateway (logicalSessionTimeoutMinutes must be present for the driver to allow sessions/transactions).")
    record("0c pymongo", "import pymongo; pymongo.__version__", pymongo.__version__, "Driver used for every step.")

    db = client[DB]
    db.drop_collection(COLL)
    coll = db[COLL]
    coll.insert_one({"_id": 1, "v": 0})
    record("0d setup", f"db.{COLL}.drop(); db.{COLL}.insertOne({{_id: 1, v: 0}})", {"inserted": 1},
           "Fresh collection with one document that both transactions will update.")

    # ---------------------------------------------------------------- 1. write conflict
    sA = client.start_session()
    sB = client2.start_session()
    sA.start_transaction()
    rA = client[DB][COLL].update_one({"_id": 1}, {"$set": {"v": 1, "by": "A"}}, session=sA)
    record("1a session A: update in txn", "sA.startTransaction(); db.docs.updateOne({_id:1},{$set:{v:1,by:'A'}}, {session: sA})",
           {"matched": rA.matched_count, "modified": rA.modified_count, "txnNumber": str(sA._server_session.transaction_id)},
           "Transaction A holds the row lock on _id 1.")

    sB.start_transaction()
    b_result = {}

    def b_update():
        t0 = time.monotonic()
        try:
            r = client2[DB][COLL].update_one({"_id": 1}, {"$set": {"v": 2, "by": "B"}}, session=sB)
            b_result["ok"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa
            b_result["error"] = err_dict(e)
        b_result["elapsed_s"] = round(time.monotonic() - t0, 3)

    tB = threading.Thread(target=b_update, daemon=True)
    t_start = time.monotonic()
    tB.start()
    tB.join(3.0)
    b_blocked_before_commit = tB.is_alive()
    record("1b session B: update same doc in txn (A uncommitted)",
           "sB.startTransaction(); db.docs.updateOne({_id:1},{$set:{v:2,by:'B'}}, {session: sB})  // waited up to 3s",
           {"still_blocked_after_3s": b_blocked_before_commit, "result_so_far": b_result or None},
           ("B's update is blocked waiting on A's row lock (no immediate error)." if b_blocked_before_commit
            else "B's update returned before A committed; see result."))

    cA = None
    try:
        sA.commit_transaction()
        cA = {"ok": 1}
    except Exception as e:  # noqa
        cA = err_dict(e)
    t_commit = round(time.monotonic() - t_start, 3)
    record("1c commit A", "sA.commitTransaction()", {"result": cA, "t_since_B_started_s": t_commit},
           "A commits while B is waiting/has failed.")

    tB.join(120.0)
    record("1d session B: outcome of the conflicting update", "(result of B's updateOne after A committed)",
           {"thread_finished": not tB.is_alive(), **b_result},
           "THE KEY OBSERVATION: exact code/codeName/errmsg and whether errorLabels (TransientTransactionError) is present on a write conflict.")

    if "ok" in b_result:
        try:
            sB.commit_transaction(); cb = {"ok": 1}
        except Exception as e:  # noqa
            cb = err_dict(e)
        record("1e commit B (update had succeeded)", "sB.commitTransaction()", cb, "If B's update went through after A's commit, does B's commit succeed?")
    else:
        try:
            sB.abort_transaction(); ab = {"ok": 1}
        except Exception as e:  # noqa
            ab = err_dict(e)
        record("1e abort B after its error", "sB.abortTransaction()", ab, "Driver-side abort of the failed transaction B (pymongo may skip the server call if it already considers the txn aborted).")
    doc = coll.find_one({"_id": 1})
    record("1f final document", "db.docs.findOne({_id:1})", doc, "Which transaction's write survived.")
    sA.end_session(); sB.end_session()

    # 1g: same conflict but with the raw wire reply (check=False) to see the untouched server document.
    coll.update_one({"_id": 1}, {"$set": {"v": 0, "by": None}})
    sA = client.start_session(); sB = client2.start_session()
    sA.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$set": {"v": 11, "by": "A2"}}, session=sA)
    sB.start_transaction()
    raw_b = {}

    def b_raw():
        t0 = time.monotonic()
        try:
            # Raw update command inside B's txn so the reply document is captured untouched.
            ids = txn_ids(sB)
            cmd = {"update": COLL, "updates": [{"q": {"_id": 1}, "u": {"$set": {"v": 22, "by": "B2"}}}],
                   "lsid": ids["lsid"], "txnNumber": ids["txnNumber"], "autocommit": False}
            with client2._conn_for_writes(None, "raw_update") as conn:
                raw_b["reply"] = conn.command(DB, cmd, check=False)
        except Exception as e:  # noqa
            raw_b["error"] = err_dict(e)
        raw_b["elapsed_s"] = round(time.monotonic() - t0, 3)

    # B must have sent startTransaction semantics: pymongo sends startTransaction:true on the first op.
    # We cannot easily add that by hand, so first run a harmless find in B's txn through pymongo to open it on the server.
    _ = list(client2[DB][COLL].find({"_id": -1}, session=sB))
    tB = threading.Thread(target=b_raw, daemon=True); tB.start(); tB.join(2.0)
    try:
        sA.commit_transaction(); cA2 = {"ok": 1}
    except Exception as e:  # noqa
        cA2 = err_dict(e)
    tB.join(120.0)
    record("1g write conflict, raw wire reply", "B: {update:'docs', updates:[...], lsid, txnNumber, autocommit:false} sent verbatim after A's update; then A commits",
           {"commitA": cA2, **raw_b},
           "Raw server reply for the conflicting write (shows exactly which fields, e.g. errorLabels, the gateway puts on the wire).")
    try:
        ab = raw_admin(client2, {"abortTransaction": 1, **txn_ids(sB), "autocommit": False})
    except Exception as e:  # noqa
        ab = err_dict(e)
    record("1h raw abortTransaction for B", "{abortTransaction:1, lsid, txnNumber, autocommit:false} on admin", ab,
           "What abortTransaction returns for a transaction that failed with a write conflict.")
    sA.end_session(); sB.end_session()

    # ---------------------------------------------------------------- 2. readConcern levels
    for level in ("snapshot", "majority", "local"):
        s = client.start_session()
        try:
            s.start_transaction(read_concern=ReadConcern(level))
            got = list(client[DB][COLL].find({"_id": 1}, session=s))
            try:
                s.commit_transaction(); c = {"ok": 1}
            except Exception as e:  # noqa
                c = err_dict(e)
            resp = {"find_result": got, "commit": c}
            reading = f"Transaction started with readConcern level '{level}' was accepted (find + commit succeeded)."
        except Exception as e:  # noqa
            resp = err_dict(e)
            reading = f"Transaction with readConcern level '{level}' rejected: see code/codeName/errmsg."
            try:
                s.abort_transaction()
            except Exception:
                pass
        record(f"2 readConcern {level}", f"s.startTransaction({{readConcern: {{level: '{level}'}}}}); db.docs.find({{_id:1}}, {{session: s}}); s.commitTransaction()", resp, reading)
        s.end_session()

    # ---------------------------------------------------------------- 3. commit twice / abort after commit (driver path)
    s = client.start_session()
    s.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$inc": {"v": 100}}, session=s)
    try:
        s.commit_transaction(); c1 = {"ok": 1}
    except Exception as e:  # noqa
        c1 = err_dict(e)
    try:
        s.commit_transaction(); c2 = {"ok": 1, "note": "pymongo re-sent commitTransaction (attempt 2 upgrades writeConcern to w:'majority', wtimeout 10000)"}
    except Exception as e:  # noqa
        c2 = err_dict(e)
    try:
        s.abort_transaction(); a1 = {"ok": 1}
    except Exception as e:  # noqa
        a1 = err_dict(e)
    record("3a driver: commit, commit again, abort after commit",
           "s.commitTransaction(); s.commitTransaction(); s.abortTransaction()",
           {"commit1": c1, "commit2": c2, "abort_after_commit": a1},
           "Driver-level behaviour: second commit is a retry (server reply recorded), abort-after-commit is refused client-side by pymongo if InvalidOperation appears.")
    s.end_session()

    # 3b raw wire: commit twice and abort after commit, exact server replies
    s = client.start_session()
    s.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$inc": {"v": 1000}}, session=s)
    ids = txn_ids(s)
    r1 = raw_admin(client, {"commitTransaction": 1, **ids, "autocommit": False})
    r2 = raw_admin(client, {"commitTransaction": 1, **ids, "autocommit": False})
    r2m = raw_admin(client, {"commitTransaction": 1, **ids, "autocommit": False, "writeConcern": {"w": "majority", "wtimeout": 10000}})
    r3 = raw_admin(client, {"abortTransaction": 1, **ids, "autocommit": False})
    record("3b raw: commitTransaction x2 (+ majority wc retry form), then abortTransaction",
           "{commitTransaction:1, lsid, txnNumber, autocommit:false} twice; same with writeConcern {w:'majority',wtimeout:10000}; then {abortTransaction:1, lsid, txnNumber, autocommit:false}",
           {"commit1": r1, "commit2": r2, "commit2_majority_wc": r2m, "abort_after_commit": r3},
           "Exact server replies: whether a repeated commit is idempotent and what abort-after-commit returns (code/codeName/errmsg/errorLabels).")
    # Mark the pymongo session as finished so end_session does not try to abort.
    try:
        s.abort_transaction()
    except Exception:
        pass
    s.end_session()

    # 3c raw: abort twice, and commit after abort
    s = client.start_session()
    s.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$inc": {"v": 1}}, session=s)
    ids = txn_ids(s)
    a1 = raw_admin(client, {"abortTransaction": 1, **ids, "autocommit": False})
    a2 = raw_admin(client, {"abortTransaction": 1, **ids, "autocommit": False})
    c_after_abort = raw_admin(client, {"commitTransaction": 1, **ids, "autocommit": False})
    record("3c raw: abortTransaction x2, then commitTransaction after abort",
           "{abortTransaction:1,...} twice; then {commitTransaction:1,...}",
           {"abort1": a1, "abort2": a2, "commit_after_abort": c_after_abort},
           "Companion to 3b: idempotency of abort and the error for commit-after-abort.")
    try:
        s.abort_transaction()
    except Exception:
        pass
    s.end_session()

    # ---------------------------------------------------------------- 4. idle > 35 s
    coll.update_one({"_id": 1}, {"$set": {"v": 0}})
    s = client.start_session()
    s.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$set": {"idle": "start"}}, session=s)
    t0 = time.monotonic()
    time.sleep(36)
    slept = round(time.monotonic() - t0, 1)
    try:
        r = client[DB][COLL].update_one({"_id": 1}, {"$set": {"idle": "after"}}, session=s)
        w = {"matched": r.matched_count, "modified": r.modified_count}
    except Exception as e:  # noqa
        w = err_dict(e)
    record("4a write after 36 s idle in txn", f"s.startTransaction(); updateOne(...); sleep({slept}s); updateOne({{_id:1}},{{$set:{{idle:'after'}}}}, {{session: s}})",
           {"slept_s": slept, "write_result": w},
           "Error (code, codeName, errmsg, errorLabels) a client gets when writing in a transaction that sat idle past the 30 s transaction lifetime.")
    try:
        s.commit_transaction(); c = {"ok": 1}
    except Exception as e:  # noqa
        c = err_dict(e)
    record("4b commit after idle timeout", "s.commitTransaction()", c, "Commit response for the expired transaction.")
    try:
        s.abort_transaction(); a = {"ok": 1}
    except Exception as e:  # noqa
        a = err_dict(e)
    record("4c abort after idle timeout", "s.abortTransaction()", a, "Abort response for the expired transaction (pymongo may short-circuit).")
    s.end_session()

    # 4d raw wire version of the idle timeout, to capture the untouched reply document
    s = client.start_session()
    s.start_transaction()
    client[DB][COLL].update_one({"_id": 1}, {"$set": {"idle2": "start"}}, session=s)
    ids = txn_ids(s)
    time.sleep(36)
    with client._conn_for_writes(None, "raw_update") as conn:
        raw_w = conn.command(DB, {"update": COLL, "updates": [{"q": {"_id": 1}, "u": {"$set": {"idle2": "after"}}}],
                                  **ids, "autocommit": False}, check=False)
    raw_c = raw_admin(client, {"commitTransaction": 1, **ids, "autocommit": False})
    raw_a = raw_admin(client, {"abortTransaction": 1, **ids, "autocommit": False})
    record("4d raw: write, commit, abort after 36 s idle",
           "{update:'docs',..., lsid, txnNumber, autocommit:false} after sleep(36); then raw commitTransaction; then raw abortTransaction",
           {"update": raw_w, "commit": raw_c, "abort": raw_a},
           "Exact wire replies for the expired transaction, including whether errorLabels is present.")
    try:
        s.abort_transaction()
    except Exception:
        pass
    s.end_session()

    doc = coll.find_one({"_id": 1})
    record("5 final state", "db.docs.findOne({_id:1})", doc, "Final document after all steps (idle-transaction writes must not have been applied).")
    client.close(); client2.close()
    return bi


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    bi = None
    fatal = None
    try:
        bi = main()
    except Exception as e:  # noqa
        fatal = {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())}
        print("FATAL", fatal)
    report = {
        "test": "transactions-labels",
        "database": DB,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "target": "documentdb-local container ddb-engine-test (ghcr.io/documentdb/documentdb/documentdb-local:latest), localhost:10260, TLS self-signed",
        "engine_version": (bi or {}).get("version"),
        "buildInfo": jsonable({k: (bi or {}).get(k) for k in ("version", "versionArray", "gitVersion", "modules")}),
        "driver": f"pymongo {pymongo.__version__}",
        "evidence_scope": "Observed on the open-source documentdb engine + gateway at the buildInfo version above (documentdb-local). This is evidence about the open-source engine/gateway only; it does not prove managed Azure DocumentDB behaviour.",
        "steps": steps,
        "fatal": fatal,
    }
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("\nreport written:", os.path.join(HERE, "report.json"))
