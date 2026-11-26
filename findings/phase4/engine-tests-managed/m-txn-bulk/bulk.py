"""m-txn-bulk part 2 (f-i): hello limits, collection-level bulk_write, client-level bulk_write (8.0
bulkWrite command), 25,001-document batches, then drop the database.

Target: MANAGED_URI from ../managed.env (plain host). Owns database mt_txn only. Never prints the
password. Writes bulk_steps.json next to this file. Mirrors
findings/phase4/engine-tests/bulkwrite-forms/run.py (open-source engine), with wire-level command
monitoring added so the driver's batch splitting and the bulkWrite command are visible.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python bulk.py
"""
import os
import sys
import time
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB, ENV, HERE, CmdLog, Recorder, err_dict, jsonable, raw_command, redact, reply_summary, write_json  # noqa: E402

import pymongo  # noqa: E402
from pymongo import DeleteOne, InsertOne, MongoClient, UpdateOne  # noqa: E402

R = Recorder()
L = CmdLog("bulk")


def bwr(res):
    return {"acknowledged": res.acknowledged, "inserted_count": res.inserted_count, "matched_count": res.matched_count,
            "modified_count": res.modified_count, "deleted_count": res.deleted_count, "upserted_count": res.upserted_count,
            "upserted_ids": jsonable(res.upserted_ids), "bulk_api_result": jsonable(res.bulk_api_result)}


def cbwr(res):
    out = {"acknowledged": res.acknowledged, "has_verbose_results": res.has_verbose_results, "inserted_count": res.inserted_count,
           "matched_count": res.matched_count, "modified_count": res.modified_count, "deleted_count": res.deleted_count,
           "upserted_count": res.upserted_count}
    if res.has_verbose_results:
        out["insert_results"] = jsonable({k: v.inserted_id for k, v in res.insert_results.items()})
        out["update_results"] = jsonable({k: {"matched": v.matched_count, "modified": v.modified_count, "upserted_id": v.upserted_id} for k, v in res.update_results.items()})
        out["delete_results"] = jsonable({k: v.deleted_count for k, v in res.delete_results.items()})
    return out


def run(step, command, fn, reading=""):
    m = L.mark()
    t0 = time.time()
    try:
        res = fn()
        resp = {"result": jsonable(res)}
        ok = True
    except Exception as e:  # noqa: BLE001
        resp = {"error": err_dict(e)}
        ok = False
    resp["elapsed_s"] = round(time.time() - t0, 3)
    resp["wire_commands"] = L.since(m)
    R.record(step, command, resp, reading)
    return ok, resp


