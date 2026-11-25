#!/usr/bin/env python
"""Engine test "query-behaviour" against a local documentdb-local container.

Owns database t_query only. Reads LOCAL_URI from ../local.env and never prints
or records the credentials. Writes report.json next to this script.

Sections:
  (a) $setWindowFields: chained stages, cumulative documents window, $group $last,
      window without sortBy
  (b) allowDiskUse true/false on a large unindexed $sort
  (c) explain('executionStats') shapes for find (no index / indexed), aggregate
      ($match/$sort) and a $search cosmosSearch pipeline on a vector-ivf index
  (d) find with maxTimeMS 1 over 200k documents
"""
import json
import os
import random
import re
import string
import sys
import time
import datetime as dt

from bson import json_util
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(HERE), "local.env")
REPORT_PATH = os.path.join(HERE, "report.json")
DB_NAME = "t_query"
BIG_N = 200_000


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


def redact_uri(uri):
    return re.sub(r"//[^@]*@", "//<redacted>@", uri)


def to_jsonable(obj):
    """bson-aware conversion so the report is plain JSON."""
    return json.loads(json_util.dumps(obj))


def error_record(exc):
    rec = {"exception": type(exc).__name__, "message": str(exc)}
    if isinstance(exc, OperationFailure):
        details = exc.details or {}
        rec["code"] = exc.code
        rec["codeName"] = details.get("codeName")
        rec["errmsg"] = details.get("errmsg")
        labels = details.get("errorLabels")
        if labels is None:
            try:
                labels = sorted(exc._error_labels) if exc._error_labels else None  # noqa
            except Exception:
                labels = None
        rec["errorLabels"] = labels
        rec["details"] = to_jsonable(details)
    return rec


class Report:
    def __init__(self):
        self.steps = []

    def add(self, section, step, command, response, reading, **extra):
        rec = {
            "section": section,
            "step": step,
            "command": command,
            "response": response,
            "reading": reading,
        }
        rec.update(extra)
        self.steps.append(rec)
        status = "ERROR" if isinstance(response, dict) and "exception" in response else "ok"
        print(f"[{section}] {step}: {status}", file=sys.stderr)
        return rec


def run_cmd(report, section, step, command_text, fn, reading_ok, reading_err=None, **extra):
    """Run fn(), record result or error."""
    t0 = time.time()
    try:
        out = fn()
        resp = to_jsonable(out)
        elapsed = round((time.time() - t0) * 1000)
        return report.add(section, step, command_text, resp,
                          reading_ok(out) if callable(reading_ok) else reading_ok,
                          elapsed_ms=elapsed, **extra)
    except PyMongoError as exc:
        resp = error_record(exc)
        elapsed = round((time.time() - t0) * 1000)
        reading = reading_err(exc) if callable(reading_err) else (
            reading_err or f"Failed with code {resp.get('code')} {resp.get('codeName')}: {resp.get('errmsg')}")
        return report.add(section, step, command_text, resp, reading, elapsed_ms=elapsed, **extra)


# ---------- explain helpers ----------

def collect_stage_names(node, acc=None):
    if acc is None:
        acc = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "stage" and isinstance(v, str):
                acc.append(v)
            collect_stage_names(v, acc)
    elif isinstance(node, list):
        for item in node:
            collect_stage_names(item, acc)
    return acc


def find_key_paths(node, key, path="", acc=None):
    if acc is None:
        acc = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if k == key:
                acc.append(p)
            find_key_paths(v, key, p, acc)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            find_key_paths(item, key, f"{path}[{i}]", acc)
    return acc


