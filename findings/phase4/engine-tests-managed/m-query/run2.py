#!/usr/bin/env python
"""Follow-up probe for test "m-query" (run 2), written after reading run 1's results.

Owns database mt_query only (re-seeded with the same generators as run.py, dropped at the end).
Never prints or records the password or a URI that contains it. Writes report.run2.json.

Why a second run:
  a2  run 1 used verbosity 'executionStats' and never saw COLLSCAN for an unindexed find, while an
      earlier agent run on this cluster (runs/01-anti-money-laundering-pattern-detector/20261124-200112,
      MCP tool documentdb_explain_operation, explain with no verbosity) recorded winningPlan.stage
      COLLSCAN. This probe crosses verbosity (none, queryPlanner, executionStats, allPlansExecution)
      with collection size and filter shape.
  b2  run 1's find with maxTimeMS 1 failed on the find command itself, while on documentdb-local the
      raw find returned its first batch. Run 1's predicate matches 1.7% of documents, so the first
      batch needed a scan of several thousand documents; this probe separates "first batch took more
      than 1 ms" from "the cursor as a whole is limited", using fast-first-batch finds and getMores.
"""
import datetime as dt
import json
import random
import string
import sys
import time
import traceback
import urllib.parse
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

import bson
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

import run as r1  # helpers from run 1 (same directory)

DB_NAME = r1.DB_NAME
REPORT_PATH = r1.os.path.join(r1.HERE, "report.run2.json")
PAYLOAD_LEN = r1.PAYLOAD_LEN


def explain_any(report, db, section, step_id, label, explain_cmd, prefix, **extra):
    cmd_text = f"db.command({r1.jtxt(explain_cmd)})  # pymongo Database.command, database {DB_NAME}"
    t0 = time.time()
    try:
        out = db.command(explain_cmd)
        s = r1.summarize_explain(out)
        d = r1.to_jsonable(out)
        wp_root = {}
        for p in s["winningPlan_paths"][:1]:
            node = r1.get_path(d, p)
            wp_root = {k: node.get(k) for k in node if k not in ("inputStage", "inputStages")}
        fes = s.get("first_executionStats", {})
        reading = (f"{prefix}: winningPlan stages {s['stage_names_by_winningPlan']}; COLLSCAN "
                   f"{'present' if s['has_COLLSCAN'] else 'absent'}; executionStats "
                   f"{'present' if s['executionStats_paths'] else 'absent'}"
                   + (f" (nReturned {fes.get('nReturned')}, totalDocsExamined {fes.get('totalDocsExamined')})"
                      if fes else "") + ".")
        report.add(section, f"{step_id} {label}", cmd_text,
                   {"summary": s, "winningPlan_root_without_children": wp_root, "full_explain": d}, reading,
                   elapsed_ms=round((time.time() - t0) * 1000), **extra)
        return s
    except PyMongoError as exc:
        resp = r1.error_record(exc)
        report.add(section, f"{step_id} {label}", cmd_text, resp,
                   f"{prefix}: explain failed with code {resp.get('code')} {resp.get('codeName')}: {resp.get('errmsg')}",
                   elapsed_ms=round((time.time() - t0) * 1000), **extra)
        return None