def main():
    client = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, socketTimeoutMS=300000, event_listeners=[L])
    db = client[DB]
    try:
        # ---------------- (f) hello / buildInfo
        hello = client.admin.command("hello")
        R.record("f1 hello", "client.admin.command('hello')", hello,
                 "Limits the gateway advertises to drivers.")
        bi = client.admin.command("buildInfo")
        R.record("f2 buildInfo", "client.admin.command('buildInfo')", {k: bi.get(k) for k in ("version", "versionArray", "bits", "maxBsonObjectSize", "ok")})
        with client._conn_for_writes(None, "probe") as conn:
            mwv = conn.max_wire_version
        R.record("f3 driver view", "pymongo.__version__; conn.max_wire_version (pooled connection); hasattr(MongoClient, 'bulk_write')",
                 {"pymongo": pymongo.__version__, "connection_max_wire_version": mwv, "client_bulk_write_api_present": hasattr(MongoClient, "bulk_write"),
                  "pymongo_client_bulk_gate": "client_bulk.py refuses only if conn.max_wire_version < 25"})

        for c in ("coll_ordered", "coll_unordered", "client_bw_a", "client_bw_b", "big", "big2"):
            db.drop_collection(c)
        R.record("g0 setup", "db.drop_collection(c) for coll_ordered, coll_unordered, client_bw_a, client_bw_b, big, big2", {"dropped": True})

        # ---------------- (g) collection-level bulk_write
        ops_clean = [InsertOne({"_id": 1, "v": "a"}), InsertOne({"_id": 2, "v": "b"}), UpdateOne({"_id": 1}, {"$set": {"v": "a2"}}),
                     UpdateOne({"_id": 99}, {"$set": {"v": "ups"}}, upsert=True), DeleteOne({"_id": 2})]
        run("g1 collection bulk_write ordered, no error",
            "db.coll_ordered.bulk_write([InsertOne({'_id':1,'v':'a'}), InsertOne({'_id':2,'v':'b'}), UpdateOne({'_id':1},{'$set':{'v':'a2'}}), "
            "UpdateOne({'_id':99},{'$set':{'v':'ups'}}, upsert=True), DeleteOne({'_id':2})], ordered=True)",
            lambda: bwr(db.coll_ordered.bulk_write(ops_clean, ordered=True)))
        run("g2 state after g1", "list(db.coll_ordered.find().sort('_id'))", lambda: list(db.coll_ordered.find().sort("_id")))

        ops_dup = [InsertOne({"_id": 10, "v": "x"}), InsertOne({"_id": 11, "v": "y"}), InsertOne({"_id": 10, "v": "dup"}),
                   InsertOne({"_id": 12, "v": "z"}), UpdateOne({"_id": 11}, {"$set": {"v": "y2"}}), DeleteOne({"_id": 10})]
        dup_cmd = ("[InsertOne({'_id':10,'v':'x'}), InsertOne({'_id':11,'v':'y'}), InsertOne({'_id':10,'v':'dup'}), InsertOne({'_id':12,'v':'z'}), "
                   "UpdateOne({'_id':11},{'$set':{'v':'y2'}}), DeleteOne({'_id':10})]")
        run("g3 collection bulk_write ordered with a duplicate _id at index 2", f"db.coll_ordered.bulk_write({dup_cmd}, ordered=True)",
            lambda: bwr(db.coll_ordered.bulk_write(ops_dup, ordered=True)))
        run("g4 state after g3", "list(db.coll_ordered.find({'_id': {'$gte': 10}}).sort('_id'))", lambda: list(db.coll_ordered.find({"_id": {"$gte": 10}}).sort("_id")))
        run("g5 collection bulk_write unordered with a duplicate _id at index 2", f"db.coll_unordered.bulk_write({dup_cmd}, ordered=False)",
            lambda: bwr(db.coll_unordered.bulk_write(ops_dup, ordered=False)))
        run("g6 state after g5", "list(db.coll_unordered.find().sort('_id'))", lambda: list(db.coll_unordered.find().sort("_id")))
        run("g7 raw insert command, unordered, one duplicate",
            "db.command({'insert': 'coll_unordered', 'documents': [{'_id': 11, 'v': 'dup-of-11'}, {'_id': 20, 'v': 'new'}], 'ordered': False})",
            lambda: db.command({"insert": "coll_unordered", "documents": [{"_id": 11, "v": "dup-of-11"}, {"_id": 20, "v": "new"}], "ordered": False}))

        # ---------------- (h) client-level bulk_write (MongoDB 8.0 bulkWrite command)
        client_ops = [InsertOne(namespace=f"{DB}.client_bw_a", document={"_id": 1, "v": "a"}),
                      InsertOne(namespace=f"{DB}.client_bw_b", document={"_id": 1, "v": "b"}),
                      UpdateOne(namespace=f"{DB}.client_bw_a", filter={"_id": 1}, update={"$set": {"v": "a2"}}),
                      DeleteOne(namespace=f"{DB}.client_bw_b", filter={"_id": 1})]
        cops = ("[InsertOne(namespace='mt_txn.client_bw_a', document={'_id':1,'v':'a'}), InsertOne(namespace='mt_txn.client_bw_b', document={'_id':1,'v':'b'}), "
                "UpdateOne(namespace='mt_txn.client_bw_a', filter={'_id':1}, update={'$set':{'v':'a2'}}), DeleteOne(namespace='mt_txn.client_bw_b', filter={'_id':1})]")
        ok_h1, _ = run("h1 MongoClient.bulk_write ordered", f"client.bulk_write({cops}, ordered=True)",
                       lambda: cbwr(client.bulk_write(client_ops, ordered=True)))
        run("h2 MongoClient.bulk_write unordered, verbose_results", f"client.bulk_write({cops}, ordered=False, verbose_results=True)",
            lambda: cbwr(client.bulk_write(client_ops, ordered=False, verbose_results=True)))
        run("h3 raw bulkWrite command on admin",
            "client.admin.command({'bulkWrite': 1, 'ops': [{'insert': 0, 'document': {'_id': 2, 'v': 'raw'}}], 'nsInfo': [{'ns': 'mt_txn.client_bw_a'}], 'ordered': True})",
            lambda: reply_summary(raw_command(client, "admin", {"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 2, "v": "raw"}}],
                                                                  "nsInfo": [{"ns": f"{DB}.client_bw_a"}], "ordered": True})))
        run("h4 state of the client_bw namespaces", "list(db.client_bw_a.find()), list(db.client_bw_b.find()), db.list_collection_names()",
            lambda: {"client_bw_a": list(db.client_bw_a.find().sort("_id")), "client_bw_b": list(db.client_bw_b.find().sort("_id")),
                     "collections": sorted(db.list_collection_names())})
        if ok_h1:
            dup_ops = [InsertOne(namespace=f"{DB}.client_bw_a", document={"_id": 50}), InsertOne(namespace=f"{DB}.client_bw_a", document={"_id": 50}),
                       InsertOne(namespace=f"{DB}.client_bw_b", document={"_id": 51})]
            run("h5 MongoClient.bulk_write ordered with a duplicate _id", "client.bulk_write([Insert a{_id:50}, Insert a{_id:50} DUP, Insert b{_id:51}], ordered=True)",
                lambda: cbwr(client.bulk_write(dup_ops, ordered=True)))

        # ---------------- (i) 25,001 documents
        docs = [{"_id": i, "k": i % 7} for i in range(25001)]
        run("i1 insert_many of 25,001 small documents",
            "db.big.insert_many([{'_id': i, 'k': i % 7} for i in range(25001)], ordered=False)  # driver splits by hello.maxWriteBatchSize",
            lambda: {"inserted_ids_count": len(db.big.insert_many(docs, ordered=False).inserted_ids)})
        run("i2 count after i1", "db.big.count_documents({})", lambda: db.big.count_documents({}))
        run("i3 raw insert command with 25,001 documents (one command, no driver split)",
            "db.command({'insert': 'big2', 'documents': [{'_id': i} for i in range(25001)], 'ordered': False})",
            lambda: db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25001)], "ordered": False}))
        run("i4 count after i3", "db.big2.count_documents({})", lambda: db.big2.count_documents({}))
        run("i5 raw insert command with exactly 25,000 documents",
            "db.drop_collection('big2'); db.command({'insert': 'big2', 'documents': [{'_id': i} for i in range(25000)], 'ordered': False})",
            lambda: (db.drop_collection("big2"), db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25000)], "ordered": False}))[1])
        run("i6 count after i5", "db.big2.count_documents({})", lambda: db.big2.count_documents({}))

        # ---------------- end: drop the test database
        run("j1 drop the test database", "client.drop_database('mt_txn')", lambda: client.drop_database(DB))
        run("j2 verify the database is gone", "'mt_txn' in client.list_database_names()", lambda: DB in client.list_database_names())
    finally:
        client.close()


if __name__ == "__main__":
    started = datetime.now(timezone.utc).isoformat()
    try:
        main()
    except Exception as e:  # noqa: BLE001
        R.record("FATAL", "bulk.py", {"exception": type(e).__name__, "message": redact(str(e)), "traceback": redact(traceback.format_exc())},
                 "Script error, not a server observation.")
    write_json(os.path.join(HERE, "bulk_steps.json"), {
        "part": "bulk writes (f-i) and cleanup", "database": DB, "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "driver": f"pymongo {pymongo.__version__}", "uri_used": "MANAGED_URI (plain host)", "steps": R.steps})
    print("\nwritten:", os.path.join(HERE, "bulk_steps.json"))
