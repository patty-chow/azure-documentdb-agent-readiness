#!/usr/bin/env python
"""Post-run amendment of report.json for test query-behaviour.

Run 1 (2026-11-25 ~20:05 UTC) completed all 32 steps and wrote report.json.
Run 2 (an extended rerun adding steps c.1b-c.1d and d.6-d.11) failed while
re-seeding the 200k-document collection because the Docker VM disk (shared by
all images/volumes on this Mac) hit 100%; PostgreSQL inside the container
PANICked and shut down. This script records that incident, fixes two reading
sentences whose lambdas misread a wrapped response, and adds conclusions.
It does not touch the container.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "report.json")
r = json.load(open(PATH))

for s in r["steps"]:
    sid = s["step"].split(" ")[0]
    if sid == "c.5b":
        inner = s["response"].get("raw", {}).get("defaultShard", {})
        s["reading"] = ("vector-ivf index created; the createIndexes reply is wrapped as raw.defaultShard: "
                        f"numIndexesBefore {inner.get('numIndexesBefore')} -> numIndexesAfter {inner.get('numIndexesAfter')}, ok {inner.get('ok')}.")
    if sid == "d.5":
        s["reading"] = ("Control: with maxTimeMS 120000 the find matches 68160 docs in about 200 ms, the same as d.1 with maxTimeMS 1, "
                        "so on this engine the find/getMore path did not enforce maxTimeMS 1 while aggregate and count did (d.3, d.4).")
    if sid == "d.1":
        s["reading"] = ("find with maxTimeMS 1 completed and returned all 68160 matches in 191 ms with no error; the whole 200k scan "
                        "(first batch of 101 via find, remainder via one getMore without maxTimeMS, as pymongo sends it) exceeded 1 ms "
                        "yet no MaxTimeMSExpired was raised.")
    if sid == "d.2":
        s["reading"] = ("Raw find command with maxTimeMS 1 returned a 101-doc first batch and an open cursor in 2 ms without error; "
                        "the first batch is produced by streaming matches, so the command itself finished under the limit.")

r["run2_incident"] = {
    "what": "An extended rerun (steps c.1b, c.1c, c.1d, d.6-d.11 added to run.py) was started at about 20:11 UTC. "
            "It dropped the t_query collections and began re-seeding 200k docs; the 7th insert_many batch failed.",
    "driver_error": {"code": 14031, "codeName": "OutOfDiskSpace",
                     "errmsg": 'could not write to file "pg_wal/xlogtemp.1556": No space left on device'},
    "postgres_log": [
        '2026-11-25 20:11:09.942 UTC [1556] PANIC:  could not write to file "pg_wal/xlogtemp.1556": No space left on device',
        "2026-11-25 20:11:09.949 UTC [97] LOG:  server process (PID 1556) was terminated by signal 6: Aborted",
        '2026-11-25 20:11:10.030 UTC [1566] FATAL:  could not extend file "base/5/19395": No space left on device',
        "2026-11-25 20:11:10.032 UTC [97] LOG:  database system is shut down",
    ],
    "after_crash": "Every new connection fails during SCRAM authentication with {ok: 0, code: 1, codeName: 'InternalError', "
                   "errmsg: '[ActivityId=...] An unexpected internal error has occurred.'}; gateway log: 'Pool error due to generic postgres error: error connecting to server'.",
    "disk_state": "docker exec df -h: overlay / and /dev/vdb1 /data both 25G size, 24G used, 0 available (100%). /data holds only 284M "
                  "(base 96M, pg_wal 177M, core 12M); docker system df shows 14.17GB images (2.8GB reclaimable), 9.07GB volumes (4.29GB reclaimable). "
                  "The pressure comes from other Docker resources on this Mac, not from this test's data.",
    "action_taken": "None on the container or Docker: the task forbids dropping the container, and pruning other images/volumes is a destructive "
                    "action outside this test's scope that needs the user's explicit permission. The container was left running (gateway up, PostgreSQL down).",
    "consequence": "Steps c.1b-c.1d and d.6-d.11 exist in run.py but have no recorded results; rerun run.py once the Docker disk has free space. "
                   "All 32 steps below are from run 1, which completed before the disk filled.",
}

r["conclusions"] = {
    "a_setWindowFields": "Observed on documentdb-local (buildInfo version 7.0.0): two chained $setWindowFields stages, each with a cumulative "
                         "documents ['unbounded','current'] window ($sum, then $max), followed by $group with $last, ran and returned values equal to a client-side "
                         "computation, with and without an explicit $sort before $group (a.1, a.2). A single stage with both $sum and $max cumulative windows also matched (a.3). "
                         "A documents window without sortBy is rejected with code 5339901 Location5339901 'Missing sortBy field for document-based window' (a.4); "
                         "a range window without sortBy with code 5339902 Location5339902 'Expected a single sort by field for range-based window' (a.7); "
                         "['unbounded','unbounded'] without sortBy and no-window/no-sortBy outputs are accepted (a.5, a.6). Explain of the pipeline lists the window stages as '$sort' entries in the stages array (c.6).",
    "b_allowDiskUse": "aggregate with a full in-memory $sort of 200k docs on an unindexed field succeeded with allowDiskUse true (362 ms) and false (339 ms) with identical results; "
                      "find.allow_disk_use(True) also accepted. A non-boolean allowDiskUse is rejected with code 14 TypeMismatch, so the field is type-validated even though its value has no observable effect here.",
    "c_explain": "Top-level find explain: keys command, executionStats, explainCommandExecTimeMillis, explainCommandPlanningTimeMillis, explainVersion (2), ok, queryPlanner; winningPlan at queryPlanner.winningPlan. "
                 "Aggregate explain: keys command, explainCommandExecTimeMillis, explainCommandPlanningTimeMillis, explainVersion, ok, stages; each stages[i] has one key ($cursor, $sort, $limit, $project, $group) holding its own queryPlanner.winningPlan and executionStats, "
                 "so the plan lives at stages[0].$cursor.queryPlanner.winningPlan. Stage names seen: FETCH, IXSCAN, SORT, LIMIT, PROJECT, PROJECTION_DEFAULT, GROUP, GROUPSORT, COLLSCAN. "
                 "An unindexed predicate on the 200k collection did NOT produce COLLSCAN: it produced FETCH (runtimeFilterSet) over IXSCAN indexName '_id_' isBitmap true, totalDocsExamined 200000, totalKeysExamined 215 (c.1). "
                 "COLLSCAN appeared only inside the $setWindowFields ('$sort') sub-plans on the 24-doc collection (c.6). The vector pipeline explain (c.5d/c.5e) has the same stages[] layout: stages[0].$cursor winningPlan FETCH with cosmosSearchCustomParams {nProbes: 2} over IXSCAN indexName 'vec_ivf', direction Forward, hasOrderBy true, then $limit and $project stages; no SORT and no COLLSCAN stage. "
                 "A K32-style recursive walk for 'stage' keys finds these names; a COLLSCAN-only check would miss the _id_ IXSCAN full scan on this engine.",
    "d_maxTimeMS": "aggregate and count_documents with maxTimeMS 1 over 200k docs failed with code 50, codeName 'ExceededTimeLimit', errmsg 'Query exceeded command timeout of 1ms', no errorLabels (pymongo raises ExecutionTimeout). "
                   "Code 50 is MongoDB's MaxTimeMSExpired, but the codeName string differs from MongoDB's (MongoDB uses ExceededTimeLimit for code 262). "
                   "find with maxTimeMS 1 did NOT fail: cursor iteration returned all 68160 matches in about 190 ms (d.1), and the raw find returned its first batch in 2 ms (d.2); the remainder was fetched by getMore, which pymongo sends without maxTimeMS, "
                   "so on this engine the limit was not carried across the cursor. Steps d.6-d.9 (predicates that force the full scan inside the find command) were written but not executed because of the disk incident.",
    "scope": "All of the above is evidence about the open-source engine and gateway in documentdb-local at buildInfo version 7.0.0 (image ghcr.io/documentdb/documentdb/documentdb-local:latest); it does not prove managed Azure DocumentDB behaviour.",
}

json.dump(r, open(PATH, "w"), indent=2, default=str)
print("amended", PATH, "steps:", len(r["steps"]))
