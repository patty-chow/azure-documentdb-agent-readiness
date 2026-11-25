#!/usr/bin/env python
"""bulkwrite-forms: collection-level bulk_write, client-level bulk_write (8.0 bulkWrite
command), and a 25,001-document insert_many against documentdb-local.

Reads LOCAL_URI from ../local.env. Never prints the password. Writes report.json next
to this file. Owns database t_bulk only.
"""
import json
import os
import re
import sys
import time
import traceback

import pymongo
from pymongo import (
    DeleteOne,
    InsertOne,
    MongoClient,
    UpdateOne,
)
from pymongo.errors import BulkWriteError, OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "local.env")
DB = "t_bulk"


def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                if v and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found")


URI = load_uri()
REDACT_RE = re.compile(r"(mongodb://[^:/]+:)[^@]+@")


def redact(s):
    return REDACT_RE.sub(r"\1***@", str(s))


def jsonable(o):
    """Make BSON/driver objects JSON-serialisable."""
    try:
        json.dumps(o)
        return o
    except TypeError:
        pass
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    return redact(repr(o))


def err_info(e):
    d = {"exception": type(e).__name__, "message": redact(str(e))}
    if isinstance(e, OperationFailure):
        d["code"] = e.code
        details = e.details or {}
        d["codeName"] = details.get("codeName")
        d["errmsg"] = details.get("errmsg")
        d["errorLabels"] = sorted(e._error_labels) if getattr(e, "_error_labels", None) else details.get("errorLabels", [])
        d["details"] = jsonable(details)
    elif isinstance(e, PyMongoError):
        d["errorLabels"] = sorted(getattr(e, "_error_labels", set()) or [])
    return d


steps = []


def record(step, command, response, reading):
    steps.append(
        {
            "step": step,
            "command": command,
            "response": jsonable(response),
            "reading": reading,
        }
    )
    print(f"[{step}] {reading}", file=sys.stderr)


def run(step, command, fn, reading_ok, reading_err=None):
    t0 = time.time()
    try:
        res = fn()
        resp = jsonable(res)
        if isinstance(resp, dict):
            resp["_elapsed_s"] = round(time.time() - t0, 3)
        record(step, command, resp, reading_ok(res) if callable(reading_ok) else reading_ok)
        return res, None
    except Exception as e:  # noqa: BLE001
        info = err_info(e)
        info["_elapsed_s"] = round(time.time() - t0, 3)
        reading = reading_err(e) if callable(reading_err) else (reading_err or f"Failed with {info['exception']}.")
        record(step, command, info, reading)
        return None, e


def bwr(res):
    """Summarise a BulkWriteResult."""
    return {
        "acknowledged": res.acknowledged,
        "inserted_count": res.inserted_count,
        "matched_count": res.matched_count,
        "modified_count": res.modified_count,
        "deleted_count": res.deleted_count,
        "upserted_count": res.upserted_count,
        "upserted_ids": jsonable(res.upserted_ids),
        "bulk_api_result": jsonable(res.bulk_api_result),
    }


def cbwr(res):
    """Summarise a ClientBulkWriteResult."""
    return {
        "acknowledged": res.acknowledged,
        "has_verbose_results": res.has_verbose_results,
        "inserted_count": res.inserted_count,
        "matched_count": res.matched_count,
        "modified_count": res.modified_count,
        "deleted_count": res.deleted_count,
        "upserted_count": res.upserted_count,
    }


