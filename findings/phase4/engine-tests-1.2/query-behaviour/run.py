#!/usr/bin/env python
"""Engine test "query-behaviour", ENGINE 1.2.0 RERUN, against the documentdb-local container.

Rerun of findings/phase4/engine-tests/query-behaviour/run.py (engine 0.117.0) against container
ddb-engine-test (image ghcr.io/documentdb/documentdb/documentdb-local:pg17-1.2.0), with 100,000
documents instead of 200,000 to spare the Docker VM disk.

Owns database t_query only and drops it at the end. Reads LOCAL_URI from local.env and never prints
or records the credentials. Writes report.json next to this script, then finalize.py adds the
comparison with the 0.117 report and the conclusions.

Sections
  (a) $setWindowFields: the exact L08 example (two chained stages with cumulative documents
      ['unbounded','current'] windows on $sum and $max, then $set and $group with $last), the 0.117
      variants on the same sales data, and the sortBy-required cases.
  (b) allowDiskUse true / false / omitted / non-boolean on aggregate and find, including a sort whose
      key data exceeds MongoDB's 100 MB blocking-sort limit, with explain of that sort.
  (c) explain executionStats shapes: unindexed find (several shapes), indexed find, aggregate
      $match/$sort, a $search cosmosSearch pipeline on a vector-ivf index, and the window pipelines.
  (d) maxTimeMS 1 on find and aggregate, consuming every cursor so getMore runs, with wire-level
      command monitoring of find / aggregate / getMore / killCursors.
  (e) plan stability after the bulk load: the unindexed explains run right after seeding and again after a
      poll that waits (up to 150 s) for the planner's choice to change; maxTimeMS 1 first-batch probes before and after.
Execution order: a, seed, c (unindexed, right after the load), e, c (unindexed again), b, c (indexed, vector,
windows), d.

Rerun: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python run.py
"""
import datetime as dt
import json
import math
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
import traceback

import pymongo
from bson import json_util
from pymongo import ASCENDING, MongoClient, monitoring
from pymongo.errors import OperationFailure, PyMongoError

SCRATCH = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad"
ENV_PATH = os.environ.get("LOCAL_ENV", os.path.join(SCRATCH, "engine-tests", "local.env"))
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(HERE, "report.json")
DB_NAME = "t_query"
BIG_N = 100_000
CONTAINER = "ddb-engine-test"
CUM = {"documents": ["unbounded", "current"]}


# ----------------------------------------------------------------------------- utilities

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def J(obj):
    """bson-aware conversion to plain JSON-able data (relaxed Extended JSON)."""
    return json.loads(json_util.dumps(obj))


def JS(obj):
    return json_util.dumps(obj)


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
    return re.sub(r"//[^@/]*@", "//<redacted>@", uri)


def error_record(exc):
    rec = {"outcome": "error", "exception": f"{type(exc).__module__}.{type(exc).__name__}"}
    if isinstance(exc, OperationFailure):
        d = exc.details or {}
        rec["code"] = exc.code
        rec["codeName"] = d.get("codeName")
        rec["errmsg"] = d.get("errmsg", str(exc))
        rec["errorLabels"] = d.get("errorLabels")  # None means the server reply carried no errorLabels field
        drv = sorted(getattr(exc, "_error_labels", None) or [])
        if drv:
            rec["driver_error_labels"] = drv
        rec["server_reply"] = J(d)
    else:
        rec["message"] = str(exc)
    return rec


def err_text(e):
    labels = e.get("errorLabels")
    return (f"code {e.get('code')} {e.get('codeName')}: '{e.get('errmsg') or e.get('message')}'"
            + (f" with errorLabels {labels}" if labels else " with no errorLabels"))


def num_close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-9)
    return a == b


def docs_close(got, exp, keys):
    return all(num_close(got.get(k), exp.get(k)) for k in keys)


# ----------------------------------------------------------------------------- wire monitoring

class WireLog(monitoring.CommandListener):
    WATCH = {"find", "getMore", "aggregate", "killCursors", "count", "explain"}

    def __init__(self):
        self.events = None

    def start(self):
        self.events = []

    def stop(self):
        ev, self.events = self.events, None
        return ev or []

    def started(self, event):
        if self.events is None or event.command_name not in self.WATCH:
            return
        cmd = event.command
        rec = {"event": "started", "command": event.command_name, "request_id": event.request_id,
               "sent_fields": [k for k in cmd.keys() if k not in ("lsid", "$clusterTime", "$db", "$readPreference")]}
        for k in ("maxTimeMS", "batchSize", "allowDiskUse", "getMore", "collection", "limit"):
            if k in cmd:
                rec[k] = J(cmd[k])
        if "cursor" in cmd and isinstance(cmd["cursor"], dict):
            rec["cursor_option"] = J(cmd["cursor"])
        self.events.append(rec)

    def succeeded(self, event):
        if self.events is None or event.command_name not in self.WATCH:
            return
        reply = event.reply
        rec = {"event": "succeeded", "command": event.command_name, "request_id": event.request_id,
               "duration_ms": round(event.duration_micros / 1000.0, 3), "ok": reply.get("ok")}
        cur = reply.get("cursor")
        if isinstance(cur, dict):
            batch = cur.get("firstBatch", cur.get("nextBatch"))
            rec["cursor_id"] = J(cur.get("id"))
            rec["batch_len"] = len(batch) if batch is not None else None
        self.events.append(rec)

    def failed(self, event):
        if self.events is None or event.command_name not in self.WATCH:
            return
        f = event.failure if isinstance(event.failure, dict) else {"failure": str(event.failure)}
        rec = {"event": "failed", "command": event.command_name, "request_id": event.request_id,
               "duration_ms": round(event.duration_micros / 1000.0, 3),
               "code": f.get("code"), "codeName": f.get("codeName"), "errmsg": f.get("errmsg"),
               "errorLabels": f.get("errorLabels"), "server_reply": J(f)}
        self.events.append(rec)


WIRE = WireLog()


def wire_summary(events):
    started = [e for e in events if e["event"] == "started"]
    initial = [e for e in started if e["command"] in ("find", "aggregate", "count")]
    getmores = [e for e in started if e["command"] == "getMore"]
    fails = [e for e in events if e["event"] == "failed"]
    out = {
        "initial_commands": [e["command"] for e in initial],
        "initial_maxTimeMS": [e.get("maxTimeMS") for e in initial],
        "getMore_count": len(getmores),
        "getMore_maxTimeMS_values": sorted({json.dumps(e.get("maxTimeMS")) for e in getmores}),
        "killCursors_count": sum(1 for e in started if e["command"] == "killCursors"),
        "batch_lens": [e.get("batch_len") for e in events
                       if e["event"] == "succeeded" and e["command"] in ("find", "aggregate", "getMore")],
        "server_round_trips_ms": [e.get("duration_ms") for e in events
                                  if e["event"] in ("succeeded", "failed")
                                  and e["command"] in ("find", "aggregate", "getMore", "count")],
        "failed_commands": [{k: f.get(k) for k in ("command", "code", "codeName", "errmsg", "errorLabels")} for f in fails],
    }
    gm_ids = [e["request_id"] for e in getmores]
    for f in fails:
        if f["command"] == "getMore" and f["request_id"] in gm_ids:
            out.setdefault("failed_getMore_index", []).append(gm_ids.index(f["request_id"]) + 1)
    return out


# ----------------------------------------------------------------------------- report

class Report:
    def __init__(self):
        self.steps = []

    def add(self, section, sid, title, command, response, reading, **extra):
        rec = {"section": section, "id": sid, "step": f"{sid} {title}", "command": command,
               "response": response, "reading": reading}
        rec.update({k: v for k, v in extra.items() if v is not None})
        self.steps.append(rec)
        print(f"[{sid}] {reading}", file=sys.stderr, flush=True)
        return rec

    def get(self, sid):
        for s in self.steps:
            if s["id"] == sid:
                return s
        return None


def run(report, section, sid, title, command, fn, ok_reading, err_reading=None, checks=None, wire=False, **extra):
    if wire:
        WIRE.start()
    t0 = time.perf_counter()
    value, err = None, None
    try:
        value = fn()
    except PyMongoError as exc:
        err = error_record(exc)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    events = WIRE.stop() if wire else None
    if err is None:
        response = {"outcome": "ok", "result": J(value)}
        reading = ok_reading(value) if callable(ok_reading) else ok_reading
        chk = checks(value) if checks else None
    else:
        response = err
        if err_reading is None:
            reading = f"{title} failed with {err_text(err)}."
        else:
            reading = err_reading(err) if callable(err_reading) else err_reading
        chk = None
    if events is not None:
        extra["wire_summary"] = wire_summary(events)
        extra["wire_events"] = events
    return report.add(section, sid, title, command, response, reading, elapsed_ms=elapsed, checks=chk, **extra)


def attempts_step(report, section, sid, title, command, call, iterate=True, attempts=3, **extra):
    """Run call() `attempts` times; when iterate is True the returned cursor is consumed completely,
    so every getMore runs. Wire events are captured per attempt."""
    results = []
    for a in range(attempts):
        WIRE.start()
        t0 = time.perf_counter()
        n, err, value, cur = 0, None, None, None
        try:
            cur = call()
            if iterate:
                for _ in cur:
                    n += 1
            else:
                value = cur
        except PyMongoError as exc:
            err = error_record(exc)
        finally:
            if iterate and cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        events = WIRE.stop()
        res = {"attempt": a + 1, "completed": err is None, "elapsed_ms": elapsed}
        if iterate:
            res["consumed_docs"] = n
        else:
            res["value"] = J(value)
        if err:
            res["error"] = err
        res["wire_summary"] = wire_summary(events)
        res["wire_events"] = events
        results.append(res)
    fails = [r for r in results if not r["completed"]]
    codes = sorted({(r["error"].get("code"), r["error"].get("codeName")) for r in fails}, key=str)
    response = {"outcome": "error" if fails else "ok",
                "attempts_total": attempts, "attempts_failed": len(fails),
                "error_codes": [{"code": c, "codeName": n} for c, n in codes],
                "attempts": results}
    reading = attempts_reading(title, results, iterate)
    return report.add(section, sid, title, command, response, reading, **extra)


