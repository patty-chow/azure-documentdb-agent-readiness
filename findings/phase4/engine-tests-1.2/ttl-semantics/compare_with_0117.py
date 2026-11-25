#!/usr/bin/env python
"""Compare the engine 1.2.0 ttl-semantics report with the engine 0.117 one.

Reads   engine-tests-1.2/ttl-semantics/report.json            (this rerun)
        findings/phase4/engine-tests/ttl-semantics/report.json (0.117 run)
        engine-tests/ttl-semantics/rerun_attempt.json         (0.117 read-only checks, if present)
Writes  the "comparisonWith0117" key back into this rerun's report.json and
        prints the table. Touches no database. Rerunnable at any time.
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "report.json")
OLD = "/Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/engine-tests/ttl-semantics/report.json"
OLD_RERUN = ("/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/"
             "scratchpad/engine-tests/ttl-semantics/rerun_attempt.json")


def step(report, name_prefix):
    for s in report.get("steps", []):
        if s.get("step", "").startswith(name_prefix):
            return s
    return None


def rule_text(resp):
    if not isinstance(resp, dict):
        return None
    return (resp.get("errmsg") or "").split("}:")[-1].strip()


def ttl_entry(indexes, name):
    for i in indexes or []:
        if i.get("name") == name:
            return i
    return None


def ms_between(a, b):
    fa = dt.datetime.strptime(a, "%Y-%m-%d %H:%M:%S.%f")
    fb = dt.datetime.strptime(b, "%Y-%m-%d %H:%M:%S.%f")
    return round((fb - fa).total_seconds() * 1000, 1)


def main():
    new = json.load(open(NEW))
    old = json.load(open(OLD))
    old_rerun = json.load(open(OLD_RERUN)) if os.path.exists(OLD_RERUN) else {}
    rows = []

    def add(item, v117, v120, same, note=""):
        rows.append({"item": item, "engine_0_117": v117, "engine_1_2_0": v120,
                     "same": same, "note": note})

    # engine identity
    add("engine build",
        "documentdb-local OCI 0.117.0, revision 28cc0120, PostgreSQL 17, buildInfo.version "
        f"{(old.get('buildInfo') or {}).get('version')} (from ENGINE-TESTS.md and the 0.117 report)",
        new.get("engine_version"), False, "Different engine builds by design: this is the 1.2.0 rerun.")

    # compound TTL
    o = step(old, "create compound TTL index")
    n = step(new, "compound TTL index attempt")
    o_r, n_r = (o or {}).get("response") or {}, (n or {}).get("response") or {}
    add("compound TTL index {a: 1, b: 1} with expireAfterSeconds",
        {"ok": (o or {}).get("ok"), "code": o_r.get("code"), "codeName": o_r.get("codeName"), "rule": rule_text(o_r),
         "errorLabels": o_r.get("errorLabels")},
        {"ok": (n or {}).get("ok"), "code": n_r.get("code"), "codeName": n_r.get("codeName"), "rule": rule_text(n_r),
         "errorLabels": n_r.get("errorLabels", "absent from reply")},
        bool(o and n and o_r.get("code") == n_r.get("code") and o_r.get("codeName") == n_r.get("codeName")
             and rule_text(o_r) == rule_text(n_r)),
        "0.117 recorded errorLabels [] (its helper defaulted a missing key to []); 1.2.0 records whether the key "
        "is present in the server reply.")

    # second TTL index accepted
    o = step(old, "create second TTL index")
    n = step(new, "create second TTL index on exp2")
    o_ms = None
    for c in old_rerun.get("readOnlyChecksPerformed", []):
        if "exp2_ttl" in c and "took" in c:
            o_ms = c
    add("second single-field TTL index (exp2) next to exp_ttl",
        {"accepted": (o or {}).get("ok"), "response": (o or {}).get("response"),
         "buildTimeOnNonEmptyCollection": o_ms or "not recorded"},
        {"accepted": (n or {}).get("ok"), "response": (n or {}).get("response"),
         "buildTimeOnNonEmptyCollectionMs": (n or {}).get("elapsedMs")},
        bool(o and n and o.get("ok") == n.get("ok")),
        "0.117 used create_index (reply = index name); 1.2.0 sends createIndexes directly and keeps the full reply.")

    # exp2 purge
    pa = new.get("purgeAttribution") or {}
    exp2 = {k: pa.get(k) for k in ("exp2_past_only", "exp_future_exp2_past") if k in pa}
    never = new.get("neverPurged") or {}
    add("documents expired through the second TTL index (exp2)",
        "not tested: no 0.117 document carried exp2, so only the index creation was observed",
        {"purged": {k: {"purgedByRun": (v or {}).get("purgedByRun", {}).get("start"),
                        "lagAfterEligibleSeconds": (v or {}).get("lagAfterEligibleSeconds")} for k, v in exp2.items()},
         "exp2FutureControlSurvived": "exp2_future_control" in never},
        None, "New evidence in the 1.2.0 run; nothing to compare against.")

    # non-numeric expireAfterSeconds
    o = step(old, "create TTL index with non-numeric")
    n = step(new, "TTL index with non-numeric expireAfterSeconds")
    o_r, n_r = (o or {}).get("response") or {}, (n or {}).get("response") or {}
    add("expireAfterSeconds: 'abc'",
        {"code": o_r.get("code"), "codeName": o_r.get("codeName"), "rule": rule_text(o_r)},
        {"code": n_r.get("code"), "codeName": n_r.get("codeName"), "rule": rule_text(n_r)},
        bool(o and n and o_r.get("code") == n_r.get("code") and rule_text(o_r) == rule_text(n_r)))

    # listIndexes shape
    o = step(old, "listIndexes after all createIndex attempts")
    n = step(new, "listIndexes after all createIndexes attempts")
    o_idx = (o or {}).get("response") or []
    n_idx = (((n or {}).get("response") or {}).get("cursor") or {}).get("firstBatch") or []
    oe, ne = ttl_entry(o_idx, "exp_ttl"), ttl_entry(n_idx, "exp_ttl")
    add("listIndexes entry for the TTL index exp_ttl", oe, ne, oe == ne,
        "Compared as whole documents; a difference here matters to any helper that reads index options.")
    add("indexes present after all createIndexes attempts",
        [i.get("name") for i in o_idx], [i.get("name") for i in n_idx],
        [i.get("name") for i in o_idx] == [i.get("name") for i in n_idx])

    # which values expire
    o = step(old, "poll collection every 15 s")
    n = step(new, "poll every 15 s")
    o_dis = sorted(((o or {}).get("response") or {}).get("disappeared", {}).keys())
    o_final = sorted(d.get("_id") for d in ((o or {}).get("response") or {}).get("finalDocuments", []))
    n_dis = sorted(((n or {}).get("response") or {}).get("disappeared", {}).keys())
    n_final = sorted(((n or {}).get("response") or {}).get("finalPresentIds", []))
    common = ["past_date_60s", "future_date_90s", "array_of_dates", "string_value", "number_value",
              "missing_field", "null_value", "probe2_past_date", "probe3_past_date"]
    add("purged within the 4-minute window (documents common to both runs)",
        [x for x in o_dis if x in common], [x for x in n_dis if x in common],
        [x for x in o_dis if x in common] == [x for x in n_dis if x in common])
    add("never purged within the 4-minute window (documents common to both runs)",
        [x for x in o_final if x in common], [x for x in n_final if x in common],
        [x for x in o_final if x in common] == [x for x in n_final if x in common],
        "Both runs: string (ISO-8601), number (64-bit epoch ms), missing and null survive; only BSON Dates expire.")

    # cadence and run durations
    o_cron = step(old, "pg_cron TTL job timestamps") or {}
    o_starts = (o_cron.get("response") or {}).get("starts_utc", [])
    o_done = (o_cron.get("response") or {}).get("completed_utc", [])
    o_offsets = sorted(float(s[-6:]) for s in o_starts)  # "SS.mmm"
    o_durs = [ms_between(a, b) for a, b in zip(o_starts, o_done)]
    runs = new.get("ttlRuns") or []
    n_offsets = sorted(float(r["startIso"][17:-1]) for r in runs)
    n_durs = [r.get("durationMs") for r in runs if r.get("durationMs") is not None]
    add("TTL job cadence",
        f"{len(o_starts)} runs read from the PostgreSQL log, one per minute, starting at hh:mm:"
        f"{o_offsets[0]:06.3f} to hh:mm:{o_offsets[-1]:06.3f}" if o_offsets else "not recorded",
        f"{len(runs)} runs read from cron.job_run_details, one per minute, starting at hh:mm:"
        f"{n_offsets[0]:06.3f} to hh:mm:{n_offsets[-1]:06.3f}" if n_offsets else "not recorded",
        bool(o_offsets and n_offsets and max(o_offsets) < 1 and max(n_offsets) < 1),
        "Same schedule (pg_cron '* * * * *'); start offsets are pg_cron dispatch jitter.")
    add("TTL job run duration (ms) on a tiny collection",
        {"min": min(o_durs), "max": max(o_durs), "source": "log 'starting' to 'COMMAND completed'"} if o_durs else None,
        {"min": min(n_durs), "max": max(n_durs), "source": "cron.job_run_details end_time - start_time"} if n_durs else None,
        None, "Different measurement sources, so only the order of magnitude is comparable.")

    # lag
    o_cad = old.get("purgeCadence") or {}
    o_lags = {c.get("doc", "").split(" ")[0]: c.get("lagAfterEligible_s") for c in o_cad.get("correlation", [])
              if c.get("lagAfterEligible_s")}
    n_lags = {k: {"lagAfterEligibleSeconds": v.get("lagAfterEligibleSeconds"),
                  "purgedByFirstRunAfterEligible": v.get("purgedByFirstRunAfterEligible"),
                  "run": (v.get("purgedByRun") or {}).get("start")} for k, v in pa.items()}
    add("lag from eligibility to purge", {"samples": o_lags, "bound": o_cad.get("boundOnLag")},
        {"samples": n_lags}, None,
        "Both runs: each document goes at the first pg_cron run after it becomes eligible, so the lag is the time "
        "to the next whole minute (0 to about 60 s); the sample values depend on when in the minute each document "
        "became eligible.")

    # pg_cron job list
    n_spec = step(new, "pg_cron schedule, exact command from the test spec") or {}
    n_fb = step(new, "pg_cron schedule, same SQL as role documentdb") or {}
    o_jobs = next((c for c in old_rerun.get("readOnlyChecksPerformed", []) if c.startswith("pglog: pg_cron jobs")),
                  "not recorded")
    add("pg_cron jobs in the container", o_jobs + " (read from the PostgreSQL log; PostgreSQL was down by then)",
        (n_fb.get("response") or {}).get("parsed") or (n_spec.get("response") or {}).get("parsed"), None,
        "Same four jobs and schedules on both builds, as far as the 0.117 log shows.")
    add("psql -U postgres -p 9712 inside the container",
        "not run on 0.117 (PostgreSQL had crashed); unknown",
        {"returncode": (n_spec.get("response") or {}).get("returncode"),
         "stderr": ((n_spec.get("response") or {}).get("stderr") or "").strip()},
        None, "On 1.2.0 the superuser role is documentdb; scripts and docs that use -U postgres need -U documentdb "
              "-d postgres.")

    # TTL settings
    g = (step(new, "TTL-related PostgreSQL settings") or {}).get("response", {}).get("parsed") or {}
    add("TTL-related GUCs",
        "not readable on 0.117 (PostgreSQL down); postgresql.conf had no documentdb TTL overrides",
        {k: v.get("setting") for k, v in g.items()}, None,
        "1.2.0 values are the compiled defaults (source = default) except where the source column says otherwise.")

    new["comparisonWith0117"] = rows

    # two independent 1.2.0 runs: run 1 (report.run1.json, 16 polls) and this report
    run1_path = os.path.join(HERE, "report.run1.json")
    if os.path.exists(run1_path):
        r1 = json.load(open(run1_path))

        def summary(rep):
            resp = (step(rep, "poll every 15 s") or {}).get("response") or {}
            polls = resp.get("polls", [])
            pa_ = rep.get("purgeAttribution") or {}
            comp = (step(rep, "compound TTL index attempt") or {}).get("response") or {}
            return {
                "insertedAt": rep.get("insertedAt"),
                "polls": len(polls),
                "pollWindowSecondsAfterInsert": polls[-1]["secondsAfterInsert"] if polls else None,
                "purged": sorted(resp.get("disappeared", {}).keys()),
                "neverPurged": sorted(resp.get("finalPresentIds", [])),
                "ttlRunsWhileSurvivorsExisted": max((v.get("ttlRunsWhileItExisted", 0)
                                                     for v in (rep.get("neverPurged") or {}).values()), default=None),
                "compoundTTL": [comp.get("code"), comp.get("codeName")],
                "exp2IndexBuildMs": (step(rep, "create second TTL index on exp2") or {}).get("elapsedMs"),
                "lagAfterEligibleSeconds": {k: v.get("lagAfterEligibleSeconds") for k, v in pa_.items()},
                "allPurgedByFirstRunAfterEligible": (all(v.get("purgedByFirstRunAfterEligible") for v in pa_.values())
                                                     if pa_ else None),
            }
        s1, s2 = summary(r1), summary(new)
        new["reproducibility"] = {
            "run1": s1, "run2_this_report": s2,
            "samePurgedSet": s1["purged"] == s2["purged"],
            "sameSurvivors": s1["neverPurged"] == s2["neverPurged"],
            "sameCompoundError": s1["compoundTTL"] == s2["compoundTTL"],
            "note": ("Run 1 (report.run1.json, run1.log) stopped after 16 polls (+226 s) because its poll deadline was "
                     "computed a few ms before the loop's own start, which dropped the +240 s poll; the bug is fixed in "
                     "run_ttl_test.py and run 2 (this report) is the primary result. Run 1's two createIndexes readings "
                     "were regenerated by amend_readings.py."),
        }
        print("reproducibility:", json.dumps({k: v for k, v in new["reproducibility"].items()
                                              if k.startswith("same")}))
    with open(NEW, "w") as f:
        f.write(json.dumps(new, indent=2, default=str) + "\n")
    for r in rows:
        print(f"- {r['item']}: same={r['same']}")
        print(f"    0.117: {json.dumps(r['engine_0_117'], default=str)[:400]}")
        print(f"    1.2.0: {json.dumps(r['engine_1_2_0'], default=str)[:400]}")


if __name__ == "__main__":
    main()
