#!/usr/bin/env python
"""bulkwrite-forms, ENGINE 1.2.0 RERUN (compare with the 0.117 report).

Steps, against the documentdb-local container ddb-engine-test on localhost:10260 (TLS, self-signed):
  0  buildInfo, hello (maxWriteBatchSize, maxWireVersion), PyMongo version, driver-side server description
  1-3 collection-level bulk_write: ordered clean batch, ordered and unordered with a duplicate _id
  4  raw insert commands with a duplicate _id (unordered and ordered) to see the server reply shape
  5  client-level MongoClient.bulk_write (ordered, unordered+verbose) and the raw MongoDB 8.0
     bulkWrite command on admin (0.117 form and a multi-namespace form) and on a non-admin database
  6  insert_many of 25,001 documents (wire commands observed with a CommandListener), a raw insert
     command with 25,001 / 25,000 / 0 documents, raw update and delete commands with 25,001
     statements, and a collection-level bulk_write of 25,001 InsertOne ops
  7  drop the test database and verify it is gone

Step ids 0a..7 match the 0.117 script where the step is the same; new steps have new ids.
Owns database t_bulk only. Reads LOCAL_URI from the shared local.env; never prints or stores the
password (every string written is passed through redact()). Writes report.json next to this file.
Rerun: <venv>/bin/python run.py && <venv>/bin/python compare.py && <venv>/bin/python finalize.py
"""
import datetime
import json
import os
import re
import sys
import time
import traceback
from collections.abc import Mapping
from urllib.parse import unquote, urlsplit

import bson
import pymongo
from pymongo import DeleteOne, InsertOne, MongoClient, UpdateOne, monitoring
from pymongo.errors import BulkWriteError, OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"
DB = "t_bulk"
SOCKET_TIMEOUT_MS = 240_000  # every single command must finish in under 5 minutes


# --------------------------------------------------------------------------- secrets / JSON helpers
def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                if v and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found in local.env")


URI = load_uri()
_pw = urlsplit(URI).password or ""
SECRETS = sorted({s for s in (_pw, unquote(_pw)) if s}, key=len, reverse=True)
URI_RE = re.compile(r"(mongodb(?:\+srv)?://[^:/@]+:)[^@]+@")


def redact(s):
    s = URI_RE.sub(r"\1***@", str(s))
    for sec in SECRETS:
        s = s.replace(sec, "***")
    return s


