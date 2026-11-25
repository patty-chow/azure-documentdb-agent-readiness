#!/usr/bin/env python
"""ttl-semantics rerun: compare this rerun with the tester's report and record verdicts.

Inputs (all in this folder unless noted):
  report.raw.json      raw output of run_ttl_test.py (copied from report.json on first use)
  supplementary.json   output of supplementary_probe.py
  extra_checks.json    output of extra_checks.py
  script.diff          diff of run_ttl_test.py against the tester's copy
  ../ttl-semantics/report.json and report.run1.json   the tester's reports
  findings/phase4/engine-tests/ttl-semantics/report.json   the 0.117 report
Output: report.json = raw rerun report + comparison, supplementary and extra steps, verdicts.
Order: run_ttl_test.py -> supplementary_probe.py -> extra_checks.py -> compare_with_tester.py
"""
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TDIR = os.path.join(os.path.dirname(HERE), "ttl-semantics")
P0117 = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/ttl-semantics/report.json"

raw_path = os.path.join(HERE, "report.raw.json")
rep_path = os.path.join(HERE, "report.json")
cur = json.load(open(rep_path))
if "verification" not in cur:
    shutil.copyfile(rep_path, raw_path)
R = json.load(open(raw_path))
T = json.load(open(os.path.join(TDIR, "report.json")))
T1 = json.load(open(os.path.join(TDIR, "report.run1.json")))
O = json.load(open(P0117))
S = json.load(open(os.path.join(HERE, "supplementary.json")))
E = json.load(open(os.path.join(HERE, "extra_checks.json")))
diff_text = open(os.path.join(HERE, "script.diff")).read()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def norm(x):
    return json.loads(json.dumps(x).replace("t_ttl_rerun", "t_ttl"))


def step(rep, prefix):
    for s in rep["steps"]:
        if s["step"].replace("t_ttl_rerun", "t_ttl").startswith(prefix):
            return s
    return None


def errkey(r):
    return {k: r.get(k) for k in ("code", "codeName", "errmsg", "errorLabelsPresent")}


# ------------------------------------------------------------------ step comparison
rows = []


def cmp(prefix, extract, note=""):
    a, b = step(T, prefix), step(R, prefix)
    va, vb = extract(a), extract(b)
    same = norm(va) == norm(vb)
    rows.append({"step": prefix, "testerStep": a["n"], "rerunStep": b["n"], "testerOk": a["ok"], "rerunOk": b["ok"],
                 "compared": note or "response", "tester": va, "rerun": vb, "same": same and a["ok"] == b["ok"]})


cmp("image identity", lambda s: s["response"]["stdout"], "docker inspect stdout")
cmp("PostgreSQL extension versions", lambda s: s["response"]["stdout"], "psql stdout")
cmp("pg_cron schedule, exact command", lambda s: {"returncode": s["response"]["returncode"],
                                                   "stderr": s["response"]["stderr"]}, "exit code and stderr")
cmp("pg_cron schedule, same SQL", lambda s: s["response"]["stdout"], "psql stdout")
cmp("TTL-related PostgreSQL settings", lambda s: s["response"]["stdout"], "psql stdout (all 21 settings)")
cmp("free space on /data before", lambda s: s["response"]["stdout"].split()[-5:-2], "Size/Used/Avail columns")
cmp("buildInfo", lambda s: s["response"])
cmp("hello", lambda s: {k: v for k, v in s["response"].items() if k not in ("localTime", "connectionId")},
    "reply without localTime and connectionId")
cmp("does t_ttl exist before", lambda s: list(s["response"].values()))
cmp("drop collection docs", lambda s: s["response"])
cmp("create TTL index on exp", lambda s: s["response"])
cmp("listIndexes after the first TTL index", lambda s: s["response"], "reply (namespace normalised)")
cmp("insert the test documents", lambda s: s["response"])
cmp("compound TTL index attempt", lambda s: errkey(s["response"]), "code, codeName, errmsg, errorLabels presence")
cmp("create second TTL index on exp2", lambda s: s["response"])
cmp("TTL index with non-numeric expireAfterSeconds", lambda s: errkey(s["response"]),
    "code, codeName, errmsg, errorLabels presence")
cmp("listIndexes after all createIndexes attempts", lambda s: s["response"], "reply (namespace normalised)")
cmp("poll every 15 s", lambda s: {"purged": sorted(s["response"]["disappeared"]),
                                  "finalPresentIds": s["response"]["finalPresentIds"],
                                  "expectedPurgedButStillPresent": s["response"]["expectedPurgedButStillPresent"],
                                  "polls": len(s["response"]["polls"]),
                                  "probesInserted": sorted(s["response"]["probes"])},
    "purged set, survivors, poll count, probes")