def attempts_reading(label, results, iterate):
    n = len(results)
    fails = [r for r in results if not r["completed"]]
    oks = [r for r in results if r["completed"]]
    parts = []
    if oks:
        r0 = oks[0]
        ws = r0["wire_summary"]
        what = (f"consuming {r0['consumed_docs']} documents" if iterate else f"returning {JS(r0.get('value'))}")
        gm = ", ".join(ws["getMore_maxTimeMS_values"]) or "none sent"
        parts.append(f"{len(oks)}/{n} attempts completed with no error, {what} via "
                     f"{'+'.join(ws['initial_commands']) or 'no initial command'} and {ws['getMore_count']} getMore "
                     f"(maxTimeMS on getMore: {gm}) in {', '.join(str(r['elapsed_ms']) for r in oks)} ms")
    if fails:
        f0 = fails[0]
        e = f0["error"]
        ws = f0["wire_summary"]
        fc = ws["failed_commands"][0]["command"] if ws["failed_commands"] else "an unmonitored command"
        if fc == "getMore" and ws.get("failed_getMore_index"):
            fc = f"getMore #{ws['failed_getMore_index'][0]}"
        what = f" after {f0['consumed_docs']} documents" if iterate else ""
        parts.append(f"{len(fails)}/{n} attempts failed on {fc}{what} with {err_text(e)}")
    return f"{label}: " + "; ".join(parts) + "."


# ----------------------------------------------------------------------------- explain helpers

SCALAR = (str, int, float, bool, type(None))


def plan_nodes(node, path="", acc=None):
    if acc is None:
        acc = []
    if isinstance(node, dict):
        if isinstance(node.get("stage"), str):
            n = {"path": path or "$"}
            for k, v in node.items():
                if isinstance(v, SCALAR):
                    n[k] = v
                elif k in ("runtimeFilterSet", "indexFilterSet", "sortKey", "cosmosSearchCustomParams"):
                    n[k] = v
            acc.append(n)
        for k, v in node.items():
            plan_nodes(v, f"{path}.{k}" if path else k, acc)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            plan_nodes(v, f"{path}[{i}]", acc)
    return acc


def key_paths(node, key, path="", acc=None):
    if acc is None:
        acc = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if k == key:
                acc.append(p)
            key_paths(v, key, p, acc)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            key_paths(v, key, f"{path}[{i}]", acc)
    return acc


