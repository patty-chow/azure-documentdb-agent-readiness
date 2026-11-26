#!/usr/bin/env python
"""Assemble report.json for test m-query from the five raw run reports, add the per-step comparison
with the open-source engine results, and the conclusions. Reads only local files; no server calls."""
import json
import os
import re
import sys
import urllib.parse

import run as r1

HERE = r1.HERE
OS_REPORT = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/query-behaviour/report.json"
RUNS = [
    ("run1", "run.py", "report.run1.json",
     "Main test: sections (a) explain, (b) maxTimeMS, (c) $setWindowFields, (d) allowDiskUse, (e) drop."),
    ("run2", "run2.py", "report.run2.json",
     "Follow-up: explain verbosity x shape matrix (COLLSCAN question) and maxTimeMS first-batch vs whole-cursor probes."),
    ("run3", "run3.py", "report.run3.json",
     "Follow-up: latency medians and maxTimeMS sweep to see which plan real execution follows; more allPlansExecution shapes."),
    ("run4", "run4.py", "report.run4.json",
     "Follow-up: the same measurements before and after the service's autovacuum processed the collection."),
    ("run5", "run5.py", "report.run5.json",
     "Follow-up: unindexed-find explain matrix after autovacuum (COLLSCAN question, vacuumed collection)."),
]

os_doc = json.load(open(OS_REPORT))
os_steps = {s["step"].split(" ")[0]: s for s in os_doc["steps"]}


def os_obs(sid):
    s = os_steps.get(sid)
    if s is None:
        return None
    resp = s["response"]
    if isinstance(resp, dict) and "summary" in resp:
        sm = resp["summary"]
        return {"top_level_keys_sorted": sm.get("top_level_keys"), "winningPlan_paths": sm.get("winningPlan_paths"),
                "stage_names_in_order": sm.get("stage_names_in_order"), "executionStats_top": sm.get("executionStats_top"),
                "has_COLLSCAN": sm.get("has_COLLSCAN")}
    if isinstance(resp, dict) and "exception" in resp:
        return {k: resp.get(k) for k in ("code", "codeName", "errmsg", "errorLabels")}
    txt = json.dumps(resp)
    return txt if len(txt) <= 600 else txt[:600] + "...(truncated; see open-source report)"


ENVELOPE = ("explain document carries two extra top-level keys that the open-source 0.117 explain lacks: "
            "currentDateTime and instanceName ('ddb-samples-shared')")
NOT_RUN_OS = ("written in the open-source script but never executed there (Docker disk-full incident, "
              "query-behaviour/report.json run2_incident)")


def explain_compare(step, os_sid):
    """Compare a managed explain step with its open-source twin."""
    mresp = step["response"]
    o = os_steps.get(os_sid)
    if not (isinstance(mresp, dict) and "summary" in mresp and o and "summary" in o["response"]):
        return None
    ms, osm = mresp["summary"], o["response"]["summary"]
    same, diff = [], []
    (same if ms["winningPlan_paths"] == osm["winningPlan_paths"] else diff).append(
        f"winningPlan paths {ms['winningPlan_paths']} vs open-source {osm['winningPlan_paths']}")
    (same if ms["stage_names_in_order"] == osm["stage_names_in_order"] else diff).append(
        f"stage names {ms['stage_names_in_order']} vs open-source {osm['stage_names_in_order']}")
    (same if ms["has_COLLSCAN"] == osm["has_COLLSCAN"] else diff).append(
        f"COLLSCAN present: managed {ms['has_COLLSCAN']}, open-source {osm['has_COLLSCAN']}")
    mk, ok_ = set(ms["top_level_keys_server_order"]), set(osm["top_level_keys"])
    if mk == ok_:
        same.append("same top-level key set")
    else:
        diff.append(f"top-level keys: managed adds {sorted(mk - ok_)}" + (f", lacks {sorted(ok_ - mk)}" if ok_ - mk else "")
                    + " (explain envelope only)")
    plan_diff = [d for d in diff if "explain envelope only" not in d]
    return {"verdict": "same" if not plan_diff else "different", "same_aspects": same, "different_aspects": diff}


