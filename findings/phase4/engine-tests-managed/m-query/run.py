#!/usr/bin/env python
"""Managed-service test "m-query" against the Azure DocumentDB cluster ddb-samples-shared.

Owns database mt_query only. Reads MANAGED_URI from ../managed.env; never prints or records
the password or any URI that contains it. Writes report.json next to this script.

Lettering follows the m-query spec (the open-source script findings/phase4/engine-tests/
query-behaviour/run.py used different letters; each step records its open-source twin):
  (a) explain('executionStats'): unindexed find, indexed find, aggregate $match/$sort,
      $search cosmosSearch on a vector-ivf index          (open-source section c)
  (b) maxTimeMS 1 on aggregate and on a fully consumed find (open-source section d)
  (c) $setWindowFields two-stage cumulative example, $group/$last, sortBy-required errors
                                                            (open-source section a)
  (d) allowDiskUse true / false / non-boolean on aggregate   (open-source section b)
  (e) drop database mt_query
Phase 1 is data-plane only: no cluster configuration is changed by this script.
"""
import datetime as dt
import json
import os
import random
import re
import string
import sys
import time
import traceback
import urllib.parse
import warnings

warnings.filterwarnings("ignore", category=UserWarning)  # PyMongo's CosmosDB notice on connect

import bson
from bson import json_util
import pymongo
from pymongo import MongoClient, ASCENDING, monitoring
from pymongo.errors import PyMongoError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(HERE), "managed.env")
REPORT_PATH = os.path.join(HERE, "report.json")
DB_NAME = "mt_query"
BIG_N = 50_000
BATCH = 5_000
PAYLOAD_LEN = 32


# ---------------------------------------------------------------- utilities

def load_env(path):
    env = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def to_jsonable(obj):
    return json.loads(json_util.dumps(obj))


def jtxt(obj):
    return json_util.dumps(obj)


GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def mask_text(s):
    s = EMAIL_RE.sub("<email-masked>", s)
    s = GUID_RE.sub("<guid-masked>", s)
    return s


def error_record(exc):
    rec = {"exception": f"{type(exc).__module__}.{type(exc).__name__}", "message": str(exc)}
    try:
        rec["driver_timeout_property"] = bool(exc.timeout)
    except Exception:  # noqa
        pass
    if isinstance(exc, OperationFailure):
        details = exc.details or {}
        rec["code"] = exc.code
        rec["codeName"] = details.get("codeName")
        rec["errmsg"] = details.get("errmsg")
        rec["errorLabels"] = details.get("errorLabels")  # as sent by the server; None = field absent
        drv = getattr(exc, "_error_labels", None)
        rec["errorLabels_driver_view"] = sorted(drv) if drv else []
        rec["details"] = to_jsonable(details)
    return rec


def is_err(resp):
    return isinstance(resp, dict) and "exception" in resp


class Recorder(monitoring.CommandListener):
    """Captures the exact commands PyMongo sends (minus session plumbing) while active."""
    SKIP = {"lsid", "$clusterTime", "$db", "documents", "$readPreference", "txnNumber"}

    def __init__(self):
        self.active = False
        self.events = []

    def begin(self):
        self.events = []
        self.active = True

    def end(self):
        self.active = False
        ev, self.events = self.events, []
        return ev

    def started(self, event):
        if not self.active:
            return
        cmd = {k: v for k, v in event.command.items() if k not in self.SKIP}
        self.events.append({"event": "started", "request_id": event.request_id,
                            "command_name": event.command_name, "command": to_jsonable(cmd)})

    def succeeded(self, event):
        if not self.active:
            return
        reply = event.reply
        summ = {"ok": reply.get("ok")}
        cur = reply.get("cursor")
        if isinstance(cur, dict):
            field = "firstBatch" if "firstBatch" in cur else ("nextBatch" if "nextBatch" in cur else None)
            summ["cursor_id"] = cur.get("id")
            summ["batch_field"] = field
            summ["batch_len"] = len(cur[field]) if field else None
        else:
            summ["reply_keys"] = list(reply.keys())
        self.events.append({"event": "succeeded", "request_id": event.request_id,
                            "command_name": event.command_name,
                            "duration_ms": round(event.duration_micros / 1000, 3), "reply_summary": to_jsonable(summ)})

    def failed(self, event):
        if not self.active:
            return
        self.events.append({"event": "failed", "request_id": event.request_id,
                            "command_name": event.command_name,
                            "duration_ms": round(event.duration_micros / 1000, 3),
                            "failure": to_jsonable(event.failure)})


class Report:
    def __init__(self):
        self.steps = []

    def add(self, section, step, command, response, reading, **extra):
        rec = {"section": section, "step": step, "command": command, "response": response, "reading": reading}
        rec.update(extra)
        self.steps.append(rec)
        status = "ERROR" if is_err(response) else "ok"
        print(f"[{section}] {step}: {status}", file=sys.stderr, flush=True)
        return rec


def run_cmd(report, section, step, command_text, fn, reading_ok, reading_err=None, recorder=None, **extra):
    """Run fn(); record its result or the raw error."""
    if recorder is not None:
        recorder.begin()
    t0 = time.time()
    try:
        out = fn()
        elapsed = round((time.time() - t0) * 1000)
        if recorder is not None:
            extra["driver_commands"] = recorder.end()
        try:
            reading = reading_ok(out) if callable(reading_ok) else reading_ok
        except Exception as rexc:  # a reading must never abort the run
            reading = f"(automatic reading failed: {type(rexc).__name__}: {rexc}; see response)"
        return report.add(section, step, command_text, to_jsonable(out), reading, elapsed_ms=elapsed, **extra)
    except PyMongoError as exc:
        elapsed = round((time.time() - t0) * 1000)
        if recorder is not None:
            extra["driver_commands"] = recorder.end()
        resp = error_record(exc)
        if callable(reading_err):
            try:
                reading = reading_err(exc)
            except Exception as rexc:  # noqa
                reading = f"(automatic reading failed: {type(rexc).__name__}: {rexc}; see response)"
        else:
            reading = reading_err or (f"Failed with code {resp.get('code')} {resp.get('codeName')}: "
                                      f"{resp.get('errmsg')}")
        return report.add(section, step, command_text, resp, reading, elapsed_ms=elapsed, **extra)