cmp("final contents of the collection", lambda s: [(d["_id"], sorted(k for k in d if k != "_id")) for d in s["response"]],
    "surviving _ids and their fields")
cmp("pg_cron run history", lambda s: sorted({r[2] for r in s["response"]["parsed"]}), "set of run statuses")
cmp("pg_cron schedule after the test", lambda s: s["response"]["stdout"], "psql stdout")
cmp("TTL lines in the PostgreSQL log",
    lambda s: len(s["response"]["parsed"]["otherTTLMessages"]), "number of TTL log lines other than pg_cron 'starting'")
cmp("free space on /data after", lambda s: s["response"]["stdout"].split()[-5:-2], "Size/Used/Avail columns")
cmp("drop the test database", lambda s: s["response"], "reply (database name normalised)")
cmp("confirm t_ttl is gone", lambda s: list(s["response"].values()))

# ------------------------------------------------------------------ purge timing
def runs_summary(rep):
    rs = rep["ttlRuns"]
    offs = [int(r["startIso"][17:19]) * 1000 + int(r["startIso"][20:26]) / 1000 for r in rs]
    return {"runs": len(rs), "startOffsetMs": [round(min(offs), 1), round(max(offs), 1)],
            "durationMs": [min(r["durationMs"] for r in rs), max(r["durationMs"] for r in rs)],
            "statuses": sorted({r["status"] for r in rs})}


def lags(rep):
    return {k: v.get("lagAfterEligibleSeconds") for k, v in rep["purgeAttribution"].items()}


def all_first(rep):
    return all(v.get("purgedByFirstRunAfterEligible") for v in rep["purgeAttribution"].values())


def skipped(rep):
    return sum(v.get("runsThatStartedWhileEligibleButDidNotPurge", 0) for v in rep["purgeAttribution"].values())


timing = {
    "tester_run1": {"setupPhaseGuard": T1["setupPhaseGuard"], "insertedAt": T1["insertedAt"], "lags": lags(T1),
                    "allPurgedByFirstRunAfterEligible": all_first(T1), "runs": runs_summary(T1)},
    "tester_run2": {"setupPhaseGuard": T["setupPhaseGuard"], "insertedAt": T["insertedAt"], "lags": lags(T),
                    "allPurgedByFirstRunAfterEligible": all_first(T), "eligibleButSkippedRuns": skipped(T),
                    "runs": runs_summary(T)},
    "this_rerun": {"setupPhaseGuard": R["setupPhaseGuard"], "insertedAt": R["insertedAt"], "lags": lags(R),
                   "allPurgedByFirstRunAfterEligible": all_first(R), "eligibleButSkippedRuns": skipped(R),
                   "runs": runs_summary(R),
                   "ttlRunsWhileSurvivorsExisted": sorted({v["ttlRunsWhileItExisted"] for v in R["neverPurged"].values()})},
    "note": ("Both tester runs hit the setup guard (second 52.4 and 53.1) and inserted at hh:mm:03, so their "
             "already-expired documents waited 55-57 s; this rerun started at second 37.0, inserted at hh:mm:37 "
             "and the same documents waited 21-23 s. The lag is the time to the next whole-minute pg_cron run."),
}

# ------------------------------------------------------------------ supplementary and extra summaries
sup_poll = next(s for s in S["steps"] if s["step"].startswith("poll every 5 s"))
sup_errors = {s["step"]: ({k: s["response"].get(k) for k in ("code", "codeName", "errmsg")} if not s["ok"] else
                          s["response"]) for s in S["steps"] if s["step"].startswith("createIndexes with")}
sup_idx = next(s for s in S["steps"] if s["step"].startswith("PostgreSQL index definitions"))
sup_collmod = next(s for s in S["steps"] if s["step"].startswith("collMod"))
sup_list_after = next(s for s in S["steps"] if s["step"].startswith("listIndexes after the supplementary"))
build_windows = [s for s in E["steps"] if s["step"].startswith("index-build pg_cron runs")]

same_all = all(r["same"] for r in rows)
diff_rows = [r["step"] for r in rows if not r["same"]]

