"""m-txn-bulk follow-up 2: what commitTransaction does after a statement inside the transaction failed.

Why: txn_followup.py showed that after a 117 ConflictingOperationInProgress inside a snapshot transaction,
commitTransaction returned ok:1, while after a 112 WriteConflict (part a) the transaction was already gone (251).
Each case here first makes one successful write (doc X), then a failing statement, then commits, then checks
outside the transaction whether X was kept. Owns database mt_txn only (collection serr). Writes txn_errors_steps.json.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python txn_errors.py
"""
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB, ENV, HERE, CmdLog, Recorder, err_dict, redact, write_json  # noqa: E402

import pymongo  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from pymongo.read_concern import ReadConcern  # noqa: E402

R = Recorder()


def attempt(fn):
    try:
        r = fn()
        return {"ok": 1, "result": r}
    except Exception as e:  # noqa: BLE001
        return err_dict(e)


def main():
    L = CmdLog("client2")
    c1 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000)
    c2 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[L])
    out1 = c1[DB]["serr"]
    tx = c2[DB]["serr"]
    try:
        c1[DB].drop_collection("serr")
        c1[DB].create_collection("serr")
        out1.insert_many([{"_id": "Y1", "v": 0}, {"_id": "Y2", "v": 0}, {"_id": "Y4", "s": "text"}])
        R.record("h0 setup", "serr.insert_many([{_id:'Y1',v:0},{_id:'Y2',v:0},{_id:'Y4',s:'text'}])", {"inserted": 3})

        # h1: snapshot transaction, serialization conflict (117) after a successful insert
        s = c2.start_session()
        s.start_transaction(read_concern=ReadConcern("snapshot"))
        m = L.mark()
        res = {}
        res["insert_X1"] = attempt(lambda: str(tx.insert_one({"_id": "X1"}, session=s).inserted_id))
        res["read_Y1"] = attempt(lambda: tx.find_one({"_id": "Y1"}, session=s))
        res["outside_update_Y1"] = attempt(lambda: out1.update_one({"_id": "Y1"}, {"$set": {"v": 7, "by": "outside"}}).modified_count)
        res["update_Y1_in_txn"] = attempt(lambda: tx.update_one({"_id": "Y1"}, {"$set": {"v": 8, "by": "txn"}}, session=s).modified_count)
        res["commit"] = attempt(lambda: s.commit_transaction())
        res["wire_commands"] = L.since(m)
        res["after_X1_visible"] = out1.count_documents({"_id": "X1"})
        res["after_Y1"] = out1.find_one({"_id": "Y1"})
        s.end_session()
        R.record("h1 snapshot txn: insert X1, read Y1, outside write to Y1 commits, update Y1 in txn (conflict), commit",
                 "s.start_transaction(read_concern=ReadConcern('snapshot')); serr.insert_one({'_id':'X1'}, session=s); serr.find_one({'_id':'Y1'}, session=s); "
                 "serr.update_one({'_id':'Y1'}, {'$set': {'v': 7}}) [other client, autocommit]; serr.update_one({'_id':'Y1'}, {'$set': {'v': 8}}, session=s); "
                 "s.commit_transaction(); serr.count_documents({'_id':'X1'})", res)

        # h2: default transaction, lock conflict (112) after a successful insert
        sA = c1.start_session()
        sA.start_transaction()
        out1.update_one({"_id": "Y2"}, {"$set": {"v": 1, "by": "A"}}, session=sA)
        s = c2.start_session()
        s.start_transaction()
        m = L.mark()
        res = {}
        res["insert_X2"] = attempt(lambda: str(tx.insert_one({"_id": "X2"}, session=s).inserted_id))
        res["update_Y2_locked_by_A"] = attempt(lambda: tx.update_one({"_id": "Y2"}, {"$set": {"v": 2, "by": "txn"}}, session=s).modified_count)
        res["commit"] = attempt(lambda: s.commit_transaction())
        res["wire_commands"] = L.since(m)
        res["A_commit"] = attempt(lambda: sA.commit_transaction())
        res["after_X2_visible"] = out1.count_documents({"_id": "X2"})
        res["after_Y2"] = out1.find_one({"_id": "Y2"})
        s.end_session()
        sA.end_session()
        R.record("h2 default txn: insert X2, update Y2 while another transaction holds its lock (112), commit",
                 "sA.start_transaction(); serr.update_one({'_id':'Y2'}, ..., session=sA); s.start_transaction(); serr.insert_one({'_id':'X2'}, session=s); "
                 "serr.update_one({'_id':'Y2'}, {'$set': {'v': 2}}, session=s); s.commit_transaction(); sA.commit_transaction(); serr.count_documents({'_id':'X2'})",
                 res)

        # h3: default transaction, duplicate key (11000) after a successful insert
        s = c2.start_session()
        s.start_transaction()
        m = L.mark()
        res = {}
        res["insert_X3"] = attempt(lambda: str(tx.insert_one({"_id": "X3", "n": 1}, session=s).inserted_id))
        res["insert_X3_again_duplicate"] = attempt(lambda: str(tx.insert_one({"_id": "X3", "n": 2}, session=s).inserted_id))
        res["commit"] = attempt(lambda: s.commit_transaction())
        res["wire_commands"] = L.since(m)
        res["after_X3_docs"] = list(out1.find({"_id": "X3"}))
        s.end_session()
        R.record("h3 default txn: insert X3, insert X3 again (duplicate key), commit",
                 "s.start_transaction(); serr.insert_one({'_id':'X3','n':1}, session=s); serr.insert_one({'_id':'X3','n':2}, session=s); s.commit_transaction(); serr.find({'_id':'X3'})",
                 res)

        # h4: default transaction, type error (14) after a successful insert
        s = c2.start_session()
        s.start_transaction()
        m = L.mark()
        res = {}
        res["insert_X4"] = attempt(lambda: str(tx.insert_one({"_id": "X4"}, session=s).inserted_id))
        res["inc_on_string_field"] = attempt(lambda: tx.update_one({"_id": "Y4"}, {"$inc": {"s": 1}}, session=s).modified_count)
        res["commit"] = attempt(lambda: s.commit_transaction())
        res["wire_commands"] = L.since(m)
        res["after_X4_visible"] = out1.count_documents({"_id": "X4"})
        res["after_Y4"] = out1.find_one({"_id": "Y4"})
        s.end_session()
        R.record("h4 default txn: insert X4, $inc on a string field (type error), commit",
                 "s.start_transaction(); serr.insert_one({'_id':'X4'}, session=s); serr.update_one({'_id':'Y4'}, {'$inc': {'s': 1}}, session=s); s.commit_transaction(); "
                 "serr.count_documents({'_id':'X4'})", res)

        # h5: control, a transaction with no failing statement
        s = c2.start_session()
        s.start_transaction()
        res = {}
        res["insert_X5"] = attempt(lambda: str(tx.insert_one({"_id": "X5"}, session=s).inserted_id))
        res["commit"] = attempt(lambda: s.commit_transaction())
        res["after_X5_visible"] = out1.count_documents({"_id": "X5"})
        s.end_session()
        R.record("h5 control: insert X5, commit", "s.start_transaction(); serr.insert_one({'_id':'X5'}, session=s); s.commit_transaction()", res)
    finally:
        c1.close()
        c2.close()


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    try:
        main()
    except Exception as e:  # noqa: BLE001
        R.record("FATAL", "txn_errors.py", {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())},
                 "Script error, not a server observation.")
    write_json(os.path.join(HERE, "txn_errors_steps.json"), {
        "part": "transactions follow-up 2 (commit after a failed statement)", "database": DB, "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(), "driver": f"pymongo {pymongo.__version__}", "steps": R.steps})
    print("\nwritten:", os.path.join(HERE, "txn_errors_steps.json"))