# step-id -> (verdict, open-source step, detail)
MAP = {
    "S.0": ("different", "target.hello/buildInfo",
            "Managed: maxWireVersion 25, documentdb_versions ['2.2-1','2.3.0','12.1-1'], kind 'azuredocumentdb', buildInfo 8.0.0, "
            "hello also carries endpointName and operationTime. Open-source 0.117: maxWireVersion 21, ['0.117-0','0.117.0'], kind '', "
            "buildInfo 7.0.0. Both: msg 'isdbgrid', maxWriteBatchSize 25000, saslSupportedMechs ['SCRAM-SHA-256']."),
    "S.1": ("n/a", None, "Setup."),
    "S.2": ("n/a", "0.2", "Setup. Open-source used 200,000 docs with 120-char payloads; this test 50,000 docs with 32-char payloads, "
                          "so counts differ by design."),
    "S.3": ("n/a", "a.0", "Same generator and seed as the open-source test; expected values identical (east 75/15, north 76/21, west 90/20)."),
    "S.4": ("n/a", None, "Setup for the exact L08 pipeline, which the open-source test did not run."),
    "a.1": ("explain", "c.1", "Both explains were taken seconds after loading: the managed explain reports "
                              "collectionPlannerStatistics.allVisibleFraction 0.0; the whole open-source run took 10 s "
                              "(20:08:35-20:08:45 UTC) and its explain has no collectionPlannerStatistics field. After autovacuum the "
                              "managed plan for the same find is a root COLLSCAN (run5 a5.P1)."),
    "a.1b": ("not_tested_locally", "c.1b", NOT_RUN_OS + "."),
    "a.1c": ("not_tested_locally", "c.1c", NOT_RUN_OS + "."),
    "a.1d": ("not_tested_locally", "c.1d", NOT_RUN_OS + "."),
    "a.2": ("same", "c.2", "Index created; create_index returns its name."),
    "a.3": ("explain", "c.3", ""),
    "a.3b": ("explain", "c.3b", ""),
    "a.4": ("explain", "c.4", ""),
    "a.4b": ("explain", "c.4b", ""),
    "a.5a": ("n/a", "c.5a", "Same generator and seed as the open-source vec collection."),
    "a.5b": ("same", "c.5b", "Same reply shape: {raw: {defaultShard: {numIndexesBefore: 1, numIndexesAfter: 2, createdCollectionAutomatically: false, ok: 1}}, ok: 1}."),
    "a.5b2": ("same", "vector-index-rules (listIndexes)",
              "Options are reported under cosmosSearchOptions and the key as {embedding: 'cosmosSearch'}, as ENGINE-TESTS.md records for the "
              "open-source gateway; there is no separate cosmosSearch options key."),
    "a.5c": ("same", "c.5c", "Same five neighbours in the same order (k 201, 122, 91, 181, 266); scores agree to 6 decimal places "
                             "(largest difference about 1e-7), and equal the exact cosine similarities computed client-side."),
    "a.5d": ("explain", "c.5d", "Both: FETCH with cosmosSearchCustomParams {nProbes: 2} over IXSCAN vec_ivf (direction Forward, hasOrderBy true)."),
    "a.5e": ("explain", "c.5e", ""),
    "a.6": ("explain", "c.6", "COLLSCAN appears only inside the $setWindowFields ('$sort') sub-plans, on both."),
    "b.0": ("same", "d.0", "Baseline completes on both (861 matches here, 68,160 on the open-source data)."),
    "b.0b": ("not_tested_locally", None, "Open-source test had no explain of its slow predicate."),
    "b.1": ("different", "d.1",
            "Open-source: completed with all 68,160 matches and no error. Managed: the initial find command itself failed with 50 "
            "ExceededTimeLimit before any document was returned. The data differ: here 1.7% of documents match, so producing the first "
            "batch of 101 takes about 3.5 ms server-side (run2 b2.1), while on the open-source data 34% matched and the first batch was "
            "cheap. Run 2 shows the managed limit behaves like the open-source observation when the first batch is cheap: the find "
            "succeeds and getMores sent without maxTimeMS are not limited (b2.5, b2.6, b2.8)."),
    "b.2": ("different", "d.2",
            "Open-source: raw find with maxTimeMS 1 returned a 101-doc first batch in 2 ms. Managed: code 50 ExceededTimeLimit on the "
            "find command (first-batch cost about 3.5 ms; see b.1)."),
    "b.3": ("same", "d.3", "Both: code 50, codeName ExceededTimeLimit, errmsg 'Query exceeded command timeout of 1ms', no errorLabels."),
    "b.4": ("same", "d.4", "Both: code 50 ExceededTimeLimit 'Query exceeded command timeout of 1ms', no errorLabels (count_documents is sent as aggregate)."),
    "b.5": ("same", "d.5", "Control completes on both."),
    "b.6": ("not_tested_locally", "d.6", NOT_RUN_OS + "."),
    "b.6b": ("not_tested_locally", "d.6b", NOT_RUN_OS + "."),
    "b.7": ("not_tested_locally", "d.7", NOT_RUN_OS + "."),
    "b.8": ("not_tested_locally", "d.8", NOT_RUN_OS + "."),
    "b.9": ("not_tested_locally", "d.9", NOT_RUN_OS + "."),
    "b.10": ("not_tested_locally", "d.10", NOT_RUN_OS + "."),
    "b.11": ("not_tested_locally", "d.11", NOT_RUN_OS + "."),
    "c.1": ("same", "a.1", "Identical result documents: east 75/15, north 76/21, west 90/20, n 8, lastTs 2026-01-08."),
    "c.2": ("same", "a.2", "Identical result documents."),
    "c.3": ("same", "a.3", "Identical rows: runningTotal 15,19,22,27,40,54,69,75; runningMax 15 throughout."),
    "c.4": ("not_tested_locally", None, "The exact L08 pipeline (with $set drawdown and $max/$last in $group) was not run on the open-source "
                                        "engine; its two-stage equivalent (open-source a.1, managed c.1) matched on both."),
    "c.4b": ("not_tested_locally", None, "Variant of the L08 pipeline; not run on the open-source engine."),
    "c.5": ("same", "a.4", "Both: code 5339901, codeName Location5339901, 'Missing sortBy field for document-based window'."),
    "c.5b": ("not_tested_locally", None, "Open-source tested only ['unbounded','current'] for the documents window."),
    "c.6": ("same", "a.5", "Accepted on both; same totals 75/76/90."),
    "c.7": ("same", "a.6", "Accepted on both; same totals 75/76/90."),
    "c.8": ("same", "a.7", "Both: code 5339902, codeName Location5339902, 'Expected a single sort by field for range-based window'."),
    "c.8b": ("not_tested_locally", None, "Open-source tested only ['unbounded','current'] for the range window."),
    "c.9": ("not_tested_locally", None, "Not tested on the open-source engine (matches the message in its source)."),
    "c.10": ("not_tested_locally", None, "Not tested on the open-source engine (matches the message in its source)."),
    "d.1": ("same", "b.1", "Accepted on both with correct results."),
    "d.2": ("same", "b.2", "Accepted on both with results identical to allowDiskUse true."),
    "d.2b": ("not_tested_locally", None, "Open-source had no no-option control."),
    "d.3": ("same", "b.3", "Both: code 14 TypeMismatch, \"The BSON field 'allowDiskUse' has an incorrect type 'string'; it should be of type 'bool'.\""),
    "d.3b": ("not_tested_locally", None, "Open-source tested only a string."),
    "d.3c": ("not_tested_locally", None, "Open-source tested only a string."),
    "d.4": ("same", "b.4", "find with allowDiskUse true accepted on both."),
    "e.1": ("n/a", None, "Cleanup."),
}
RUN2_MAP = {
    "a2.T1.executionStats": ("explain", "c.1", "Same as run1 a.1 (fresh collection)."),
    "a2.T4.executionStats": ("explain", "c.3", "Same as run1 a.3."),
}