def summarize_explain(doc):
    d = to_jsonable(doc)
    summary = {
        "top_level_keys": sorted(d.keys()),
        "explainVersion": d.get("explainVersion"),
        "stage_names_in_order": collect_stage_names(d),
        "stage_names_unique": sorted(set(collect_stage_names(d))),
        "winningPlan_paths": find_key_paths(d, "winningPlan"),
        "executionStats_paths": find_key_paths(d, "executionStats"),
        "queryPlanner_paths": find_key_paths(d, "queryPlanner"),
        "has_COLLSCAN": "COLLSCAN" in collect_stage_names(d),
        "has_IXSCAN": "IXSCAN" in collect_stage_names(d),
        "has_SORT": "SORT" in collect_stage_names(d),
    }
    if "stages" in d and isinstance(d["stages"], list):
        summary["stages_array_keys"] = [sorted(s.keys()) if isinstance(s, dict) else str(type(s)) for s in d["stages"]]
    es = None
    for p in summary["executionStats_paths"][:1]:
        # resolve first executionStats
        cur = d
        for part in re.split(r"\.(?![^\[]*\])", p):
            m = re.match(r"([^\[]+)((\[\d+\])*)", part)
            cur = cur[m.group(1)]
            for idx in re.findall(r"\[(\d+)\]", m.group(2)):
                cur = cur[int(idx)]
        es = cur
    if isinstance(es, dict):
        summary["executionStats_top"] = {k: es.get(k) for k in
                                         ("nReturned", "executionTimeMillis", "totalKeysExamined", "totalDocsExamined",
                                          "executionSuccess") if k in es}
    return summary


def explain_step(report, db, step_id, label, explain_cmd, reading_prefix):
    cmd_text = f"db.command({json.dumps(to_jsonable(explain_cmd))})  # pymongo, database {DB_NAME}"

    def fn():
        return db.command(explain_cmd)

    t0 = time.time()
    try:
        out = fn()
        summary = summarize_explain(out)
        reading = (f"{reading_prefix}: top-level keys {summary['top_level_keys']}; stages seen {summary['stage_names_in_order']}; "
                   f"winningPlan at {summary['winningPlan_paths'] or 'nowhere'}.")
        report.add("c", f"{step_id} {label}", cmd_text,
                   {"summary": summary, "full_explain": to_jsonable(out)}, reading,
                   elapsed_ms=round((time.time() - t0) * 1000))
        return out
    except PyMongoError as exc:
        resp = error_record(exc)
        report.add("c", f"{step_id} {label}", cmd_text, resp,
                   f"{reading_prefix}: explain failed with code {resp.get('code')} {resp.get('codeName')}: {resp.get('errmsg')}",
                   elapsed_ms=round((time.time() - t0) * 1000))
        return None


# ---------- main ----------