def first_value(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            r = first_value(v, key)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = first_value(v, key)
            if r is not None:
                return r
    return None


def summarize_explain(doc):
    d = J(doc)
    nodes = plan_nodes(d)
    qp = [n for n in nodes if "executionStats" not in n["path"]]
    ex = [n for n in nodes if "executionStats" in n["path"]]
    s = {
        "top_level_keys": sorted(d.keys()),
        "explainVersion": d.get("explainVersion"),
        "winningPlan_paths": key_paths(d, "winningPlan"),
        "executionStats_paths": key_paths(d, "executionStats"),
        "plan_stage_names": [n["stage"] for n in qp],
        "execution_stage_names": [n["stage"] for n in ex],
        "all_stage_names_unique": sorted({n["stage"] for n in nodes}),
        "has_COLLSCAN": any(n["stage"] == "COLLSCAN" for n in nodes),
        "has_SORT": any(n["stage"] == "SORT" for n in nodes),
        "index_names_used": sorted({n["indexName"] for n in nodes if "indexName" in n}),
    }
    if isinstance(d.get("stages"), list):
        s["stages_array_keys"] = [sorted(st.keys()) if isinstance(st, dict) else str(type(st)) for st in d["stages"]]
    es = first_value(d, "executionStats")
    if isinstance(es, dict):
        s["first_executionStats"] = {k: es.get(k) for k in ("nReturned", "executionTimeMillis", "totalKeysExamined",
                                                           "totalDocsExamined") if k in es}
    s["chain"] = chain_text(nodes)
    exn = [n["totalDocsExamined"] for n in ex if isinstance(n.get("totalDocsExamined"), (int, float))]
    if exn:
        s["max_node_totalDocsExamined"] = max(exn)
    rf = [n["totalDocsRemovedByRuntimeFilter"] for n in ex
          if isinstance(n.get("totalDocsRemovedByRuntimeFilter"), (int, float))]
    if rf:
        s["max_node_totalDocsRemovedByRuntimeFilter"] = max(rf)
    csp = [n["cosmosSearchCustomParams"] for n in qp if n.get("cosmosSearchCustomParams")]
    if csp:
        s["cosmosSearchCustomParams"] = csp[0]
    loops = [n for n in ex if isinstance(n.get("actualLoops"), int) and n["actualLoops"] > 1]
    s["parallel"] = bool(loops) or any(n["stage"].startswith("PARALLEL") for n in nodes)
    if loops:
        s["max_actualLoops"] = max(n["actualLoops"] for n in loops)
        tot = [n["totalDocsExamined"] * n["actualLoops"] for n in loops if isinstance(n.get("totalDocsExamined"), (int, float))]
        if tot:
            s["max_node_totalDocsExamined_x_actualLoops"] = max(tot)
    ic = first_value(d, "indexCosts")
    if isinstance(ic, list) and ic and isinstance(ic[0], dict) and ic[0].get("costs"):
        c0 = ic[0]["costs"][0]
        s["indexCosts_first"] = {k: c0.get(k) for k in ("indexName", "estimatedTotalIndexEntries", "selectivity",
                                                       "correlation") if k in c0}
    s["nodes"] = nodes
    return s


def chain_text(nodes):
    parts, order = {}, []
    for n in nodes:
        if "executionStats" in n["path"]:
            continue
        m = re.match(r"stages\[(\d+)\]\.(\$\w+)", n["path"])
        key = f"stages[{m.group(1)}].{m.group(2)}" if m else ""
        if key not in parts:
            parts[key] = []
            order.append(key)
        label = n["stage"]
        if "indexName" in n:
            label += f"({n['indexName']}{', bitmap' if n.get('isBitmap') else ''})"
        if "runtimeFilterSet" in n:
            label += "[runtimeFilter]"
        parts[key].append(label)
    return "; ".join((f"{k}: " if k else "") + " > ".join(parts[k]) for k in order)


def explain_step(report, section, sid, title, db, explain_cmd, what, **extra):
    def fn():
        out = db.command(explain_cmd)
        return {"summary": summarize_explain(out), "full_explain": J(out)}

    def ok(out):
        s = out["summary"]
        fe = s.get("first_executionStats", {})
        tde = fe.get("totalDocsExamined")
        if fe:
            tail = f"; first executionStats totalDocsExamined {tde} for nReturned {fe.get('nReturned')}"
            mx = s.get("max_node_totalDocsExamined")
            if mx is not None and mx != tde:
                tail += f", while a deeper execution node examined {mx}"
            rf = s.get("max_node_totalDocsRemovedByRuntimeFilter")
            if rf:
                tail += f", with {rf} removed by the runtime filter"
            if s.get("max_actualLoops"):
                tail += (f" (parallel plan: node counts are per-loop averages over actualLoops {s['max_actualLoops']}, "
                         f"about {s.get('max_node_totalDocsExamined_x_actualLoops')} documents in total)")
        else:
            tail = "; no executionStats in this verbosity"
        return (f"{what}: plan {s['chain']}; COLLSCAN {'appears' if s['has_COLLSCAN'] else 'does not appear'}{tail}.")

    return run(report, section, sid, title, f"db.command({JS(explain_cmd)})  # database {DB_NAME}", fn, ok,
               checks=lambda out: {"has_COLLSCAN": out["summary"]["has_COLLSCAN"],
                                   "all_stage_names_unique": out["summary"]["all_stage_names_unique"],
                                   "index_names_used": out["summary"]["index_names_used"],
                                   "first_executionStats": out["summary"].get("first_executionStats"),
                                   "max_node_totalDocsExamined": out["summary"].get("max_node_totalDocsExamined"),
                                   "max_node_totalDocsRemovedByRuntimeFilter":
                                       out["summary"].get("max_node_totalDocsRemovedByRuntimeFilter"),
                                   "parallel": out["summary"].get("parallel"),
                                   "indexCosts_first": out["summary"].get("indexCosts_first")},
               **extra)


# ----------------------------------------------------------------------------- data

def make_sales_docs():
    rng = random.Random(7)  # identical sequence to random.seed(7) + random.choice(...) in the 0.117 run
    docs = []
    base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    for region in ("east", "west", "north"):
        for i in range(8):
            docs.append({"region": region, "ts": base + dt.timedelta(days=i),
                         "amount": rng.choice([5, 12, 3, 20, 7, 15, 1, 9]) + (i % 3)})
    return docs


TRADE_PNL = {
    "momentum-1": [120.0, -45.5, 80.25, -200.0, 35.0, -15.0, 60.0, -90.0, 150.0, -30.0, 10.0, -5.0],
    "mean-revert-2": [-20.0, 40.0, -60.0, 25.0, 5.0, -35.0, 70.0, -10.0],
}


def make_trade_docs():
    tbase = dt.datetime(2026, 3, 2, 14, 30, tzinfo=dt.timezone.utc)
    docs = []
    for off, (sid, pnls) in enumerate(TRADE_PNL.items()):
        for k, p in enumerate(pnls):
            docs.append({"strategyId": sid, "closedAt": tbase + dt.timedelta(hours=3 * k + off), "pnl": p, "seq": k})
    return docs


def l08_rows(docs, strategy):
    rows = sorted([d for d in docs if d["strategyId"] == strategy], key=lambda d: d["closedAt"])
    out, cum, peak = [], 0.0, None
    for d in rows:
        cum += d["pnl"]
        peak = cum if peak is None else max(peak, cum)
        out.append({"seq": d["seq"], "pnl": d["pnl"], "cumulativePnl": cum, "runningPeak": peak, "drawdown": peak - cum})
    return out


def l08_group(docs, strategy):
    rows = l08_rows(docs, strategy)
    return {"_id": strategy, "maxDrawdown": max(r["drawdown"] for r in rows), "finalPnl": rows[-1]["cumulativePnl"]}


L08 = [
    {"$match": {"strategyId": "momentum-1"}},
    {"$setWindowFields": {"partitionBy": "$strategyId", "sortBy": {"closedAt": 1},
                          "output": {"cumulativePnl": {"$sum": "$pnl", "window": {"documents": ["unbounded", "current"]}}}}},
    {"$setWindowFields": {"partitionBy": "$strategyId", "sortBy": {"closedAt": 1},
                          "output": {"runningPeak": {"$max": "$cumulativePnl", "window": {"documents": ["unbounded", "current"]}}}}},
    {"$set": {"drawdown": {"$subtract": ["$runningPeak", "$cumulativePnl"]}}},
    {"$sort": {"closedAt": 1}},
    {"$group": {"_id": "$strategyId", "maxDrawdown": {"$max": "$drawdown"}, "finalPnl": {"$last": "$cumulativePnl"}}},
]

L08_JS = """db.trades.aggregate([
  { $match: { strategyId: "momentum-1" } },
  { $setWindowFields: { partitionBy: "$strategyId", sortBy: { closedAt: 1 },
      output: { cumulativePnl: { $sum: "$pnl", window: { documents: ["unbounded", "current"] } } } } },
  // separate stage: an output can't reference another output of the same stage
  { $setWindowFields: { partitionBy: "$strategyId", sortBy: { closedAt: 1 },
      output: { runningPeak: { $max: "$cumulativePnl", window: { documents: ["unbounded", "current"] } } } } },
  { $set: { drawdown: { $subtract: ["$runningPeak", "$cumulativePnl"] } } },
  { $sort: { closedAt: 1 } },
  { $group: { _id: "$strategyId", maxDrawdown: { $max: "$drawdown" }, finalPnl: { $last: "$cumulativePnl" } } }
])"""

SALES_CHAINED = [
    {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                          "output": {"runningTotal": {"$sum": "$amount", "window": CUM}}}},
    {"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                          "output": {"runningMax": {"$max": "$amount", "window": CUM}}}},
    {"$sort": {"region": 1, "ts": 1}},
    {"$group": {"_id": "$region", "finalTotal": {"$last": "$runningTotal"}, "finalMax": {"$last": "$runningMax"},
                "lastTs": {"$last": "$ts"}, "n": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
]

SLOW = {"$and": [{"payload": {"$regex": "q.*z.*q.*z"}}, {"rnd": {"$lt": 0.5}},
                 {"$expr": {"$gt": [{"$strLenCP": "$payload"}, 119]}}]}
NONE = {"payload": {"$regex": "zzzzzzzzzz"}, "$expr": {"$gt": [{"$strLenCP": "$payload"}, 119]}}
HEAVY = [{"$project": {"i": 1, "k": {"$concat": ["$payload"] * 20}}},
         {"$sort": {"k": 1, "i": 1}},
         {"$skip": BIG_N - 1},
         {"$project": {"_id": 0, "i": 1, "klen": {"$strLenCP": "$k"}}}]


# ----------------------------------------------------------------------------- (a) $setWindowFields

def section_a(report, db):
    sales, trades = db["sales"], db["trades"]
    sales_docs = make_sales_docs()
    run(report, "a", "a.0a", "seed sales (same generator and seed as the 0.117 run)",
        "db.sales.insert_many(<24 docs: region in east/west/north x 8 days; ts = 2026-01-01 + i days (Date); "
        "amount = random.choice([5,12,3,20,7,15,1,9]) + i%3 after random.seed(7)>)",
        lambda: {"inserted": len(sales.insert_many([dict(d) for d in sales_docs]).inserted_ids)},
        lambda out: f"Inserted {out['inserted']} sales documents, the same data the 0.117 run used.")
    trade_docs = make_trade_docs()
    shuffled = list(trade_docs)
    random.Random(5).shuffle(shuffled)
    run(report, "a", "a.0b", "seed trades for the exact L08 example",
        f"db.trades.insert_many({JS(shuffled)})",
        lambda: {"inserted": len(trades.insert_many([dict(d) for d in shuffled]).inserted_ids)},
        lambda out: (f"Inserted {out['inserted']} trades (12 momentum-1, 8 mean-revert-2) in shuffled order, "
                     "so natural order differs from closedAt order."))

    # a.1 the exact L08 example
    exp_m = l08_group(trade_docs, "momentum-1")
    gkeys = ("_id", "maxDrawdown", "finalPnl")

    def chk_a1(out):
        return {"matches_expected": len(out) == 1 and docs_close(out[0], exp_m, gkeys)}

    run(report, "a", "a.1",
        "exact L08 example: $match, $setWindowFields cumulative $sum, $setWindowFields cumulative $max over that output, "
        "$set drawdown, $sort, $group with $max and $last",
        f"db.trades.aggregate({JS(L08)})", lambda: list(trades.aggregate(L08)),
        lambda out: (f"The exact L08 pipeline ran and returned {JS(out)}, "
                     + ("which equals the client-side computation." if chk_a1(out)["matches_expected"]
                        else f"which differs from the client-side computation {JS(exp_m)}.")),
        checks=chk_a1, expected=J([exp_m]), l08_javascript=L08_JS,
        compare_0117="0.117 did not run this exact pipeline; its a.1 used $max over the raw field on the sales collection")

    # a.1b per-row values of the first four L08 stages
    exp_rows = l08_rows(trade_docs, "momentum-1")
    pipe_rows = L08[:4] + [{"$sort": {"closedAt": 1}},
                           {"$project": {"_id": 0, "seq": 1, "pnl": 1, "cumulativePnl": 1, "runningPeak": 1, "drawdown": 1}}]
    rkeys = ("seq", "pnl", "cumulativePnl", "runningPeak", "drawdown")

    def chk_rows(out):
        return {"matches_expected": len(out) == len(exp_rows) and all(docs_close(g, e, rkeys) for g, e in zip(out, exp_rows))}

    run(report, "a", "a.1b", "L08 stages 1-4 per row (cumulativePnl, runningPeak, drawdown) in closedAt order",
        f"db.trades.aggregate({JS(pipe_rows)})", lambda: list(trades.aggregate(pipe_rows)),
        lambda out: (f"Returned {len(out)} rows whose cumulativePnl, runningPeak and drawdown "
                     + ("all equal a client-side running sum and running max." if chk_rows(out)["matches_expected"]
                        else "do NOT all equal a client-side running sum and running max.")),
        checks=chk_rows, expected=J(exp_rows))

    # a.1c without $match: two partitions
    exp_both = sorted([l08_group(trade_docs, s) for s in TRADE_PNL], key=lambda r: r["_id"])
    pipe_c = L08[1:]

    def chk_c(out):
        got = sorted(out, key=lambda r: r["_id"])
        return {"matches_expected": len(got) == 2 and all(docs_close(g, e, gkeys) for g, e in zip(got, exp_both))}

    run(report, "a", "a.1c", "L08 pipeline without the $match (two strategy partitions)",
        f"db.trades.aggregate({JS(pipe_c)})", lambda: list(trades.aggregate(pipe_c)),
        lambda out: (f"Returned {JS(sorted(out, key=lambda r: r['_id']))}, "
                     + ("which equals the client-side computation for both partitions." if chk_c(out)["matches_expected"]
                        else f"which differs from the client-side computation {JS(exp_both)}.")),
        checks=chk_c, expected=J(exp_both))

    # a.1d without the $sort before $group
    pipe_d = L08[:4] + [L08[5]]
    run(report, "a", "a.1d", "L08 pipeline without the $sort before $group ($last relies on window output order)",
        f"db.trades.aggregate({JS(pipe_d)})", lambda: list(trades.aggregate(pipe_d)),
        lambda out: (f"Returned {JS(out)}; $last "
                     + ("picked the latest-closedAt row, matching the client-side computation." if chk_a1(out)["matches_expected"]
                        else "did not match the client-side computation, so the $sort before $group is needed.")),
        checks=chk_a1, expected=J([exp_m]))

    # a.1e one stage whose second output references the first output
    pipe_e = [{"$match": {"strategyId": "momentum-1"}},
              {"$setWindowFields": {"partitionBy": "$strategyId", "sortBy": {"closedAt": 1},
                                    "output": {"cumulativePnl": {"$sum": "$pnl", "window": CUM},
                                               "runningPeak": {"$max": "$cumulativePnl", "window": CUM}}}},
              {"$sort": {"closedAt": 1}},
              {"$project": {"_id": 0, "seq": 1, "cumulativePnl": 1, "runningPeak": 1}}]

    def read_e(out):
        peaks = [r.get("runningPeak") for r in out]
        if all(p is None for p in peaks):
            return (f"runningPeak came back null in all {len(out)} rows, so within one stage an output cannot see another "
                    "output, which is what the L08 comment says.")
        if [r.get("runningPeak") for r in out] == [e["runningPeak"] for e in exp_rows]:
            return "runningPeak equals the running max of cumulativePnl, so this engine let an output reference a sibling output."
        return f"runningPeak values {peaks} are neither null nor the running max of cumulativePnl."

    run(report, "a", "a.1e", "one $setWindowFields stage whose runningPeak output references the cumulativePnl output",
        f"db.trades.aggregate({JS(pipe_e)})", lambda: list(trades.aggregate(pipe_e)), read_e,
        checks=lambda out: {"runningPeak_all_null": all(r.get("runningPeak") is None for r in out)})

    # a.2 - a.4 the 0.117 sales variants
    exp_sales = {}
    for region in ("east", "west", "north"):
        rs = sorted([d for d in sales_docs if d["region"] == region], key=lambda d: d["ts"])
        exp_sales[region] = {"finalTotal": sum(d["amount"] for d in rs), "finalMax": max(d["amount"] for d in rs)}

    def chk_sales(out):
        got = {r["_id"]: {"finalTotal": r["finalTotal"], "finalMax": r["finalMax"]} for r in out}
        return {"matches_expected": got == exp_sales}

    run(report, "a", "a.2", "0.117 variant: chained $setWindowFields ($sum, then $max over amount) + $sort + $group $last on sales",
        f"db.sales.aggregate({JS(SALES_CHAINED)})", lambda: list(sales.aggregate(SALES_CHAINED)),
        lambda out: ("Two chained cumulative-window stages followed by $group/$last ran and "
                     + ("match the client-side computation." if chk_sales(out)["matches_expected"]
                        else f"DIFFER from the client-side computation {exp_sales}.")),
        checks=chk_sales, expected=exp_sales, compare_0117_step="a.1")

    pipe_a3 = [SALES_CHAINED[0], SALES_CHAINED[1], SALES_CHAINED[3], SALES_CHAINED[4]]
    run(report, "a", "a.3", "0.117 variant: same with no $sort before $group",
        f"db.sales.aggregate({JS(pipe_a3)})", lambda: list(sales.aggregate(pipe_a3)),
        lambda out: ("Ran without error and $last "
                     + ("picked the sortBy-last row in every partition." if chk_sales(out)["matches_expected"]
                        else f"did not pick the sortBy-last row (expected {exp_sales}).")),
        checks=chk_sales, expected=exp_sales, compare_0117_step="a.2")

    pipe_a4 = [{"$setWindowFields": {"partitionBy": "$region", "sortBy": {"ts": 1},
                                     "output": {"runningTotal": {"$sum": "$amount", "window": CUM},
                                                "runningMax": {"$max": "$amount", "window": CUM}}}},
               {"$match": {"region": "east"}}, {"$sort": {"ts": 1}},
               {"$project": {"_id": 0, "ts": 1, "amount": 1, "runningTotal": 1, "runningMax": 1}}]

    def chk_a4(out):
        running, mx, ok = 0, None, len(out) == 8
        for r in out:
            running += r["amount"]
            mx = r["amount"] if mx is None else max(mx, r["amount"])
            ok = ok and r["runningTotal"] == running and r["runningMax"] == mx
        return {"matches_expected": ok}

    run(report, "a", "a.4", "0.117 variant: one stage with cumulative $sum and $max over amount (east rows)",
        f"db.sales.aggregate({JS(pipe_a4)})", lambda: list(sales.aggregate(pipe_a4)),
        lambda out: ("One stage with cumulative $sum and $max returned per-row values that "
                     + ("match a client-side running sum and max." if chk_a4(out)["matches_expected"] else "do NOT match.")),
        checks=chk_a4, compare_0117_step="a.3")

    # sortBy-required cases
    S = "engine main-branch source (pg_documentdb/src/aggregation/bson_aggregation_window_operators.c)"
    cases = [
        ("s.1", "documents ['unbounded','current'] window, no sortBy",
         {"output": {"t": {"$sum": "$amount", "window": {"documents": ["unbounded", "current"]}}}},
         {"code": 5339901, "errmsg": "Missing sortBy field for document-based window"}, "a.4"),
        ("s.2", "documents [-1, 1] window, no sortBy",
         {"output": {"t": {"$sum": "$amount", "window": {"documents": [-1, 1]}}}},
         {"code": 5339901, "errmsg": "Missing sortBy field for document-based window"}, None),
        ("s.3", "documents ['current','unbounded'] window, no sortBy",
         {"output": {"t": {"$sum": "$amount", "window": {"documents": ["current", "unbounded"]}}}},
         {"code": 5339901, "errmsg": "Missing sortBy field for document-based window"}, None),
        ("s.4", "documents ['unbounded','unbounded'] window, no sortBy",
         {"output": {"t": {"$sum": "$amount", "window": {"documents": ["unbounded", "unbounded"]}}}},
         "accepted", "a.5"),
        ("s.5", "$sum output with no window and no sortBy",
         {"output": {"t": {"$sum": "$amount"}}}, "accepted", "a.6"),
        ("s.6", "range ['unbounded','current'] window, no sortBy",
         {"output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}},
         {"code": 5339902, "errmsg": "Expected a single sort by field for range-based window"}, "a.7"),
        ("s.7", "range [-1, 0] window with a compound sortBy {amount: 1, ts: 1}",
         {"sortBy": {"amount": 1, "ts": 1}, "output": {"t": {"$sum": "$amount", "window": {"range": [-1, 0]}}}},
         {"code": 5339902, "errmsg": "Expected a single sort by field for range-based window"}, None),
        ("s.8", "range ['unbounded','current'] window with a descending sortBy {amount: -1}",
         {"sortBy": {"amount": -1}, "output": {"t": {"$sum": "$amount", "window": {"range": ["unbounded", "current"]}}}},
         {"code": 9, "errmsg": "Expected ascending sortBy field definition"}, None),
        ("s.9", "positive control: range [-1, 0] unit 'day' window with sortBy {ts: 1}",
         {"sortBy": {"ts": 1}, "output": {"t": {"$sum": "$amount", "window": {"range": [-1, 0], "unit": "day"}}}},
         "accepted", None),
        ("s.10", "positive control: documents ['unbounded','current'] window with a compound sortBy {ts: 1, amount: 1}",
         {"sortBy": {"ts": 1, "amount": 1}, "output": {"t": {"$sum": "$amount", "window": CUM}}}, "accepted", None),
        ("s.11", "$rank with no sortBy", {"output": {"r": {"$rank": {}}}},
         {"code": 5371602, "errmsg": "$rank must be provided along with a top-level sortBy expression that contains exactly one element"}, None),
        ("s.12", "$denseRank with no sortBy", {"output": {"r": {"$denseRank": {}}}},
         {"code": 5371602, "errmsg": "$denseRank must be provided along with a top-level sortBy expression that contains exactly one element"}, None),
        ("s.13", "$documentNumber with no sortBy", {"output": {"r": {"$documentNumber": {}}}},
         {"code": 5371602, "errmsg": "$documentNumber must be provided along with a top-level sortBy expression that contains exactly one element"}, None),
        ("s.14", "$rank with a compound sortBy {amount: 1, ts: 1}",
         {"sortBy": {"amount": 1, "ts": 1}, "output": {"r": {"$rank": {}}}},
         {"code": 5371602, "errmsg": "$rank must be provided along with a top-level sortBy expression that contains exactly one element"}, None),
        ("s.15", "positive control: $rank with sortBy {amount: 1}",
         {"sortBy": {"amount": 1}, "output": {"r": {"$rank": {}}}}, "accepted", None),
        ("s.16", "$shift with no sortBy",
         {"output": {"prev": {"$shift": {"output": "$amount", "by": -1, "default": None}}}},
         {"code": 9, "errmsg": "'sortBy' parameters must be specified for $shift"}, None),
        ("s.17", "$derivative with no sortBy (documents ['unbounded','unbounded'] so only the operator rule applies)",
         {"output": {"d": {"$derivative": {"input": "$amount"}, "window": {"documents": ["unbounded", "unbounded"]}}}},
         {"code": 9, "errmsg": "$derivative requires a sortBy"}, None),
        ("s.18", "$integral with no sortBy (documents ['unbounded','unbounded'] so only the operator rule applies)",
         {"output": {"g": {"$integral": {"input": "$amount"}, "window": {"documents": ["unbounded", "unbounded"]}}}},
         {"code": 9, "errmsg": "$integral requires a sortBy"}, None),
        ("s.19", "$expMovingAvg with no sortBy", {"output": {"e": {"$expMovingAvg": {"input": "$amount", "N": 2}}}},
         {"code": 9, "errmsg": "'sortBy' parameters must be specified for $shift"}, None),
        ("s.20", "$linearFill with no sortBy", {"output": {"f": {"$linearFill": "$amount"}}},
         {"code": 605001, "errmsg": "$linearFill requires specifying a top-level sortBy expression that contains exactly one element"}, None),
        ("s.21", "$locf with no sortBy", {"output": {"f": {"$locf": "$amount"}}}, "accepted", None),
        ("s.22", "$first and $last with no window and no sortBy",
         {"output": {"f": {"$first": "$amount"}, "l": {"$last": "$amount"}}}, "accepted", None),
    ]
    for sid, title, spec, expected, cmp in cases:
        pipe = [{"$setWindowFields": dict({"partitionBy": "$region"}, **spec)}]

        def chk(out, expected=expected):
            return {"outcome": "accepted", "matches_source_prediction": expected == "accepted"}

        rec = run(report, "a", sid, title, f"db.sales.aggregate({JS(pipe)})",
                  lambda pipe=pipe: {"n_docs": len(r := list(sales.aggregate(pipe))), "first_docs": r[:2]},
                  lambda out, title=title: f"Accepted: {title} returned {out['n_docs']} documents.",
                  lambda err, title=title: f"Rejected: {title} failed with {err_text(err)}.",
                  checks=chk, expected_per_source={"source": S, "prediction": expected}, compare_0117_step=cmp)
        if rec["response"]["outcome"] == "error":
            e = rec["response"]
            pred_ok = (isinstance(expected, dict) and e.get("code") == expected["code"]
                       and e.get("errmsg") == expected["errmsg"])
            rec["checks"] = {"outcome": "rejected", "code": e.get("code"), "codeName": e.get("codeName"),
                             "matches_source_prediction": pred_ok}


# ----------------------------------------------------------------------------- big collection

def seed_big(report, db):
    big = db["big"]
    rnd = random.Random(11)
    alphabet = string.ascii_lowercase
    stats = {"min_rnd": None, "max_rnd": None, "max_payload_i": None}
    max_payload = None
    t0 = time.perf_counter()
    inserted, batch = 0, []
    for i in range(BIG_N):
        doc = {"i": i, "rnd": rnd.random(), "grp": i % 97,
               "payload": "".join(rnd.choice(alphabet) for _ in range(120)),
               "tags": [f"t{i % 13}", f"u{i % 7}"]}
        r = doc["rnd"]
        stats["min_rnd"] = r if stats["min_rnd"] is None else min(stats["min_rnd"], r)
        stats["max_rnd"] = r if stats["max_rnd"] is None else max(stats["max_rnd"], r)
        if max_payload is None or doc["payload"] > max_payload:
            max_payload, stats["max_payload_i"] = doc["payload"], i
        batch.append(doc)
        if len(batch) == 10_000:
            inserted += len(big.insert_many(batch, ordered=False).inserted_ids)
            batch = []
    if batch:
        inserted += len(big.insert_many(batch, ordered=False).inserted_ids)
    cnt = big.count_documents({})
    SEED_DONE["t"] = time.perf_counter()
    report.add("setup", "0.2", "seed big collection",
               f"db.big.insert_many(<batch of 10000>, ordered=False) x {BIG_N // 10000}: docs {{i: 0..{BIG_N - 1}, "
               "rnd: random.Random(11).random(), grp: i % 97, payload: 120 random lowercase letters, "
               "tags: ['t'+str(i%13), 'u'+str(i%7)]}; then db.big.count_documents({})",
               {"outcome": "ok", "result": {"inserted": inserted, "count_documents": cnt,
                                            "client_side_stats": stats}},
               f"Inserted {inserted} documents (count_documents {cnt}) for the sort, explain and maxTimeMS tests.",
               elapsed_ms=round((time.perf_counter() - t0) * 1000, 1))
    return stats


# ----------------------------------------------------------------------------- (b) allowDiskUse

def section_b(report, db, stats):
    big = db["big"]
    pipe_sort = [{"$sort": {"rnd": 1}},
                 {"$group": {"_id": None, "n": {"$sum": 1}, "firstRnd": {"$first": "$rnd"}, "lastRnd": {"$last": "$rnd"}}}]
    exp = {"_id": None, "n": BIG_N, "firstRnd": stats["min_rnd"], "lastRnd": stats["max_rnd"]}
    for sid, flag, cmp in (("b.1", True, "b.1"), ("b.2", False, "b.2"), ("b.3", None, None)):
        kwargs = {} if flag is None else {"allowDiskUse": flag}
        label = "omitted" if flag is None else str(flag)
        run(report, "b", sid, f"full $sort on unindexed rnd over {BIG_N} docs, allowDiskUse {label}",
            f"db.big.aggregate({JS(pipe_sort)}" + (f", allowDiskUse={flag})" if flag is not None else ")"),
            lambda kwargs=kwargs: list(big.aggregate(pipe_sort, **kwargs)),
            lambda out, label=label: (f"allowDiskUse {label} was accepted and the sort covered {out[0]['n']} documents "
                                      f"(firstRnd {out[0]['firstRnd']!r}, lastRnd {out[0]['lastRnd']!r})"
                                      + (", equal to the client-side min and max." if out == [exp] else ", NOT equal to the client-side min and max.")),
            checks=lambda out: {"matches_expected": out == [exp]}, compare_0117_step=cmp)

    exp_heavy = [{"i": stats["max_payload_i"], "klen": 2400}]
    for sid, flag in (("b.4", False), ("b.5", True)):
        run(report, "b", sid,
            f"$sort over 240 MB of sort-key string data (above MongoDB's 100 MB blocking-sort limit), allowDiskUse {flag}",
            f"db.big.aggregate({JS(HEAVY)}, allowDiskUse={flag}, maxTimeMS=240000)",
            lambda flag=flag: list(big.aggregate(HEAVY, allowDiskUse=flag, maxTimeMS=240000)),
            lambda out, flag=flag: (f"With allowDiskUse {flag} the 240 MB sort completed and returned {JS(out)}"
                                    + (", the client-side expected last document." if out == exp_heavy
                                       else f", not the expected {JS(exp_heavy)}.")),
            lambda err, flag=flag: f"With allowDiskUse {flag} the 240 MB sort failed with {err_text(err)}.",
            checks=lambda out: {"matches_expected": out == exp_heavy}, expected=exp_heavy)

    for sid, flag in (("b.6", False), ("b.7", True)):
        cmd = {"explain": {"aggregate": "big", "pipeline": HEAVY, "cursor": {}, "allowDiskUse": flag},
               "verbosity": "executionStats"}

        def fn(cmd=cmd):
            out = db.command(cmd)
            s = summarize_explain(out)
            sorts = [n for n in s["nodes"] if n["stage"] == "SORT"]
            return {"sort_nodes": sorts, "summary": s, "full_explain": J(out)}

        def ok(out, flag=flag):
            ex = [n for n in out["sort_nodes"] if "executionStats" in n["path"]]
            fields = {k: v for n in ex[:1] for k, v in n.items() if k not in ("path",)}
            return (f"Explain of the 240 MB sort with allowDiskUse {flag}: SORT executionStages fields "
                    f"{JS(fields) if fields else 'not present'}"
                    + (f", so the sort spilled to disk with allowDiskUse {flag}." if fields.get("usedDisk") else "."))

        run(report, "b", sid, f"explain executionStats of the 240 MB sort, allowDiskUse {flag}",
            f"db.command({JS(cmd)})", fn, ok,
            checks=lambda out: {"sortMethod_values": sorted({str(n.get('sortMethod')) for n in out['sort_nodes']
                                                             if 'executionStats' in n['path']})})

    for sid, val, label, cmp in (("b.8", "yes", "string 'yes'", "b.3"), ("b.9", 1, "int32 1", None),
                                 ("b.10", 1.0, "double 1.0", None), ("b.11", None, "null", None)):
        cmd = {"aggregate": "big", "pipeline": [{"$limit": 1}, {"$project": {"_id": 0, "i": 1}}], "cursor": {},
               "allowDiskUse": val}
        run(report, "b", sid, f"raw aggregate with allowDiskUse {label}", f"db.command({JS(cmd)})",
            lambda cmd=cmd: db.command(cmd),
            lambda out, label=label: f"allowDiskUse {label} was accepted on aggregate without a type error.",
            lambda err, label=label: f"allowDiskUse {label} was rejected on aggregate with {err_text(err)}.",
            compare_0117_step=cmp)

    for sid, flag, cmp in (("b.12", True, "b.4"), ("b.13", False, None)):
        run(report, "b", sid, f"find sorted on unindexed rnd with allow_disk_use({flag})",
            f"list(db.big.find({{}}, {{'_id': 0, 'rnd': 1}}).sort('rnd', 1).limit(3).allow_disk_use({flag}))",
            lambda flag=flag: list(big.find({}, {"_id": 0, "rnd": 1}).sort("rnd", 1).limit(3).allow_disk_use(flag)),
            lambda out, flag=flag: (f"find with allowDiskUse {flag} was accepted and returned the 3 smallest rnd values "
                                    + ("(first equals the client-side minimum)." if out and out[0]["rnd"] == stats["min_rnd"]
                                       else "(first does NOT equal the client-side minimum).")),
            compare_0117_step=cmp)

    for sid, val, label in (("b.14", "yes", "string 'yes'"), ("b.15", 1, "int32 1")):
        cmd = {"find": "big", "filter": {}, "projection": {"_id": 0, "rnd": 1}, "sort": {"rnd": 1}, "limit": 3,
               "allowDiskUse": val}
        run(report, "b", sid, f"raw find with allowDiskUse {label}", f"db.command({JS(cmd)})",
            lambda cmd=cmd: db.command(cmd),
            lambda out, label=label: f"allowDiskUse {label} was accepted on find without a type error.",
            lambda err, label=label: f"allowDiskUse {label} was rejected on find with {err_text(err)}.")


# ----------------------------------------------------------------------------- (c) explain

UNINDEXED_FINDS = [
    ("c.1", "find {rnd: {$gt: 0.999}} (0.117 c.1 shape)", {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "c.1"),
    ("c.1b", "find {grp: 5} equality", {"find": "big", "filter": {"grp": 5}}, None),
    ("c.1c", "find {} empty filter", {"find": "big", "filter": {}}, None),
    ("c.1d", "find {rnd: {$gt: 0.999}} sorted on unindexed payload",
     {"find": "big", "filter": {"rnd": {"$gt": 0.999}}, "sort": {"payload": 1}}, None),
    ("c.1e", "find {grp: 5} limit 5", {"find": "big", "filter": {"grp": 5}, "limit": 5}, None),
    ("c.1f", "find {tags: 't3'} on an array field", {"find": "big", "filter": {"tags": "t3"}}, None),
    ("c.1g", "find {payload: {$regex: '^abc'}}", {"find": "big", "filter": {"payload": {"$regex": "^abc"}}}, None),
    ("c.1h", "find with the $expr/$regex predicate used in section d", {"find": "big", "filter": SLOW}, None),
    ("c.1i", "find {rnd: {$gt: 0.999}} with hint {$natural: 1}",
     {"find": "big", "filter": {"rnd": {"$gt": 0.999}}, "hint": {"$natural": 1}}, None),
    ("c.1j", "find {region: 'east'} on the 24-document sales collection", {"find": "sales", "filter": {"region": "east"}}, None),
]
UNINDEXED_AGGS = [
    ("c.2", "aggregate unindexed $match {rnd: {$gt: 0.999}} + $sort {rnd: -1}",
     {"aggregate": "big", "pipeline": [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"rnd": -1}}], "cursor": {}},
     "Aggregate with unindexed $match and $sort"),
    ("c.2b", "aggregate unindexed $match {grp: 5} + $sort {rnd: 1} + $limit 10",
     {"aggregate": "big", "pipeline": [{"$match": {"grp": 5}}, {"$sort": {"rnd": 1}}, {"$limit": 10}], "cursor": {}},
     "Aggregate with unindexed equality $match, $sort and $limit"),
]
SEED_DONE = {"t": None}


def since_seed():
    return None if SEED_DONE["t"] is None else round(time.perf_counter() - SEED_DONE["t"], 1)


def section_c_unindexed(report, db, suffix, state):
    """Unindexed explains; suffix '' = right after the bulk load, '-post' = after the plan change seen in e.2."""
    ES = "executionStats"
    for sid, title, find_cmd, cmp in UNINDEXED_FINDS:
        explain_step(report, "c", sid + suffix, f"explain {ES}: unindexed {title} [{state}]", db,
                     {"explain": find_cmd, "verbosity": ES}, f"Unindexed {title} [{state}]",
                     compare_0117_step=cmp if not suffix else None, seconds_after_bulk_load=since_seed())
    explain_step(report, "c", "c.1q" + suffix, f"explain queryPlanner: unindexed find {{rnd: {{$gt: 0.999}}}} [{state}]", db,
                 {"explain": {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "verbosity": "queryPlanner"},
                 f"Unindexed find {{rnd: {{$gt: 0.999}}}} at queryPlanner verbosity [{state}]",
                 seconds_after_bulk_load=since_seed())
    for sid, title, agg_cmd, what in UNINDEXED_AGGS:
        explain_step(report, "c", sid + suffix, f"explain {ES}: {title} [{state}]", db,
                     {"explain": agg_cmd, "verbosity": ES}, f"{what} [{state}]", seconds_after_bulk_load=since_seed())


RAW_FIND_1MS = {"find": "big", "filter": SLOW, "projection": {"_id": 1}, "maxTimeMS": 1}


def raw_find_once(client, db):
    with client.start_session() as s1:
        r = db.command(RAW_FIND_1MS, session=s1)
        cid_ = r["cursor"]["id"]
        out_ = {"firstBatch_len": len(r["cursor"]["firstBatch"]), "cursor_open": bool(cid_)}
        if cid_:
            db.command({"killCursors": "big", "cursors": [cid_]}, session=s1)
    return out_


RAW_FIND_CMD_TEXT = (f"with client.start_session() as s: db.command({JS(RAW_FIND_1MS)}, session=s); "
                     "then db.command({'killCursors': 'big', 'cursors': [id]}, session=s) if a cursor was opened")


def section_e(report, client, db):
    """Plan stability after the bulk load: maxTimeMS-1 first batch before and after, and a plan poll in between."""
    attempts_step(report, "e", "e.1", "raw find with maxTimeMS 1 on the slow predicate, right after the bulk load",
                  RAW_FIND_CMD_TEXT, lambda: raw_find_once(client, db), iterate=False, attempts=5,
                  seconds_after_bulk_load=since_seed())
    cmd = {"explain": {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "verbosity": "queryPlanner"}
    samples, first_chain, changed_at = [], None, None
    t0 = time.perf_counter()
    started_after = since_seed()
    while True:
        el = round(time.perf_counter() - t0, 1)
        try:
            out = db.command(cmd)
            sm = summarize_explain(out)
            samples.append({"t_s": el, "seconds_after_bulk_load": since_seed(), "utc": now(), "chain": sm["chain"],
                            "has_COLLSCAN": sm["has_COLLSCAN"], "indexCosts_first": sm.get("indexCosts_first")})
        except PyMongoError as exc:
            samples.append({"t_s": el, "seconds_after_bulk_load": since_seed(), "error": error_record(exc)})
        cur = samples[-1].get("chain")
        if first_chain is None:
            first_chain = cur
        if changed_at is None and cur != first_chain:
            changed_at = samples[-1]["seconds_after_bulk_load"]
        if changed_at is not None and samples[-1]["seconds_after_bulk_load"] - changed_at >= 6:
            break
        if el >= 150:
            break
        time.sleep(3)
    last = samples[-1]
    first = samples[0]
    if changed_at is not None:
        reading = (f"With no client action the plan for the unindexed find changed from '{first_chain}' to "
                   f"'{last.get('chain')}' about {changed_at} s after the bulk load; the _id_ index cost estimate went "
                   f"from {JS(first.get('indexCosts_first'))} to {JS(last.get('indexCosts_first'))}, consistent with "
                   "PostgreSQL refreshing the new table's statistics (autovacuum analyze, inferred).")
    else:
        reading = (f"The plan stayed '{first_chain}' from {started_after} s to {last.get('seconds_after_bulk_load')} s "
                   f"after the bulk load (index cost estimate {JS(last.get('indexCosts_first'))}).")
    report.add("e", "e.2", "poll the queryPlanner explain of find {rnd: {$gt: 0.999}} every 3 s until the plan changes (150 s cap)",
               f"loop: db.command({JS(cmd)}); time.sleep(3)  # until the chain differs from the first sample, then 6 s more",
               {"outcome": "ok", "result": {"first_chain": first_chain, "last_chain": last.get("chain"),
                                            "changed_after_bulk_load_s": changed_at, "samples": samples}},
               reading, checks={"plan_changed": changed_at is not None, "changed_after_bulk_load_s": changed_at})
    attempts_step(report, "e", "e.3", "raw find with maxTimeMS 1 on the slow predicate, after the poll",
                  RAW_FIND_CMD_TEXT, lambda: raw_find_once(client, db), iterate=False, attempts=5,
                  seconds_after_bulk_load=since_seed())


def section_c(report, db):
    big, sales, vec = db["big"], db["sales"], db["vec"]
    ES = "executionStats"
    run(report, "c", "c.3", "createIndex {i: 1} on big", "db.big.create_index([('i', ASCENDING)], name='i_1')",
        lambda: big.create_index([("i", ASCENDING)], name="i_1"), lambda out: f"Index {out} created on big.i.")

    explain_step(report, "c", "c.4", f"explain {ES}: indexed find {{i: 12345}}", db,
                 {"explain": {"find": "big", "filter": {"i": 12345}}, "verbosity": ES}, "Indexed equality find",
                 compare_0117_step="c.3")
    explain_step(report, "c", "c.4b", f"explain {ES}: indexed range {{i: {{$gt: {BIG_N - 1000}}}}} sorted on unindexed rnd", db,
                 {"explain": {"find": "big", "filter": {"i": {"$gt": BIG_N - 1000}}, "sort": {"rnd": -1}}, "verbosity": ES},
                 "Indexed range find with a sort on an unindexed field", compare_0117_step="c.3b")
    explain_step(report, "c", "c.4c", f"explain {ES}: indexed range {{i: {{$gt: {BIG_N - 1000}}}}} sorted on indexed i", db,
                 {"explain": {"find": "big", "filter": {"i": {"$gt": BIG_N - 1000}}, "sort": {"i": 1}}, "verbosity": ES},
                 "Indexed range find with a sort on the indexed field")
    explain_step(report, "c", "c.5", f"explain {ES}: aggregate indexed $match {{i: {{$gt: {BIG_N - 1000}}}}} + $sort {{rnd: -1}} + $limit 10", db,
                 {"explain": {"aggregate": "big", "pipeline": [{"$match": {"i": {"$gt": BIG_N - 1000}}}, {"$sort": {"rnd": -1}},
                                                                {"$limit": 10}], "cursor": {}}, "verbosity": ES},
                 "Aggregate with indexed $match, $sort and $limit", compare_0117_step="c.4")
    explain_step(report, "c", "c.5b", f"explain {ES}: aggregate unindexed $match {{rnd: {{$gt: 0.999}}}} + $sort on indexed i", db,
                 {"explain": {"aggregate": "big", "pipeline": [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"i": 1}}],
                              "cursor": {}}, "verbosity": ES},
                 "Aggregate with unindexed $match and a $sort on an indexed field", compare_0117_step="c.4b")
    explain_step(report, "c", "c.5c", f"explain {ES}: aggregate indexed $match + $sort on the same indexed field", db,
                 {"explain": {"aggregate": "big", "pipeline": [{"$match": {"i": {"$gt": BIG_N - 1000}}}, {"$sort": {"i": 1}}],
                              "cursor": {}}, "verbosity": ES},
                 "Aggregate with indexed $match and $sort on the same field")

    # vector-ivf
    vrnd = random.Random(3)
    dims = 8
    vdocs = [{"k": i, "embedding": [vrnd.uniform(-1, 1) for _ in range(dims)], "cat": f"c{i % 4}"} for i in range(500)]
    run(report, "c", "c.6a", "seed vec collection",
        "db.vec.insert_many(<500 docs {k: i, embedding: 8 floats from random.Random(3).uniform(-1, 1), cat: 'c'+str(i%4)}>)",
        lambda: {"inserted": len(vec.insert_many([dict(d) for d in vdocs]).inserted_ids)},
        lambda out: f"Inserted {out['inserted']} documents with 8-dimension embeddings.")
    create_vec = {"createIndexes": "vec",
                  "indexes": [{"name": "vec_ivf", "key": {"embedding": "cosmosSearch"},
                               "cosmosSearchOptions": {"kind": "vector-ivf", "numLists": 2, "similarity": "COS",
                                                       "dimensions": dims}}]}
    run(report, "c", "c.6b", "createIndexes cosmosSearch vector-ivf on vec.embedding", f"db.command({JS(create_vec)})",
        lambda: db.command(create_vec),
        lambda out: f"vector-ivf index created; reply {JS(out)}.")
    qvec = [vrnd.uniform(-1, 1) for _ in range(dims)]

    def cos(a, b):
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

    exact_top5 = [d["k"] for d in sorted(vdocs, key=lambda d: -cos(d["embedding"], qvec))[:5]]
    search_pipe = [{"$search": {"cosmosSearch": {"vector": qvec, "path": "embedding", "k": 5}, "returnStoredSource": True}},
                   {"$project": {"_id": 0, "k": 1, "score": {"$meta": "searchScore"}}}]
    run(report, "c", "c.6c", "run the $search cosmosSearch pipeline (k 5)", f"db.vec.aggregate({JS(search_pipe)})",
        lambda: list(vec.aggregate(search_pipe)),
        lambda out: (f"$search cosmosSearch returned {len(out)} rows (k {[r['k'] for r in out]}); "
                     f"{len(set(r['k'] for r in out) & set(exact_top5))} of 5 are in the exact cosine top 5 {exact_top5}."),
        checks=lambda out: {"returned": len(out), "overlap_with_exact_top5": len(set(r["k"] for r in out) & set(exact_top5))})
    explain_step(report, "c", "c.6d", f"explain {ES}: $search cosmosSearch pipeline on the vector-ivf index", db,
                 {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}}, "verbosity": ES},
                 "$search cosmosSearch on vector-ivf", compare_0117_step="c.5d")
    explain_step(report, "c", "c.6e", "explain queryPlanner: $search cosmosSearch pipeline", db,
                 {"explain": {"aggregate": "vec", "pipeline": search_pipe, "cursor": {}}, "verbosity": "queryPlanner"},
                 "$search cosmosSearch on vector-ivf at queryPlanner verbosity", compare_0117_step="c.5e")
    explain_step(report, "c", "c.6f", f"explain {ES}: unindexed find {{cat: 'c1'}} on the 500-document vec collection", db,
                 {"explain": {"find": "vec", "filter": {"cat": "c1"}}, "verbosity": ES},
                 "Unindexed find on the 500-document vec collection")

    # window pipelines
    explain_step(report, "c", "c.7", f"explain {ES}: the exact L08 pipeline", db,
                 {"explain": {"aggregate": "trades", "pipeline": L08, "cursor": {}}, "verbosity": ES},
                 "The L08 window pipeline")
    explain_step(report, "c", "c.7b", f"explain {ES}: the 0.117 chained $setWindowFields pipeline on sales", db,
                 {"explain": {"aggregate": "sales", "pipeline": SALES_CHAINED, "cursor": {}}, "verbosity": ES},
                 "The 0.117 chained window pipeline", compare_0117_step="c.6")


# ----------------------------------------------------------------------------- (d) maxTimeMS

def section_d(report, client, db):
    big = db["big"]
    sp = JS(SLOW)
    attempts_step(report, "d", "d.0", "baseline: find on the slow predicate, no maxTimeMS, whole cursor consumed",
                  f"for doc in db.big.find({sp}, {{'_id': 1}}): pass",
                  lambda: big.find(SLOW, {"_id": 1}), attempts=1, compare_0117_step="d.0")
    run(report, "d", "d.0b", "baseline: aggregate $match slow predicate + $count, no maxTimeMS",
        f"list(db.big.aggregate([{{'$match': {sp}}}, {{'$count': 'n'}}]))",
        lambda: list(big.aggregate([{"$match": SLOW}, {"$count": "n"}])),
        lambda out: f"Baseline aggregate counted {out[0]['n'] if out else 0} matches with no time limit.", wire=True)

    attempts_step(report, "d", "d.1", "find, slow predicate, max_time_ms(1), default batch size, whole cursor consumed",
                  f"for doc in db.big.find({sp}, {{'_id': 1}}).max_time_ms(1): pass",
                  lambda: big.find(SLOW, {"_id": 1}).max_time_ms(1), attempts=10, compare_0117_step="d.1")
    attempts_step(report, "d", "d.1b",
                  "find, slow predicate, max_time_ms(20), default batch size, whole cursor consumed "
                  "(first batch about 1 ms, getMore about 90 ms: tests whether the limit is cumulative)",
                  f"for doc in db.big.find({sp}, {{'_id': 1}}).max_time_ms(20): pass",
                  lambda: big.find(SLOW, {"_id": 1}).max_time_ms(20), attempts=5)
    attempts_step(report, "d", "d.2", "find, slow predicate, max_time_ms(1), batch_size(1000), whole cursor consumed",
                  f"for doc in db.big.find({sp}, {{'_id': 1}}).max_time_ms(1).batch_size(1000): pass",
                  lambda: big.find(SLOW, {"_id": 1}).max_time_ms(1).batch_size(1000))
    attempts_step(report, "d", "d.3", "find, predicate matching nothing (full scan before the first batch), max_time_ms(1)",
                  f"for doc in db.big.find({JS(NONE)}, {{'_id': 1}}).max_time_ms(1): pass",
                  lambda: big.find(NONE, {"_id": 1}).max_time_ms(1))
    attempts_step(report, "d", "d.4", "find {} sorted on unindexed payload (blocking sort), max_time_ms(1), whole cursor consumed",
                  "for doc in db.big.find({}, {'_id': 1}).sort('payload', 1).max_time_ms(1): pass",
                  lambda: big.find({}, {"_id": 1}).sort("payload", 1).max_time_ms(1))

    # d.5 raw find with maxTimeMS 1 (0.117 d.2), ten attempts; any cursor it opens is killed in the same session
    from bson.int64 import Int64
    attempts_step(report, "d", "d.5", "raw find command with maxTimeMS 1 (first batch only; any open cursor killed after)",
                  RAW_FIND_CMD_TEXT, lambda: raw_find_once(client, db), iterate=False, attempts=10,
                  compare_0117_step="d.2")

    # d.5a-d.5g getMore carrying maxTimeMS, on cursors opened WITHOUT maxTimeMS (so the first batch cannot time out)
    def gm_summary(r):
        return {"cursor_id": r["cursor"]["id"], "nextBatch_len": len(r["cursor"]["nextBatch"]), "ok": r.get("ok")}

    open_cmd = {"find": "big", "filter": SLOW, "projection": {"_id": 1}}
    with client.start_session() as s:
        def do_open():
            r = db.command(open_cmd, session=s)
            return {"cursor_id": r["cursor"]["id"], "ns": r["cursor"].get("ns"),
                    "firstBatch_len": len(r["cursor"]["firstBatch"]), "ok": r.get("ok")}

        def open_reading(out):
            return (f"Raw find with no maxTimeMS returned a first batch of {out['firstBatch_len']} documents and "
                    f"{'an open cursor' if out['cursor_id'] else 'no open cursor'}.")

        rec = run(report, "d", "d.5a", "raw find with no maxTimeMS, to open a cursor for the getMore tests",
                  f"db.command({JS(open_cmd)}, session=s)", do_open, open_reading, wire=True)
        cid = rec["response"]["result"]["cursor_id"] if rec["response"]["outcome"] == "ok" else 0
        if cid:
            gm1 = {"getMore": Int64(cid), "collection": "big", "maxTimeMS": 1}
            run(report, "d", "d.5b", "raw getMore carrying maxTimeMS 1 on that non-tailable cursor",
                f"db.command({JS(gm1)}, session=s)", lambda: gm_summary(db.command(gm1, session=s)),
                lambda out: (f"getMore carrying maxTimeMS 1 completed and returned {out['nextBatch_len']} documents "
                             f"({'cursor still open' if out['cursor_id'] else 'cursor exhausted'})."),
                lambda err: f"getMore carrying maxTimeMS 1 failed with {err_text(err)}.", wire=True)
            progress = {"getMore_batches": [], "docs_from_getMore": 0, "cursor_id": cid}

            def drain():
                cur_id = Int64(cid)
                while cur_id:
                    r = db.command({"getMore": cur_id, "collection": "big"}, session=s)
                    progress["getMore_batches"].append(len(r["cursor"]["nextBatch"]))
                    progress["docs_from_getMore"] += len(r["cursor"]["nextBatch"])
                    cur_id = r["cursor"]["id"]
                    progress["cursor_id"] = int(cur_id)
                return dict(progress)

            run(report, "d", "d.5c", "then drain the same cursor with plain getMore (no maxTimeMS) until cursor id 0",
                "while cursor_id: r = db.command({'getMore': cursor_id, 'collection': 'big'}, session=s); "
                "cursor_id = r['cursor']['id']",
                drain,
                lambda out: (f"Plain getMore drained the cursor in {len(out['getMore_batches'])} batches "
                             f"({out['docs_from_getMore']} documents) with no error."),
                lambda err: (f"After {len(progress['getMore_batches'])} successful batches a plain getMore failed with "
                             f"{err_text(err)}, so the cursor no longer existed after the timed-out getMore."),
                wire=True, partial_progress=progress)
            if progress["cursor_id"]:
                kc = {"killCursors": "big", "cursors": [Int64(progress["cursor_id"])]}
                run(report, "d", "d.5d", "killCursors on that cursor id", f"db.command({JS(kc)}, session=s)",
                    lambda: db.command(kc, session=s), lambda out: f"killCursors replied {JS(out)}.")

        rec = run(report, "d", "d.5e", "second raw find with no maxTimeMS (new cursor)",
                  f"db.command({JS(open_cmd)}, session=s)", do_open, open_reading, wire=True)
        cid2 = rec["response"]["result"]["cursor_id"] if rec["response"]["outcome"] == "ok" else 0
        if cid2:
            gm2 = {"getMore": Int64(cid2), "collection": "big", "maxTimeMS": 60000}
            rec = run(report, "d", "d.5f", "raw getMore carrying maxTimeMS 60000 on the new cursor",
                      f"db.command({JS(gm2)}, session=s)", lambda: gm_summary(db.command(gm2, session=s)),
                      lambda out: (f"getMore carrying maxTimeMS 60000 was accepted and returned {out['nextBatch_len']} "
                                   f"documents ({'cursor still open' if out['cursor_id'] else 'cursor exhausted'})."),
                      lambda err: f"getMore carrying maxTimeMS 60000 failed with {err_text(err)}.", wire=True)
            left = rec["response"].get("result", {}).get("cursor_id") if rec["response"]["outcome"] == "ok" else cid2
            if left:
                kc = {"killCursors": "big", "cursors": [Int64(left)]}
                run(report, "d", "d.5g", "killCursors on the second cursor", f"db.command({JS(kc)}, session=s)",
                    lambda: db.command(kc, session=s), lambda out: f"killCursors replied {JS(out)}.")

    attempts_step(report, "d", "d.6", "aggregate $match slow predicate + $count, maxTimeMS=1",
                  f"list(db.big.aggregate([{{'$match': {sp}}}, {{'$count': 'n'}}], maxTimeMS=1))",
                  lambda: big.aggregate([{"$match": SLOW}, {"$count": "n"}], maxTimeMS=1), compare_0117_step="d.3")
    attempts_step(report, "d", "d.7", "aggregate $match slow predicate + $project (streaming), maxTimeMS=1, whole cursor consumed",
                  f"for doc in db.big.aggregate([{{'$match': {sp}}}, {{'$project': {{'_id': 1}}}}], maxTimeMS=1): pass",
                  lambda: big.aggregate([{"$match": SLOW}, {"$project": {"_id": 1}}], maxTimeMS=1), attempts=10)
    attempts_step(report, "d", "d.7b",
                  "aggregate streaming, maxTimeMS=20, whole cursor consumed (tests whether the limit is cumulative)",
                  f"for doc in db.big.aggregate([{{'$match': {sp}}}, {{'$project': {{'_id': 1}}}}], maxTimeMS=20): pass",
                  lambda: big.aggregate([{"$match": SLOW}, {"$project": {"_id": 1}}], maxTimeMS=20), attempts=5)
    attempts_step(report, "d", "d.8", "aggregate streaming, maxTimeMS=1, batchSize=1000, whole cursor consumed",
                  f"for doc in db.big.aggregate([{{'$match': {sp}}}, {{'$project': {{'_id': 1}}}}], maxTimeMS=1, batchSize=1000): pass",
                  lambda: big.aggregate([{"$match": SLOW}, {"$project": {"_id": 1}}], maxTimeMS=1, batchSize=1000))
    attempts_step(report, "d", "d.9", "aggregate $sort on unindexed payload (blocking) + $project, maxTimeMS=1, whole cursor consumed",
                  "for doc in db.big.aggregate([{'$sort': {'payload': 1}}, {'$project': {'_id': 1}}], maxTimeMS=1): pass",
                  lambda: big.aggregate([{"$sort": {"payload": 1}}, {"$project": {"_id": 1}}], maxTimeMS=1))
    attempts_step(report, "d", "d.10", "count_documents on the slow predicate, maxTimeMS=1",
                  f"db.big.count_documents({sp}, maxTimeMS=1)",
                  lambda: big.count_documents(SLOW, maxTimeMS=1), iterate=False, compare_0117_step="d.4")
    attempts_step(report, "d", "d.11", "control: find, slow predicate, max_time_ms(120000), whole cursor consumed",
                  f"for doc in db.big.find({sp}, {{'_id': 1}}).max_time_ms(120000): pass",
                  lambda: big.find(SLOW, {"_id": 1}).max_time_ms(120000), attempts=1, compare_0117_step="d.5")
    attempts_step(report, "d", "d.12", "control: aggregate $match + $count, maxTimeMS=120000",
                  f"list(db.big.aggregate([{{'$match': {sp}}}, {{'$count': 'n'}}], maxTimeMS=120000))",
                  lambda: big.aggregate([{"$match": SLOW}, {"$count": "n"}], maxTimeMS=120000), attempts=1)


# ----------------------------------------------------------------------------- target info

def docker_info():
    info = {"container": CONTAINER}
    try:
        out = subprocess.run(["docker", "inspect", CONTAINER, "--format",
                              "{{.Config.Image}}|{{.Image}}|{{json .Config.Labels}}"],
                             capture_output=True, text=True, timeout=20)
        if out.returncode == 0:
            image, image_id, labels = out.stdout.strip().split("|", 2)
            lab = json.loads(labels)
            info.update({"image": image, "image_id": image_id,
                         "label_version": lab.get("org.opencontainers.image.version"),
                         "label_revision": lab.get("org.opencontainers.image.revision"),
                         "label_created": lab.get("org.opencontainers.image.created")})
        else:
            info["docker_inspect_error"] = out.stderr.strip()[:300]
    except Exception as exc:  # noqa: BLE001
        info["docker_inspect_error"] = repr(exc)[:300]
    return info


def docker_df():
    try:
        out = subprocess.run(["docker", "exec", CONTAINER, "df", "-h", "/data"], capture_output=True, text=True, timeout=20)
        return out.stdout.strip().splitlines()[-1] if out.returncode == 0 else out.stderr.strip()[:200]
    except Exception as exc:  # noqa: BLE001
        return repr(exc)[:200]


# ----------------------------------------------------------------------------- main

def main():
    env = load_env(ENV_PATH)
    uri = env["LOCAL_URI"]
    secret = env.get("LOCAL_PASS")
    report = Report()
    meta = {"test": "query-behaviour", "run": "ENGINE 1.2.0 RERUN (compare with 0.117 results in ENGINE-TESTS.md)",
            "database": DB_NAME, "started_utc": now()}
    client = MongoClient(uri, serverSelectionTimeoutMS=15000, socketTimeoutMS=290000, event_listeners=[WIRE],
                         appname="engine-test-query-behaviour")
    bi = client.admin.command("buildInfo")
    he = client.admin.command("hello")
    meta["target"] = dict(docker_info(), **{
        "uri_redacted": redact_uri(uri),
        "driver": f"pymongo {pymongo.version}, Python {platform.python_version()}",
        "buildInfo": J(bi),
        "hello": J({k: v for k, v in he.items() if k not in ("localTime",)}),
        "documentdb_versions": J(he.get("internal", {}).get("documentdb_versions")),
        "docker_data_df_before": docker_df(),
    })
    db = client[DB_NAME]
    try:
        existed = DB_NAME in client.list_database_names()
        if existed:
            client.drop_database(DB_NAME)
        report.add("setup", "0.1", "start from an empty t_query",
                   f"'{DB_NAME}' in client.list_database_names(); client.drop_database('{DB_NAME}') if present",
                   {"outcome": "ok", "result": {"existed_before": existed}},
                   f"t_query {'existed and was dropped' if existed else 'did not exist'}; no other database was touched.")
        section_a(report, db)
        stats = seed_big(report, db)
        section_c_unindexed(report, db, "", "right after the bulk load")
        section_e(report, client, db)
        section_c_unindexed(report, db, "-post", "after the plan poll")
        section_b(report, db, stats)
        section_c(report, db)
        section_d(report, client, db)
    except Exception as exc:  # noqa: BLE001
        meta["aborted"] = {"exception": repr(exc), "traceback": traceback.format_exc()}
        print(meta["aborted"]["traceback"], file=sys.stderr)
    finally:
        try:
            client.drop_database(DB_NAME)
            gone = DB_NAME not in client.list_database_names()
            report.add("cleanup", "z.1", "drop the test database",
                       f"client.drop_database('{DB_NAME}'); '{DB_NAME}' in client.list_database_names()",
                       {"outcome": "ok", "result": {"dropped": True, "still_listed": not gone}},
                       f"t_query was dropped and is {'no longer listed' if gone else 'STILL listed'}.")
        except PyMongoError as exc:
            report.add("cleanup", "z.1", "drop the test database", f"client.drop_database('{DB_NAME}')",
                       error_record(exc), "Dropping t_query failed.")
        meta["target"]["docker_data_df_after"] = docker_df()
        meta["finished_utc"] = now()
        client.close()
    out = dict(meta)
    out["steps"] = report.steps
    text = json.dumps(out, indent=1, default=str)
    if secret and secret in text:
        text = text.replace(secret, "<redacted>")
    with open(REPORT_PATH, "w") as fh:
        fh.write(text)
    print(f"wrote {REPORT_PATH} with {len(report.steps)} steps", file=sys.stderr)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("finalize", os.path.join(HERE, "finalize.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.finalize(REPORT_PATH)
    except FileNotFoundError:
        print("finalize.py not found; report has raw steps only", file=sys.stderr)


if __name__ == "__main__":
    main()