manual = [
    {"n": 1, "at": "2026-11-25T21:23:48Z (during poll loop of this rerun)",
     "command": "docker exec ddb-engine-test psql -U documentdb -p 9712 -d postgres -tAc \"select collection_id, database_name, collection_name from documentdb_api_catalog.collections where database_name = 't_ttl_rerun' order by collection_id\"",
     "response": {"returncode": 0, "stdout": "SET\nSET\n306|t_ttl_rerun|system.dbSentinel\n307|t_ttl_rerun|docs\n"},
     "reading": "The database holds the test collection docs (collection_id 307) and an engine-created system.dbSentinel collection (306), which is what the 'sentinel database' lines in step 23's log excerpt refer to."},
    {"n": 2, "at": "2026-11-25T21:23:55Z (during poll loop of this rerun)",
     "command": "docker exec ddb-engine-test psql -U documentdb -p 9712 -d postgres -tAc \"select indexname || ' ==> ' || indexdef from pg_indexes where schemaname = 'documentdb_data' and tablename = 'documents_307' order by indexname\"",
     "response": {"returncode": 0, "stdout": "SET\nSET\ncollection_pk_307 ==> CREATE UNIQUE INDEX collection_pk_307 ON documentdb_data.documents_307 USING btree (shard_key_value, object_id)\ndocuments_rum_index_466 ==> CREATE INDEX documents_rum_index_466 ON documentdb_data.documents_307 USING documentdb_extended_rum (document documentdb_extended_rum_catalog.bson_extended_rum_composite_path_ops (pathspec='[ \"exp\" ]', tl='2691'))\ndocuments_rum_index_467 ==> CREATE INDEX documents_rum_index_467 ON documentdb_data.documents_307 USING documentdb_extended_rum (document documentdb_extended_rum_catalog.bson_extended_rum_composite_path_ops (pathspec='[ \"exp2\" ]', tl='2691'))\n"},
     "reading": "Both TTL indexes are documentdb_extended_rum indexes with op class bson_extended_rum_composite_path_ops on a single path."},
    {"n": 3, "at": "2026-11-25T21:23:55Z (during poll loop of this rerun)",
     "command": "docker exec ddb-engine-test psql -U documentdb -p 9712 -d postgres -tAc \"select index_id, index_spec::text, index_is_valid from documentdb_api_catalog.collection_indexes where collection_id = 307 order by index_id\"",
     "response": {"returncode": 0, "stdout": "SET\nSET\n465|(_id_,\"{ \"\"_id\"\" : { \"\"$numberInt\"\" : \"\"1\"\" } }\",,,,,2,,,)|t\n466|(exp_ttl,\"{ \"\"exp\"\" : { \"\"$numberInt\"\" : \"\"1\"\" } }\",,,,,2,5,,\"{ \"\"enableOrderedIndex\"\" : { \"\"$numberInt\"\" : \"\"1\"\" } }\")|t\n467|(exp2_ttl,\"{ \"\"exp2\"\" : { \"\"$numberInt\"\" : \"\"1\"\" } }\",,,,,2,5,,\"{ \"\"enableOrderedIndex\"\" : { \"\"$numberInt\"\" : \"\"1\"\" } }\")|t\n"},
     "reading": "The catalog stores expireAfterSeconds 5 and storageEngine {enableOrderedIndex: 1} for both TTL indexes, both valid."},
    {"n": 4, "at": "2026-11-25T21:28Z (after this rerun and the supplementary probe had started)",
     "command": "docker exec ddb-engine-test sh -c \"grep -n 't_ttl_rerun' /data/pglog.log | tail -n 20\"",
     "response": {"returncode": 0, "stdout": "9091:2026-11-25 21:22:37.041 UTC [26129] LOG:  database t_ttl_rerun has collections: false\n9092:2026-11-25 21:22:37.042 UTC [26129] LOG:  Creating and returning documentdb_data.documents_306 for the sentinel database t_ttl_rerun\n9822:2026-11-25 21:27:02.126 UTC [26129] LOG:  database t_ttl_rerun has collections: false\n9823:2026-11-25 21:27:02.128 UTC [26129] LOG:  Creating and returning documentdb_data.documents_315 for the sentinel database t_ttl_rerun\n"},
     "reading": "The only log lines naming the database are the sentinel-collection creation at the first createIndexes of each run; the engine logs nothing per TTL deletion (documentdb.logTTLProgressActivity is off)."},
]

