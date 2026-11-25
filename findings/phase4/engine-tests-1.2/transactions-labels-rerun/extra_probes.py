#!/usr/bin/env python3
"""transactions-labels-rerun: added probes run by the rerun agent (not part of the tester's run.py).

Owns database t_txn_rerun only (drops it at the start and at the end). Reuses the helpers of run.py in this folder
(credential loading, redaction, wire capture, raw command sending), so the same rules apply: nothing printed or
written contains the password.

Rerun:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I \
    /private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/transactions-labels-rerun/extra_probes.py

Writes extra_probes.json next to this file. Takes about 5 seconds.

Probes (each answers something a conclusion of the tester relies on but did not test):
  P1  commitTransaction / abortTransaction for a transaction number that never started (is "commit returns ok"
      evidence that something was committed?)
  P2  a NON-transactional update to a document that an open transaction has locked (does the 20 ms lock timeout
      apply outside transactions too, and with which code/labels?)
  P3  the 1k lost-update ordering, but B uses an atomic $inc instead of a client-computed $set
  P4  the 1k lost-update ordering, but B uses optimistic concurrency (version field in the update filter)
  P5  two transactions insert the same _id (unique-key race inside transactions)
  P6  the 1k read ordering with readConcern majority on B's transaction (does the accepted level change visibility?)
"""
import json
import os
import sys
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as T  # noqa: E402  (the rerun copy of the tester's script; DB is t_txn_rerun)

from bson import Int64  # noqa: E402
from bson.binary import Binary, UUID_SUBTYPE  # noqa: E402
from pymongo import MongoClient  # noqa: E402

assert T.DB == "t_txn_rerun", T.DB
DB, COLL = T.DB, T.COLL
RES = {"database": DB, "probes": {}}


def doc1(c, _id=1):
    return c[DB][COLL].find_one({"_id": _id})


def put(name, command, response, reading, m):
    RES["probes"][name] = {"command": command, "response": T.jsonable(response), "reading": reading,
                           "wire": T.wire_since(m)}
    T.log(f"\n### {name}\n  resp: {json.dumps(T.jsonable(response), default=str)[:1500]}\n  read: {reading}")