def err_reading(e, prefix="Failed"):
    d = getattr(e, "details", None) or {}
    return (f"{prefix}: code {getattr(e, 'code', None)} {d.get('codeName')}: {d.get('errmsg')}; "
            f"errorLabels {d.get('errorLabels')}.")


# ---------------------------------------------------------------- explain helpers

STAGE_ATTRS = ("indexName", "isBitmap", "runtimeFilterSet", "indexFilterSet", "direction", "hasOrderBy",
               "cosmosSearchCustomParams", "nReturned", "totalDocsExamined", "totalKeysExamined", "docsExamined",
               "keysExamined", "totalDocsRemovedByRuntimeFilter", "estimatedTotalKeysExamined", "sortKeysCount",
               "executionTimeMillis", "executionTimeMillisEstimate", "numBlocksFromCache", "numBlocksFromDisk",
               "parallelism", "workersLaunched")
STAT_KEYS = ("nReturned", "totalDocsExamined", "totalKeysExamined", "docsExamined", "keysExamined",
             "executionTimeMillis", "totalDocsRemovedByRuntimeFilter")


def walk(node, path, fn):
    fn(node, path)
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}" if path else k, fn)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", fn)


def find_key_paths(node, key):
    acc = []

    def visit(n, p):
        if isinstance(n, dict) and key in n:
            acc.append(f"{p}.{key}" if p else key)
    walk(node, "", visit)
    return acc


def get_path(doc, path):
    cur = doc
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            cur = cur[int(part[1:-1])]
        else:
            cur = cur[part]
    return cur


def stage_names(node):
    acc = []

    def visit(n, p):
        if isinstance(n, dict) and isinstance(n.get("stage"), str):
            acc.append(n["stage"])
    walk(node, "", visit)
    return acc


def summarize_explain(doc):
    d = to_jsonable(doc)
    nodes = []

    def visit(n, p):
        if isinstance(n, dict) and isinstance(n.get("stage"), str):
            info = {"path": p, "stage": n["stage"]}
            for k in STAGE_ATTRS:
                if k in n:
                    info[k] = n[k]
            nodes.append(info)
    walk(d, "", visit)
    stats = []

    def visit2(n, p):
        if isinstance(n, dict):
            for k in STAT_KEYS:
                if k in n and not isinstance(n[k], (dict, list)):
                    stats.append({"path": f"{p}.{k}" if p else k, "value": n[k]})
    walk(d, "", visit2)
    wp_paths = find_key_paths(d, "winningPlan")
    es_paths = find_key_paths(d, "executionStats")
    ex_paths = find_key_paths(d, "executionStages")
    names = [n["stage"] for n in nodes]
    summary = {
        "top_level_keys_server_order": list(d.keys()),
        "explainVersion": d.get("explainVersion"),
        "winningPlan_paths": wp_paths,
        "executionStats_paths": es_paths,
        "queryPlanner_paths": find_key_paths(d, "queryPlanner"),
        "stage_names_in_order": names,
        "stage_names_unique": sorted(set(names)),
        "stage_names_by_winningPlan": {p: stage_names(get_path(d, p)) for p in wp_paths},
        "stage_names_by_executionStages": {p: stage_names(get_path(d, p)) for p in ex_paths},
        "has_COLLSCAN": "COLLSCAN" in names,
        "has_IXSCAN": "IXSCAN" in names,
        "has_FETCH": "FETCH" in names,
        "has_SORT": "SORT" in names,
        "stage_nodes": nodes,
        "stat_occurrences": stats,
    }
    if isinstance(d.get("stages"), list):
        summary["stages_array_keys"] = [list(s.keys()) if isinstance(s, dict) else str(type(s)) for s in d["stages"]]
    if es_paths:
        es = get_path(d, es_paths[0])
        if isinstance(es, dict):
            summary["first_executionStats"] = {"path": es_paths[0], **{k: es.get(k) for k in
                                               ("nReturned", "executionTimeMillis", "totalKeysExamined",
                                                "totalDocsExamined", "totalDocsRemovedByRuntimeFilter",
                                                "executionSuccess") if k in es}}
    return summary


def explain_step(report, db, step_id, label, explain_cmd, prefix, **extra):
    cmd_text = f"db.command({jtxt(explain_cmd)})  # pymongo Database.command, database {DB_NAME}"
    t0 = time.time()
    try:
        out = db.command(explain_cmd)
        s = summarize_explain(out)
        fes = s.get("first_executionStats", {})
        reading = (f"{prefix}: top-level keys {s['top_level_keys_server_order']}; winningPlan at "
                   f"{s['winningPlan_paths'] or 'nowhere'}; stage names {s['stage_names_in_order']}; "
                   f"COLLSCAN {'present' if s['has_COLLSCAN'] else 'absent'}; first executionStats "
                   f"({fes.get('path', 'none')}) nReturned {fes.get('nReturned')}, totalDocsExamined "
                   f"{fes.get('totalDocsExamined')}.")
        report.add("a", f"{step_id} {label}", cmd_text, {"summary": s, "full_explain": to_jsonable(out)}, reading,
                   elapsed_ms=round((time.time() - t0) * 1000), **extra)
        return out
    except PyMongoError as exc:
        resp = error_record(exc)
        report.add("a", f"{step_id} {label}", cmd_text, resp,
                   f"{prefix}: explain failed with code {resp.get('code')} {resp.get('codeName')}: {resp.get('errmsg')}",
                   elapsed_ms=round((time.time() - t0) * 1000), **extra)
        return None


def consume(cursor, keep=3):
    """Iterate a cursor to exhaustion; keep a few docs; never swallow the error silently."""
    n, first = 0, []
    try:
        for doc in cursor:
            if n < keep:
                first.append(doc)
            n += 1
    except PyMongoError as exc:
        return {"completed": False, "docs_received_before_error": n, "first_docs": to_jsonable(first),
                "error": error_record(exc)}
    return {"completed": True, "docs_received": n, "first_docs": to_jsonable(first), "error": None}