verdicts = [
    {"question": "On engine 1.2.0, is a compound TTL index rejected, and with what error?",
     "verdict": "CONFIRMED",
     "reason": ("Rerun step 15 returned the same reply byte for byte (code 67 CannotCreateIndex, same errmsg, no errorLabels "
                "key), and step 17 likewise for expireAfterSeconds 'abc'. The 0.117 report has the same code, codeName and "
                "rule text; its full errmsg differs only in the order of the echoed spec, because that run built the spec "
                "with create_index. The answer reports the real code and text (CannotCreateIndex, not 'unsupported') and is "
                "scoped to documentdb-local.")},
    {"question": "Can one collection carry a second single-field TTL index, and does that index expire documents on its own?",
     "verdict": "CONFIRMED_EXCEPT_BUILD_TIME_FRAMING",
     "reason": ("Rerun: exp2_ttl accepted (numIndexesAfter 3); exp2_past_only and exp_future_exp2_past were purged by the first "
                "pg_cron run after the index existed (2026-11-25T21:23:00.016280Z, lag 21.0 s), and exp2_future_control survived "
                "4 runs. The build-time sentence compares 2006 ms 'on the 10-document collection' with about 17 ms 'on the empty "
                "collection', which implies the documents cause the delay. They do not: in the supplementary probe, "
                "createIndexes on an existing but empty collection took 1004.8 ms (pexp_ttl_pfe) and 2007.5 ms (plain_idx). "
                "Only the createIndexes that also creates the collection returns in milliseconds (4.5 to 17.5 ms). Every "
                "slow call had one documentdb_index_build_task_1 run of 12.0 to 23.3 ms inside its window (idle runs take "
                "1.5 to 2.9 ms). That indicates the index on an existing collection is built by the 2-second pg_cron "
                "index-build job, and the call returns about 1 or 2 s after it starts (an inference from cron.job_run_details).")},
    {"question": "Which values of a TTL-indexed field expire (Date, string, number, null, missing, array)?",
     "verdict": "CONFIRMED",
     "reason": ("Rerun: past_date_60s and array_of_dates were purged; string_value, number_value (64-bit integer), "
                "null_value and missing_field survived 4 TTL runs. The tester observed only one numeric type (int64), so 'only "
                "BSON Dates' was a generalisation. The supplementary probe supports it: int32 epoch seconds, double and "
                "Decimal128 epoch ms, a BSON Timestamp, an ObjectId with a past embedded time, an embedded document holding a "
                "past Date, an empty array and a future-only array all survived 2 TTL runs. A past Date and the "
                "reversed-order array [Date +1 day, Date -60 s] were purged by the first run.")},
    {"question": "What is the TTL purge cadence and lag on engine 1.2.0 with open-source defaults?",
     "verdict": "CONFIRMED_WITH_SCOPE_CAVEAT",
     "reason": ("Rerun: the same pg_cron job and schedule. 6 runs, each starting 14 to 28 ms after a whole minute and lasting "
                "2.3 to 8.6 ms, all succeeded. All 7 expired documents went at the first run after they became eligible, "
                "with 0 skipped runs. Lags were 21.0 to 50.9 s, against 22.0 to 57.0 s for the tester. This rerun inserted "
                "at hh:mm:37, while both tester runs were held to hh:mm:03, which directly confirms that the lag is the time "
                "to the next whole minute. The general expectation '0 to about 60 s plus milliseconds' is shown only when "
                "each run finishes its work in milliseconds (13 documents or fewer here). A backlog that needs the 1000-row "
                "batches or the 60 s budget was not tested.")},
    {"question": "Did TTL behaviour change between engine 0.117 and engine 1.2.0?",
     "verdict": "CONFIRMED",
     "reason": ("The rerun matches the tester on every compared item. The 0.117 report shows the same errors, the same "
                "listIndexes entry for exp_ttl, the same survivors and a per-minute cadence. The settings remarks are source "
                "readings. On 1.2.0 the TTL-specific GUC has no visible effect: a plain non-TTL index (plain_idx) also got "
                "bson_extended_rum_composite_path_ops and storageEngine {enableOrderedIndex: true}. Neither the op class nor "
                "that listIndexes flag marks an index as TTL on this build.")},
    {"question": "Does the spec's command docker exec ddb-engine-test psql -U postgres -p 9712 -tAc \"select jobname, schedule, command from cron.job\" work on 1.2.0?",
     "verdict": "CONFIRMED",
     "reason": ("Rerun step 03 exits 2 with the same 'role \"postgres\" does not exist'. The fallback lists the same 4 jobs, "
                "identical before and after. The tester recorded no step for 'PostgreSQL runs as OS user documentdb' or "
                "'documentdb is the superuser and owns the pg_cron jobs'. The extra read-only checks E01 to E04 now back "
                "both: documentdb is the only superuser, no role is named postgres, all four cron.job rows have username "
                "documentdb, and the postmaster runs as OS user documentdb (uid 1000).")},
    {"question": "Does this settle the managed service's TTL purge cadence (DECISIONS topic 10, open item 5)?",
     "verdict": "CONFIRMED",
     "reason": ("The answer correctly says no and stays inconclusive. The GUC values match the rerun's pg_settings exactly. "
                "The loop description matches ttl_index.c in the scratchpad engine-src copy, which is the main branch, not "
                "the 1.2.0 tag: the loop runs while elapsed time is within TTLTaskMaxRunTimeInMS (with "
                "repeatPurgeIndexesForTTLTask on) and stops when a pass deletes 0 rows. The engine logs 'TTL Index delete "
                "rows exceeded time budget' when a run passes its budget. No such line was among the last 30 matching log "
                "lines (step 23, about the last 28 minutes), which is consistent with no run reaching its budget.")},
    {"question": "Incidental: what shape do the gateway's createIndexes and drop replies have on 1.2.0?",
     "verdict": "CONFIRMED_EXCEPT_KIT_ADVICE",
     "reason": ("Rerun replies are identical: raw.defaultShard wrapper, hello msg 'isdbgrid', and {ok: 1.0, dropped: 'docs'} "
                "for dropping a collection that did not exist. The advice that a kit helper 'should look under raw.<shard>' "
                "goes past the evidence. Only the documentdb-local gateway was observed, and the kit targets the managed "
                "service, so a helper should accept both top-level counts and raw.<shard>. Also, 'as on 0.117' holds only for "
                "the reply shape. The 0.117 report reads 'dropped (or did not exist)', so it does not show that the 0.117 "
                "collection was absent.")},
]