def jsonable(o):
    """Convert BSON/driver values to JSON-safe values, redacting every string."""
    if o is None or isinstance(o, (bool, float)):
        return o
    if isinstance(o, int):
        return int(o)
    if isinstance(o, str):
        return redact(o)
    if isinstance(o, Mapping):
        return {redact(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in o]
    if isinstance(o, datetime.datetime):
        return {"$date": o.isoformat()}
    if isinstance(o, bson.timestamp.Timestamp):
        return {"$timestamp": {"t": o.time, "i": o.inc}}
    if isinstance(o, bson.objectid.ObjectId):
        return {"$oid": str(o)}
    if isinstance(o, (bytes, bson.binary.Binary)):
        return {"$binary_len": len(o)}
    return redact(repr(o))


def err_info(e):
    """Exact error fields: exception class, code, codeName, errmsg, errorLabels, full details."""
    d = {"exception": type(e).__name__, "message": redact(str(e))}
    labels = sorted(getattr(e, "_error_labels", None) or [])
    if isinstance(e, BulkWriteError):
        det = e.details or {}
        d["code"] = e.code  # driver-assigned 65 for BulkWriteError
        d["details"] = jsonable(det)
        d["writeErrors"] = jsonable(det.get("writeErrors", []))
        d["errorLabels"] = labels or jsonable(det.get("errorLabels", []))
    elif isinstance(e, OperationFailure):
        det = e.details or {}
        d["code"] = e.code
        d["codeName"] = det.get("codeName")
        d["errmsg"] = redact(det.get("errmsg")) if det.get("errmsg") is not None else None
        d["errorLabels"] = labels or jsonable(det.get("errorLabels", []))
        d["details"] = jsonable(det)
    elif isinstance(e, PyMongoError):
        d["errorLabels"] = labels
    return d


# --------------------------------------------------------------------------- wire capture
WRITE_FIELDS = {"insert": "documents", "update": "updates", "delete": "deletes", "bulkWrite": "ops"}


class WireLog(monitoring.CommandListener):
    """Records every command the driver sends (name, db, op count) and a summary of the reply."""

    def __init__(self):
        self.events = []
        self._open = {}

    def clear(self):
        self.events = []
        self._open = {}

    def started(self, e):
        rec = {"command": e.command_name, "db": e.database_name}
        field = WRITE_FIELDS.get(e.command_name)
        if field:
            ops = e.command.get(field) or []
            rec["n_ops"] = len(ops)
            rec["ordered"] = e.command.get("ordered")
            target = e.command.get(e.command_name)
            rec["target"] = jsonable(target) if not isinstance(target, (list, dict)) else "(see nsInfo)"
            if e.command_name == "bulkWrite":
                rec["nsInfo"] = jsonable(e.command.get("nsInfo"))
            elif e.command_name in ("update", "delete") and len(ops) <= 10:
                rec["ops"] = jsonable(ops)
            if e.command_name == "insert" and len(ops) <= 10:
                rec["ops"] = jsonable(ops)
        self.events.append(rec)
        self._open[(e.request_id, e.connection_id)] = rec

    def succeeded(self, e):
        rec = self._open.pop((e.request_id, e.connection_id), None)
        if rec is None:
            return
        r = e.reply or {}
        summ = {"ok": r.get("ok")}
        for k in ("n", "nModified"):
            if k in r:
                summ[k] = jsonable(r[k])
        if "upserted" in r:
            summ["upserted"] = jsonable(r["upserted"][:10])
        we = r.get("writeErrors")
        if we:
            summ["writeErrors_count"] = len(we)
            summ["writeErrors_first"] = jsonable(we[:3])
        for k in ("writeConcernError", "errorLabels", "code", "codeName", "errmsg"):
            if k in r:
                summ[k] = jsonable(r[k])
        rec["reply"] = summ
        rec["duration_ms"] = round(e.duration_micros / 1000, 1)

    def failed(self, e):
        rec = self._open.pop((e.request_id, e.connection_id), None)
        if rec is None:
            return
        rec["failure"] = jsonable(e.failure)
        rec["duration_ms"] = round(e.duration_micros / 1000, 1)


# --------------------------------------------------------------------------- step recording
steps = []


def record(step, command, response, reading, **extra):
    entry = {"step": step, "command": redact(command), "response": jsonable(response), "reading": redact(reading)}
    entry.update({k: jsonable(v) for k, v in extra.items()})
    steps.append(entry)
    print(f"[{step}] {entry['reading']}", file=sys.stderr, flush=True)
    return entry


def run(step, command, fn, reading_ok, reading_err=None, wire=None):
    """Run fn(); record its result or its exact error. Returns (result, exception)."""
    if wire is not None:
        wire.clear()
    t0 = time.time()
    res, exc = None, None
    try:
        res = fn()
        resp = jsonable(res)
        reading = reading_ok(res) if callable(reading_ok) else reading_ok
    except Exception as e:  # noqa: BLE001 - every error is evidence
        exc = e
        resp = err_info(e)
        if callable(reading_err):
            reading = reading_err(e)
        else:
            reading = reading_err or f"Failed with {type(e).__name__}: {redact(e)}."
    elapsed = round(time.time() - t0, 3)
    extra = {"elapsed_s": elapsed}
    if wire is not None:
        extra["wire_commands"] = list(wire.events)
    record(step, command, resp, reading, **extra)
    return res, exc


def bwr(res):
    """Summarise a collection-level BulkWriteResult."""
    return {
        "acknowledged": res.acknowledged,
        "inserted_count": res.inserted_count,
        "matched_count": res.matched_count,
        "modified_count": res.modified_count,
        "deleted_count": res.deleted_count,
        "upserted_count": res.upserted_count,
        "upserted_ids": res.upserted_ids,
        "bulk_api_result": res.bulk_api_result,
    }


def cbwr(res):
    """Summarise a client-level ClientBulkWriteResult."""
    out = {
        "acknowledged": res.acknowledged,
        "has_verbose_results": res.has_verbose_results,
        "inserted_count": res.inserted_count,
        "matched_count": res.matched_count,
        "modified_count": res.modified_count,
        "deleted_count": res.deleted_count,
        "upserted_count": res.upserted_count,
    }
    if res.has_verbose_results:
        out["insert_results"] = {k: v.inserted_id for k, v in res.insert_results.items()}
        out["update_results"] = {k: {"matched": v.matched_count, "modified": v.modified_count} for k, v in res.update_results.items()}
        out["delete_results"] = {k: v.deleted_count for k, v in res.delete_results.items()}
    return out


def wire_summary(wire_events, names=("insert", "update", "delete", "bulkWrite")):
    return [(w["command"], w.get("n_ops")) for w in wire_events if w["command"] in names]


def bwe_reading(e, tail):
    if isinstance(e, BulkWriteError):
        d = e.details
        we = d.get("writeErrors", [])
        return (
            f"BulkWriteError (driver code {e.code}): nInserted={d.get('nInserted')} nMatched={d.get('nMatched')} "
            f"nModified={d.get('nModified')} nRemoved={d.get('nRemoved')} nUpserted={d.get('nUpserted')}; "
            f"{len(we)} writeError(s) at index {[w.get('index') for w in we]} with code {[w.get('code') for w in we]} "
            f"and codeName {[w.get('codeName') for w in we]}, errorLabels {sorted(e._error_labels or [])}; {tail}"
        )
    return f"Unexpected {type(e).__name__}: {redact(e)}."


def of_reading(prefix):
    def _r(e):
        i = err_info(e)
        return (
            f"{prefix} failed: {i['exception']} code={i.get('code')} codeName={i.get('codeName')} "
            f"errmsg={i.get('errmsg')!r} errorLabels={i.get('errorLabels')}."
        )

    return _r


# --------------------------------------------------------------------------- the test
def main():
    wire = WireLog()
    client = MongoClient(
        URI,
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=15000,
        socketTimeoutMS=SOCKET_TIMEOUT_MS,
        event_listeners=[wire],
        appname="engine-tests-1.2-bulkwrite-forms",
    )
    db = client[DB]

    # ---- 0. versions and limits -------------------------------------------------------------
    bi, _ = run(
        "0a-buildInfo",
        "client.admin.command('buildInfo')",
        lambda: client.admin.command("buildInfo"),
        lambda r: f"buildInfo reports version {r.get('version')} (versionArray {r.get('versionArray')}); every observation below applies to this documentdb-local build only.",
    )
    hello, _ = run(
        "0b-hello",
        "client.admin.command('hello')",
        lambda: client.admin.command("hello"),
        lambda r: (
            f"hello advertises maxWriteBatchSize={r.get('maxWriteBatchSize')}, maxWireVersion={r.get('maxWireVersion')}, "
            f"maxBsonObjectSize={r.get('maxBsonObjectSize')}, maxMessageSizeBytes={r.get('maxMessageSizeBytes')}, "
            f"internal.documentdb_versions={(r.get('internal') or {}).get('documentdb_versions')}."
        ),
    )
    hello = hello or {}

    def driver_view():
        sds = client.topology_description.server_descriptions()
        return {
            str(addr): {
                "server_type": sd.server_type_name,
                "max_wire_version": sd.max_wire_version,
                "max_write_batch_size": sd.max_write_batch_size,
                "max_message_size": sd.max_message_size,
                "max_bson_size": sd.max_bson_size,
            }
            for addr, sd in sds.items()
        }

    def client_bulk_gate():
        """Lines of the installed PyMongo that gate MongoClient.bulk_write on the wire version."""
        path = os.path.join(os.path.dirname(pymongo.__file__), "synchronous", "client_bulk.py")
        try:
            with open(path) as f:
                return {"file": path, "lines": [f"{i}: {ln.strip()}" for i, ln in enumerate(f, 1) if "max_wire_version < " in ln]}
        except OSError as e:
            return {"file": path, "error": str(e)}

    record(
        "0c-pymongo",
        "pymongo.__version__; hasattr(MongoClient, 'bulk_write'); pymongo.common.MAX_WRITE_BATCH_SIZE; client.topology_description.server_descriptions(); grep 'max_wire_version < ' pymongo/synchronous/client_bulk.py",
        {
            "pymongo": pymongo.__version__,
            "client_bulk_write_available": hasattr(MongoClient, "bulk_write"),
            "driver_default_MAX_WRITE_BATCH_SIZE_if_hello_omits_it": pymongo.common.MAX_WRITE_BATCH_SIZE,
            "driver_server_descriptions": driver_view(),
            "client_bulk_write_gate": client_bulk_gate(),
        },
        (
            f"PyMongo {pymongo.__version__} (MongoClient.bulk_write present: {hasattr(MongoClient, 'bulk_write')}) "
            f"stores the server's max_write_batch_size={list(driver_view().values())[0]['max_write_batch_size'] if driver_view() else '?'} "
            f"and max_wire_version={list(driver_view().values())[0]['max_wire_version'] if driver_view() else '?'} from hello, "
            f"which is what it splits batches on (fallback {pymongo.common.MAX_WRITE_BATCH_SIZE} if hello omits the field) and what gates client.bulk_write "
            f"(installed source: {client_bulk_gate().get('lines')})."
        ),
    )
    run(
        "0d-pre-clean-dropDatabase",
        "client.drop_database('t_bulk')",
        lambda: client.drop_database(DB),
        "Dropped t_bulk (the only database this test owns) before starting, so the run starts from an empty database.",
    )

    # ---- 1. collection-level ordered bulk_write, clean --------------------------------------
    ops_clean = [
        InsertOne({"_id": 1, "v": "a"}),
        InsertOne({"_id": 2, "v": "b"}),
        UpdateOne({"_id": 1}, {"$set": {"v": "a2"}}),
        UpdateOne({"_id": 99}, {"$set": {"v": "ups"}}, upsert=True),
        DeleteOne({"_id": 2}),
    ]
    run(
        "1a-coll-bulk-ordered-clean",
        "db.coll_ordered.bulk_write([InsertOne({'_id':1,'v':'a'}), InsertOne({'_id':2,'v':'b'}), UpdateOne({'_id':1},{'$set':{'v':'a2'}}), UpdateOne({'_id':99},{'$set':{'v':'ups'}},upsert=True), DeleteOne({'_id':2})], ordered=True)",
        lambda: bwr(db.coll_ordered.bulk_write(ops_clean, ordered=True)),
        lambda r: (
            f"Ordered collection-level bulk_write succeeded (inserted={r['inserted_count']} matched={r['matched_count']} "
            f"modified={r['modified_count']} upserted={r['upserted_count']} deleted={r['deleted_count']}) and went over the wire as "
            f"{wire_summary(wire.events)}, i.e. one insert/update/delete command per run of same-type ops."
        ),
        wire=wire,
    )
    run(
        "1b-coll-ordered-state",
        "list(db.coll_ordered.find().sort('_id'))",
        lambda: list(db.coll_ordered.find().sort("_id")),
        lambda r: f"coll_ordered holds {len(r)} documents after the mixed batch: {r}.",
    )

    # ---- 2. collection-level ordered bulk_write with a duplicate _id at index 2 ---------------
    ops_dup = [
        InsertOne({"_id": 10, "v": "x"}),
        InsertOne({"_id": 11, "v": "y"}),
        InsertOne({"_id": 10, "v": "dup"}),  # duplicate _id at index 2
        InsertOne({"_id": 12, "v": "z"}),
        UpdateOne({"_id": 11}, {"$set": {"v": "y2"}}),
        DeleteOne({"_id": 10}),
    ]
    def stopped_tail(e):
        d = e.details if isinstance(e, BulkWriteError) else {}
        stopped = d.get("nInserted") == 2 and d.get("nMatched") == 0 and d.get("nRemoved") == 0
        return (f"the ordered run {'stopped at the duplicate (nothing after index 2 applied)' if stopped else 'did NOT stop at the duplicate as MongoDB would'}; "
                f"wire commands sent: {wire_summary(wire.events)}.")

    run(
        "2a-coll-bulk-ordered-dup",
        "db.coll_ordered.bulk_write([InsertOne({'_id':10,'v':'x'}), InsertOne({'_id':11,'v':'y'}), InsertOne({'_id':10,'v':'dup'}), InsertOne({'_id':12,'v':'z'}), UpdateOne({'_id':11},{'$set':{'v':'y2'}}), DeleteOne({'_id':10})], ordered=True)",
        lambda: {"unexpected_success": bwr(db.coll_ordered.bulk_write(ops_dup, ordered=True))},
        "Unexpectedly succeeded despite the duplicate _id.",
        lambda e: bwe_reading(e, stopped_tail(e)),
        wire=wire,
    )
    expect_2b = [{"_id": 10, "v": "x"}, {"_id": 11, "v": "y"}, {"_id": 99, "v": "ups"}]
    run(
        "2b-coll-ordered-dup-state",
        "list(db.coll_ordered.find({'_id': {'$gte': 10}}).sort('_id'))",
        lambda: list(db.coll_ordered.find({"_id": {"$gte": 10}}).sort("_id")),
        lambda r: (
            f"Documents with _id >= 10 after the ordered failure: {r}, "
            + ("which is MongoDB's ordered result: 10 and 11 as first inserted, no 12, the later update and delete not applied (99 is from step 1a)."
               if r == expect_2b else f"which differs from MongoDB's ordered result {expect_2b}.")
        ),
    )

    # ---- 3. collection-level unordered bulk_write with the same duplicate -----------------------
    def continued_tail(e):
        d = e.details if isinstance(e, BulkWriteError) else {}
        cont = d.get("nInserted") == 3 and d.get("nMatched") == 1 and d.get("nRemoved") == 1
        return (f"the unordered run {'continued past the duplicate (every other op applied)' if cont else 'did NOT apply every other op as MongoDB would'}; "
                f"wire commands sent: {wire_summary(wire.events)}.")

    run(
        "3a-coll-bulk-unordered-dup",
        "db.coll_unordered.bulk_write([same 6 ops as 2a], ordered=False)",
        lambda: {"unexpected_success": bwr(db.coll_unordered.bulk_write(ops_dup, ordered=False))},
        "Unexpectedly succeeded despite the duplicate _id.",
        lambda e: bwe_reading(e, continued_tail(e)),
        wire=wire,
    )
    expect_3b = [{"_id": 11, "v": "y2"}, {"_id": 12, "v": "z"}]
    run(
        "3b-coll-unordered-dup-state",
        "list(db.coll_unordered.find().sort('_id'))",
        lambda: list(db.coll_unordered.find().sort("_id")),
        lambda r: (
            f"coll_unordered after the unordered failure: {r}, "
            + ("which is MongoDB's unordered result: 10 inserted then deleted, 11 updated to y2, 12 inserted."
               if r == expect_3b else f"which differs from MongoDB's unordered result {expect_3b}.")
        ),
    )

    # ---- 4. raw insert commands with a duplicate: server-level reply shape ----------------------
    def raw_unordered_reading(r):
        we = r.get("writeErrors") or []
        std = r.get("ok") == 1 and r.get("n") == 1 and [w.get("index") for w in we] == [0]
        return (
            f"Raw unordered insert with a duplicate returns ok={r.get('ok')} n={r.get('n')} and writeErrors={we} in the reply body with no exception"
            + (", the standard MongoDB partial-failure shape (write error keys: " + str(sorted(we[0].keys())) + ")." if std else ", which is not the MongoDB shape.")
        )

    run(
        "4-raw-insert-dup-unordered",
        "db.command({'insert':'coll_unordered','documents':[{'_id':11,'v':'dup-of-11'},{'_id':20,'v':'new'}],'ordered':False})",
        lambda: db.command({"insert": "coll_unordered", "documents": [{"_id": 11, "v": "dup-of-11"}, {"_id": 20, "v": "new"}], "ordered": False}),
        raw_unordered_reading,
        of_reading("Raw unordered insert with a duplicate"),
    )

    def raw_ordered_reading(r):
        we = r.get("writeErrors") or []
        stops = r.get("n") == 1 and [w.get("index") for w in we] == [1]
        return (
            f"Raw ordered insert with a duplicate at index 1 returns ok={r.get('ok')} n={r.get('n')} writeErrors={we}, "
            + ("so the server itself stops an ordered batch at the first error." if stops else "which is not MongoDB's stop-at-first-error result.")
        )

    run(
        "4b-raw-insert-dup-ordered",
        "db.command({'insert':'coll_raw_ordered','documents':[{'_id':1},{'_id':1},{'_id':2}],'ordered':True})",
        lambda: db.command({"insert": "coll_raw_ordered", "documents": [{"_id": 1}, {"_id": 1}, {"_id": 2}], "ordered": True}),
        raw_ordered_reading,
        of_reading("Raw ordered insert with a duplicate"),
    )
    run(
        "4c-raw-ordered-state",
        "list(db.coll_raw_ordered.find().sort('_id'))",
        lambda: list(db.coll_raw_ordered.find().sort("_id")),
        lambda r: f"coll_raw_ordered holds {r}: the document after the duplicate (_id 2) {'was not' if all(d['_id'] != 2 for d in r) else 'WAS'} inserted.",
    )

    # ---- 5. client-level bulk_write (MongoDB 8.0 bulkWrite command) ----------------------------
    client_ops = [
        InsertOne(namespace=f"{DB}.client_bw_a", document={"_id": 1, "v": "a"}),
        InsertOne(namespace=f"{DB}.client_bw_b", document={"_id": 1, "v": "b"}),
        UpdateOne(namespace=f"{DB}.client_bw_a", filter={"_id": 1}, update={"$set": {"v": "a2"}}),
        DeleteOne(namespace=f"{DB}.client_bw_b", filter={"_id": 1}),
    ]

    def client_reading(e):
        i = err_info(e)
        sent = [w["command"] for w in wire.events]
        return (
            f"MongoClient.bulk_write failed: {i['exception']} {i['message']!r} code={i.get('code')} codeName={i.get('codeName')} "
            f"errorLabels={i.get('errorLabels')}; commands the driver sent during the call: {sent}."
        )

    run(
        "5a-client-bulk-ordered",
        "client.bulk_write([InsertOne(namespace='t_bulk.client_bw_a', document={'_id':1,'v':'a'}), InsertOne(namespace='t_bulk.client_bw_b', document={'_id':1,'v':'b'}), UpdateOne(namespace='t_bulk.client_bw_a', filter={'_id':1}, update={'$set':{'v':'a2'}}), DeleteOne(namespace='t_bulk.client_bw_b', filter={'_id':1})], ordered=True)",
        lambda: cbwr(client.bulk_write(client_ops, ordered=True)),
        lambda r: f"Client-level bulk_write (MongoDB 8.0 bulkWrite command) succeeded: {r}; wire: {wire_summary(wire.events)}.",
        client_reading,
        wire=wire,
    )
    run(
        "5b-client-bulk-unordered-verbose",
        "client.bulk_write([same 4 ops as 5a], ordered=False, verbose_results=True)",
        lambda: cbwr(client.bulk_write(client_ops, ordered=False, verbose_results=True)),
        lambda r: f"Client-level unordered verbose bulk_write succeeded: {r}; wire: {wire_summary(wire.events)}.",
        client_reading,
        wire=wire,
    )
    raw_bw_min = {
        "bulkWrite": 1,
        "ops": [{"insert": 0, "document": {"_id": 2, "v": "raw"}}],
        "nsInfo": [{"ns": f"{DB}.client_bw_a"}],
        "ordered": True,
    }
    run(
        "5c-raw-bulkWrite-command",
        "client.admin.command({'bulkWrite':1,'ops':[{'insert':0,'document':{'_id':2,'v':'raw'}}],'nsInfo':[{'ns':'t_bulk.client_bw_a'}],'ordered':True})",
        lambda: client.admin.command(dict(raw_bw_min)),
        lambda r: f"Raw MongoDB 8.0 bulkWrite command on admin was accepted: {r}.",
        of_reading("Raw MongoDB 8.0 bulkWrite command on admin"),
    )
    raw_bw_full = {
        "bulkWrite": 1,
        "ops": [
            {"insert": 0, "document": {"_id": 3, "v": "raw-a"}},
            {"insert": 1, "document": {"_id": 3, "v": "raw-b"}},
            {"update": 0, "filter": {"_id": 3}, "updateMods": {"$set": {"v": "raw-a2"}}, "multi": False},
            {"delete": 1, "filter": {"_id": 3}, "multi": False},
        ],
        "nsInfo": [{"ns": f"{DB}.client_bw_a"}, {"ns": f"{DB}.client_bw_b"}],
        "ordered": False,
        "errorsOnly": False,
    }
    run(
        "5c2-raw-bulkWrite-command-multi-namespace",
        "client.admin.command({'bulkWrite':1,'ops':[{'insert':0,...},{'insert':1,...},{'update':0,'filter':{'_id':3},'updateMods':{'$set':{'v':'raw-a2'}},'multi':False},{'delete':1,'filter':{'_id':3},'multi':False}],'nsInfo':[{'ns':'t_bulk.client_bw_a'},{'ns':'t_bulk.client_bw_b'}],'ordered':False,'errorsOnly':False})",
        lambda: client.admin.command(dict(raw_bw_full)),
        lambda r: f"Well-formed multi-namespace 8.0 bulkWrite on admin was accepted: {r}.",
        of_reading("Well-formed multi-namespace 8.0 bulkWrite on admin"),
    )
    run(
        "5d-raw-bulkWrite-on-test-db",
        "db.command({'bulkWrite':1,'ops':[{'insert':0,'document':{'_id':2,'v':'raw'}}],'nsInfo':[{'ns':'t_bulk.client_bw_a'}],'ordered':True})  # sent to t_bulk, not admin",
        lambda: db.command(dict(raw_bw_min)),
        lambda r: f"8.0 bulkWrite sent to the non-admin database t_bulk was accepted: {r}.",
        of_reading("8.0 bulkWrite sent to the non-admin database t_bulk"),
    )
    run(
        "5e-client-bw-state",
        "{c: list(db[c].find()) for c in ('client_bw_a', 'client_bw_b')}",
        lambda: {c: list(db[c].find()) for c in ("client_bw_a", "client_bw_b")},
        lambda r: f"Target collections after steps 5a-5d: client_bw_a={r['client_bw_a']} client_bw_b={r['client_bw_b']} (empty means none of the client-level or raw bulkWrite ops was applied).",
    )

    # ---- 6. batch-size limit ---------------------------------------------------------------
    mwbs = hello.get("maxWriteBatchSize")
    docs = [{"_id": i, "k": i % 7} for i in range(25001)]
    run(
        "6a-insert_many-25001",
        "db.big.insert_many([{'_id': i, 'k': i % 7} for i in range(25001)], ordered=False)  # CommandListener records the wire commands",
        lambda: (lambda r: {"inserted_ids_count": len(r.inserted_ids), "acknowledged": r.acknowledged})(db.big.insert_many(docs, ordered=False)),
        lambda r: (
            f"insert_many of 25,001 documents succeeded ({r['inserted_ids_count']} ids) because PyMongo split it into "
            f"{len(wire_summary(wire.events))} insert command(s) of {[n for _, n in wire_summary(wire.events)]} documents "
            f"at hello.maxWriteBatchSize={mwbs}."
        ),
        lambda e: bwe_reading(e, f"wire commands sent: {wire_summary(wire.events)}.") if isinstance(e, BulkWriteError) else of_reading("insert_many(25001)")(e),
        wire=wire,
    )
    run(
        "6b-big-count",
        "db.big.count_documents({})",
        lambda: db.big.count_documents({}),
        lambda r: f"big holds {r} documents after the 25,001-document insert_many.",
    )
    run("6c-drop-big2", "db.big2.drop()", lambda: db.big2.drop(), "Dropped big2 (absent) before the raw single-command inserts.")
    run(
        "6d-raw-insert-25001-one-command",
        "db.command({'insert':'big2','documents':[{'_id': i} for i in range(25001)],'ordered':False})  # one command, no driver split",
        lambda: db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25001)], "ordered": False}),
        lambda r: f"A single insert command carrying 25,001 documents was accepted: ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')}.",
        of_reading("A single insert command carrying 25,001 documents"),
        wire=wire,
    )
    run(
        "6e-big2-count",
        "db.big2.count_documents({})",
        lambda: db.big2.count_documents({}),
        lambda r: f"big2 holds {r} documents after the single 25,001-document insert command ({'nothing was written: the command was rejected as a whole' if r == 0 else 'some or all documents were written'}).",
    )

    def raw_25000():
        db.big2.drop()
        return db.command({"insert": "big2", "documents": [{"_id": i} for i in range(25000)], "ordered": False})

    run(
        "6f-raw-insert-25000-one-command",
        "db.big2.drop(); db.command({'insert':'big2','documents':[{'_id': i} for i in range(25000)],'ordered':False})",
        raw_25000,
        lambda r: f"A single insert command carrying exactly 25,000 documents succeeded: ok={r.get('ok')} n={r.get('n')} writeErrors={r.get('writeErrors')}.",
        of_reading("A single insert command carrying exactly 25,000 documents"),
    )
    run(
        "6g-big2-count-after-25000",
        "db.big2.count_documents({})",
        lambda: db.big2.count_documents({}),
        lambda r: f"big2 holds {r} documents after the 25,000-document insert command.",
    )
    run(
        "6h-raw-insert-0-docs",
        "db.command({'insert':'empty0','documents':[],'ordered':False})",
        lambda: db.command({"insert": "empty0", "documents": [], "ordered": False}),
        lambda r: f"An insert command with an empty documents array was accepted: {r}.",
        of_reading("An insert command with an empty documents array"),
    )
    run(
        "6i-raw-update-25001-one-command",
        "db.command({'update':'big','updates':[{'q':{'_id': i},'u':{'$set':{'u':1}}} for i in range(25001)],'ordered':False})",
        lambda: db.command({"update": "big", "updates": [{"q": {"_id": i}, "u": {"$set": {"u": 1}}} for i in range(25001)], "ordered": False}),
        lambda r: f"A single update command with 25,001 statements was accepted: ok={r.get('ok')} n={r.get('n')} nModified={r.get('nModified')}.",
        of_reading("A single update command with 25,001 statements"),
    )
    run(
        "6i2-big-updated-count",
        "db.big.count_documents({'u': 1})",
        lambda: db.big.count_documents({"u": 1}),
        lambda r: f"{r} documents in big carry u=1 after the 25,001-statement update command ({'nothing was applied' if r == 0 else 'statements were applied'}).",
    )
    run(
        "6j-raw-delete-25001-one-command",
        "db.command({'delete':'big','deletes':[{'q':{'_id': i},'limit':1} for i in range(25001)],'ordered':False})",
        lambda: db.command({"delete": "big", "deletes": [{"q": {"_id": i}, "limit": 1} for i in range(25001)], "ordered": False}),
        lambda r: f"A single delete command with 25,001 statements was accepted: ok={r.get('ok')} n={r.get('n')}.",
        of_reading("A single delete command with 25,001 statements"),
    )
    run(
        "6j2-big-count-after-delete",
        "db.big.count_documents({})",
        lambda: db.big.count_documents({}),
        lambda r: f"big holds {r} documents after the 25,001-statement delete command ({'nothing was deleted' if r == 25001 else 'documents were deleted'}).",
    )
    run(
        "6k-coll-bulk_write-25001-inserts",
        "db.big3.bulk_write([InsertOne({'_id': i}) for i in range(25001)], ordered=False)  # CommandListener records the wire commands",
        lambda: bwr(db.big3.bulk_write([InsertOne({"_id": i}) for i in range(25001)], ordered=False)),
        lambda r: (
            f"Collection-level bulk_write of 25,001 InsertOne ops succeeded (inserted={r['inserted_count']}) as "
            f"{[n for _, n in wire_summary(wire.events)]} documents per insert command, the same driver-side split as insert_many."
        ),
        lambda e: bwe_reading(e, f"wire: {wire_summary(wire.events)}.") if isinstance(e, BulkWriteError) else of_reading("bulk_write(25001)")(e),
        wire=wire,
    )
    run(
        "6k2-big3-count",
        "db.big3.count_documents({})",
        lambda: db.big3.count_documents({}),
        lambda r: f"big3 holds {r} documents after the 25,001-op collection-level bulk_write.",
    )

    # ---- 7. cleanup ------------------------------------------------------------------------
    run("7-dropDatabase", "client.drop_database('t_bulk')", lambda: client.drop_database(DB), "Dropped t_bulk at the end; no other database was touched and the container was left running.")

    def verify_gone():
        try:
            r = client.admin.command({"listDatabases": 1, "nameOnly": True, "filter": {"name": DB}})
            return {"method": "listDatabases nameOnly with filter {name:'t_bulk'}", "t_bulk_present": any(d.get("name") == DB for d in r.get("databases", [])), "databases_returned": [d.get("name") for d in r.get("databases", []) if d.get("name") == DB]}
        except OperationFailure as e:  # filter unsupported: fall back but record only t_bulk's presence
            return {"method": "list_database_names() (filter rejected)", "filter_error": err_info(e), "t_bulk_present": DB in client.list_database_names()}

    run(
        "7b-verify-dropped",
        "client.admin.command({'listDatabases':1,'nameOnly':True,'filter':{'name':'t_bulk'}})",
        verify_gone,
        lambda r: f"After the final drop, t_bulk present = {r['t_bulk_present']} (checked with {r['method']}).",
    )

    report = {
        "test": "bulkwrite-forms",
        "goal": "ENGINE 1.2.0 RERUN; compare with the 0.117 results in ENGINE-TESTS.md",
        "database": DB,
        "ran_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "target": "documentdb-local container ddb-engine-test, localhost:10260, TLS with self-signed certificate (tlsAllowInvalidCertificates)",
        "script": os.path.join(HERE, "run.py"),
        "pymongo_version": pymongo.__version__,
        "python": sys.version.split()[0],
        "engine_version": (bi or {}).get("version"),
        "engine_version_detail": {
            "buildInfo.version": (bi or {}).get("version"),
            "hello.maxWireVersion": hello.get("maxWireVersion"),
            "hello.internal.documentdb_versions": jsonable((hello.get("internal") or {}).get("documentdb_versions")),
        },
        "buildInfo": jsonable(bi),
        "hello": jsonable(hello),
        "evidence_scope": (
            "Facts observed on documentdb-local are evidence about the open-source DocumentDB engine and gateway at the "
            "version buildInfo/hello report; they do not prove managed Azure DocumentDB behaviour."
        ),
        "steps": steps,
    }
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=lambda o: redact(repr(o)))
    print(json.dumps({"engine_version": report["engine_version"], "documentdb_versions": report["engine_version_detail"]["hello.internal.documentdb_versions"], "n_steps": len(steps)}))
    client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        print(redact(traceback.format_exc()), file=sys.stderr)
        sys.exit(1)
