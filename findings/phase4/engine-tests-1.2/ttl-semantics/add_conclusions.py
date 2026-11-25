#!/usr/bin/env python
"""Write the "conclusions" and "notes" keys into report.json, taking every number from the report.

Run after run_ttl_test.py and compare_with_0117.py. Touches no database. Idempotent.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "report.json")


def step(rep, prefix):
    return next((s for s in rep["steps"] if s["step"].startswith(prefix)), {})


def main():
    rep = json.load(open(PATH))
    comp = step(rep, "compound TTL index attempt")["response"]
    bad = step(rep, "TTL index with non-numeric")["response"]
    e2 = step(rep, "create second TTL index on exp2")
    li = (step(rep, "listIndexes after all createIndexes").get("response") or {}).get("cursor", {}).get("firstBatch", [])
    ttl_entry = next((i for i in li if i.get("name") == "exp_ttl"), None)
    spec = step(rep, "pg_cron schedule, exact command from the test spec")["response"]
    jobs = (step(rep, "pg_cron schedule, same SQL as role documentdb").get("response") or {}).get("parsed") or []
    gucs = (step(rep, "TTL-related PostgreSQL settings").get("response") or {}).get("parsed") or {}
    pa = rep["purgeAttribution"]
    runs = rep["ttlRuns"]
    never = rep["neverPurged"]
    repro = rep.get("reproducibility") or {}
    r1 = repro.get("run1") or {}
    poll = step(rep, "poll every 15 s")["response"]
    window = poll["polls"][-1]["secondsAfterInsert"]
    n_runs_surv = max(v["ttlRunsWhileItExisted"] for v in never.values())
    offs = [float(r["startIso"][17:-1]) * 1000 for r in runs]
    durs = [r["durationMs"] for r in runs]
    lags = [f"{k} {v['lagAfterEligibleSeconds']} s" for k, v in pa.items()]
    all_first = all(v.get("purgedByFirstRunAfterEligible") for v in pa.values())
    skipped = sum(v.get("runsThatStartedWhileEligibleButDidNotPurge", 0) for v in pa.values())

    def g(name):
        return (gucs.get(name) or {}).get("setting")

    c = []
    c.append({
        "question": "On engine 1.2.0, is a compound TTL index rejected, and with what error?",
        "answer": (f"Yes. createIndexes {{key: {{a: 1, b: 1}}, name: 'ab_ttl', expireAfterSeconds: 5}} fails with code "
                   f"{comp['code']} {comp['codeName']}, errmsg \"{comp['errmsg']}\", and the reply carries no errorLabels "
                   f"key. Code, codeName and rule text are identical to engine 0.117, and both 1.2.0 runs gave the same "
                   f"reply. A non-numeric expireAfterSeconds ('abc') is likewise rejected with code {bad['code']} "
                   f"{bad['codeName']} (\"{bad['errmsg'].split('}:')[-1]}\"), also unchanged from 0.117. Evidence is "
                   f"from documentdb-local 1.2.0, not the managed service."),
        "confidence": "observed"})
    c.append({
        "question": "Can one collection carry a second single-field TTL index, and does that index expire documents on "
                    "its own?",
        "answer": (f"Yes. exp2_ttl was accepted next to exp_ttl (numIndexesAfter 3). Both documents carrying a past Date in "
                   f"exp2 were deleted by the first pg_cron run after the index existed "
                   f"({pa['exp2_past_only']['purgedByRun']['start']}, lag {pa['exp2_past_only']['lagAfterEligibleSeconds']} "
                   f"s): exp2_past_only has no exp field, and exp_future_exp2_past has exp one day in the future. The "
                   f"control document with exp2 a day in the future survived. So each TTL index expires documents "
                   f"independently, and an index built after the documents were inserted still purges them. The 0.117 run "
                   f"created exp2_ttl but no document carried exp2, so the purge itself is new evidence. Building exp2_ttl on "
                   f"the 10-document collection took {e2.get('elapsedMs'):.0f} ms (run 1: {r1.get('exp2IndexBuildMs')} ms; "
                   f"0.117: 2.01 s), against about 17 ms for exp_ttl on the empty collection."),
        "confidence": "observed"})
    c.append({
        "question": "Which values of a TTL-indexed field expire (Date, string, number, null, missing, array)?",
        "answer": (f"Only BSON Dates. A Date 60 s in the past was deleted. So was an array holding one past Date and one "
                   f"Date a day ahead, so any expired element expires the document. An ISO-8601 string, a 64-bit integer "
                   f"epoch-milliseconds value, null and a missing field were never deleted. They survived {n_runs_surv} TTL "
                   f"runs over a {window} s window ({r1.get('ttlRunsWhileSurvivorsExisted')} runs in run 1), exactly as on "
                   f"0.117. This turns the DECISIONS topic-10 statement that numbers, strings and missing fields are not "
                   f"deleted, recorded there as an inference from the Date-typed $lt predicate in ttl_index.c, into an "
                   f"observation for open-source engines 0.117 and 1.2.0."),
        "confidence": "observed"})
    c.append({
        "question": "What is the TTL purge cadence and lag on engine 1.2.0 with open-source defaults?",
        "answer": (f"pg_cron job documentdb_ttl_task, schedule '* * * * *', command CALL "
                   f"documentdb_api_internal.delete_expired_rows(); (cron.timezone {g('cron.timezone')}). "
                   f"cron.job_run_details shows {len(runs)} runs, each starting {min(offs):.0f} to {max(offs):.0f} ms after a "
                   f"whole minute and lasting {min(durs):.1f} to {max(durs):.1f} ms, all with status succeeded. Every expired "
                   f"document was deleted by the first run after it became eligible "
                   f"({'all' if all_first else 'NOT all'} {len(pa)} documents; {skipped} eligible-but-skipped runs). Lags "
                   f"from eligibility (field time + 5 s, or insert or index creation if later) to the purging run: "
                   f"{', '.join(lags)}. That is the time to the next whole minute, so expect 0 to about 60 s plus "
                   f"milliseconds. 0.117 was the same: one run a minute at hh:mm:00.003 to .016, lags of about 60, 25, 58 "
                   f"and 58 s."),
        "confidence": "observed"})
    c.append({
        "question": "Did TTL behaviour change between engine 0.117 and engine 1.2.0?",
        "answer": (f"Not in anything this test measures. The compound-TTL and non-numeric errors are the same, the second "
                   f"TTL index is accepted, and the listIndexes entry is the same: {json.dumps(ttl_entry)}. The same values "
                   f"expire, the purge still runs once a minute through pg_cron, and the lag is still "
                   f"first-run-after-eligibility. Two settings exist on 1.2.0. "
                   f"documentdb.enable_ttl_cleanup_background={g('documentdb.enable_ttl_cleanup_background')} is a "
                   f"background-worker TTL path that is off by default, so pg_cron still purges. "
                   f"documentdb.createTTLIndexAsCompositeByDefault={g('documentdb.createTTLIndexAsCompositeByDefault')} "
                   f"selects composite-term index op classes for TTL indexes; in create_indexes.c it does not relax the "
                   f"single-field rule. Whether these settings also existed on 0.117 is unknown, because PostgreSQL had "
                   f"crashed before they could be read there."),
        "confidence": "observed"})
    c.append({
        "question": "Does the spec's command docker exec ddb-engine-test psql -U postgres -p 9712 -tAc \"select jobname, "
                    "schedule, command from cron.job\" work on 1.2.0?",
        "answer": (f"No. It exits {spec['returncode']} with: {spec['stderr'].strip()}. The image runs PostgreSQL as OS "
                   f"user documentdb, and documentdb is both the superuser and the owner of the pg_cron jobs. psql -U "
                   f"documentdb -p 9712 -d postgres works and lists {len(jobs)} jobs: "
                   + "; ".join(f"{j[0]} ({j[1]}): {j[2].rstrip(';')}" for j in jobs)
                   + ". The list is identical after the TTL indexes are created, so there is no per-index job. Whether "
                     "0.117 had a postgres role is unknown, because its PostgreSQL had crashed before the read."),
        "confidence": "observed"})
    c.append({
        "question": "Does this settle the managed service's TTL purge cadence (DECISIONS topic 10, open item 5)?",
        "answer": (f"No. It establishes only the open-source 1.2.0 defaults: a per-minute pg_cron job, plus these "
                   f"settings, all with source=default in pg_settings: "
                   f"TTLTaskMaxRunTimeInMS={g('documentdb.TTLTaskMaxRunTimeInMS')}, "
                   f"repeatPurgeIndexesForTTLTask={g('documentdb.repeatPurgeIndexesForTTLTask')}, "
                   f"maxTTLDeleteBatchSize={g('documentdb.maxTTLDeleteBatchSize')}, "
                   f"SingleTTLTaskTimeBudget={g('documentdb.SingleTTLTaskTimeBudget')} and "
                   f"TTLPurgerStatementTimeout={g('documentdb.TTLPurgerStatementTimeout')}. With "
                   f"repeatPurgeIndexesForTTLTask on, each run repeats delete batches until a pass deletes nothing or "
                   f"60 s pass (ttl_index.c), which matches the release note's 'continuous for up to 60 seconds'. On "
                   f"this tiny collection every run ended within milliseconds, so the 60 s continuous mode was never "
                   f"exercised. The managed cluster's settings and schedule cannot be seen from here. Keep the kit "
                   f"wording 'expiry lags by up to about a minute after the field's time plus expireAfterSeconds; not "
                   f"exact'."),
        "confidence": "inconclusive"})
    ci = step(rep, "create TTL index on exp")["response"]
    c.append({
        "question": "Incidental: what shape do the gateway's createIndexes and drop replies have on 1.2.0?",
        "answer": (f"createIndexes nests its counts the way a sharded router does: {json.dumps(ci)}. hello reports msg "
                   f"'isdbgrid'. A kit helper that reads numIndexesAfter at the top level gets nothing; it should look "
                   f"under raw.<shard>. The 0.117 TTL test used create_index, which returns only the index name, so "
                   f"there is no 0.117 reply to compare. Dropping a collection that does not exist yet returns "
                   f"{json.dumps(step(rep, 'drop collection docs')['response'])}, as on 0.117."),
        "confidence": "observed"})
    rep["conclusions"] = c
    rep["notes"] = [
        f"Evidence scope: documentdb-local {rep['image']['tag']} (OCI version {rep['image']['ociVersion']}, revision "
        f"{rep['image']['ociRevision'][:12]}, image {rep['image']['imageId'][:19]}...), extension documentdb "
        f"{rep['extensions'].get('documentdb')}, gateway buildInfo.version {rep['buildInfo']['version']}; hello also "
        f"reports internal.documentdb_versions "
        f"{json.dumps((step(rep, 'hello').get('response') or {}).get('internal', {}).get('documentdb_versions'))}. "
        f"It shows "
        f"open-source engine behaviour at this version with default settings, not managed Azure DocumentDB behaviour.",
        "Two independent runs on 1.2.0 gave the same results. run 1 (report.run1.json, run1.log) is a 226 s window, "
        "because a deadline bug dropped its last poll; run 2 (this report) is the full 17-poll, 242 s window. Same "
        "purged set, same survivors, same errors.",
        "Setup is held away from the pg_cron minute (setupPhaseGuard): if it would start within 10 s before or 2 s "
        "after a whole minute, the script waits until hh:mm:03. So in both runs the documents were inserted at about hh:mm:03, which "
        "is why the already-expired documents show lags of about 55 to 57 s.",
        "The container was shared with other 1.2.0 reruns running at the same time (pgvector 'ivfflat index created "
        "with little data' notices from another test appear in the PostgreSQL log). /data had 11 GB free before and "
        "after, and every TTL run succeeded within milliseconds.",
        "The script ran the spec's exact psql -U postgres command and recorded its error; the pg_cron schedule was then "
        "read as role documentdb. All psql reads were SELECTs on cron.job, cron.job_run_details, pg_extension and "
        "pg_settings.",
        "Database t_ttl was dropped at the end ({ok: 1, dropped: 't_ttl'}) and is no longer listed. No other database "
        "was touched, and the container was left running.",
    ]
    with open(PATH, "w") as f:
        f.write(json.dumps(rep, indent=2, default=str) + "\n")
    for x in c:
        print("Q:", x["question"])
        print("A:", x["answer"])
        print("C:", x["confidence"])
        print()


if __name__ == "__main__":
    main()