def consume_reading(out, what):
    if out["completed"]:
        return f"{what}: cursor fully consumed without error, {out['docs_received']} docs received."
    e = out["error"]
    return (f"{what}: failed after {out['docs_received_before_error']} docs with code {e.get('code')} "
            f"{e.get('codeName')}: {e.get('errmsg')}; errorLabels {e.get('errorLabels')}; "
            f"pymongo raised {e.get('exception')}.")


def trim_cursor_reply(reply, keep=3):
    r = to_jsonable(reply)
    cur = r.get("cursor")
    if isinstance(cur, dict):
        for f in ("firstBatch", "nextBatch"):
            if f in cur:
                cur[f + "_len"] = len(cur[f])
                cur[f] = cur[f][:keep]
                cur[f + "_note"] = f"truncated to the first {keep} docs in this record"
    return r


# ---------------------------------------------------------------- main

def main():
    env = load_env(ENV_PATH)
    pw = env["MANAGED_PASS"]
    secret_forms = {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}
    report = Report()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    recorder = Recorder()
    client = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, socketTimeoutMS=540000,
                         appname="m-query", event_listeners=[recorder])
    target = {"cluster": env.get("MANAGED_CLUSTER"), "resource_group": env.get("MANAGED_RG"),
              "host_used": env.get("MANAGED_HOST"),
              "connection_options": urllib.parse.urlsplit(env["MANAGED_URI"]).query,
              "scheme": urllib.parse.urlsplit(env["MANAGED_URI"]).scheme,
              "driver": f"pymongo {pymongo.version}", "python": sys.version.split()[0],
              "client_kwargs": "serverSelectionTimeoutMS=30000, socketTimeoutMS=540000, appname='m-query'"}
    dropped = False
    fatal = None
    try:
        hello = client.admin.command("hello")
        build_info = client.admin.command("buildInfo")
        target["hello"] = to_jsonable(hello)
        target["buildInfo"] = to_jsonable(build_info)
        report.add("setup", "S.0 hello and buildInfo",
                   "client.admin.command('hello'); client.admin.command('buildInfo')",
                   {"hello": to_jsonable(hello), "buildInfo": to_jsonable(build_info)},
                   f"Managed service reports maxWireVersion {hello.get('maxWireVersion')}, documentdb_versions "
                   f"{hello.get('internal', {}).get('documentdb_versions')}, kind {hello.get('internal', {}).get('kind')!r}, "
                   f"buildInfo.version {build_info.get('version')}.")
        db = client[DB_NAME]

        existing = db.list_collection_names()
        for coll in existing:
            db.drop_collection(coll)
        report.add("setup", "S.1 reset database mt_query",
                   f"db.list_collection_names(); db.drop_collection(c) for each  # database {DB_NAME} only",
                   {"collections_found": existing, "dropped": existing},
                   "Owned database checked before seeding; no other database touched.")

        # ---------------- seed: big (50,000 small docs)
        big = db["big"]
        alphabet = string.ascii_lowercase
        rnd = random.Random(11)
        t0 = time.time()
        batch, inserted, sizes = [], 0, []
        for i in range(BIG_N):
            doc = {"i": i, "rnd": rnd.random(), "grp": i % 97,
                   "payload": "".join(rnd.choice(alphabet) for _ in range(PAYLOAD_LEN)),
                   "tags": [f"t{i % 13}", f"u{i % 7}"]}
            if i % 1000 == 0:
                sizes.append(len(bson.encode(doc)))
            batch.append(doc)
            if len(batch) == BATCH:
                big.insert_many(batch, ordered=False)
                inserted += len(batch)
                batch = []
        if batch:
            big.insert_many(batch, ordered=False)
            inserted += len(batch)
        cnt = big.count_documents({})
        report.add("setup", "S.2 seed big collection (50,000 small documents)",
                   f"db.big.insert_many(batch, ordered=False) x {BIG_N // BATCH} batches of {BATCH}; docs "
                   f"{{i: int, rnd: double (random.Random(11)), grp: i % 97, payload: {PAYLOAD_LEN}-char lowercase "
                   f"string, tags: ['t<i%13>', 'u<i%7>']}}; then db.big.count_documents({{}})",
                   {"inserted": inserted, "count_documents": cnt,
                    "approx_bson_bytes_per_doc_before_id": round(sum(sizes) / len(sizes), 1),
                    "elapsed_ms": round((time.time() - t0) * 1000)},
                   f"Loaded {cnt} small documents (about {round(sum(sizes) / len(sizes))} BSON bytes each before _id).")

        # ---------------- seed: sales (identical to the open-source seed)
        sales = db["sales"]
        srnd = random.Random(7)  # same sequence as the open-source random.seed(7)
        sdocs = []
        base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        for region in ("east", "west", "north"):
            for i in range(8):
                sdocs.append({"region": region, "ts": base + dt.timedelta(days=i),
                              "amount": srnd.choice([5, 12, 3, 20, 7, 15, 1, 9]) + (i % 3)})
        sales.insert_many(sdocs)
        expected_sales = {}
        for region in ("east", "west", "north"):
            rs = sorted([d for d in sdocs if d["region"] == region], key=lambda d: d["ts"])
            expected_sales[region] = {"finalTotal": sum(d["amount"] for d in rs),
                                      "finalMax": max(d["amount"] for d in rs)}
        report.add("setup", "S.3 seed sales collection (same generator and seed as the open-source test)",
                   "db.sales.insert_many(24 docs: 3 regions x 8 days, fields region, ts (Date), amount; random.Random(7))",
                   {"inserted": len(sdocs), "client_side_expected": expected_sales},
                   "Seed data for the window-function tests; expected per-region totals and maxima computed client-side.")

        # ---------------- seed: trades (for the exact L08 example)
        trades = db["trades"]
        trnd = random.Random(23)
        tdocs = []
        tbase = dt.datetime(2026, 3, 2, 9, 0, tzinfo=dt.timezone.utc)
        strategies = ("momentum-1", "meanrev-2", "breakout-3")
        for si, sid in enumerate(strategies):
            for j in range(30):
                tdocs.append({"strategyId": sid, "closedAt": tbase + dt.timedelta(hours=j, minutes=7 * si),
                              "pnl": trnd.randint(-50, 60)})
        trades.insert_many(tdocs)
        expected_l08 = {}
        for sid in strategies:
            rows = sorted([d for d in tdocs if d["strategyId"] == sid], key=lambda d: d["closedAt"])
            cum, peak, maxdd = 0, None, None
            for r in rows:
                cum += r["pnl"]
                peak = cum if peak is None else max(peak, cum)
                dd = peak - cum
                maxdd = dd if maxdd is None else max(maxdd, dd)
            expected_l08[sid] = {"maxDrawdown": maxdd, "finalPnl": cum}
        report.add("setup", "S.4 seed trades collection for the exact L08 example",
                   "db.trades.insert_many(90 docs: strategyId in ['momentum-1','meanrev-2','breakout-3'] x 30, "
                   "closedAt (Date, hourly), pnl int in [-50, 60]; random.Random(23))",
                   {"inserted": len(tdocs), "client_side_expected": expected_l08},
                   "Seed data for the L08 drawdown pipeline; expected maxDrawdown and finalPnl computed client-side.")

        # ================= (a) explain =================
        explain_step(report, db, "a.1", "find on unindexed field rnd, range (executionStats)",
                     {"explain": {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "verbosity": "executionStats"},
                     "Unindexed range find", open_source_step="c.1")
        explain_step(report, db, "a.1b", "find on unindexed field region in the 24-doc sales collection (executionStats)",
                     {"explain": {"find": "sales", "filter": {"region": "east"}}, "verbosity": "executionStats"},
                     "Unindexed find on a tiny collection", open_source_step="c.1b")
        explain_step(report, db, "a.1c", "find with empty filter on big (executionStats)",
                     {"explain": {"find": "big", "filter": {}}, "verbosity": "executionStats"},
                     "Find with no filter", open_source_step="c.1c")
        explain_step(report, db, "a.1d", "find equality on unindexed field grp on big (executionStats)",
                     {"explain": {"find": "big", "filter": {"grp": 5}}, "verbosity": "executionStats"},
                     "Unindexed equality find", open_source_step="c.1d")

        run_cmd(report, "a", "a.2 createIndex on big.i",
                "db.big.create_index([('i', ASCENDING)], name='i_1')",
                lambda: big.create_index([("i", ASCENDING)], name="i_1"),
                lambda out: f"Index {out} created on big.i.", open_source_step="c.2")

        explain_step(report, db, "a.3", "find equality on indexed field i (executionStats)",
                     {"explain": {"find": "big", "filter": {"i": 12345}}, "verbosity": "executionStats"},
                     "Indexed equality find", open_source_step="c.3")
        explain_step(report, db, "a.3b", "find range on indexed field i with sort on unindexed rnd (executionStats)",
                     {"explain": {"find": "big", "filter": {"i": {"$gt": 49000}}, "sort": {"rnd": -1}},
                      "verbosity": "executionStats"},
                     "Indexed range find with in-memory sort", open_source_step="c.3b")
        explain_step(report, db, "a.4", "aggregate $match (indexed i) + $sort (rnd) + $limit (executionStats)",
                     {"explain": {"aggregate": "big",
                                  "pipeline": [{"$match": {"i": {"$gt": 49000}}}, {"$sort": {"rnd": -1}},
                                               {"$limit": 10}], "cursor": {}}, "verbosity": "executionStats"},
                     "Aggregate $match/$sort/$limit on indexed i", open_source_step="c.4")
        explain_step(report, db, "a.4b", "aggregate $match (unindexed rnd) + $sort (i) (executionStats)",
                     {"explain": {"aggregate": "big",
                                  "pipeline": [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"i": 1}}],
                                  "cursor": {}}, "verbosity": "executionStats"},
                     "Aggregate unindexed $match then $sort", open_source_step="c.4b")

        # vector collection, identical generator and seed to the open-source test
        vec = db["vec"]
        vrnd = random.Random(3)
        DIMS = 8
        vdocs = [{"k": i, "embedding": [vrnd.uniform(-1, 1) for _ in range(DIMS)], "cat": f"c{i % 4}"}
                 for i in range(500)]
        vec.insert_many(vdocs)
        report.add("a", "a.5a seed vec collection",
                   "db.vec.insert_many(500 docs {k, embedding: 8 doubles from random.Random(3).uniform(-1,1), cat})",
                   {"inserted": len(vdocs)}, "Seed data for the vector index (same generator as the open-source test).",
                   open_source_step="c.5a")
        create_vec_idx = {"createIndexes": "vec",
                          "indexes": [{"name": "vec_ivf", "key": {"embedding": "cosmosSearch"},
                                       "cosmosSearchOptions": {"kind": "vector-ivf", "numLists": 2,
                                                               "similarity": "COS", "dimensions": DIMS}}]}
        run_cmd(report, "a", "a.5b createIndexes cosmosSearch vector-ivf on vec.embedding",
                f"db.command({jtxt(create_vec_idx)})",
                lambda: db.command(create_vec_idx),
                lambda out: f"vector-ivf index created; raw reply {jtxt(out)}.",
                lambda e: err_reading(e, "vector-ivf index creation failed"), open_source_step="c.5b")
        run_cmd(report, "a", "a.5b2 listIndexes on vec (to name the index the explain should use)",
                "list(db.vec.list_indexes())",
                lambda: list(vec.list_indexes()),
                lambda out: f"listIndexes returned {len(out)} indexes: {[ix.get('name') for ix in out]}.",
                open_source_step=None)
        qvec = [vrnd.uniform(-1, 1) for _ in range(DIMS)]
        search_pipe = [{"$search": {"cosmosSearch": {"vector": qvec, "path": "embedding", "k": 5},
                                    "returnStoredSource": True}},
                       {"$project": {"_id": 0, "k": 1, "score": {"$meta": "searchScore"}}}]
        run_cmd(report, "a", "a.5c run the $search cosmosSearch pipeline (sanity)",
                f"list(db.vec.aggregate({jtxt(search_pipe)}))",
                lambda: list(vec.aggregate(search_pipe)),
                lambda out: f"$search cosmosSearch returned {len(out)} rows: {[(r.get('k'), round(r.get('score', 0), 6)) for r in out]}.",
                lambda e: err_reading(e, "$search cosmosSearch failed"), open_source_step="c.5c")
        explain_step(report, db, "a.5d", "explain $search cosmosSearch on vector-ivf (executionStats)",
                     {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}},
                      "verbosity": "executionStats"},
                     "Vector $search pipeline", open_source_step="c.5d")
        explain_step(report, db, "a.5e", "explain $search cosmosSearch on vector-ivf (queryPlanner)",
                     {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}},
                      "verbosity": "queryPlanner"},
                     "Vector $search pipeline, queryPlanner verbosity", open_source_step="c.5e")

        cumulative = {"documents": ["unbounded", "current"]}
        pipe_c1 = [
            {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                                  "output": {"runningTotal": {"$sum": "$amount", "window": cumulative}}}},
            {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                                  "output": {"runningMax": {"$max": "$amount", "window": cumulative}}}},
            {"$sort": {"region": 1, "ts": 1}},
            {"$group": {"_id": "$region", "finalTotal": {"$last": "$runningTotal"},
                        "finalMax": {"$last": "$runningMax"}, "lastTs": {"$last": "$ts"}, "n": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        explain_step(report, db, "a.6", "explain the chained $setWindowFields pipeline on sales (executionStats)",
                     {"explain": {"aggregate": "sales", "pipeline": pipe_c1, "cursor": {}},
                      "verbosity": "executionStats"},
                     "Aggregate with two $setWindowFields stages", open_source_step="c.6")

        # ================= (b) maxTimeMS =================
        slow_filter = {"$and": [{"payload": {"$regex": "q.*z.*q.*z"}}, {"rnd": {"$lt": 0.5}},
                                {"$expr": {"$gt": [{"$strLenCP": "$payload"}, PAYLOAD_LEN - 1]}}]}
        none_filter = {"payload": {"$regex": "zzzzzzzzzz"},
                       "$expr": {"$gt": [{"$strLenCP": "$payload"}, PAYLOAD_LEN - 1]}}

        run_cmd(report, "b", "b.0 baseline: slow predicate, no maxTimeMS, cursor fully consumed",
                f"for d in db.big.find({jtxt(slow_filter)}, {{'_id': 1}}): count",
                lambda: consume(big.find(slow_filter, {"_id": 1})),
                lambda out: consume_reading(out, "Baseline with no maxTimeMS"), recorder=recorder,
                open_source_step="d.0")
        explain_step(report, db, "b.0b", "explain the slow predicate (executionStats) to show its server-side time",
                     {"explain": {"find": "big", "filter": slow_filter, "projection": {"_id": 1}},
                      "verbosity": "executionStats"},
                     "Slow-predicate find", open_source_step=None)
        report.steps[-1]["section"] = "b"

        run_cmd(report, "b", "b.1 find with max_time_ms(1), cursor fully consumed (default batch size)",
                f"for d in db.big.find({jtxt(slow_filter)}, {{'_id': 1}}).max_time_ms(1): count",
                lambda: consume(big.find(slow_filter, {"_id": 1}).max_time_ms(1)),
                lambda out: consume_reading(out, "find with maxTimeMS 1"), recorder=recorder,
                open_source_step="d.1")

        def b2():
            reply = db.command({"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "maxTimeMS": 1})
            cid = reply["cursor"]["id"]
            out = {"find_reply": trim_cursor_reply(reply)}
            if cid:
                out["killCursors_reply"] = to_jsonable(db.command({"killCursors": "big", "cursors": [cid]}))
            return out
        run_cmd(report, "b", "b.2 raw find command with maxTimeMS: 1 (first batch only)",
                f"db.command({{'find': 'big', 'filter': {jtxt(slow_filter)}, 'projection': {{'_id': 1}}, "
                f"'maxTimeMS': 1}}); then killCursors on the returned cursor id",
                b2,
                lambda out: (f"Raw find with maxTimeMS 1 returned a first batch of "
                             f"{out['find_reply']['cursor'].get('firstBatch_len')} docs and cursor id "
                             f"{out['find_reply']['cursor'].get('id')} without error."),
                lambda e: err_reading(e, "Raw find with maxTimeMS 1 failed"), open_source_step="d.2")

        run_cmd(report, "b", "b.3 aggregate with maxTimeMS=1 on the slow predicate",
                f"list(db.big.aggregate([{{'$match': {jtxt(slow_filter)}}}, {{'$count': 'n'}}], maxTimeMS=1))",
                lambda: list(big.aggregate([{"$match": slow_filter}, {"$count": "n"}], maxTimeMS=1)),
                lambda out: f"Unexpectedly completed within maxTimeMS 1: {jtxt(out)}.",
                lambda e: err_reading(e, "aggregate maxTimeMS 1 expired"), recorder=recorder,
                open_source_step="d.3")

        run_cmd(report, "b", "b.4 count_documents with maxTimeMS=1 on the slow predicate",
                f"db.big.count_documents({jtxt(slow_filter)}, maxTimeMS=1)",
                lambda: {"count": big.count_documents(slow_filter, maxTimeMS=1)},
                lambda out: f"Unexpectedly completed within maxTimeMS 1: {out}.",
                lambda e: err_reading(e, "count_documents maxTimeMS 1 expired"), recorder=recorder,
                open_source_step="d.4")

        run_cmd(report, "b", "b.5 control: find with max_time_ms(120000), cursor fully consumed",
                f"for d in db.big.find({jtxt(slow_filter)}, {{'_id': 1}}).max_time_ms(120000): count",
                lambda: consume(big.find(slow_filter, {"_id": 1}).max_time_ms(120000)),
                lambda out: consume_reading(out, "Control find with maxTimeMS 120000"), recorder=recorder,
                open_source_step="d.5")

        run_cmd(report, "b", "b.6 find with max_time_ms(1), predicate matching nothing (full scan before the first batch)",
                f"for d in db.big.find({jtxt(none_filter)}, {{'_id': 1}}).max_time_ms(1): count",
                lambda: consume(big.find(none_filter, {"_id": 1}).max_time_ms(1)),
                lambda out: consume_reading(out, "find with maxTimeMS 1 and a full scan inside the find command"),
                recorder=recorder, open_source_step="d.6")
        run_cmd(report, "b", "b.6b control: same predicate, no maxTimeMS",
                f"for d in db.big.find({jtxt(none_filter)}, {{'_id': 1}}): count",
                lambda: consume(big.find(none_filter, {"_id": 1})),
                lambda out: consume_reading(out, "Control for b.6 with no maxTimeMS"), recorder=recorder,
                open_source_step="d.6b")

        run_cmd(report, "b", "b.7 find with max_time_ms(1) and sort on unindexed rnd, limit 5",
                f"for d in db.big.find({jtxt(slow_filter)}, {{'_id': 1}}).sort('rnd', 1).limit(5).max_time_ms(1): count",
                lambda: consume(big.find(slow_filter, {"_id": 1}).sort("rnd", 1).limit(5).max_time_ms(1)),
                lambda out: consume_reading(out, "find with maxTimeMS 1 and an in-memory sort"), recorder=recorder,
                open_source_step="d.7")

        run_cmd(report, "b", "b.8 find with max_time_ms(1), batch_size(50), cursor fully consumed (many getMores)",
                f"for d in db.big.find({jtxt(slow_filter)}, {{'_id': 1}}).max_time_ms(1).batch_size(50): count",
                lambda: consume(big.find(slow_filter, {"_id": 1}).max_time_ms(1).batch_size(50)),
                lambda out: consume_reading(out, "find with maxTimeMS 1 and batch size 50"), recorder=recorder,
                open_source_step="d.8")

        raw_find_single = {"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "singleBatch": True,
                           "batchSize": 1_000_000, "maxTimeMS": 1}

        def b9():
            reply = db.command(raw_find_single)
            return {"find_reply": trim_cursor_reply(reply)}
        run_cmd(report, "b", "b.9 raw find command, singleBatch true, batchSize 1e6, maxTimeMS 1",
                f"db.command({jtxt(raw_find_single)})",
                b9,
                lambda out: (f"Raw singleBatch find returned {out['find_reply']['cursor'].get('firstBatch_len')} docs "
                             f"in one batch without error despite maxTimeMS 1."),
                lambda e: err_reading(e, "Raw singleBatch find with maxTimeMS 1 failed"), open_source_step="d.9")

        def b10():
            first = db.command({"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "batchSize": 10})
            cid = first["cursor"]["id"]
            out = {"find_reply": trim_cursor_reply(first)}
            try:
                gm = db.command({"getMore": cid, "collection": "big", "batchSize": 1_000_000, "maxTimeMS": 1})
                out["getMore_reply"] = trim_cursor_reply(gm)
                cid_after = gm["cursor"]["id"]
            except PyMongoError as exc:
                out["getMore_error"] = error_record(exc)
                cid_after = cid
            if cid_after:
                try:
                    out["killCursors_reply"] = to_jsonable(db.command({"killCursors": "big", "cursors": [cid_after]}))
                except PyMongoError as exc:
                    out["killCursors_error"] = error_record(exc)
            return out

        def b10_reading(out):
            if "getMore_error" in out:
                e = out["getMore_error"]
                return (f"getMore carrying maxTimeMS 1 on a non-tailable find cursor failed with code {e.get('code')} "
                        f"{e.get('codeName')}: {e.get('errmsg')}.")
            return (f"getMore carrying maxTimeMS 1 was accepted and returned "
                    f"{out['getMore_reply']['cursor'].get('nextBatch_len')} docs without a timeout error.")
        run_cmd(report, "b", "b.10 raw getMore with maxTimeMS 1 on a non-tailable find cursor",
                f"first = db.command({{'find': 'big', 'filter': {jtxt(slow_filter)}, 'projection': {{'_id': 1}}, "
                f"'batchSize': 10}}); db.command({{'getMore': first['cursor']['id'], 'collection': 'big', "
                f"'batchSize': 1000000, 'maxTimeMS': 1}}); killCursors if still open",
                b10, b10_reading, open_source_step="d.10")

        run_cmd(report, "b", "b.11 control: aggregate $match + $count with maxTimeMS=60000",
                f"list(db.big.aggregate([{{'$match': {jtxt(slow_filter)}}}, {{'$count': 'n'}}], maxTimeMS=60000))",
                lambda: list(big.aggregate([{"$match": slow_filter}, {"$count": "n"}], maxTimeMS=60000)),
                lambda out: f"With maxTimeMS 60000 the aggregate completes: {jtxt(out)}.", recorder=recorder,
                open_source_step="d.11")

        # ================= (c) $setWindowFields =================
        def read_c1(out):
            got = {r["_id"]: {"finalTotal": r["finalTotal"], "finalMax": r["finalMax"]} for r in out}
            return ("Two chained $setWindowFields stages with cumulative ['unbounded','current'] windows ($sum, then $max) "
                    "followed by $sort and $group/$last ran; "
                    + ("values match the client-side computation." if got == expected_sales
                       else f"values DIFFER from the client-side computation {expected_sales}."))
        run_cmd(report, "c", "c.1 chained $setWindowFields ($sum, then $max) + $sort + $group $last on sales",
                f"list(db.sales.aggregate({jtxt(pipe_c1)}))",
                lambda: list(sales.aggregate(pipe_c1)), read_c1, expected=expected_sales, open_source_step="a.1")

        pipe_c2 = [pipe_c1[0], pipe_c1[1], pipe_c1[3], pipe_c1[4]]
        run_cmd(report, "c", "c.2 same pipeline with no $sort between the window stages and $group",
                f"list(db.sales.aggregate({jtxt(pipe_c2)}))",
                lambda: list(sales.aggregate(pipe_c2)),
                lambda out: ("Ran without error; $last picked "
                             + ("the sortBy-last row in every partition (matches the client-side computation)."
                                if {r['_id']: {'finalTotal': r['finalTotal'], 'finalMax': r['finalMax']} for r in out}
                                == expected_sales else
                                f"rows that do not match {expected_sales}, so $group order after $setWindowFields is not guaranteed.")),
                expected=expected_sales, open_source_step="a.2")

        pipe_c3 = [
            {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                                  "output": {"runningTotal": {"$sum": "$amount", "window": cumulative},
                                             "runningMax": {"$max": "$amount", "window": cumulative}}}},
            {"$match": {"region": "east"}},
            {"$sort": {"ts": 1}},
            {"$project": {"_id": 0, "ts": 1, "amount": 1, "runningTotal": 1, "runningMax": 1}},
        ]

        def read_c3(out):
            running, mx, ok = 0, None, True
            for r in out:
                running += r["amount"]
                mx = r["amount"] if mx is None else max(mx, r["amount"])
                if r["runningTotal"] != running or r["runningMax"] != mx:
                    ok = False
            return ("One $setWindowFields stage with cumulative $sum and $max returned per-row running values"
                    + (" that match a client-side scan." if ok else " that DO NOT match a client-side scan."))
        run_cmd(report, "c", "c.3 one $setWindowFields stage with $sum and $max cumulative windows (east rows)",
                f"list(db.sales.aggregate({jtxt(pipe_c3)}))",
                lambda: list(sales.aggregate(pipe_c3)), read_c3, open_source_step="a.3")

        pipe_l08 = [
            {"$match": {"strategyId": "momentum-1"}},
            {"$setWindowFields": {"partitionBy": "$strategyId", "sortBy": {"closedAt": 1},
                                  "output": {"cumulativePnl": {"$sum": "$pnl",
                                                               "window": {"documents": ["unbounded", "current"]}}}}},
            {"$setWindowFields": {"partitionBy": "$strategyId", "sortBy": {"closedAt": 1},
                                  "output": {"runningPeak": {"$max": "$cumulativePnl",
                                                             "window": {"documents": ["unbounded", "current"]}}}}},
            {"$set": {"drawdown": {"$subtract": ["$runningPeak", "$cumulativePnl"]}}},
            {"$sort": {"closedAt": 1}},
            {"$group": {"_id": "$strategyId", "maxDrawdown": {"$max": "$drawdown"},
                        "finalPnl": {"$last": "$cumulativePnl"}}},
        ]

        def read_l08(out, sids):
            got = {r["_id"]: {"maxDrawdown": r["maxDrawdown"], "finalPnl": r["finalPnl"]} for r in out}
            exp = {s: expected_l08[s] for s in sids}
            return ("The L08 example ran as written (two chained cumulative $setWindowFields, $set, $sort, $group with "
                    "$max and $last); " + ("results match the client-side computation " + jtxt(exp) + "."
                                           if got == exp else f"results {jtxt(got)} DIFFER from {jtxt(exp)}."))
        run_cmd(report, "c", "c.4 the exact L08 example (with $match strategyId 'momentum-1') on trades",
                f"list(db.trades.aggregate({jtxt(pipe_l08)}))",
                lambda: list(trades.aggregate(pipe_l08)),
                lambda out: read_l08(out, ["momentum-1"]), expected={"momentum-1": expected_l08["momentum-1"]},
                open_source_step=None)
        pipe_l08_all = pipe_l08[1:] + [{"$sort": {"_id": 1}}]
        run_cmd(report, "c", "c.4b the L08 example without the $match (all three strategies), sorted by _id",
                f"list(db.trades.aggregate({jtxt(pipe_l08_all)}))",
                lambda: list(trades.aggregate(pipe_l08_all)),
                lambda out: read_l08(out, list(strategies)), expected=expected_l08, open_source_step=None)

        def sortby_err(e):
            return err_reading(e, "Rejected")
        pipe_c5 = [{"$setWindowFields": {"partitionBy": "$region",
                                         "output": {"runningTotal": {"$sum": "$amount", "window": cumulative}}}}]
        run_cmd(report, "c", "c.5 documents window ['unbounded','current'] with no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c5)}))",
                lambda: list(sales.aggregate(pipe_c5)),
                "Accepted a bounded documents window without sortBy.", sortby_err, open_source_step="a.4")
        pipe_c5b = [{"$setWindowFields": {"partitionBy": "$region",
                                          "output": {"movingSum": {"$sum": "$amount", "window": {"documents": [-1, 0]}}}}}]
        run_cmd(report, "c", "c.5b documents window [-1, 0] (bounded both ends) with no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c5b)}))",
                lambda: list(sales.aggregate(pipe_c5b)),
                "Accepted a [-1, 0] documents window without sortBy.", sortby_err, open_source_step=None)
        pipe_c6 = [{"$setWindowFields": {"partitionBy": "$region",
                                         "output": {"regionTotal": {"$sum": "$amount",
                                                                    "window": {"documents": ["unbounded", "unbounded"]}}}}},
                   {"$group": {"_id": "$region", "regionTotal": {"$first": "$regionTotal"}}}, {"$sort": {"_id": 1}}]
        run_cmd(report, "c", "c.6 documents window ['unbounded','unbounded'] with no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c6)}))",
                lambda: list(sales.aggregate(pipe_c6)),
                lambda out: f"Fully unbounded documents window without sortBy accepted: {jtxt(out)}.",
                sortby_err, open_source_step="a.5")
        pipe_c7 = [{"$setWindowFields": {"partitionBy": "$region", "output": {"regionTotal": {"$sum": "$amount"}}}},
                   {"$group": {"_id": "$region", "regionTotal": {"$first": "$regionTotal"}}}, {"$sort": {"_id": 1}}]
        run_cmd(report, "c", "c.7 output with no window and no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c7)}))",
                lambda: list(sales.aggregate(pipe_c7)),
                lambda out: f"No-window, no-sortBy output accepted: {jtxt(out)}.", sortby_err, open_source_step="a.6")
        pipe_c8 = [{"$setWindowFields": {"partitionBy": "$region",
                                         "output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}}}]
        run_cmd(report, "c", "c.8 range window ['unbounded','current'] with no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c8)}))",
                lambda: list(sales.aggregate(pipe_c8)),
                "Accepted a range window without sortBy.", sortby_err, open_source_step="a.7")
        pipe_c8b = [{"$setWindowFields": {"partitionBy": "$region",
                                          "output": {"t": {"$sum": "$amount", "window": {"range": [-1, 0]}}}}}]
        run_cmd(report, "c", "c.8b range window [-1, 0] with no sortBy",
                f"list(db.sales.aggregate({jtxt(pipe_c8b)}))",
                lambda: list(sales.aggregate(pipe_c8b)),
                "Accepted a numeric range window without sortBy.", sortby_err, open_source_step=None)
        pipe_c9 = [{"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1, "amount": 1},
                                         "output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}}}]
        run_cmd(report, "c", "c.9 range window ['unbounded','current'] with a compound sortBy {ts: 1, amount: 1}",
                f"list(db.sales.aggregate({jtxt(pipe_c9)}))",
                lambda: list(sales.aggregate(pipe_c9)),
                lambda out: f"Accepted a range window with a compound sortBy ({len(out)} rows).", sortby_err,
                open_source_step=None)
        pipe_c10 = [{"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": -1},
                                          "output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}}}]
        run_cmd(report, "c", "c.10 range window ['unbounded','current'] with a descending sortBy {ts: -1}",
                f"list(db.sales.aggregate({jtxt(pipe_c10)}))",
                lambda: list(sales.aggregate(pipe_c10)),
                lambda out: f"Accepted a range window with a descending sortBy ({len(out)} rows).", sortby_err,
                open_source_step=None)

        # ================= (d) allowDiskUse =================
        pipe_sort = [{"$sort": {"rnd": 1}},
                     {"$group": {"_id": None, "n": {"$sum": 1}, "firstRnd": {"$first": "$rnd"},
                                 "lastRnd": {"$last": "$rnd"}}}]
        for idx, flag in ((1, True), (2, False)):
            run_cmd(report, "d", f"d.{idx} aggregate full $sort on unindexed rnd over 50,000 docs, allowDiskUse={flag}",
                    f"list(db.big.aggregate({jtxt(pipe_sort)}, allowDiskUse={flag}))",
                    lambda flag=flag: list(big.aggregate(pipe_sort, allowDiskUse=flag)),
                    lambda out, flag=flag: (f"Accepted: sorted all {out[0]['n']} docs (firstRnd {out[0]['firstRnd']:.6f}, "
                                            f"lastRnd {out[0]['lastRnd']:.6f}) with allowDiskUse={flag}."),
                    lambda e, flag=flag: err_reading(e, f"allowDiskUse={flag} failed"), recorder=recorder,
                    open_source_step=f"b.{idx}")
        run_cmd(report, "d", "d.2b control: same aggregate with no allowDiskUse option",
                f"list(db.big.aggregate({jtxt(pipe_sort)}))",
                lambda: list(big.aggregate(pipe_sort)),
                lambda out: f"Without allowDiskUse the same pipeline returns n {out[0]['n']}, firstRnd {out[0]['firstRnd']:.6f}.",
                recorder=recorder, open_source_step=None)
        for sid, val, osid in (("d.3", "yes", "b.3"), ("d.3b", 1, None), ("d.3c", None, None)):
            raw = {"aggregate": "big", "pipeline": [{"$limit": 1}], "cursor": {}, "allowDiskUse": val}
            run_cmd(report, "d", f"{sid} raw aggregate command with allowDiskUse: {jtxt(val)} ({type(val).__name__})",
                    f"db.command({jtxt(raw)})",
                    lambda raw=raw: trim_cursor_reply(db.command(raw)),
                    lambda out, val=val: f"Accepted allowDiskUse {jtxt(val)}: the value is not type-checked.",
                    lambda e, val=val: err_reading(e, f"Rejected allowDiskUse {jtxt(val)}"),
                    open_source_step=osid)
        run_cmd(report, "d", "d.4 find().sort('rnd').limit(3) with allow_disk_use(True)",
                "list(db.big.find({}, {'_id': 0, 'rnd': 1}).sort('rnd', 1).limit(3).allow_disk_use(True))",
                lambda: list(big.find({}, {"_id": 0, "rnd": 1}).sort("rnd", 1).limit(3).allow_disk_use(True)),
                lambda out: f"find with allowDiskUse true accepted: {jtxt(out)}.",
                lambda e: err_reading(e, "find with allowDiskUse failed"), recorder=recorder,
                open_source_step="b.4")

        # ================= (e) drop =================
        t0 = time.time()
        client.drop_database(DB_NAME)
        dropped = True
        still_there = DB_NAME in client.list_database_names()
        report.add("e", "e.1 drop database mt_query and verify",
                   f"client.drop_database('{DB_NAME}'); '{DB_NAME}' in client.list_database_names()",
                   {"dropped": True, "mt_query_still_listed": still_there, "elapsed_ms": round((time.time() - t0) * 1000)},
                   "Database mt_query dropped; it is " + ("still listed." if still_there else "no longer listed."))
    except Exception as exc:  # record, then fall through to cleanup and report
        fatal = {"exception": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        print("FATAL: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
    finally:
        if not dropped:
            try:
                client.drop_database(DB_NAME)
                report.add("e", "e.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"dropped": True}, "Owned database dropped during cleanup.")
            except Exception as exc:  # noqa
                report.add("e", "e.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"exception": type(exc).__name__, "message": str(exc)},
                           "Cleanup drop failed; mt_query may still exist.")
        client.close()

    report_doc = {
        "test": "m-query",
        "database": DB_NAME,
        "started_utc": started,
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target": target,
        "cluster_context": ("Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus, "
                            "tier M30, one shard, server version 8.0, Premium SSD v2, HA disabled, public access with a "
                            "firewall rule for this Mac (as given in the task; not re-read from ARM by this test)."),
        "evidence_scope": ("Observations of the managed Azure DocumentDB service on 2026-11-25 at hello.maxWireVersion 25 and "
                           "hello.internal.documentdb_versions ['2.2-1','2.3.0','12.1-1'] (kind 'azuredocumentdb'). Other "
                           "tests ran against the same cluster in other databases at the same time, so elapsed times are "
                           "client-observed (about 80 ms round trip from this Mac) and only indicative."),
        "fatal_error": fatal,
        "config_changes": [],
        "steps": report.steps,
    }
    text = json.dumps(report_doc, indent=2, default=str)
    text = mask_text(text)
    leaked = any(s and s in text for s in secret_forms)
    for s in secret_forms:
        if s:
            text = text.replace(s, "<redacted>")
    if leaked:
        print("WARNING: a credential string was found in the report and redacted", file=sys.stderr)
    with open(REPORT_PATH, "w") as fh:
        fh.write(text)
    print(json.dumps({"steps": len(report.steps), "fatal": bool(fatal), "report": REPORT_PATH}))


if __name__ == "__main__":
    main()