def verdict_for(run, step):
    sid = step["step"].split(" ")[0]
    if run == "run1":
        entry = MAP.get(sid)
    else:
        entry = RUN2_MAP.get(sid) if run == "run2" else None
        if entry is None:
            if sid.startswith(("R.", "R3.", "R4.", "R5.", "e2.", "e3.", "e4.", "e5.")) or sid.endswith(".M") or sid.startswith("M.poll"):
                entry = ("n/a", None, "Setup, cleanup or derived summary.")
            else:
                note = "The open-source test did not run this probe."
                if sid in ("b2.5", "b2.6", "b2.8"):
                    note += (" The pattern (first batch returned under maxTimeMS 1, getMore without maxTimeMS not limited) matches what "
                             "the open-source d.1/d.2 steps showed.")
                if sid.startswith("a5."):
                    note += (" The open-source c.1 explain was taken on a freshly loaded collection, which is the condition of managed "
                             "run1 a.1 (same result); this vacuumed-collection case was not examined there.")
                entry = ("not_tested_locally", None, note)
    verdict, os_sid, detail = entry
    out = {"open_source_step": os_sid}
    if verdict == "explain":
        cmp_ = explain_compare(step, os_sid)
        out.update(cmp_ or {"verdict": "inconclusive"})
        if detail:
            out["detail"] = detail
        out["different_aspects"] = [d.replace(" (explain envelope only)", "") + " (explain envelope only; " + ENVELOPE + ")"
                                    if "explain envelope only" in d else d for d in out.get("different_aspects", [])]
    else:
        out["verdict"] = verdict
        out["detail"] = detail
    if os_sid and os_sid in os_steps:
        out["open_source_observation"] = os_obs(os_sid)
    return out