def main():
    env = r1.load_env(r1.ENV_PATH)
    pw = env["MANAGED_PASS"]
    secret_forms = {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}
    report = r1.Report()
    recorder = r1.Recorder()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    client = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, socketTimeoutMS=540000,
                         appname="m-query-run2", event_listeners=[recorder])
    dropped, fatal = False, None
    try:
        hello = client.admin.command("hello")
        report.add("setup2", "R.0 hello (version check for run 2)", "client.admin.command('hello')",
                   {"maxWireVersion": hello.get("maxWireVersion"), "internal": r1.to_jsonable(hello.get("internal"))},
                   f"Same service build as run 1: maxWireVersion {hello.get('maxWireVersion')}, "
                   f"documentdb_versions {hello.get('internal', {}).get('documentdb_versions')}.")
        db = client[DB_NAME]
        existing = db.list_collection_names()
        for c in existing:
            db.drop_collection(c)
        report.add("setup2", "R.1 reset database mt_query", "db.list_collection_names(); drop each  # mt_query only",
                   {"collections_found": existing}, "Owned database was empty before run 2.")

        big = db["big"]
        rnd = random.Random(11)
        alphabet = string.ascii_lowercase
        t0 = time.time()
        batch, inserted = [], 0
        for i in range(r1.BIG_N):
            batch.append({"i": i, "rnd": rnd.random(), "grp": i % 97,
                          "payload": "".join(rnd.choice(alphabet) for _ in range(PAYLOAD_LEN)),
                          "tags": [f"t{i % 13}", f"u{i % 7}"]})
            if len(batch) == r1.BATCH:
                big.insert_many(batch, ordered=False)
                inserted += len(batch)
                batch = []
        if batch:
            big.insert_many(batch, ordered=False)
            inserted += len(batch)
        sales = db["sales"]
        srnd = random.Random(7)
        base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        sdocs = [{"region": region, "ts": base + dt.timedelta(days=i),
                  "amount": srnd.choice([5, 12, 3, 20, 7, 15, 1, 9]) + (i % 3)}
                 for region in ("east", "west", "north") for i in range(8)]
        sales.insert_many(sdocs)
        idx = big.create_index([("i", ASCENDING)], name="i_1")
        report.add("setup2", "R.2 re-seed big (50,000 docs, same generator as run 1), sales (24 docs) and index i_1",
                   "db.big.insert_many(...) x 10 batches of 5000 (random.Random(11), 32-char payload); "
                   "db.sales.insert_many(24 docs, random.Random(7)); db.big.create_index([('i', 1)], name='i_1')",
                   {"big_inserted": inserted, "big_count": big.count_documents({}), "sales_inserted": len(sdocs),
                    "index": idx, "elapsed_ms": round((time.time() - t0) * 1000)},
                   "Same data as run 1, re-created because run 1 dropped the database.")

        # ================= a2: explain verbosity x shape =================
        targets = [
            ("T1", "big", {"rnd": {"$gt": 0.999}}, "unindexed range on rnd, 50,000 docs"),
            ("T2", "sales", {"region": "east"}, "unindexed equality on region, 24 docs"),
            ("T3", "big", {}, "empty filter, 50,000 docs"),
            ("T4", "big", {"i": 12345}, "indexed equality on i"),
        ]
        verbosities = [None, "queryPlanner", "executionStats", "allPlansExecution"]
        matrix = {}
        for tid, coll, flt, desc in targets:
            for v in verbosities:
                cmd = {"explain": {"find": coll, "filter": flt}}
                if v:
                    cmd["verbosity"] = v
                vname = v or "none(default)"
                s = explain_any(report, db, "a2", f"a2.{tid}.{vname}", f"find {desc}, verbosity {vname}", cmd,
                                f"{desc}, verbosity {vname}",
                                open_source_step=("c.1" if (tid == "T1" and v == "executionStats") else
                                                  "c.3" if (tid == "T4" and v == "executionStats") else None))
                if s:
                    matrix[f"{tid}/{vname}"] = {
                        "winningPlan_stages": s["stage_names_by_winningPlan"],
                        "has_COLLSCAN": s["has_COLLSCAN"],
                        "executionStats_present": bool(s["executionStats_paths"]),
                        "first_executionStats": s.get("first_executionStats")}

        # PyMongo's own explain helper (what an agent typing cursor.explain() gets)
        recorder.begin()
        t0 = time.time()
        try:
            out = big.find({"rnd": {"$gt": 0.999}}).explain()
            sent = recorder.end()
            s = r1.summarize_explain(out)
            report.add("a2", "a2.H1 pymongo Cursor.explain() helper on the unindexed range find",
                       "db.big.find({'rnd': {'$gt': 0.999}}).explain()",
                       {"summary": s, "full_explain": r1.to_jsonable(out)},
                       f"PyMongo's helper sent {[e.get('command') for e in sent if e['event'] == 'started']}; winningPlan stages "
                       f"{s['stage_names_by_winningPlan']}; COLLSCAN {'present' if s['has_COLLSCAN'] else 'absent'}.",
                       driver_commands=sent, elapsed_ms=round((time.time() - t0) * 1000), open_source_step=None)
            matrix["H1/pymongo-helper"] = {"winningPlan_stages": s["stage_names_by_winningPlan"],
                                           "has_COLLSCAN": s["has_COLLSCAN"],
                                           "executionStats_present": bool(s["executionStats_paths"])}
        except PyMongoError as exc:
            recorder.end()
            report.add("a2", "a2.H1 pymongo Cursor.explain() helper on the unindexed range find",
                       "db.big.find({'rnd': {'$gt': 0.999}}).explain()", r1.error_record(exc),
                       r1.err_reading(exc, "explain helper failed"))

        agg_pipe = [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"i": 1}}]
        for v in (None, "queryPlanner"):
            cmd = {"explain": {"aggregate": "big", "pipeline": agg_pipe, "cursor": {}}}
            if v:
                cmd["verbosity"] = v
            vname = v or "none(default)"
            s = explain_any(report, db, "a2", f"a2.A.{vname}", f"aggregate unindexed $match + $sort, verbosity {vname}",
                            cmd, f"aggregate unindexed $match + $sort, verbosity {vname}", open_source_step=None)
            if s:
                matrix[f"A/{vname}"] = {"winningPlan_stages": s["stage_names_by_winningPlan"],
                                        "has_COLLSCAN": s["has_COLLSCAN"],
                                        "executionStats_present": bool(s["executionStats_paths"])}
        report.add("a2", "a2.M matrix of the explains above", "(derived from steps a2.*; no server call)",
                   matrix, "Summary of which verbosity and shape shows COLLSCAN; see the individual steps for raw documents.")

        # ================= b2: maxTimeMS, fast first batch vs whole cursor =================
        slow_filter = {"$and": [{"payload": {"$regex": "q.*z.*q.*z"}}, {"rnd": {"$lt": 0.5}},
                                {"$expr": {"$gt": [{"$strLenCP": "$payload"}, PAYLOAD_LEN - 1]}}]}
        explain_any(report, db, "b2", "b2.1", "explain executionStats of the slow predicate with limit 101 (first-batch cost)",
                    {"explain": {"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "limit": 101},
                     "verbosity": "executionStats"}, "Slow predicate, first 101 matches", open_source_step=None)
        explain_any(report, db, "b2", "b2.2", "explain executionStats of an empty filter with limit 101 (first-batch cost)",
                    {"explain": {"find": "big", "filter": {}, "projection": {"_id": 1}, "limit": 101},
                     "verbosity": "executionStats"}, "Empty filter, first 101 docs", open_source_step=None)

        r1.run_cmd(report, "b2", "b2.3 control: indexed point find {i: 12345} with max_time_ms(1), fully consumed",
                   "for d in db.big.find({'i': 12345}, {'_id': 0, 'i': 1}).max_time_ms(1): count",
                   lambda: r1.consume(big.find({"i": 12345}, {"_id": 0, "i": 1}).max_time_ms(1)),
                   lambda out: r1.consume_reading(out, "Indexed point find with maxTimeMS 1"), recorder=recorder,
                   open_source_step=None)
        r1.run_cmd(report, "b2", "b2.4 control: indexed point aggregate [{$match: {i: 12345}}] with maxTimeMS=1",
                   "list(db.big.aggregate([{'$match': {'i': 12345}}, {'$project': {'_id': 0, 'i': 1}}], maxTimeMS=1))",
                   lambda: list(big.aggregate([{"$match": {"i": 12345}}, {"$project": {"_id": 0, "i": 1}}], maxTimeMS=1)),
                   lambda out: f"Indexed point aggregate with maxTimeMS 1 completed: {r1.jtxt(out)}.",
                   lambda e: r1.err_reading(e, "Indexed point aggregate with maxTimeMS 1 failed"), recorder=recorder,
                   open_source_step=None)
        r1.run_cmd(report, "b2", "b2.5 find({}) with max_time_ms(1), default batch size, fully consumed (fast first batch, one large getMore)",
                   "for d in db.big.find({}, {'_id': 1}).max_time_ms(1): count",
                   lambda: r1.consume(big.find({}, {"_id": 1}).max_time_ms(1)),
                   lambda out: r1.consume_reading(out, "find({}) with maxTimeMS 1"), recorder=recorder,
                   open_source_step=None)

        def raw_then_getmore(flt, first_batch):
            first = db.command({"find": "big", "filter": flt, "projection": {"_id": 1}, "batchSize": first_batch,
                                "maxTimeMS": 1})
            cid = first["cursor"]["id"]
            out = {"find_reply": r1.trim_cursor_reply(first)}
            if cid:
                try:
                    gm = db.command({"getMore": cid, "collection": "big", "batchSize": 1_000_000})
                    out["getMore_reply"] = r1.trim_cursor_reply(gm)
                    cid = gm["cursor"]["id"]
                except PyMongoError as exc:
                    out["getMore_error"] = r1.error_record(exc)
                if cid:
                    try:
                        out["killCursors_reply"] = r1.to_jsonable(db.command({"killCursors": "big", "cursors": [cid]}))
                    except PyMongoError as exc:
                        out["killCursors_error"] = r1.error_record(exc)
            return out

        def rg_reading(out):
            fb = out["find_reply"]["cursor"].get("firstBatch_len")
            if "getMore_error" in out:
                e = out["getMore_error"]
                return (f"find with maxTimeMS 1 returned a first batch of {fb}; the following getMore (no maxTimeMS) failed "
                        f"with code {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}.")
            if "getMore_reply" in out:
                return (f"find with maxTimeMS 1 returned a first batch of {fb}; the following getMore (no maxTimeMS) returned "
                        f"{out['getMore_reply']['cursor'].get('nextBatch_len')} docs without error, so the limit was not "
                        f"carried to the getMore.")
            return f"find with maxTimeMS 1 returned {fb} docs and closed the cursor."
        r1.run_cmd(report, "b2", "b2.6 raw find {} batchSize 101 maxTimeMS 1, then raw getMore with no maxTimeMS (batchSize 1e6)",
                   "first = db.command({'find': 'big', 'filter': {}, 'projection': {'_id': 1}, 'batchSize': 101, 'maxTimeMS': 1}); "
                   "db.command({'getMore': first['cursor']['id'], 'collection': 'big', 'batchSize': 1000000}); killCursors if open",
                   lambda: raw_then_getmore({}, 101), rg_reading,
                   lambda e: r1.err_reading(e, "The initial find with maxTimeMS 1 failed"), open_source_step=None)
        r1.run_cmd(report, "b2", "b2.7 raw find slow predicate batchSize 1 maxTimeMS 1, then raw getMore with no maxTimeMS (batchSize 1e6)",
                   f"first = db.command({{'find': 'big', 'filter': {r1.jtxt(slow_filter)}, 'projection': {{'_id': 1}}, "
                   f"'batchSize': 1, 'maxTimeMS': 1}}); db.command({{'getMore': first['cursor']['id'], 'collection': 'big', "
                   f"'batchSize': 1000000}}); killCursors if open",
                   lambda: raw_then_getmore(slow_filter, 1), rg_reading,
                   lambda e: r1.err_reading(e, "The initial find with maxTimeMS 1 failed"), open_source_step=None)
        r1.run_cmd(report, "b2", "b2.8 find({}) with max_time_ms(1).batch_size(1000), fully consumed (about 50 small getMores)",
                   "for d in db.big.find({}, {'_id': 1}).max_time_ms(1).batch_size(1000): count",
                   lambda: r1.consume(big.find({}, {"_id": 1}).max_time_ms(1).batch_size(1000)),
                   lambda out: r1.consume_reading(out, "find({}) with maxTimeMS 1 and batch size 1000"), recorder=recorder,
                   open_source_step=None)
        r1.run_cmd(report, "b2", "b2.9 control: find({}) with max_time_ms(5000), fully consumed",
                   "for d in db.big.find({}, {'_id': 1}).max_time_ms(5000): count",
                   lambda: r1.consume(big.find({}, {"_id": 1}).max_time_ms(5000)),
                   lambda out: r1.consume_reading(out, "find({}) with maxTimeMS 5000"), recorder=recorder,
                   open_source_step=None)

        def repeat_raw():
            res = []
            for _ in range(3):
                t = time.time()
                try:
                    rep = db.command({"find": "big", "filter": slow_filter, "projection": {"_id": 1}, "maxTimeMS": 1})
                    res.append({"ok": True, "firstBatch_len": len(rep["cursor"]["firstBatch"]),
                                "elapsed_ms": round((time.time() - t) * 1000)})
                    if rep["cursor"]["id"]:
                        db.command({"killCursors": "big", "cursors": [rep["cursor"]["id"]]})
                except PyMongoError as exc:
                    e = r1.error_record(exc)
                    res.append({"ok": False, "code": e.get("code"), "codeName": e.get("codeName"), "errmsg": e.get("errmsg"),
                                "errorLabels": e.get("errorLabels"), "elapsed_ms": round((time.time() - t) * 1000)})
            return res
        r1.run_cmd(report, "b2", "b2.10 repeat run 1's raw find (slow predicate, maxTimeMS 1) three times",
                   f"3 x db.command({{'find': 'big', 'filter': {r1.jtxt(slow_filter)}, 'projection': {{'_id': 1}}, 'maxTimeMS': 1}})",
                   repeat_raw,
                   lambda out: f"Three repeats: {[(x.get('ok'), x.get('code'), x.get('codeName')) for x in out]}.",
                   open_source_step=None)

        def small_getmore():
            first = db.command({"find": "big", "filter": {}, "projection": {"_id": 1}, "batchSize": 2})
            cid = first["cursor"]["id"]
            out = {"find_reply": r1.trim_cursor_reply(first)}
            try:
                gm = db.command({"getMore": cid, "collection": "big", "batchSize": 2, "maxTimeMS": 1})
                out["getMore_reply"] = r1.trim_cursor_reply(gm)
                cid = gm["cursor"]["id"]
            except PyMongoError as exc:
                out["getMore_error"] = r1.error_record(exc)
            if cid:
                try:
                    out["killCursors_reply"] = r1.to_jsonable(db.command({"killCursors": "big", "cursors": [cid]}))
                except PyMongoError as exc:
                    out["killCursors_error"] = r1.error_record(exc)
            return out

        def sg_reading(out):
            if "getMore_error" in out:
                e = out["getMore_error"]
                return (f"A 2-document getMore carrying maxTimeMS 1 on a non-tailable cursor failed with code {e.get('code')} "
                        f"{e.get('codeName')}: {e.get('errmsg')}.")
            return (f"A 2-document getMore carrying maxTimeMS 1 on a non-tailable cursor was accepted and returned "
                    f"{out['getMore_reply']['cursor'].get('nextBatch_len')} docs (no validation error for maxTimeMS on getMore).")
        r1.run_cmd(report, "b2", "b2.11 raw getMore with maxTimeMS 1 and batchSize 2 on a non-tailable cursor (fast getMore)",
                   "first = db.command({'find': 'big', 'filter': {}, 'projection': {'_id': 1}, 'batchSize': 2}); "
                   "db.command({'getMore': first['cursor']['id'], 'collection': 'big', 'batchSize': 2, 'maxTimeMS': 1}); killCursors",
                   small_getmore, sg_reading, open_source_step=None)

        # ================= e2: drop =================
        client.drop_database(DB_NAME)
        dropped = True
        listed = DB_NAME in client.list_database_names()
        report.add("e2", "e2.1 drop database mt_query and verify",
                   f"client.drop_database('{DB_NAME}'); '{DB_NAME}' in client.list_database_names()",
                   {"dropped": True, "mt_query_still_listed": listed},
                   "Database mt_query dropped; it is " + ("still listed." if listed else "no longer listed."))
    except Exception as exc:
        fatal = {"exception": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        print("FATAL: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
    finally:
        if not dropped:
            try:
                client.drop_database(DB_NAME)
                report.add("e2", "e2.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"dropped": True}, "Owned database dropped during cleanup.")
            except Exception as exc:  # noqa
                report.add("e2", "e2.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"exception": type(exc).__name__, "message": str(exc)},
                           "Cleanup drop failed; mt_query may still exist.")
        client.close()

    doc = {"test": "m-query (run 2 follow-up probe)", "database": DB_NAME, "started_utc": started,
           "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "fatal_error": fatal, "config_changes": [],
           "steps": report.steps}
    text = r1.mask_text(json.dumps(doc, indent=2, default=str))
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