def main():
    env = load_env(ENV_PATH)
    uri = env["LOCAL_URI"]
    report = Report()
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    build_info = to_jsonable(client.admin.command("buildInfo"))
    hello = to_jsonable(client.admin.command("hello"))
    db = client[DB_NAME]

    # clean slate for our own database only
    for coll in db.list_collection_names():
        db.drop_collection(coll)
    report.add("setup", "0.1 drop existing collections in t_query",
               f"for c in db.list_collection_names(): db.drop_collection(c)  # database {DB_NAME} only",
               {"ok": 1}, "Owned database reset; no other database touched.")

    # ===================== (a) $setWindowFields =====================
    sales = db["sales"]
    random.seed(7)
    docs = []
    base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    for region in ("east", "west", "north"):
        for i in range(8):
            docs.append({"region": region, "ts": base + dt.timedelta(days=i),
                         "amount": random.choice([5, 12, 3, 20, 7, 15, 1, 9]) + (i % 3)})
    sales.insert_many(docs)
    report.add("a", "a.0 seed sales collection",
               "db.sales.insert_many(24 docs: 3 regions x 8 days, fields region, ts (Date), amount)",
               {"inserted": len(docs)}, "Seed data for window-function tests.")

    cumulative = {"documents": ["unbounded", "current"]}

    # a.1 two chained $setWindowFields stages ($sum then $max), then $group with $last (the L08 shape)
    pipe_a1 = [
        {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                              "output": {"runningTotal": {"$sum": "$amount", "window": cumulative}}}},
        {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                              "output": {"runningMax": {"$max": "$amount", "window": cumulative}}}},
        {"$sort": {"region": 1, "ts": 1}},
        {"$group": {"_id": "$region", "finalTotal": {"$last": "$runningTotal"}, "finalMax": {"$last": "$runningMax"},
                    "lastTs": {"$last": "$ts"}, "n": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    expected = {}
    for region in ("east", "west", "north"):
        rs = sorted([d for d in docs if d["region"] == region], key=lambda d: d["ts"])
        expected[region] = {"finalTotal": sum(d["amount"] for d in rs), "finalMax": max(d["amount"] for d in rs)}

    def read_a1(out):
        got = {r["_id"]: {"finalTotal": r["finalTotal"], "finalMax": r["finalMax"]} for r in out}
        ok = got == expected
        return ("Two chained $setWindowFields stages with cumulative ['unbounded','current'] windows on $sum and $max followed by $group/$last ran; "
                + ("values match the client-side computation." if ok else f"values DIFFER from expected {expected}."))

    run_cmd(report, "a", "a.1 chained $setWindowFields ($sum, then $max) + $sort + $group $last",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a1))})",
            lambda: list(sales.aggregate(pipe_a1)), read_a1, expected=expected)

    # a.2 same, but WITHOUT the explicit $sort before $group (relies on window output order)
    pipe_a2 = [pipe_a1[0], pipe_a1[1], pipe_a1[3], pipe_a1[4]]
    run_cmd(report, "a", "a.2 chained $setWindowFields + $group $last with no intermediate $sort",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a2))})",
            lambda: list(sales.aggregate(pipe_a2)),
            lambda out: ("Ran without error; $last picked " +
                         ("the sortBy-last row in every partition (matches expected)." if
                          {r['_id']: {'finalTotal': r['finalTotal'], 'finalMax': r['finalMax']} for r in out} == expected
                          else f"rows that do not match expected {expected}, so $group order after $setWindowFields is not guaranteed.")),
            expected=expected)

    # a.3 single $setWindowFields with both $sum and $max in one output block
    pipe_a3 = [
        {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                              "output": {"runningTotal": {"$sum": "$amount", "window": cumulative},
                                         "runningMax": {"$max": "$amount", "window": cumulative}}}},
        {"$match": {"region": "east"}},
        {"$sort": {"ts": 1}},
        {"$project": {"_id": 0, "ts": 1, "amount": 1, "runningTotal": 1, "runningMax": 1}},
    ]

    def read_a3(out):
        running, mx, ok = 0, None, True
        for r in out:
            running += r["amount"]
            mx = r["amount"] if mx is None else max(mx, r["amount"])
            if r["runningTotal"] != running or r["runningMax"] != mx:
                ok = False
        return ("Single $setWindowFields with $sum and $max cumulative windows returned per-row running total and running max"
                + (" that match a client-side scan." if ok else " that DO NOT match a client-side scan."))

    run_cmd(report, "a", "a.3 one $setWindowFields stage with $sum and $max cumulative windows (east partition rows)",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a3))})",
            lambda: list(sales.aggregate(pipe_a3)), read_a3)

    # a.4 documents window WITHOUT sortBy -> expected engine error 'Missing sortBy field for document-based window'
    pipe_a4 = [{"$setWindowFields": {"partitionBy": "$region",
                                     "output": {"runningTotal": {"$sum": "$amount", "window": cumulative}}}}]
    run_cmd(report, "a", "a.4 cumulative documents window with no sortBy",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a4))})",
            lambda: list(sales.aggregate(pipe_a4)),
            "Engine accepted a bounded documents window without sortBy (unexpected given EnsureSortRequirements).",
            lambda e: f"Rejected as expected: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    # a.5 fully unbounded documents window without sortBy -> engine source says allowed
    pipe_a5 = [{"$setWindowFields": {"partitionBy": "$region",
                                     "output": {"regionTotal": {"$sum": "$amount", "window": {"documents": ["unbounded", "unbounded"]}}}}},
               {"$group": {"_id": "$region", "regionTotal": {"$first": "$regionTotal"}}}, {"$sort": {"_id": 1}}]
    run_cmd(report, "a", "a.5 ['unbounded','unbounded'] documents window with no sortBy",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a5))})",
            lambda: list(sales.aggregate(pipe_a5)),
            "Fully unbounded documents window without sortBy is accepted (only case EnsureSortRequirements allows).")

    # a.6 output with no window and no sortBy
    pipe_a6 = [{"$setWindowFields": {"partitionBy": "$region", "output": {"regionTotal": {"$sum": "$amount"}}}},
               {"$group": {"_id": "$region", "regionTotal": {"$first": "$regionTotal"}}}, {"$sort": {"_id": 1}}]
    run_cmd(report, "a", "a.6 output with no window and no sortBy",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a6))})",
            lambda: list(sales.aggregate(pipe_a6)),
            "No-window, no-sortBy output accepted (whole-partition aggregate).")

    # a.7 range window without sortBy
    pipe_a7 = [{"$setWindowFields": {"partitionBy": "$region",
                                     "output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}}}]
    run_cmd(report, "a", "a.7 range window ['unbounded','current'] with no sortBy",
            f"db.sales.aggregate({json.dumps(to_jsonable(pipe_a7))})",
            lambda: list(sales.aggregate(pipe_a7)),
            "Range window without sortBy accepted (unexpected).",
            lambda e: f"Rejected: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    # ===================== big collection (used by b, c, d) =====================
    big = db["big"]
    alphabet = string.ascii_lowercase
    rnd = random.Random(11)
    t0 = time.time()
    batch = []
    inserted = 0
    for i in range(BIG_N):
        batch.append({"i": i, "rnd": rnd.random(), "grp": i % 97,
                      "payload": "".join(rnd.choice(alphabet) for _ in range(120)),
                      "tags": [f"t{i % 13}", f"u{i % 7}"]})
        if len(batch) == 10_000:
            big.insert_many(batch, ordered=False)
            inserted += len(batch)
            batch = []
    if batch:
        big.insert_many(batch, ordered=False)
        inserted += len(batch)
    cnt = big.count_documents({})
    report.add("setup", "0.2 seed big collection",
               f"db.big.insert_many(...) in batches of 10000: {BIG_N} docs with fields i (int), rnd (double), grp (int), payload (120-char string), tags (array)",
               {"inserted": inserted, "count_documents": cnt, "elapsed_ms": round((time.time() - t0) * 1000)},
               "200k-document collection for the sort, explain and maxTimeMS tests.")

    # ===================== (b) allowDiskUse =====================
    pipe_sort = [{"$sort": {"rnd": 1}},
                 {"$group": {"_id": None, "n": {"$sum": 1}, "firstRnd": {"$first": "$rnd"}, "lastRnd": {"$last": "$rnd"}}}]
    for flag in (True, False):
        run_cmd(report, "b", f"b.{1 if flag else 2} aggregate full $sort on unindexed rnd over 200k docs, allowDiskUse={flag}",
                f"db.big.aggregate({json.dumps(pipe_sort)}, allowDiskUse={flag})",
                lambda flag=flag: list(big.aggregate(pipe_sort, allowDiskUse=flag)),
                lambda out: f"Accepted and completed: sorted all {out[0]['n']} docs (firstRnd {out[0]['firstRnd']:.6f}, lastRnd {out[0]['lastRnd']:.6f}); allowDiskUse={flag} raised no error.",
                lambda e, flag=flag: f"allowDiskUse={flag} failed: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    # b.3 raw command with allowDiskUse as a string (type check: is the option validated or ignored?)
    run_cmd(report, "b", "b.3 raw aggregate command with allowDiskUse: 'yes' (wrong BSON type)",
            "db.command({'aggregate': 'big', 'pipeline': [{'$limit': 1}], 'cursor': {}, 'allowDiskUse': 'yes'})",
            lambda: db.command({"aggregate": "big", "pipeline": [{"$limit": 1}], "cursor": {}, "allowDiskUse": "yes"}),
            "Accepted a non-boolean allowDiskUse: the option is not type-checked, consistent with it being in IgnoredCommonSpecFields.",
            lambda e: f"Rejected non-boolean allowDiskUse: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')} (so the field is at least type-validated).")

    # b.4 find with allowDiskUse (driver sends it as a find option)
    run_cmd(report, "b", "b.4 find().sort('rnd').limit(3) with allow_disk_use=True",
            "db.big.find({}, {'_id':0,'rnd':1}).sort('rnd', 1).limit(3).allow_disk_use(True)",
            lambda: list(big.find({}, {"_id": 0, "rnd": 1}).sort("rnd", 1).limit(3).allow_disk_use(True)),
            "find with allowDiskUse accepted.",
            lambda e: f"find with allowDiskUse failed: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    # ===================== (c) explain =====================
    # c.1 find, no index on rnd
    explain_step(report, db, "c.1", "find on unindexed field rnd (executionStats)",
                 {"explain": {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "verbosity": "executionStats"},
                 "find with no usable index")

    explain_step(report, db, "c.1b", "find on unindexed field region in the 24-doc sales collection (executionStats)",
                 {"explain": {"find": "sales", "filter": {"region": "east"}}, "verbosity": "executionStats"},
                 "find with no usable index on a tiny collection")

    explain_step(report, db, "c.1c", "find with empty filter {} on big (executionStats)",
                 {"explain": {"find": "big", "filter": {}}, "verbosity": "executionStats"},
                 "find with no filter")

    explain_step(report, db, "c.1d", "find equality on unindexed field grp on big (executionStats)",
                 {"explain": {"find": "big", "filter": {"grp": 5}}, "verbosity": "executionStats"},
                 "find equality with no usable index")

    # create index on i
    run_cmd(report, "c", "c.2 createIndex on big.i",
            "db.big.create_index([('i', ASCENDING)], name='i_1')",
            lambda: big.create_index([("i", ASCENDING)], name="i_1"),
            lambda out: f"Index {out} created on big.i.")

    explain_step(report, db, "c.3", "find on indexed field i (executionStats)",
                 {"explain": {"find": "big", "filter": {"i": 123456}}, "verbosity": "executionStats"},
                 "find on indexed field")

    explain_step(report, db, "c.3b", "find on indexed field i with range + sort on rnd (executionStats)",
                 {"explain": {"find": "big", "filter": {"i": {"$gt": 199000}}, "sort": {"rnd": -1}}, "verbosity": "executionStats"},
                 "find on indexed range with in-memory sort")

    # c.4 aggregate $match/$sort
    explain_step(report, db, "c.4", "aggregate $match (indexed i) + $sort (rnd) + $limit (executionStats)",
                 {"explain": {"aggregate": "big",
                              "pipeline": [{"$match": {"i": {"$gt": 199000}}}, {"$sort": {"rnd": -1}}, {"$limit": 10}],
                              "cursor": {}}, "verbosity": "executionStats"},
                 "aggregate with $match/$sort")

    explain_step(report, db, "c.4b", "aggregate $match (unindexed rnd) + $sort (i) (executionStats)",
                 {"explain": {"aggregate": "big",
                              "pipeline": [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"i": 1}}],
                              "cursor": {}}, "verbosity": "executionStats"},
                 "aggregate with unindexed $match and $sort")

    # c.5 vector: seed vec collection, create vector-ivf index, explain $search cosmosSearch
    vec = db["vec"]
    vrnd = random.Random(3)
    DIMS = 8
    vdocs = [{"k": i, "embedding": [vrnd.uniform(-1, 1) for _ in range(DIMS)], "cat": f"c{i % 4}"} for i in range(500)]
    vec.insert_many(vdocs)
    report.add("c", "c.5a seed vec collection", f"db.vec.insert_many(500 docs with 8-dim 'embedding' arrays)",
               {"inserted": len(vdocs)}, "Seed data for the vector index.")

    create_vec_idx = {"createIndexes": "vec",
                      "indexes": [{"name": "vec_ivf", "key": {"embedding": "cosmosSearch"},
                                   "cosmosSearchOptions": {"kind": "vector-ivf", "numLists": 2, "similarity": "COS", "dimensions": DIMS}}]}
    r = run_cmd(report, "c", "c.5b createIndexes cosmosSearch vector-ivf on vec.embedding",
                f"db.command({json.dumps(create_vec_idx)})",
                lambda: db.command(create_vec_idx),
                lambda out: ("vector-ivf index created; response is wrapped as raw.defaultShard: "
                             + json.dumps(to_jsonable(out.get('raw', {}).get('defaultShard', out)))),
                lambda e: f"vector-ivf index creation failed: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    qvec = [vrnd.uniform(-1, 1) for _ in range(DIMS)]
    search_pipe = [{"$search": {"cosmosSearch": {"vector": qvec, "path": "embedding", "k": 5}, "returnStoredSource": True}},
                   {"$project": {"_id": 0, "k": 1, "score": {"$meta": "searchScore"}}}]
    # sanity run first
    run_cmd(report, "c", "c.5c run the $search cosmosSearch pipeline (sanity)",
            f"db.vec.aggregate({json.dumps(search_pipe)})",
            lambda: list(vec.aggregate(search_pipe)),
            lambda out: f"$search cosmosSearch returned {len(out)} rows with searchScore.",
            lambda e: f"$search cosmosSearch failed: code {e.code} {(e.details or {}).get('codeName')}: {(e.details or {}).get('errmsg')}")

    explain_step(report, db, "c.5d", "explain $search cosmosSearch pipeline on vector-ivf index (executionStats)",
                 {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}}, "verbosity": "executionStats"},
                 "aggregate with $search cosmosSearch on vector-ivf")

    explain_step(report, db, "c.5e", "explain $search cosmosSearch pipeline (queryPlanner verbosity)",
                 {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}}, "verbosity": "queryPlanner"},
                 "aggregate with $search cosmosSearch, queryPlanner verbosity")

    # c.6 explain via the driver helper form (explain as a find option) to show the second entry point
    explain_step(report, db, "c.6", "explain the chained $setWindowFields pipeline (executionStats)",
                 {"explain": {"aggregate": "sales", "pipeline": pipe_a1, "cursor": {}}, "verbosity": "executionStats"},
                 "aggregate with two $setWindowFields stages")

    # ===================== (d) maxTimeMS =====================
    slow_filter = {"$and": [{"payload": {"$regex": "q.*z.*q.*z"}}, {"rnd": {"$lt": 0.5}},
                            {"$expr": {"$gt": [{"$strLenCP": "$payload"}, 119]}}]}

    # baseline timing without maxTimeMS
    run_cmd(report, "d", "d.0 baseline: same predicate with no maxTimeMS (count via find)",
            f"len(list(db.big.find({json.dumps(slow_filter)}, {{'_id': 1}})))",
            lambda: {"matched": len(list(big.find(slow_filter, {"_id": 1})))},
            lambda out: f"Predicate scans all 200k docs without a time limit and matched {out['matched']} docs; elapsed_ms is the baseline.")

    def read_d_err(e):
        d = e.details or {}
        return (f"maxTimeMS expired: code {e.code} {d.get('codeName')}: {d.get('errmsg')}; errorLabels={d.get('errorLabels')}. "
                + ("This is MongoDB code 50 MaxTimeMSExpired." if e.code == 50 else "NOT code 50; a different code is used."))

    run_cmd(report, "d", "d.1 find with max_time_ms=1 on the slow predicate",
            f"list(db.big.find({json.dumps(slow_filter)}, {{'_id': 1}}).max_time_ms(1))",
            lambda: {"matched": len(list(big.find(slow_filter, {"_id": 1}).max_time_ms(1)))},
            lambda out: f"Unexpectedly completed within maxTimeMS 1, matched {out['matched']} docs.",
            read_d_err)

    run_cmd(report, "d", "d.2 raw find command with maxTimeMS: 1",
            f"db.command({{'find': 'big', 'filter': {json.dumps(slow_filter)}, 'projection': {{'_id': 1}}, 'maxTimeMS': 1}})",
            lambda: db.command({"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "maxTimeMS": 1}),
            lambda out: f"Raw find with maxTimeMS 1 returned a first batch of {len(out['cursor']['firstBatch'])} docs (cursor id {out['cursor']['id']}) without error.",
            read_d_err)

    run_cmd(report, "d", "d.3 aggregate with maxTimeMS=1 on the slow predicate",
            f"list(db.big.aggregate([{{'$match': {json.dumps(slow_filter)}}}, {{'$count': 'n'}}], maxTimeMS=1))",
            lambda: list(big.aggregate([{"$match": slow_filter}, {"$count": "n"}], maxTimeMS=1)),
            lambda out: f"Unexpectedly completed within maxTimeMS 1: {out}.",
            read_d_err)

    run_cmd(report, "d", "d.4 count_documents with maxTimeMS=1 on the slow predicate",
            f"db.big.count_documents({json.dumps(slow_filter)}, maxTimeMS=1)",
            lambda: {"count": big.count_documents(slow_filter, maxTimeMS=1)},
            lambda out: f"Unexpectedly completed within maxTimeMS 1: {out}.",
            read_d_err)

    run_cmd(report, "d", "d.5 control: find with max_time_ms=120000 on the slow predicate",
            f"len(list(db.big.find({json.dumps(slow_filter)}, {{'_id': 1}}).max_time_ms(120000)))",
            lambda: {"matched": len(list(big.find(slow_filter, {"_id": 1}).max_time_ms(120000)))},
            lambda out: f"With a generous maxTimeMS the same query completes and matches {out['matched']} docs; compare with d.1.")

    # d.6 predicate that matches nothing: the find command itself must scan all 200k docs before the first batch
    none_filter = {"payload": {"$regex": "zzzzzzzzzz"}, "$expr": {"$gt": [{"$strLenCP": "$payload"}, 119]}}
    run_cmd(report, "d", "d.6 find with max_time_ms=1, predicate matching nothing (full scan before first batch)",
            f"list(db.big.find({json.dumps(none_filter)}, {{'_id': 1}}).max_time_ms(1))",
            lambda: {"matched": len(list(big.find(none_filter, {"_id": 1}).max_time_ms(1)))},
            lambda out: f"Completed without error despite maxTimeMS 1 and a full scan; matched {out['matched']} docs.",
            read_d_err)

    run_cmd(report, "d", "d.6b control: same predicate, no maxTimeMS",
            f"list(db.big.find({json.dumps(none_filter)}, {{'_id': 1}}))",
            lambda: {"matched": len(list(big.find(none_filter, {"_id": 1})))},
            lambda out: f"Baseline for d.6: matched {out['matched']} docs; elapsed_ms is the unbounded scan time.")

    # d.7 unindexed sort forces full materialisation before the first batch
    run_cmd(report, "d", "d.7 find with max_time_ms=1 and sort on unindexed rnd, limit 5",
            f"list(db.big.find({json.dumps(slow_filter)}, {{'_id': 1}}).sort('rnd', 1).limit(5).max_time_ms(1))",
            lambda: {"rows": len(list(big.find(slow_filter, {"_id": 1}).sort("rnd", 1).limit(5).max_time_ms(1)))},
            lambda out: f"Completed without error despite maxTimeMS 1 and an in-memory sort of the matches; rows {out['rows']}.",
            read_d_err)

    # d.8 small batches: does a getMore ever fail?
    def d8():
        cur = big.find(slow_filter, {"_id": 1}).max_time_ms(1).batch_size(50)
        n = 0
        try:
            for _ in cur:
                n += 1
        except PyMongoError as exc:
            return {"docs_before_error": n, "error": error_record(exc)}
        return {"docs_before_error": None, "total": n, "error": None}

    run_cmd(report, "d", "d.8 find with max_time_ms=1, batch_size=50, iterate all getMores",
            f"for d in db.big.find({json.dumps(slow_filter)}, {{'_id': 1}}).max_time_ms(1).batch_size(50): ...",
            d8,
            lambda out: (f"No getMore failed; iterated {out['total']} docs with maxTimeMS 1 (pymongo does not send maxTimeMS on non-tailable getMore)."
                         if out["error"] is None else
                         f"Failed after {out['docs_before_error']} docs with code {out['error'].get('code')} {out['error'].get('codeName')}: {out['error'].get('errmsg')}."))

    # d.9 raw find with singleBatch and a huge batchSize: the whole scan happens inside the find command
    raw_find = {"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "singleBatch": True, "batchSize": 1_000_000, "maxTimeMS": 1}
    run_cmd(report, "d", "d.9 raw find command, singleBatch true, batchSize 1e6, maxTimeMS 1",
            f"db.command({json.dumps(raw_find)})",
            lambda: {"firstBatch_len": len(db.command(raw_find)["cursor"]["firstBatch"])},
            lambda out: f"Returned {out['firstBatch_len']} docs in one batch without error despite maxTimeMS 1.",
            read_d_err)

    # d.10 getMore carrying maxTimeMS on a non-tailable cursor
    def d10():
        first = db.command({"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "batchSize": 10})
        cid = first["cursor"]["id"]
        out = db.command({"getMore": cid, "collection": "big", "batchSize": 1_000_000, "maxTimeMS": 1})
        return {"cursor_id": cid, "nextBatch_len": len(out["cursor"]["nextBatch"]), "cursor_id_after": out["cursor"]["id"]}

    run_cmd(report, "d", "d.10 raw getMore with maxTimeMS 1 on a non-tailable find cursor",
            "first = db.command({'find':'big','filter':<slow_filter>,'projection':{'_id':1},'batchSize':10}); "
            "db.command({'getMore': first.cursor.id, 'collection':'big', 'batchSize':1000000, 'maxTimeMS':1})",
            d10,
            lambda out: f"getMore accepted maxTimeMS 1 and returned {out['nextBatch_len']} docs without a timeout error.",
            read_d_err)

    # d.11 aggregate with a slightly larger maxTimeMS to confirm the limit scales (should still fail at 1ms-level, pass at 60000)
    run_cmd(report, "d", "d.11 control: aggregate $match + $count with maxTimeMS=60000",
            f"list(db.big.aggregate([{{'$match': {json.dumps(slow_filter)}}}, {{'$count': 'n'}}], maxTimeMS=60000))",
            lambda: list(big.aggregate([{"$match": slow_filter}, {"$count": "n"}], maxTimeMS=60000)),
            lambda out: f"Aggregate with a generous maxTimeMS completes: {to_jsonable(out)}; d.3's failure is the 1 ms limit, not the pipeline.")

    # ===================== report =====================
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    report_doc = {
        "test": "query-behaviour",
        "database": DB_NAME,
        "started_utc": started,
        "finished_utc": finished,
        "target": {
            "container": "ddb-engine-test (documentdb-local, ghcr.io/documentdb/documentdb/documentdb-local:latest)",
            "uri_redacted": redact_uri(uri),
            "driver": "pymongo " + __import__("pymongo").version,
            "buildInfo": build_info,
            "hello": hello,
        },
        "evidence_scope": ("Every observation below was made on the documentdb-local container at the version reported in target.buildInfo. "
                           "It is evidence about the open-source engine and gateway at that version only and does not prove managed Azure DocumentDB behaviour."),
        "decisions_context": {
            "source": "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/DECISIONS.md, topic 10 (Schema validation, TTL, indexing and query behaviour)",
            "open_question_2": "Does the exact L08 example (two chained $setWindowFields stages with a cumulative documents ['unbounded','current'] window on $sum and $max, followed by $group with $last) run? -> section a",
            "settled_allowDiskUse_noop": "allowDiskUse is in IgnoredCommonSpecFields (engine_source) -> section b checks acceptance",
            "open_question_3": "Explain layout for a cosmosSearch pipeline and whether COLLSCAN/SORT stage names appear -> section c.5",
            "settled_COLLSCAN_layout": "COLLSCAN check works if the walker descends into stages[].$cursor -> section c",
            "settled_120s_default": "120 s default query limit, maxTimeMS overrides -> section d records the error code when maxTimeMS 1 expires",
        },
        "steps": report.steps,
    }
    with open(REPORT_PATH, "w") as fh:
        json.dump(report_doc, fh, indent=2, default=str)
    print(f"report written: {REPORT_PATH}", file=sys.stderr)
    print(json.dumps({"steps": len(report.steps), "report": REPORT_PATH}))


if __name__ == "__main__":
    main()
