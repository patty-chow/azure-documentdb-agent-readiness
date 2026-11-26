#!/usr/bin/env python
"""Follow-up probe for test "m-query" (run 3), written after reading run 2's results.

Owns database mt_query only (re-seeded with the same generators, dropped at the end). Never prints
or records the password or a URI that contains it. Writes report.run3.json.

Run 2 found that explain at verbosity allPlansExecution reports winningPlan COLLSCAN with
cursorScanType 'Primary Key Scan' and totalDocsExamined 50,000 even for an indexed equality
find (i_1 exists), while executionStats reports FETCH over IXSCAN i_1 with 1 document examined;
and that a real find {i: 12345} with maxTimeMS 1 fails with code 50. This run checks which of the
two plans real execution resembles, without any server-side instrumentation:
  t3  client-side latency medians, interleaved, for indexed / _id / unindexed full-scan queries
  m3  maxTimeMS sweep (1..64 ms, 3 attempts each): the smallest limit that passes bounds the
      server-side execution time of the real command as the gateway measures it
  x3  explain allPlansExecution for more shapes (limit/singleBatch, hint, aggregate, range, sort)
"""
import datetime as dt
import json
import random
import statistics
import string
import sys
import time
import traceback
import urllib.parse
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

import run as r1
import run2 as r2

DB_NAME = r1.DB_NAME
REPORT_PATH = r1.os.path.join(r1.HERE, "report.run3.json")