extra = [
    "The rerun inserted at hh:mm:37, while both tester runs were held to hh:mm:03. The already-expired documents waited 21 to 23 s instead of 55 to 57 s, and future_date_90s waited 48.0 s instead of 22.0 s. Purge time depends only on the phase of the next whole-minute pg_cron run.",
    "A partialFilterExpression on a TTL index limits what the purger deletes, observed on 1.2.0. pexp_ttl_pfe {pexp: 1}, expireAfterSeconds 5, partialFilterExpression {purge: {$eq: true}} purged pfe_match. pfe_nomatch (purge false) and pfe_flag_missing (no purge field) survived 2 TTL runs. The PostgreSQL index carries WHERE (document #= '{ \"purge\" : true }'::bsonquery). Until now DECISIONS topic 10 had this only from a ttl_index.c comment.",
    "Non-Date TTL values beyond the tester's set survived 2 TTL runs (2026-11-25T21:28:00.018699Z and 21:29:00.013006Z): int32, double, Decimal128, BSON Timestamp, ObjectId, embedded document {at: Date}, empty array, and array of future Dates. A [future, past] array was purged, so element order does not matter.",
    "TTL index op class on 1.2.0: exp_ttl, exp2_ttl, pexp_ttl_pfe, frac_ttl and a plain non-TTL index all use documentdb_extended_rum with bson_extended_rum_composite_path_ops (pathspec single path, tl 2691). All non-_id indexes list storageEngine {enableOrderedIndex: true}. createTTLIndexAsCompositeByDefault is therefore not distinguishable on this build, and that listIndexes flag does not identify TTL indexes.",
    "Index build path: createIndexes that auto-creates the collection returns in 4.5 to 17.5 ms. Any later createIndexes on that collection, empty or not, takes 1005 to 2010 ms, in about 1 s steps. Each such call had one documentdb_index_build_task_1 run of 12.0 to 23.3 ms inside its window, which indicates the build is done by the 2-second pg_cron index-build job and the call waits for it (an inference from cron.job_run_details).",
    "TTL createIndexes validation codes on 1.2.0 vary by rule: negative expireAfterSeconds gives code 67 CannotCreateIndex ('cannot be less than 0'), and 2147483648 gives code 67 ('must be within an acceptable range'). TTL on _id gives code 197 InvalidIndexSpecificationOption. TTL on a hashed key gives code 115 CommandNotSupported ('Creating a hash index as ttl index is not supported.', with no 'Error in specification' prefix). expireAfterSeconds 5.7 is accepted and stored as 5 (truncated). None carried errorLabels.",
    "collMod {collMod: 'supp', index: {name: 'exp_ttl', expireAfterSeconds: 7}} succeeds with reply {ok: 1, expireAfterSeconds_old: 5, expireAfterSeconds_new: 7.0} (new value echoed as a double), and listIndexes then shows 7.",
    "When t_ttl_rerun got its first collection, the engine also created a system.dbSentinel collection (catalog rows 306 and 315, one per run). That is the source of the 'database ... has collections: false / Creating ... for the sentinel database' lines that the tester's step 23 counted as 'mention database t_ttl'. With documentdb.logTTLProgressActivity off (default), the engine logged no TTL progress lines, so the log cross-check cannot attribute purges. Only cron.job_run_details plus polling can.",
    "documentdb.enable_ttl_cleanup_background is not an alternative purge path on main: delete_expired_rows_background in ttl_index.c returns immediately whether the setting is on or off. This is a main-branch source reading, not the 1.2.0 tag.",
]

