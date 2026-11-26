#!/usr/bin/env python
"""Follow-up probe for test "m-query" (run 5): explain plans for unindexed (and indexed) finds after
the service's autovacuum has processed the collections.

Owns database mt_query only (re-seeded, dropped at the end). Never prints or records the password or
a URI that contains it. Writes report.run5.json.

Runs 1-2 explained collections seconds after loading (collectionPlannerStatistics.allVisibleFraction
0.0). Run 4 showed the cursor plan for an indexed find changes once allVisibleFraction reaches 1.0.
This run waits for that (polling every 20 s, max 300 s) on a 50,000-doc and a 5,000-doc collection,
then repeats the unindexed-find explains across verbosities.
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

from pymongo import MongoClient, ASCENDING

import run as r1
import run2 as r2

DB_NAME = r1.DB_NAME
REPORT_PATH = r1.os.path.join(r1.HERE, "report.run5.json")


def cps(db, coll):
    out = db.command({"explain": {"find": coll, "filter": {"grp": 5}}, "verbosity": "queryPlanner"})
    node = out["queryPlanner"]["winningPlan"]
    while "collectionPlannerStatistics" not in node and "inputStage" in node:
        node = node["inputStage"]
    return r1.to_jsonable(node.get("collectionPlannerStatistics"))


def main():
    env = r1.load_env(r1.ENV_PATH)
    pw = env["MANAGED_PASS"]
    secret_forms = {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}
    report = r1.Report()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    client = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, socketTimeoutMS=540000,
                         appname="m-query-run5")
    dropped, fatal = False, None
    try:
        db = client[DB_NAME]
        for c in db.list_collection_names():
            db.drop_collection(c)
        rnd = random.Random(11)
        alphabet = string.ascii_lowercase
        big, mid = db["big"], db["mid"]
        batch, midbatch = [], []
        for i in range(r1.BIG_N):
            d = {"i": i, "rnd": rnd.random(), "grp": i % 97,
                 "payload": "".join(rnd.choice(alphabet) for _ in range(r1.PAYLOAD_LEN)),
                 "tags": [f"t{i % 13}", f"u{i % 7}"]}
            batch.append(d)
            if i < 5000:
                midbatch.append(dict(d))
            if len(batch) == r1.BATCH:
                big.insert_many(batch, ordered=False)
                batch = []
        mid.insert_many(midbatch, ordered=False)
        big.create_index([("i", ASCENDING)], name="i_1")
        loaded = time.time()
        report.add("setup5", "R5.1 reset mt_query; seed big (50,000 docs, same generator, index i_1) and mid (first 5,000 of the same docs, no secondary index)",
                   "db.big.insert_many(...) x 10 batches of 5000; db.mid.insert_many(5000 docs); db.big.create_index([('i', 1)], name='i_1')",
                   {"big": big.count_documents({}), "mid": mid.count_documents({})}, "Fresh collections for the post-vacuum explain matrix.")

        polls = []
        while True:
            row = {"seconds_since_load": round(time.time() - loaded, 1), "big": cps(db, "big"), "mid": cps(db, "mid")}
            polls.append(row)
            done = all((row[c] or {}).get("allVisibleFraction", 0) > 0 for c in ("big", "mid"))
            if done or time.time() - loaded > 300:
                break
            time.sleep(20)
        report.add("setup5", "R5.2 poll queryPlanner explain every 20 s until allVisibleFraction > 0 on both collections (max 300 s)",
                   "db.command({'explain': {'find': <coll>, 'filter': {'grp': 5}}, 'verbosity': 'queryPlanner'}) -> collectionPlannerStatistics",
                   polls, f"Last poll at {polls[-1]['seconds_since_load']} s: big {polls[-1]['big']}, mid {polls[-1]['mid']}.")

        shapes = [
            ("P1", "big", {"find": "big", "filter": {"rnd": {"$gt": 0.999}}}, "unindexed range on rnd, 50,000 docs",
             [None, "queryPlanner", "executionStats", "allPlansExecution"]),
            ("P2", "big", {"find": "big", "filter": {"grp": 5}}, "unindexed equality on grp, 50,000 docs",
             [None, "executionStats", "allPlansExecution"]),
            ("P3", "big", {"find": "big", "filter": {}}, "empty filter, 50,000 docs", ["executionStats", "allPlansExecution"]),
            ("P4", "mid", {"find": "mid", "filter": {"grp": 5}}, "unindexed equality on grp, 5,000 docs",
             [None, "executionStats", "allPlansExecution"]),
            ("P5", "big", {"find": "big", "filter": {"i": 12345}}, "indexed equality on i", ["executionStats", "allPlansExecution"]),
            ("P6", "big", {"find": "big", "filter": {"i": 12345}, "limit": 1, "singleBatch": True},
             "indexed equality, limit 1 singleBatch (find_one shape)", ["executionStats"]),
            ("P7", "big", {"find": "big", "filter": {"grp": 5}, "limit": 1, "singleBatch": True},
             "unindexed equality, limit 1 singleBatch (find_one shape)", ["executionStats"]),
            ("P8", "big", {"aggregate": "big", "pipeline": [{"$match": {"rnd": {"$gt": 0.999}}}, {"$sort": {"i": 1}}], "cursor": {}},
             "aggregate unindexed $match + $sort", ["executionStats", "allPlansExecution"]),
        ]
        matrix = {}
        for pid, coll, inner, desc, verbs in shapes:
            for v in verbs:
                cmd = {"explain": inner}
                if v:
                    cmd["verbosity"] = v
                vname = v or "none(default)"
                s = r2.explain_any(report, db, "a5", f"a5.{pid}.{vname}", f"post-vacuum explain {desc}, verbosity {vname}",
                                   cmd, f"post-vacuum {desc}, verbosity {vname}", open_source_step=None)
                if s:
                    leaf = s["stage_nodes"][-1] if s["stage_nodes"] else {}
                    roots = [n for n in s["stage_nodes"] if n["path"].endswith("winningPlan")]
                    matrix[f"{pid}/{vname}"] = {
                        "winningPlan_stages": s["stage_names_by_winningPlan"],
                        "has_COLLSCAN": s["has_COLLSCAN"],
                        "first_executionStats": s.get("first_executionStats"),
                        "executionStages_leaf": {k: leaf.get(k) for k in ("stage", "indexName", "totalDocsExamined",
                                                                          "totalDocsRemovedByRuntimeFilter", "nReturned") if k in leaf},
                    }
        report.add("a5", "a5.M matrix of the post-vacuum explains above", "(derived from steps a5.*; no server call)", matrix,
                   "Which verbosity and shape shows COLLSCAN after autovacuum; see the individual steps for raw documents.")

        client.drop_database(DB_NAME)
        dropped = True
        listed = DB_NAME in client.list_database_names()
        report.add("e5", "e5.1 drop database mt_query and verify",
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
                report.add("e5", "e5.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"dropped": True}, "Owned database dropped during cleanup.")
            except Exception as exc:  # noqa
                report.add("e5", "e5.1 drop database mt_query (cleanup after a fatal error)",
                           f"client.drop_database('{DB_NAME}')", {"exception": type(exc).__name__, "message": str(exc)},
                           "Cleanup drop failed; mt_query may still exist.")
        client.close()

    doc = {"test": "m-query (run 5 follow-up probe)", "database": DB_NAME, "started_utc": started,
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