all_steps = []
runs_meta = []
for run, script, fname, purpose in RUNS:
    d = json.load(open(os.path.join(HERE, fname)))
    runs_meta.append({"run": run, "script": os.path.join(HERE, script), "raw_report": os.path.join(HERE, fname),
                      "started_utc": d.get("started_utc"), "finished_utc": d.get("finished_utc"), "purpose": purpose,
                      "fatal_error": d.get("fatal_error"), "steps": len(d["steps"])})
    for s in d["steps"]:
        s2 = {"run": run, "script": os.path.join(HERE, script)}
        s2.update(s)
        s2.pop("open_source_step", None)
        s2["vs_open_source"] = verdict_for(run, s)
        all_steps.append(s2)
run1 = json.load(open(os.path.join(HERE, "report.run1.json")))

CONCLUSIONS = [
    {"question": "(a) Where does winningPlan live in find and aggregate explain output?",
     "answer": ("find: queryPlanner.winningPlan. aggregate: a top-level stages[] array whose entries each have one key ($cursor, $sort, "
                "$limit, $project, $group) holding their own queryPlanner.winningPlan and executionStats; the scan plan is at "
                "stages[0].$cursor.queryPlanner.winningPlan. The $search cosmosSearch pipeline uses the same stages[] layout "
                "($cursor, $limit, $project). explainVersion is 2."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 a.1-a.6", "run2 a2.*", "run5 a5.*"]},
    {"question": "(a) What are the top-level keys of an explain document?",
     "answer": ("In server order, at executionStats or allPlansExecution: explainVersion, currentDateTime, command (a mongosh-style "
                "string echo of the command, without the verbosity), explainCommandPlanningTimeMillis, explainCommandExecTimeMillis, "
                "instanceName ('ddb-samples-shared'), queryPlanner, executionStats, ok. With no verbosity or queryPlanner the "
                "two timing keys and executionStats are absent. For aggregate, stages replaces queryPlanner and executionStats. "
                "The open-source 0.117 explain has the same keys except currentDateTime and instanceName."),
     "vs_open_source": "different", "confidence": "observed", "evidence": ["run1 a.1", "run1 a.4", "run1 a.5e", "run2 a2.T1.*"]},
    {"question": "(a) Which stage names appear?",
     "answer": ("FETCH, IXSCAN, COLLSCAN, SORT, LIMIT, PROJECT, PROJECTION_DEFAULT, GROUP and GROUPSORT; nothing else in any explain of "
                "the five runs. The chained $setWindowFields explain has the same 28-entry stage-name sequence as on the open-source "
                "engine, including COLLSCAN inside the window ('$sort') sub-plans."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 a.*", "run2 a2.*", "run3 x3.*", "run5 a5.*"]},
    {"question": "(a) Is COLLSCAN ever shown for the unindexed find?",
     "answer": ("Yes, but it depends on whether the service's autovacuum has processed the collection and on the verbosity. Freshly "
                "loaded collection (collectionPlannerStatistics.allVisibleFraction 0.0, the first roughly 20-30 s after a 50,000-doc "
                "load): with no verbosity, queryPlanner or executionStats, the unindexed find (range, equality, empty filter, 24-doc "
                "collection) shows FETCH with runtimeFilterSet over IXSCAN on _id_ with isBitmap true, and no COLLSCAN. This is what the "
                "open-source test saw on its freshly loaded data. allPlansExecution instead shows winningPlan COLLSCAN with "
                "cursorScanType 'Primary Key Scan' on _id_. After autovacuum (allVisibleFraction 1.0, observed 20-31 s after loading), "
                "the unindexed find shows a root COLLSCAN (with ns and collectionPlannerStatistics) with no verbosity, queryPlanner or "
                "executionStats, on both the 50,000-doc and a 5,000-doc collection. allPlansExecution shows FETCH (cursorScanType "
                "'Primary Key Scan') over IXSCAN _id_ for the same full scan. COLLSCAN also appears for a limit-1 singleBatch find "
                "(LIMIT over COLLSCAN) and inside $setWindowFields sub-plans. The earlier agent run's COLLSCAN "
                "(runs/01-anti-money-laundering-pattern-detector/20261124-200112) matches the vacuumed-collection case: root COLLSCAN "
                "with ns, plus execution timing keys. So a COLLSCAN-only check misses full scans in some states and labels in others."),
     "vs_open_source": "same", "confidence": "observed",
     "evidence": ["run1 a.1-a.1d", "run2 a2.T1-T3 (all verbosities)", "run5 a5.P1-P4", "run5 a5.P7", "run3 x3.1"]},
    {"question": "(a) totalDocsExamined and nReturned for the four required explains",
     "answer": ("Unindexed range find {rnd: {$gt: 0.999}} on 50,000 docs: nReturned 45, totalDocsExamined 50,000 (FETCH removed 49,955 "
                "by runtime filter); equality {grp: 5}: 516 / 50,000; empty filter: 50,000 / 50,000; 24-doc collection: 8 / 24. Indexed "
                "find {i: 12345}: 1 / 1 on i_1; indexed range with sort: 999 / 999. Aggregate $match(i) + $sort(rnd) + $limit: "
                "stages[0].$cursor 999 / 999, $sort and $limit stages 10 / 10; unindexed $match + $sort: stages[0].$cursor 45 / 50,000. "
                "$search cosmosSearch k 5 on vector-ivf: 5 / 5. Caveat: the top-level executionStats reports the root stage's counts. "
                "For a LIMIT-rooted plan it showed totalDocsExamined 1 while the leaf COLLSCAN examined 12,346 (fresh collection, "
                "run3 x3.1) or 6 (run5 a5.P7). So nReturned against totalDocsExamined is only reliable when read from the leaf scan "
                "stage, or from totalDocsRemovedByRuntimeFilter."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 a.1-a.5d", "run3 x3.1", "run5 a5.P7"]},
    {"question": "(a) Explain layout of a $search cosmosSearch pipeline on a vector-ivf index (DECISIONS topic 10 open item 3)",
     "answer": ("stages[0].$cursor.queryPlanner.winningPlan is FETCH with cosmosSearchCustomParams {nProbes: 2} over IXSCAN indexName "
                "vec_ivf, direction Forward, hasOrderBy true; then a $limit stage (LIMIT) and a $project stage (PROJECT). executionStats: "
                "nReturned 5, totalDocsExamined 5, totalKeysExamined 5. No SORT and no COLLSCAN anywhere. queryPlanner verbosity gives "
                "the same plan without executionStats. The search returned the same five neighbours in the same order as the "
                "open-source engine on identical data, with scores equal to the exact cosine similarities to 6 decimals. listIndexes "
                "reports cosmosSearchOptions {kind: 'vector-ivf', numLists: 2, similarity: 'COS', dimensions: 8}."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 a.5b-a.5e"]},
    {"question": "(a) Does the explain verbosity change the plan reported?",
     "answer": ("Yes. With no verbosity, queryPlanner or executionStats the explain shows the ordinary planner plan. With "
                "allPlansExecution it shows the plan of the streaming cursor a real find uses (a cursorScanType field: 'Primary Key "
                "Scan', 'Secondary Index Scan'). On a freshly loaded collection that cursor plan was a full Primary Key Scan even for an "
                "indexed equality, an indexed range and an aggregate $match on the indexed field: COLLSCAN, totalDocsExamined 50,000 for "
                "1 or 999 returned. executionStats meanwhile showed IXSCAN i_1 with 1 document examined. Real execution followed the "
                "cursor plan. Run 3 median latency against an _id lookup: find {i: 12345} +14.0 ms and aggregate +13.2 ms, against +15.1 "
                "ms for an unindexed full scan; with hint('i_1') +1.4 ms and count_documents +0.6 ms. The smallest maxTimeMS that passed "
                "3 of 3 was 16-32 ms for the find, 16 for the aggregate and the full scan, and 1 for the _id lookup, the hinted find and "
                "count_documents. After autovacuum (allVisibleFraction 1.0, about 30 s after loading) allPlansExecution showed 'Secondary "
                "Index Scan' on i_1. The same find and aggregate then ran at _id-lookup latency (+2.9 and +0.8 ms) and passed at "
                "maxTimeMS 1. hint('i_1') or a sort on the indexed field made the cursor use the index even before autovacuum."),
     "vs_open_source": "not_tested_locally", "confidence": "inferred",
     "evidence": ["run2 a2.T4.allPlansExecution", "run3 t3.1", "run3 m3.1", "run3 x3.2-x3.6", "run4 M0.*", "run4 M.poll", "run4 M1.*"]},
    {"question": "(a) What does explain return when no verbosity is given (PyMongo Cursor.explain())?",
     "answer": ("PyMongo 4.20.1's Cursor.explain() sends {explain: {find: ...}} with no verbosity field. The managed service then "
                "answers at queryPlanner level: explainVersion, currentDateTime, command, instanceName, queryPlanner, ok; no "
                "executionStats and no timing keys. The plan is identical to verbosity 'queryPlanner'. (MongoDB documents "
                "allPlansExecution as the explain command's default.)"),
     "vs_open_source": "not_tested_locally", "confidence": "observed", "evidence": ["run2 a2.H1", "run2 a2.T*.none(default)"]},
    {"question": "(b) maxTimeMS 1 on an aggregate: code and codeName?",
     "answer": ("Code 50, codeName 'ExceededTimeLimit', errmsg 'Query exceeded command timeout of 1ms' (the number tracks the limit, "
                "e.g. 'of 8ms'). No errorLabels field. PyMongo raises pymongo.errors.ExecutionTimeout, whose timeout property is True. "
                "count_documents, which PyMongo sends as aggregate, fails identically. Never 'MaxTimeMSExpired', which is MongoDB's "
                "codeName for code 50."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 b.3", "run1 b.4", "run2 b2.4"]},
    {"question": "(b) maxTimeMS 1 on a find whose cursor is fully consumed: code and codeName?",
     "answer": ("When the find command has to work more than about 1 ms to produce its first batch, the find command itself fails "
                "before any document is returned. That covered the slow predicate with default batch, batch size 50, a predicate "
                "matching nothing, an unindexed sort with limit 5, the raw find and singleBatch, and an indexed predicate on a "
                "not-yet-vacuumed collection. It fails with code 50 'ExceededTimeLimit', 'Query exceeded command timeout of 1ms', no "
                "errorLabels, PyMongo ExecutionTimeout. When the first batch is cheap (find({}), or batchSize 1), the find succeeds "
                "and the cursor is fully consumed with no error. PyMongo sends getMore without maxTimeMS and the service does not "
                "carry the find's limit to it: 50,000 docs came back through one getMore, or through 49 getMores of 1,000. Never "
                "'MaxTimeMSExpired'. The open-source run's find never failed because its first batch was cheap. That is the same "
                "per-command behaviour, but the observed result for the same step differs."),
     "vs_open_source": "different", "confidence": "observed",
     "evidence": ["run1 b.1", "run1 b.2", "run1 b.6-b.9", "run2 b2.1-b2.10", "run3 m3.1"]},
    {"question": "(b) Is maxTimeMS on a getMore accepted and enforced?",
     "answer": ("Accepted and enforced on a non-tailable find cursor. A 2-document getMore with maxTimeMS 1 succeeded. A getMore with "
                "maxTimeMS 1 and batchSize 1,000,000 failed with code 50 ExceededTimeLimit 'Query exceeded command timeout of 1ms', and "
                "the cursor was then gone (killCursors returned cursorsNotFound for it)."),
     "vs_open_source": "not_tested_locally", "confidence": "observed", "evidence": ["run1 b.10", "run2 b2.11"]},
    {"question": "(c) Does the two-stage $setWindowFields example (cumulative ['unbounded','current'] with $sum and $max, then $group with $last) run and give correct values?",
     "answer": ("Yes. On the same 24 documents as the open-source test it returned the same documents: east finalTotal 75 / finalMax 15, "
                "north 76/21, west 90/20, each n 8, matching a client-side computation. That held with and without a $sort before "
                "$group, and a single stage holding both cumulative outputs also matched row by row."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 c.1", "run1 c.2", "run1 c.3"]},
    {"question": "(c) Does the exact L08 example (two chained cumulative windows, $set drawdown, $sort, $group with $max and $last) run as written? (DECISIONS topic 10 open item 2)",
     "answer": ("Yes. With the $match on 'momentum-1' it returned [{_id: 'momentum-1', maxDrawdown: 246, finalPnl: -58}]. Without the "
                "$match it returned breakout-3 157/123, meanrev-2 67/289 and momentum-1 246/-58. Both equal the client-side computation "
                "over 90 trades."),
     "vs_open_source": "not_tested_locally", "confidence": "observed", "evidence": ["run1 c.4", "run1 c.4b"]},
    {"question": "(c) sortBy-required error codes for a bounded documents window and a range window",
     "answer": ("Documents window without sortBy, both ['unbounded','current'] and [-1, 0]: code 5339901, codeName 'Location5339901', "
                "'Missing sortBy field for document-based window'. Range window without sortBy, both ['unbounded','current'] and "
                "[-1, 0], and also with a compound sortBy {ts: 1, amount: 1}: code 5339902, codeName 'Location5339902', 'Expected a "
                "single sort by field for range-based window'. Range window with a descending sortBy {ts: -1}: code 9 'FailedToParse', "
                "'Expected ascending sortBy field definition'. No errorLabels on any of them. A fully unbounded documents window and "
                "an output with no window are accepted without sortBy."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 c.5-c.10"]},
    {"question": "(d) allowDiskUse true, false and non-boolean on aggregate",
     "answer": ("true, false and no option are all accepted. A full $sort of 50,000 documents on an unindexed field gave identical "
                "results each time (n 50000, the same first and last values), in 216, 238 and 275 ms client-side, which over this "
                "connection cannot tell them apart. A non-boolean is rejected with code 14 'TypeMismatch': string 'yes' gives \"The "
                "BSON field 'allowDiskUse' has an incorrect type 'string'; it should be of type 'bool'.\", and int 1 and null get the "
                "same message with 'int' and 'null'. find with allowDiskUse true is accepted."),
     "vs_open_source": "same", "confidence": "observed", "evidence": ["run1 d.1-d.4"]},
    {"question": "Was database mt_query dropped and was any other database touched?",
     "answer": ("Each of the five runs re-created mt_query, dropped it at the end, and checked that list_database_names no longer "
                "lists it. No other database was read or written; list_database_names was used only to check for mt_query."),
     "vs_open_source": "n/a", "confidence": "observed", "evidence": ["run1 e.1", "run2 e2.1", "run3 e3.1", "run4 e4.1", "run5 e5.1"]},
]

NOTES = [
    "Facts are observations of the managed service on 2026-11-25 at hello.maxWireVersion 25, documentdb_versions ['2.2-1','2.3.0','12.1-1'].",
    "Other tests ran against the same cluster in other databases at the same time. Latency numbers are client-observed medians over "
    "a ~75 ms round trip; only the large differences (>= ~10 ms) are interpreted.",
    "The 'real execution follows the allPlansExecution cursor plan' reading is inferred from client-side latency and maxTimeMS "
    "thresholds; no server-side instrumentation was available. The latency and maxTimeMS evidence agree with each other and with the "
    "allPlansExecution explain, and the switch at allVisibleFraction 0 -> 1 was seen by all three.",
    "One maxTimeMS sweep cell was non-monotonic (run4 M1, hinted find: 0 of 3 at 8 ms, 3 of 3 at 1, 2, 4, 16, 32 ms), so single "
    "observations within a few ms are noisy.",
    "Engine source context (open-source main a5f1636, not necessarily the managed build): pg_documentdb/src/customscan/"
    "dynamic_cursor_scan.c plans the first page of a streaming cursor, converting a SeqScan path to a 'Primary Key Scan' and "
    "emitting cursorScanType values 'Primary Key Scan', 'Secondary Index Scan', 'Secondary Index Bitmap Scan', 'TID Range Scan'.",
    "Masking: every report is passed through an e-mail and GUID masker before it is written (the local scratchpad directory "
    "name, a session id, is exempt so paths stay usable); no e-mail address, GUID, credential, URI with credentials, "
    "subscription, tenant or object id occurs in any recorded server response. The connection is described by host and query "
    "options only.",
]

doc = {
    "test": "m-query",
    "database": "mt_query",
    "date": "2026-11-25",
    "target": run1["target"],
    "cluster_context": run1["cluster_context"],
    "evidence_scope": run1["evidence_scope"],
    "open_source_reference": {
        "summary": "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/ENGINE-TESTS.md (Query behaviour)",
        "report": OS_REPORT,
        "engine": "documentdb-local image 0.117.0 (revision 28cc0120), hello.maxWireVersion 21, documentdb_versions ['0.117-0','0.117.0']",
        "note": "Open-source section letters differ: its (a) window functions, (b) allowDiskUse, (c) explain, (d) maxTimeMS.",
    },
    "decisions_context": {
        "source": "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/DECISIONS.md, topic 10",
        "open_item_2": "Exact L08 $setWindowFields example on the managed service -> run1 c.4 (runs, correct).",
        "open_item_3": "Explain layout for a cosmosSearch pipeline and whether COLLSCAN/SORT appear -> run1 a.5d/a.5e (no COLLSCAN, no SORT).",
        "settled_COLLSCAN_check": "Settled item says a COLLSCAN walker works if it descends into stages[].$cursor -> layout confirmed, but whether COLLSCAN appears depends on vacuum state and verbosity (runs 2, 4, 5).",
        "settled_allowDiskUse_noop": "Accepted for true/false/absent with identical results; type-checked (run1 d.*).",
        "settled_120s_default": "Not re-tested; maxTimeMS overrides behave per command (run1 b.*, run2 b2.*).",
    },
    "config_changes": [],
    "runs": runs_meta,
    "conclusions": CONCLUSIONS,
    "notes": NOTES,
    "steps": all_steps,
}

env = r1.load_env(r1.ENV_PATH)
pw = env["MANAGED_PASS"]
# The local scratchpad directory name is a GUID-shaped session id (a path segment, not an Azure identifier):
# protect it so file paths stay usable, then mask every other GUID-shaped string and e-mail address.
SESSION_DIR = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
text = json.dumps(doc, indent=2, default=str)
if r1.GUID_RE.fullmatch(SESSION_DIR):
    text = text.replace(SESSION_DIR, "@@SESSIONDIR@@")
text = r1.mask_text(text).replace("@@SESSIONDIR@@", SESSION_DIR)
for s in {pw, urllib.parse.quote_plus(pw), urllib.parse.quote(pw, safe="")}:
    if s and s in text:
        print("credential found and redacted", file=sys.stderr)
        text = text.replace(s, "<redacted>")
for k in ("MANAGED_URI", "MANAGED_GLOBAL_URI"):
    if env[k] in text:
        print("URI found and redacted", file=sys.stderr)
        text = text.replace(env[k], "<redacted-uri>")
with open(os.path.join(HERE, "report.json"), "w") as fh:
    fh.write(text)
counts = {}
for s in all_steps:
    v = s["vs_open_source"].get("verdict")
    counts[v] = counts.get(v, 0) + 1
print(json.dumps({"steps": len(all_steps), "verdicts": counts, "report": os.path.join(HERE, "report.json")}))