verdict = {
    "rerun_ok": bool(same_all and all(v["verdict"].startswith("CONFIRMED") for v in verdicts)),
    "allComparedStepsSame": same_all,
    "stepsThatDiffer": diff_rows,
    "summary": ("Reproduced. The renamed copy (database t_ttl_rerun, no logic change) ran 26 steps in 242.4 s. Every compared "
                "step matched the tester's run 2: errors byte for byte, the same purged set and survivors, all purges at the "
                "first pg_cron run after eligibility. Lags were 21.0 to 50.9 s instead of 22.0 to 57.0 s because the insert "
                "was at hh:mm:37 instead of hh:mm:03. Three wording issues: the C2 build-time framing (the delay comes from "
                "the collection already existing, not from its documents), C4's general 0 to 60 s expectation (shown only "
                "for tiny backlogs), and C8's kit-helper advice (local gateway shape only). Evidence is about open-source "
                "engine and gateway 1.2.0 on documentdb-local, not the managed service."),
}

R["rerunOf"] = {
    "testerReport": os.path.join(TDIR, "report.json"),
    "testerScript": os.path.join(TDIR, "run_ttl_test.py"), "testerScriptSha256": sha(os.path.join(TDIR, "run_ttl_test.py")),
    "rerunScript": os.path.join(HERE, "run_ttl_test.py"), "rerunScriptSha256": sha(os.path.join(HERE, "run_ttl_test.py")),
    "scriptChange": ("sed 's/t_ttl/t_ttl_rerun/g' on a copy: the DB constant plus the literal database name in step names, "
                     "command texts, the presence-flag key and the step-23 log grep pattern; no test logic changed."),
    "scriptDiff": diff_text,
    "rerunCommandOrder": ["run_ttl_test.py", "supplementary_probe.py", "extra_checks.py", "compare_with_tester.py"],
}
R["verification"] = {
    "comparisonWithTesterReport": rows,
    "purgeTimingComparison": timing,
    "supplementaryProbe": {"script": os.path.join(HERE, "supplementary_probe.py"), "steps": S["steps"],
                           "setupPhaseGuard": S.get("setupPhaseGuard"), "insertCompletedAt": S.get("insertCompletedAt"),
                           "summary": {"purged": sorted(sup_poll["response"]["goneAt"]),
                                       "survived": sup_poll["response"]["finalPresentIds"],
                                       "mismatchesWithExpectation": sup_poll["response"]["mismatchesWithExpectation"],
                                       "validationProbes": sup_errors,
                                       "collMod": sup_collmod["response"]}},
    "extraReadOnlyChecks": {"script": os.path.join(HERE, "extra_checks.py"), "steps": E["steps"]},
    "manualReadOnlyChecksDuringRerun": manual,
    "conclusionVerdicts": verdicts,
    "extraObservations": extra,
    "verdict": verdict,
    "evidenceScope": ("Everything here was observed on documentdb-local ghcr.io/documentdb/documentdb/documentdb-local:pg17-1.2.0 "
                      "(OCI 1.2.0, revision 965b6e7ad1c4; extensions documentdb 1.2-0; gateway buildInfo 7.0.0) with default "
                      "settings, in a container shared with other tests. Source remarks come from the main-branch copy in "
                      "scratchpad/engine-src. None of it proves managed Azure DocumentDB behaviour."),
}
text = json.dumps(R, indent=2, default=str)
with open(rep_path, "w") as f:
    f.write(text + "\n")
print(json.dumps({"allComparedStepsSame": same_all, "stepsThatDiffer": diff_rows,
                  "rows": [(r["step"], r["same"]) for r in rows], "timing": timing}, indent=1, default=str))