def main():
    client = MongoClient(URI, serverSelectionTimeoutMS=15000, socketTimeoutMS=240000)
    db = client[DB]

    # 0. buildInfo + hello
    bi, _ = run(
        "0a-buildInfo",
        "client.admin.command('buildInfo')",
        lambda: client.admin.command("buildInfo"),
        lambda r: f"Local engine reports version {r.get('version')}; this is the build all observations below apply to.",
    )
    hello, _ = run(
        "0b-hello",
        "client.admin.command('hello')",
        lambda: client.admin.command("hello"),
        lambda r: f"hello advertises maxWriteBatchSize={r.get('maxWriteBatchSize')}, maxWireVersion={r.get('maxWireVersion')}, maxBsonObjectSize={r.get('maxBsonObjectSize')}, maxMessageSizeBytes={r.get('maxMessageSizeBytes')}.",
    )
    record(
        "0c-pymongo",
        "pymongo.__version__; hasattr(MongoClient, 'bulk_write')",
        {"pymongo": pymongo.__version__, "client_bulk_write_available": hasattr(MongoClient, "bulk_write")},
        f"PyMongo {pymongo.__version__} is in the repo venv; MongoClient.bulk_write (4.9+ API) is available.",
    )

    # clean collections (own db only)
    for c in ("coll_ordered", "coll_unordered", "client_bw_a", "client_bw_b", "big"):
        run(f"0d-drop-{c}", f"db.{c}.drop()", lambda c=c: db[c].drop(), "Dropped (or absent) before test; t_bulk is the only database touched.")

    # 1. collection-level ordered bulk_write, clean
    ops_clean = [
        InsertOne({"_id": 1, "v": "a"}),
        InsertOne({"_id": 2, "v": "b"}),
        UpdateOne({"_id": 1}, {"$set": {"v": "a2"}}),
        UpdateOne({"_id": 99}, {"$set": {"v": "ups"}}, upsert=True),
        DeleteOne({"_id": 2}),
    ]
    res, err = run(
        "1a-coll-bulk-ordered-clean",
        "db.coll_ordered.bulk_write([InsertOne{_id:1}, InsertOne{_id:2}, UpdateOne{_id:1 $set}, UpdateOne{_id:99 upsert}, DeleteOne{_id:2}], ordered=True)",
        lambda: bwr(db.coll_ordered.bulk_write(ops_clean, ordered=True)),
        lambda r: f"Ordered collection-level bulk_write succeeded: inserted={r['inserted_count']} matched={r['matched_count']} modified={r['modified_count']} upserted={r['upserted_count']} deleted={r['deleted_count']}.",
    )
    run(
        "1b-coll-ordered-state",
        "list(db.coll_ordered.find().sort('_id'))",
        lambda: list(db.coll_ordered.find().sort("_id")),
        lambda r: f"Collection holds {len(r)} docs after the mixed batch: {r}.",
    )

    # 2. collection-level ordered bulk_write with duplicate _id mid-batch
    ops_dup = [
        InsertOne({"_id": 10, "v": "x"}),
        InsertOne({"_id": 11, "v": "y"}),
        InsertOne({"_id": 10, "v": "dup"}),  # duplicate -> should stop here when ordered
        InsertOne({"_id": 12, "v": "z"}),
        UpdateOne({"_id": 11}, {"$set": {"v": "y2"}}),
        DeleteOne({"_id": 10}),
    ]

    def ordered_dup():
        try:
            return {"unexpected_success": bwr(db.coll_ordered.bulk_write(ops_dup, ordered=True))}
        except BulkWriteError as e:
            raise e

    def read_dup_err(e):
        if isinstance(e, BulkWriteError):
            d = e.details
            we = d.get("writeErrors", [])
            return (
                f"BulkWriteError: nInserted={d.get('nInserted')} nMatched={d.get('nMatched')} nModified={d.get('nModified')} nRemoved={d.get('nRemoved')}; "
                f"{len(we)} writeError(s) at index {[w.get('index') for w in we]} code {[w.get('code') for w in we]}; "
                f"ordered run stopped at the duplicate so later ops were not applied."
            )
        return f"Unexpected {type(e).__name__}."

    run(
        "2a-coll-bulk-ordered-dup",
        "db.coll_ordered.bulk_write([InsertOne{_id:10}, InsertOne{_id:11}, InsertOne{_id:10 DUP}, InsertOne{_id:12}, UpdateOne{_id:11}, DeleteOne{_id:10}], ordered=True)",
        ordered_dup,
        lambda r: "Unexpectedly succeeded despite duplicate _id.",
        read_dup_err,
    )
    run(
        "2b-coll-ordered-dup-state",
        "list(db.coll_ordered.find({'_id': {'$gte': 10}}).sort('_id'))",
        lambda: list(db.coll_ordered.find({"_id": {"$gte": 10}}).sort("_id")),
        lambda r: f"Docs with _id>=10 after ordered failure: {r} (expect 10 and 11 only, untouched by later ops).",
    )

    # 3. collection-level unordered bulk_write with duplicate _id mid-batch
    def unordered_dup():
        return {"unexpected_success": bwr(db.coll_unordered.bulk_write(ops_dup, ordered=False))}

    def read_unordered_err(e):
        if isinstance(e, BulkWriteError):
            d = e.details
            we = d.get("writeErrors", [])
            return (
                f"BulkWriteError: nInserted={d.get('nInserted')} nMatched={d.get('nMatched')} nModified={d.get('nModified')} nRemoved={d.get('nRemoved')}; "
                f"{len(we)} writeError(s) at index {[w.get('index') for w in we]} code {[w.get('code') for w in we]}; "
                f"unordered run continued past the duplicate."
            )
        return f"Unexpected {type(e).__name__}."

    run(
        "3a-coll-bulk-unordered-dup",
        "db.coll_unordered.bulk_write([same 6 ops as 2a], ordered=False)",
        unordered_dup,
        lambda r: "Unexpectedly succeeded despite duplicate _id.",
        read_unordered_err,
    )
    run(
        "3b-coll-unordered-dup-state",
        "list(db.coll_unordered.find().sort('_id'))",
        lambda: list(db.coll_unordered.find().sort("_id")),
        lambda r: f"Docs after unordered failure: {r} (expect 11 with v=y2 and 12; 10 inserted then deleted).",
    )

    # 4. raw insert command with duplicate, ordered=false, to see the server-level reply shape
    def raw_insert():
        return db.command(
            {
                "insert": "coll_unordered",
                "documents": [{"_id": 11, "v": "dup-of-11"}, {"_id": 20, "v": "new"}],
                "ordered": False,
            }
        )

    run(
        "4-raw-insert-dup-unordered",
        "db.command({'insert':'coll_unordered','documents':[{_id:11 DUP},{_id:20}],'ordered':False})",
        raw_insert,
        lambda r: f"Raw insert reply: ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')} (server-level shape of a partial failure).",
        lambda e: f"Raw insert command raised {type(e).__name__} instead of returning writeErrors in the reply body.",
    )

    # 5. client-level bulk_write (MongoDB 8.0 bulkWrite command)
    client_ops = [
        InsertOne(namespace=f"{DB}.client_bw_a", document={"_id": 1, "v": "a"}),
        InsertOne(namespace=f"{DB}.client_bw_b", document={"_id": 1, "v": "b"}),
        UpdateOne(namespace=f"{DB}.client_bw_a", filter={"_id": 1}, update={"$set": {"v": "a2"}}),
        DeleteOne(namespace=f"{DB}.client_bw_b", filter={"_id": 1}),
    ]

    def client_bw(ordered, verbose):
        return cbwr(client.bulk_write(client_ops, ordered=ordered, verbose_results=verbose))

    def read_client_err(e):
        info = err_info(e)
        return (
            f"MongoClient.bulk_write failed: {info['exception']} code={info.get('code')} codeName={info.get('codeName')} "
            f"errmsg={info.get('errmsg')!r} errorLabels={info.get('errorLabels')}."
        )

    run(
        "5a-client-bulk-ordered",
        "client.bulk_write([InsertOne(ns=t_bulk.client_bw_a), InsertOne(ns=t_bulk.client_bw_b), UpdateOne(ns=a), DeleteOne(ns=b)], ordered=True)",
        lambda: client_bw(True, False),
        lambda r: f"Client-level bulk_write (8.0 bulkWrite command) succeeded: {r}.",
        read_client_err,
    )
    run(
        "5b-client-bulk-unordered-verbose",
        "client.bulk_write([same 4 ops], ordered=False, verbose_results=True)",
        lambda: client_bw(False, True),
        lambda r: f"Client-level unordered bulk_write succeeded: {r}.",
        read_client_err,
    )

    # 5c. raw bulkWrite command on admin to capture exact server reply independent of driver checks
    def raw_bulkwrite():
        return client.admin.command(
            {
                "bulkWrite": 1,
                "ops": [{"insert": 0, "document": {"_id": 2, "v": "raw"}}],
                "nsInfo": [{"ns": f"{DB}.client_bw_a"}],
                "ordered": True,
            }
        )

    run(
        "5c-raw-bulkWrite-command",
        "client.admin.command({'bulkWrite':1,'ops':[{'insert':0,'document':{_id:2}}],'nsInfo':[{'ns':'t_bulk.client_bw_a'}],'ordered':True})",
        raw_bulkwrite,
        lambda r: f"Raw 8.0 bulkWrite command on admin returned: {r}.",
        lambda e: f"Raw 8.0 bulkWrite command on admin failed: code={err_info(e).get('code')} codeName={err_info(e).get('codeName')} errmsg={err_info(e).get('errmsg')!r}.",
    )

    # 6. insert_many of 25,001 docs
    docs = [{"_id": i, "k": i % 7} for i in range(25001)]

    def big_insert():
        r = db.big.insert_many(docs, ordered=False)
        return {"inserted_ids_count": len(r.inserted_ids), "acknowledged": r.acknowledged}

    def read_big_err(e):
        info = err_info(e)
        if isinstance(e, BulkWriteError):
            d = e.details
            we = d.get("writeErrors", [])
            first = we[0] if we else {}
            return (
                f"insert_many(25001) raised BulkWriteError: nInserted={d.get('nInserted')} writeErrors={len(we)} "
                f"first code={first.get('code')} codeName={first.get('codeName')} errmsg={first.get('errmsg')!r}."
            )
        return f"insert_many(25001) raised {info['exception']} code={info.get('code')} codeName={info.get('codeName')} errmsg={info.get('errmsg')!r}."

    big_res, big_err = run(
        "6a-insert_many-25001",
        "db.big.insert_many([{_id:i,k:i%7} for i in range(25001)], ordered=False)  # driver splits at hello.maxWriteBatchSize",
        big_insert,
        lambda r: f"insert_many of 25,001 docs succeeded with {r['inserted_ids_count']} ids; the driver splits at hello.maxWriteBatchSize={hello.get('maxWriteBatchSize') if hello else '?'} so the engine saw batches of at most that size.",
        read_big_err,
    )
    run(
        "6b-big-count",
        "db.big.count_documents({})",
        lambda: db.big.count_documents({}),
        lambda r: f"big holds {r} documents after the 25,001-doc insert_many.",
    )

    # 6c. raw insert command with 25,001 docs in ONE command (bypasses driver split) to see the engine cap
    run("6c-drop-big2", "db.big2.drop()", lambda: db.big2.drop(), "Dropped before raw single-command insert.")

    def raw_big():
        return db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25001)], "ordered": False})

    run(
        "6d-raw-insert-25001-one-command",
        "db.command({'insert':'big2','documents':[25001 docs],'ordered':False})  # single wire message, no driver split",
        raw_big,
        lambda r: f"A single insert command carrying 25,001 documents was accepted: ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')}.",
        lambda e: f"A single insert command carrying 25,001 documents failed: code={err_info(e).get('code')} codeName={err_info(e).get('codeName')} errmsg={err_info(e).get('errmsg')!r}.",
    )
    run(
        "6e-big2-count",
        "db.big2.count_documents({})",
        lambda: db.big2.count_documents({}),
        lambda r: f"big2 holds {r} documents after the single 25,001-doc insert command.",
    )

    def raw_big_25000():
        db.big2.drop()
        return db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25000)], "ordered": False})

    run(
        "6f-raw-insert-25000-one-command",
        "db.big2.drop(); db.command({'insert':'big2','documents':[25000 docs],'ordered':False})",
        raw_big_25000,
        lambda r: f"A single insert command carrying exactly 25,000 documents: ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')}.",
        lambda e: f"A single insert command carrying exactly 25,000 documents failed: code={err_info(e).get('code')} codeName={err_info(e).get('codeName')} errmsg={err_info(e).get('errmsg')!r}.",
    )

    # cleanup
    run("7-dropDatabase", "client.drop_database('t_bulk')", lambda: client.drop_database(DB), "Dropped t_bulk at the end; container untouched.")

    report = {
        "test": "bulkwrite-forms",
        "database": DB,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "target": "documentdb-local container ddb-engine-test, localhost:10260, TLS self-signed",
        "pymongo_version": pymongo.__version__,
        "engine_version": (bi or {}).get("version"),
        "buildInfo": jsonable(bi),
        "hello": jsonable(hello),
        "evidence_scope": "Facts observed on documentdb-local are evidence about the open-source engine and gateway at the version buildInfo reports; they do not prove managed Azure DocumentDB behaviour.",
        "steps": steps,
    }
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=lambda o: redact(repr(o)))
    print(json.dumps({"engine_version": report["engine_version"], "n_steps": len(steps)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
