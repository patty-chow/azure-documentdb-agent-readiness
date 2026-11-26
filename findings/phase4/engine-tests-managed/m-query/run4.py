#!/usr/bin/env python
"""Follow-up probe for test "m-query" (run 4): does run 3's cursor-plan behaviour persist after the
collection has been vacuumed/analyzed by the service?

Owns database mt_query only (re-seeded with the same generator, dropped at the end). Never prints
or records the password or a URI that contains it. Writes report.run4.json.

Runs 1-3 measured collections seconds after loading. explain reports
queryPlanner.winningPlan.collectionPlannerStatistics {estimatedDocumentCount, allVisibleFraction};
allVisibleFraction stays 0.0 until a VACUUM has set the visibility map. This run measures once
right after loading (M0), polls a queryPlanner explain every 20 s for up to 300 s until
allVisibleFraction > 0 (evidence that autovacuum processed the table; an analyze normally runs in
the same pass, but this cannot be seen from the client), then measures again (M1).
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
REPORT_PATH = r1.os.path.join(r1.HERE, "report.run4.json")


def plan_stats(db):
    out = db.command({"explain": {"find": "big", "filter": {"i": 12345}}, "verbosity": "queryPlanner"})
    wp = out["queryPlanner"]["winningPlan"]
    return r1.to_jsonable(wp.get("collectionPlannerStatistics")), wp.get("stage")


def measure(report, db, big, target_id, tag):
    qs = {
        "Q1_find_i_cursor": lambda mt=None: list(big.find({"i": 12345}) if mt is None else big.find({"i": 12345}).max_time_ms(mt)),
        "Q3_find_id": lambda mt=None: list(big.find({"_id": target_id}) if mt is None else big.find({"_id": target_id}).max_time_ms(mt)),
        "Q4_find_unindexed_nomatch": lambda mt=None: list(big.find({"grp": -1}) if mt is None else big.find({"grp": -1}).max_time_ms(mt)),
        "Q5_aggregate_match_i": lambda mt=None: list(big.aggregate([{"$match": {"i": 12345}}]) if mt is None else
                                                     big.aggregate([{"$match": {"i": 12345}}], maxTimeMS=mt)),
        "Q6_find_i_hint": lambda mt=None: list(big.find({"i": 12345}).hint("i_1") if mt is None else
                                               big.find({"i": 12345}).hint("i_1").max_time_ms(mt)),
    }
    cmds = {"Q1_find_i_cursor": "list(db.big.find({'i': 12345}))", "Q3_find_id": "list(db.big.find({'_id': <oid>}))",
            "Q4_find_unindexed_nomatch": "list(db.big.find({'grp': -1}))",
            "Q5_aggregate_match_i": "list(db.big.aggregate([{'$match': {'i': 12345}}]))",
            "Q6_find_i_hint": "list(db.big.find({'i': 12345}).hint('i_1'))"}
    for fn in qs.values():
        fn()
    samples = {k: [] for k in qs}
    for _ in range(11):
        for k, fn in qs.items():
            t = time.perf_counter()
            fn()
            samples[k].append(round((time.perf_counter() - t) * 1000, 2))
    lat = {k: {"median_ms": round(statistics.median(v), 2), "min_ms": min(v), "samples_ms": v} for k, v in samples.items()}
    base = lat["Q3_find_id"]["median_ms"]
    for k in lat:
        lat[k]["median_minus_Q3_ms"] = round(lat[k]["median_ms"] - base, 2)
    sweep = {}
    for k in ("Q1_find_i_cursor", "Q5_aggregate_match_i", "Q6_find_i_hint"):
        rows = []
        for mt in (1, 2, 4, 8, 16, 32):
            ok = 0
            err = None
            for _ in range(3):
                try:
                    qs[k](mt)
                    ok += 1
                except PyMongoError as exc:
                    e = r1.error_record(exc)
                    err = {"code": e.get("code"), "codeName": e.get("codeName"), "errmsg": e.get("errmsg")}
            rows.append({"maxTimeMS": mt, "passed_of_3": ok, "last_error": err})
        sweep[k] = {"rows": rows, "smallest_passing_3_of_3": next((r["maxTimeMS"] for r in rows if r["passed_of_3"] == 3), None)}
    stats_now, _ = plan_stats(db)
    report.add(f"m4", f"{tag}.1 latency medians (11 interleaved rounds) and maxTimeMS sweep",
               {"latency": cmds, "sweep": "same calls with max_time_ms(N) / maxTimeMS=N, N in 1,2,4,8,16,32, 3 attempts each"},
               {"collectionPlannerStatistics_at_measurement": stats_now, "latency": lat, "sweep": sweep},
               f"{tag}: medians vs _id lookup " + ", ".join(f"{k} {v['median_minus_Q3_ms']:+.1f} ms" for k, v in lat.items())
               + "; smallest maxTimeMS passing 3/3: " + ", ".join(f"{k} {v['smallest_passing_3_of_3']}" for k, v in sweep.items())
               + f"; collectionPlannerStatistics {stats_now}.")
    for v in ("executionStats", "allPlansExecution"):
        r2.explain_any(report, db, "m4", f"{tag}.2.{v}", f"explain find {{i: 12345}}, verbosity {v}",
                       {"explain": {"find": "big", "filter": {"i": 12345}}, "verbosity": v}, f"{tag} find i, {v}",
                       open_source_step=None)
    r2.explain_any(report, db, "m4", f"{tag}.3.allPlansExecution", "explain aggregate [$match {i: 12345}], verbosity allPlansExecution",
                   {"explain": {"aggregate": "big", "pipeline": [{"$match": {"i": 12345}}], "cursor": {}},
                    "verbosity": "allPlansExecution"}, f"{tag} aggregate $match i, allPlansExecution", open_source_step=None)


def main():
    env = r1.load_env(r1.ENV_PATH)
    pw = env["MANAGED_PASS"]
    secret_forms = {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}
    report = r1.Report()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    client = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, socketTimeoutMS=540000,
                         appname="m-query-run4")
    dropped, fatal = False, None
    try:
        db = client[DB_NAME]
        for c in db.list_collection_names():
            db.drop_collection(c)
        big = db["big"]
        rnd = random.Random(11)
        alphabet = string.ascii_lowercase
        batch = []
        t_load = time.time()
        for i in range(r1.BIG_N):
            batch.append({"i": i, "rnd": rnd.random(), "grp": i % 97,
                          "payload": "".join(rnd.choice(alphabet) for _ in range(r1.PAYLOAD_LEN)),
                          "tags": [f"t{i % 13}", f"u{i % 7}"]})
            if len(batch) == r1.BATCH:
                big.insert_many(batch, ordered=False)
                batch = []
        big.create_index([("i", ASCENDING)], name="i_1")
        loaded_at = time.time()
        target_id = big.find_one({"i": 12345}, {"_id": 1})["_id"]
        report.add("setup4", "R4.1 reset mt_query, re-seed big (50,000 docs, same generator) and index i_1",
                   "db.big.insert_many(...) x 10 batches of 5000; db.big.create_index([('i', 1)], name='i_1')",
                   {"count": big.count_documents({}), "load_and_index_s": round(loaded_at - t_load, 1)},
                   "Same data as runs 1-3.")

        measure(report, db, big, target_id, "M0")

        polls = []
        t_poll = time.time()
        while True:
            st, stage = plan_stats(db)
            polls.append({"seconds_since_load": round(time.time() - loaded_at, 1),
                          "collectionPlannerStatistics": st, "winningPlan_stage_queryPlanner": stage})
            if (st or {}).get("allVisibleFraction", 0) > 0 or time.time() - t_poll > 300:
                break
            time.sleep(20)
        vacuumed = (polls[-1]["collectionPlannerStatistics"] or {}).get("allVisibleFraction", 0) > 0
        report.add("m4", "M.poll queryPlanner explain every 20 s until allVisibleFraction > 0 (max 300 s)",
                   "db.command({'explain': {'find': 'big', 'filter': {'i': 12345}}, 'verbosity': 'queryPlanner'}) "
                   "-> queryPlanner.winningPlan.collectionPlannerStatistics", polls,
                   (f"allVisibleFraction became {polls[-1]['collectionPlannerStatistics'].get('allVisibleFraction')} after "
                    f"{polls[-1]['seconds_since_load']} s, so a VACUUM had processed the table before M1."
                    if vacuumed else "allVisibleFraction stayed 0.0 for 300 s; M1 is measured anyway."))

        measure(report, db, big, target_id, "M1")

        client.drop_database(DB_NAME)
        dropped = True
        listed = DB_NAME in client.list_database_names()
        report.add("e4", "e4.1 drop database mt_query and verify",
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
                report.add("e4", "e4.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"dropped": True}, "Owned database dropped during cleanup.")
            except Exception as exc:  # noqa
                report.add("e4", "e4.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"exception": type(exc).__name__, "message": str(exc)},
                           "Cleanup drop failed; mt_query may still exist.")
        client.close()

    doc = {"test": "m-query (run 4 follow-up probe)", "database": DB_NAME, "started_utc": started,
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
