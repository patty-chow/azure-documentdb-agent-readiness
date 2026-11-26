"""m-txn-bulk follow-up 3: reproduce the silent rollback after a 117 in a snapshot transaction (h1) twice,
and add a write after the conflict. Owns database mt_txn only (collection serr2). Writes txn_errors2_steps.json.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python txn_errors2.py
"""
import os
import sys
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
        return {"ok": 1, "result": fn()}
    except Exception as e:  # noqa: BLE001
        return err_dict(e)


def main():
    L = CmdLog("client2")
    c1 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000)
    c2 = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=150000, event_listeners=[L])
    out1 = c1[DB]["serr2"]
    tx = c2[DB]["serr2"]
    try:
        c1[DB].drop_collection("serr2")
        c1[DB].create_collection("serr2")
        for run in (1, 2):
            y = f"Y-{run}"
            out1.insert_one({"_id": y, "v": 0})
            s = c2.start_session()
            s.start_transaction(read_concern=ReadConcern("snapshot"))
            m = L.mark()
            res = {}
            res["insert_pre"] = attempt(lambda: str(tx.insert_one({"_id": f"pre-{run}"}, session=s).inserted_id))
            res["read_Y"] = attempt(lambda: tx.find_one({"_id": y}, session=s))
            res["outside_update_Y"] = attempt(lambda: out1.update_one({"_id": y}, {"$set": {"v": 7, "by": "outside"}}).modified_count)
            res["update_Y_in_txn"] = attempt(lambda: tx.update_one({"_id": y}, {"$set": {"v": 8, "by": "txn"}}, session=s).modified_count)
            if run == 2:
                res["insert_post_after_conflict"] = attempt(lambda: str(tx.insert_one({"_id": f"post-{run}"}, session=s).inserted_id))
            res["commit"] = attempt(lambda: s.commit_transaction())
            res["wire_commands"] = L.since(m)
            res["after_pre_visible"] = out1.count_documents({"_id": f"pre-{run}"})
            res["after_post_visible"] = out1.count_documents({"_id": f"post-{run}"})
            res["after_Y"] = out1.find_one({"_id": y})
            s.end_session()
            extra = "; serr2.insert_one({'_id':'post-2'}, session=s)" if run == 2 else ""
            R.record(f"h1-repeat-{run} snapshot txn: insert pre, read Y, outside write to Y, update Y in txn (117){', insert post' if run == 2 else ''}, commit",
                     "s.start_transaction(read_concern=ReadConcern('snapshot')); serr2.insert_one({'_id':'pre-%d'}, session=s); serr2.find_one({'_id':'%s'}, session=s); "
                     "serr2.update_one({'_id':'%s'}, {'$set': {'v': 7}}) [other client]; serr2.update_one({'_id':'%s'}, {'$set': {'v': 8}}, session=s)%s; "
                     "s.commit_transaction(); serr2.count_documents(...)" % (run, y, y, y, extra), res)
    finally:
        c1.close()
        c2.close()


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    try:
        main()
    except Exception as e:  # noqa: BLE001
        R.record("FATAL", "txn_errors2.py", {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())})
    write_json(os.path.join(HERE, "txn_errors2_steps.json"), {"part": "transactions follow-up 3 (repeat of h1)", "database": DB,
               "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "driver": f"pymongo {pymongo.__version__}", "steps": R.steps})