def main():
    env = r1.load_env(r1.ENV_PATH)
    pw = env["MANAGED_PASS"]
    secret_forms = {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}
    report = r1.Report()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    client = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, socketTimeoutMS=540000,
                         appname="m-query-run3")
    dropped, fatal = False, None
    try:
        hello = client.admin.command("hello")
        report.add("setup3", "R3.0 hello (version check for run 3)", "client.admin.command('hello')",
                   {"maxWireVersion": hello.get("maxWireVersion"), "internal": r1.to_jsonable(hello.get("internal"))},
                   f"Same service build: maxWireVersion {hello.get('maxWireVersion')}, documentdb_versions "
                   f"{hello.get('internal', {}).get('documentdb_versions')}.")
        db = client[DB_NAME]
        existing = db.list_collection_names()
        for c in existing:
            db.drop_collection(c)
        big = db["big"]
        rnd = random.Random(11)
        alphabet = string.ascii_lowercase
        t0 = time.time()
        batch = []
        for i in range(r1.BIG_N):
            batch.append({"i": i, "rnd": rnd.random(), "grp": i % 97,
                          "payload": "".join(rnd.choice(alphabet) for _ in range(r1.PAYLOAD_LEN)),
                          "tags": [f"t{i % 13}", f"u{i % 7}"]})
            if len(batch) == r1.BATCH:
                big.insert_many(batch, ordered=False)
                batch = []
        big.create_index([("i", ASCENDING)], name="i_1")
        target_id = big.find_one({"i": 12345}, {"_id": 1})["_id"]
        report.add("setup3", "R3.1 reset mt_query, re-seed big (50,000 docs, same generator) and index i_1",
                   "db.big.insert_many(...) x 10 batches of 5000; db.big.create_index([('i', 1)], name='i_1'); "
                   "db.big.find_one({'i': 12345}, {'_id': 1})",
                   {"collections_found_before": existing, "count": big.count_documents({}),
                    "elapsed_ms": round((time.time() - t0) * 1000), "target_id_found": target_id is not None},
                   "Same data as runs 1 and 2; _id of the i=12345 document captured for the _id lookup.")

        queries = {
            "Q1_find_i_cursor": ("list(db.big.find({'i': 12345}))", lambda mt=None: list(
                (big.find({"i": 12345}) if mt is None else big.find({"i": 12345}).max_time_ms(mt)))),
            "Q2_find_one_i": ("db.big.find_one({'i': 12345})  # limit 1, singleBatch", lambda mt=None: (
                big.find_one({"i": 12345}) if mt is None else big.find_one({"i": 12345}, max_time_ms=mt))),
            "Q3_find_id": ("list(db.big.find({'_id': <oid of i=12345>}))", lambda mt=None: list(
                (big.find({"_id": target_id}) if mt is None else big.find({"_id": target_id}).max_time_ms(mt)))),
            "Q4_find_unindexed_nomatch": ("list(db.big.find({'grp': -1}))  # unindexed, no match: full scan",
                                          lambda mt=None: list((big.find({"grp": -1}) if mt is None else
                                                                big.find({"grp": -1}).max_time_ms(mt)))),
            "Q5_aggregate_match_i": ("list(db.big.aggregate([{'$match': {'i': 12345}}]))", lambda mt=None: list(
                (big.aggregate([{"$match": {"i": 12345}}]) if mt is None else
                 big.aggregate([{"$match": {"i": 12345}}], maxTimeMS=mt)))),
            "Q6_find_i_hint": ("list(db.big.find({'i': 12345}).hint('i_1'))", lambda mt=None: list(
                (big.find({"i": 12345}).hint("i_1") if mt is None else
                 big.find({"i": 12345}).hint("i_1").max_time_ms(mt)))),
            "Q7_find_i_limit1": ("list(db.big.find({'i': 12345}).limit(1))", lambda mt=None: list(
                (big.find({"i": 12345}).limit(1) if mt is None else big.find({"i": 12345}).limit(1).max_time_ms(mt)))),
            "Q8_count_i": ("db.big.count_documents({'i': 12345})", lambda mt=None: (
                big.count_documents({"i": 12345}) if mt is None else big.count_documents({"i": 12345}, maxTimeMS=mt))),
        }

        # ---------------- t3: interleaved latency samples
        for name, (_, fn) in queries.items():  # warm-up, one each
            fn()
        samples = {k: [] for k in queries}
        N = 15
        for _ in range(N):
            for name, (_, fn) in queries.items():
                t = time.perf_counter()
                fn()
                samples[name].append(round((time.perf_counter() - t) * 1000, 2))
        summary = {k: {"median_ms": round(statistics.median(v), 2), "min_ms": min(v), "max_ms": max(v), "samples_ms": v}
                   for k, v in samples.items()}
        base = summary["Q3_find_id"]["median_ms"]
        for k in summary:
            summary[k]["median_minus_Q3_id_lookup_ms"] = round(summary[k]["median_ms"] - base, 2)
        report.add("t3", "t3.1 client-side latency, 15 interleaved rounds of 8 queries (after one warm-up each)",
                   {k: v[0] for k, v in queries.items()}, summary,
                   "Medians relative to the _id lookup (Q3): " + ", ".join(
                       f"{k} {summary[k]['median_minus_Q3_id_lookup_ms']:+.1f} ms" for k in summary) + ".")

        # ---------------- m3: maxTimeMS sweep
        sweep = {}
        for name, (_, fn) in queries.items():
            rows = []
            for mt in (1, 2, 4, 8, 16, 32, 64):
                ok, errs = 0, []
                for _ in range(3):
                    try:
                        fn(mt)
                        ok += 1
                    except PyMongoError as exc:
                        e = r1.error_record(exc)
                        errs.append({"code": e.get("code"), "codeName": e.get("codeName"), "errmsg": e.get("errmsg")})
                rows.append({"maxTimeMS": mt, "passed_of_3": ok,
                             "distinct_errors": [json.loads(x) for x in sorted({json.dumps(e, sort_keys=True) for e in errs})]})
            first_all = next((r["maxTimeMS"] for r in rows if r["passed_of_3"] == 3), None)
            sweep[name] = {"rows": rows, "smallest_maxTimeMS_passing_3_of_3": first_all}
        report.add("m3", "m3.1 maxTimeMS sweep: each query at maxTimeMS 1, 2, 4, 8, 16, 32, 64 (3 attempts each)",
                   {k: v[0] + "  with max_time_ms/maxTimeMS = N" for k, v in queries.items()}, sweep,
                   "Smallest maxTimeMS that passed 3 of 3: " + ", ".join(
                       f"{k} {v['smallest_maxTimeMS_passing_3_of_3']}" for k, v in sweep.items()) + ".")

        # ---------------- x3: allPlansExecution for more shapes
        shapes = [
            ("x3.1", "find {i: 12345} limit 1 singleBatch", {"find": "big", "filter": {"i": 12345}, "limit": 1, "singleBatch": True}),
            ("x3.2", "find {i: 12345} hint i_1", {"find": "big", "filter": {"i": 12345}, "hint": "i_1"}),
            ("x3.3", "find {i: {$gt: 49000}} (indexed range)", {"find": "big", "filter": {"i": {"$gt": 49000}}}),
            ("x3.4", "find {i: 12345} sort {i: 1}", {"find": "big", "filter": {"i": 12345}, "sort": {"i": 1}}),
            ("x3.5", "find {_id: <oid>}", {"find": "big", "filter": {"_id": target_id}}),
        ]
        for sid, label, inner in shapes:
            for v in ("executionStats", "allPlansExecution"):
                r2.explain_any(report, db, "x3", f"{sid}.{v}", f"explain {label}, verbosity {v}",
                               {"explain": inner, "verbosity": v}, f"{label}, {v}", open_source_step=None)
        for v in ("executionStats", "allPlansExecution"):
            r2.explain_any(report, db, "x3", f"x3.6.{v}", f"explain aggregate [$match {{i: 12345}}], verbosity {v}",
                           {"explain": {"aggregate": "big", "pipeline": [{"$match": {"i": 12345}}], "cursor": {}},
                            "verbosity": v}, f"aggregate $match i, {v}", open_source_step=None)

        client.drop_database(DB_NAME)
        dropped = True
        listed = DB_NAME in client.list_database_names()
        report.add("e3", "e3.1 drop database mt_query and verify",
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
                report.add("e3", "e3.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"dropped": True}, "Owned database dropped during cleanup.")
            except Exception as exc:  # noqa
                report.add("e3", "e3.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"exception": type(exc).__name__, "message": str(exc)},
                           "Cleanup drop failed; mt_query may still exist.")
        client.close()

    doc = {"test": "m-query (run 3 follow-up probe)", "database": DB_NAME, "started_utc": started,
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