def main():
    c1 = MongoClient(T.URI, serverSelectionTimeoutMS=10000, socketTimeoutMS=90000, appname="t_txn-probe-c1",
                     event_listeners=[T.Wire("c1")])
    c2 = MongoClient(T.URI, serverSelectionTimeoutMS=10000, socketTimeoutMS=90000, appname="t_txn-probe-c2",
                     event_listeners=[T.Wire("c2")])
    coll1, coll2 = c1[DB][COLL], c2[DB][COLL]
    try:
        c1.drop_database(DB)
        c1[DB].create_collection(COLL)
        coll1.insert_one({"_id": 1, "v": 0, "ver": 0})

        # ---------------------------------------------------------------- P1 commit/abort of a never-started txn
        m = T.mark()
        lsid = {"id": Binary(uuid.uuid4().bytes, UUID_SUBTYPE)}
        cmds, reps = [], []
        for doc, db in (({"commitTransaction": 1, "lsid": lsid, "txnNumber": Int64(1), "autocommit": False}, "admin"),
                        ({"abortTransaction": 1, "lsid": lsid, "txnNumber": Int64(2), "autocommit": False}, "admin")):
            cmds.append(doc)
            reps.append(T.raw(c1, db, doc))
        # same lsid: run and commit txn 3, then commit txn 7 (never started) and txn 3 again
        rt = T.RawTxn(c1)
        rt.lsid = lsid
        rt.txn = Int64(3)
        u = rt.update({"_id": 1}, {"$inc": {"v": 0}})
        c3 = rt.commit()
        never = {"commitTransaction": 1, "lsid": lsid, "txnNumber": Int64(7), "autocommit": False}
        r7 = T.raw(c1, "admin", never)
        c3b = rt.commit()
        rt.end()
        resp = {"commit_never_started_txn_1_fresh_lsid": reps[0], "abort_never_started_txn_2": reps[1],
                "txn_3_update": u[1], "txn_3_commit": c3[1], "commit_never_started_txn_7_after_txn_3": r7,
                "txn_3_commit_again": c3b[1]}
        put("P1 commitTransaction/abortTransaction for transaction numbers that never started",
            [cmds[0], cmds[1], u[0], c3[0], never, c3b[0]], resp,
            f"commitTransaction for a never-started transaction returned {T.desc(reps[0])} on a fresh lsid and "
            f"{T.desc(r7)} for txnNumber 7 after txn 3 committed, abortTransaction for a never-started one returned "
            f"{T.desc(reps[1])}, and re-committing txn 3 returned {T.desc(c3b[1])}.", m)

        # ---------------------------------------------------------------- P2 non-transactional write vs a txn lock
        coll1.replace_one({"_id": 1}, {"_id": 1, "v": 0, "ver": 0})
        sA = c1.start_session()
        m = T.mark()
        sA.start_transaction()
        coll1.update_one({"_id": 1}, {"$set": {"v": 1, "by": "A-txn"}}, session=sA)
        out = {}
        a_commit = {}

        def commit_a():
            try:
                sA.commit_transaction()
                a_commit["result"] = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                a_commit["result"] = T.err(e)
            a_commit["at_s"] = T.now_s()

        tm = threading.Timer(1.0, commit_a)
        t0 = time.monotonic()
        out["sent_at_s"] = T.now_s()
        tm.start()
        try:
            r = coll2.update_one({"_id": 1}, {"$set": {"v": 2, "by": "B-plain"}})
            out["result"] = {"matched": r.matched_count, "modified": r.modified_count}
        except Exception as e:  # noqa: BLE001
            out["error"] = T.err(e)
        out["elapsed_s"] = round(time.monotonic() - t0, 3)
        out["finished_at_s"] = T.now_s()
        tm.join(10)
        sA.end_session()
        out["A_commit"] = a_commit
        out["document_after"] = doc1(c1)
        if "error" in out:
            rd = (f"A non-transactional update to a document locked by an open transaction failed after "
                  f"{out['elapsed_s']} s, before the transaction committed at 1.0 s, with {T.desc(out['error'])}.")
        else:
            rd = (f"A non-transactional update to a document locked by an open transaction waited {out['elapsed_s']} s, "
                  f"until the transaction committed at about 1.0 s, and then succeeded ({out['result']}), so the 20 ms "
                  f"lock timeout seen inside transactions did not apply to this non-transactional write.")
        put("P2 non-transactional update_one on a document locked by an open transaction (A commits after 1.0 s)",
            "sA.start_transaction(); c1...update_one({'_id': 1}, {'$set': {'v': 1, 'by': 'A-txn'}}, session=sA); "
            "threading.Timer(1.0, sA.commit_transaction).start(); "
            "c2.t_txn_rerun.docs.update_one({'_id': 1}, {'$set': {'v': 2, 'by': 'B-plain'}})   (no session argument)",
            out, rd, m)

        # ---------------------------------------------------------------- P3 / P4 lost-update ordering variants
        def ordering(name, b_update, filt_desc):
            coll1.replace_one({"_id": 1}, {"_id": 1, "v": 0, "ver": 0})
            sA, sB = c1.start_session(), c2.start_session()
            m = T.mark()
            sB.start_transaction()
            b_first = coll2.find_one({"_id": 1}, session=sB)
            sA.start_transaction()
            coll1.update_one({"_id": 1}, {"$inc": {"v": 1, "ver": 1}, "$set": {"by": "A"}}, session=sA)
            try:
                sA.commit_transaction()
                a_c = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                a_c = T.err(e)
            q, u = b_update(b_first)
            try:
                r = coll2.update_one(q, u, session=sB)
                b_u = {"filter": q, "update": u, "matched": r.matched_count, "modified": r.modified_count}
            except Exception as e:  # noqa: BLE001
                b_u = {"filter": q, "update": u, "error": T.err(e)}
            try:
                sB.commit_transaction()
                b_c = {"ok": 1}
            except Exception as e:  # noqa: BLE001
                b_c = T.err(e)
            sA.end_session()
            sB.end_session()
            final = doc1(c1)
            return {"B_first_read": b_first, "A_commit": a_c, "B_update": b_u, "B_commit": b_c,
                    "document_after": final}, m

        resp, m = ordering("P3", lambda first: ({"_id": 1}, {"$inc": {"v": 10}, "$set": {"by": "B"}}), "")
        f = resp["document_after"] or {}
        put("P3 1k ordering with an atomic $inc in B (B reads, A $inc and commits, B $inc v by 10, B commits)",
            "sB.start_transaction(); c2...find_one({'_id': 1}, session=sB); sA.start_transaction(); "
            "c1...update_one({'_id': 1}, {'$inc': {'v': 1, 'ver': 1}, '$set': {'by': 'A'}}, session=sA); "
            "sA.commit_transaction(); c2...update_one({'_id': 1}, {'$inc': {'v': 10}, '$set': {'by': 'B'}}, session=sB); "
            "sB.commit_transaction()", resp,
            f"With an atomic $inc instead of a client-computed $set, the final v is {f.get('v')} "
            f"({'both increments kept, no lost update' if f.get('v') == 11 else 'see response'}), B's update matched "
            f"{(resp['B_update'] or {}).get('matched')} and B's commit returned {T.desc(resp['B_commit'])}.", m)

        resp, m = ordering("P4", lambda first: ({"_id": 1, "ver": (first or {}).get("ver")},
                                                {"$set": {"v": (first or {}).get("v", 0) + 10, "by": "B"},
                                                 "$inc": {"ver": 1}}), "")
        f = resp["document_after"] or {}
        put("P4 1k ordering with optimistic concurrency in B (update filter carries the version B read first)",
            "same ordering as P3, but B sends update_one({'_id': 1, 'ver': <ver from B's first read>}, "
            "{'$set': {'v': <v from B's first read> + 10, 'by': 'B'}, '$inc': {'ver': 1}}, session=sB)", resp,
            f"With the version B read in the update filter, B's update matched "
            f"{(resp['B_update'] or {}).get('matched')} document(s) after A's commit, B's commit returned "
            f"{T.desc(resp['B_commit'])}, and the final document is {f}, so "
            + ("the stale write was detected (matched 0) and A's increment survived."
               if (resp['B_update'] or {}).get('matched') == 0 and f.get('v') == 1 else "see response."), m)

        # ---------------------------------------------------------------- P5 duplicate _id insert race
        sA, sB = c1.start_session(), c2.start_session()
        m = T.mark()
        sA.start_transaction()
        coll1.insert_one({"_id": 50, "by": "A"}, session=sA)
        sB.start_transaction()
        t0 = time.monotonic()
        try:
            coll2.insert_one({"_id": 50, "by": "B"}, session=sB)
            b_ins = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            b_ins = T.err(e)
        b_el = round(time.monotonic() - t0, 3)
        try:
            sA.commit_transaction()
            a_c = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            a_c = T.err(e)
        try:
            sB.commit_transaction()
            b_c = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            b_c = T.err(e)
        sA.end_session()
        sB.end_session()
        resp = {"B_insert": b_ins, "B_insert_elapsed_s": b_el, "A_commit": a_c, "B_commit": b_c,
                "document_after": doc1(c1, 50)}
        put("P5 two transactions insert the same _id (A uncommitted when B inserts)",
            "sA.start_transaction(); c1...insert_one({'_id': 50, 'by': 'A'}, session=sA); sB.start_transaction(); "
            "c2...insert_one({'_id': 50, 'by': 'B'}, session=sB); sA.commit_transaction(); sB.commit_transaction()",
            resp,
            f"B's insert of an _id that A had inserted but not committed returned {T.desc(b_ins)} after {b_el} s, "
            f"A's commit returned {T.desc(a_c)} and B's commit returned {T.desc(b_c)}.", m)

        # ---------------------------------------------------------------- P6 does readConcern majority change visibility?
        from pymongo.read_concern import ReadConcern
        coll1.replace_one({"_id": 1}, {"_id": 1, "v": 0, "ver": 0})
        sA, sB = c1.start_session(), c2.start_session()
        m = T.mark()
        sB.start_transaction(read_concern=ReadConcern("majority"))
        b1 = coll2.find_one({"_id": 1}, session=sB)
        sA.start_transaction()
        coll1.update_one({"_id": 1}, {"$inc": {"v": 1}}, session=sA)
        try:
            sA.commit_transaction()
            a_c = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            a_c = T.err(e)
        b2 = coll2.find_one({"_id": 1}, session=sB)
        try:
            sB.commit_transaction()
            b_c = {"ok": 1}
        except Exception as e:  # noqa: BLE001
            b_c = T.err(e)
        sA.end_session()
        sB.end_session()
        first_find = next((e["command"] for e in T.wire_since(m) if e["event"] == "started"
                           and e["command_name"] == "find" and e["client"] == "c2"), {})
        resp = {"B_first_read": b1, "A_commit": a_c, "B_second_read_after_A_commit": b2, "B_commit": b_c,
                "B_first_find_readConcern_on_wire": first_find.get("readConcern")}
        put("P6 1k read ordering with readConcern majority on B's transaction (B reads, A $inc and commits, B reads again)",
            "sB.start_transaction(read_concern=ReadConcern('majority')); c2...find_one({'_id': 1}, session=sB); "
            "sA.start_transaction(); c1...update_one({'_id': 1}, {'$inc': {'v': 1}}, session=sA); "
            "sA.commit_transaction(); c2...find_one({'_id': 1}, session=sB); sB.commit_transaction()", resp,
            f"With readConcern {resp['B_first_find_readConcern_on_wire']} sent on B's first find, B read v="
            f"{(b1 or {}).get('v')} and then v={(b2 or {}).get('v')} after A's commit inside the same transaction, so "
            + ("the accepted 'majority' level does not give the transaction a stable snapshot."
               if (b2 or {}).get("v") != (b1 or {}).get("v") else "B kept its first snapshot."), m)
    finally:
        try:
            m = T.mark()
            c1.drop_database(DB)
            RES["drop"] = {"command": f"c1.drop_database('{DB}'); '{DB}' in c1.list_database_names()",
                           "still_listed": DB in c1.list_database_names()}
        except Exception as e:  # noqa: BLE001
            RES["drop"] = {"error": T.err(e)}
        c1.close()
        c2.close()


if __name__ == "__main__":
    RES["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        main()
    except BaseException as e:  # noqa: BLE001
        RES["fatal"] = {"exception": type(e).__name__, "message": T.redact(str(e))}
        T.log(f"FATAL {RES['fatal']}")
    RES["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    text = T.redact(json.dumps(RES, indent=2, default=str))
    for sec in T.SECRETS:
        assert sec not in text
    with open(os.path.join(HERE, "extra_probes.json"), "w") as f:
        f.write(text + "\n")
    T.log("written: " + os.path.join(HERE, "extra_probes.json"))
