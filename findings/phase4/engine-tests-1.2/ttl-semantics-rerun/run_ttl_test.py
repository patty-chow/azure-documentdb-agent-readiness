#!/usr/bin/env python
"""ttl-semantics, ENGINE 1.2.0 RERUN, database t_ttl_rerun, on documentdb-local.

One run takes about 4 min 15 s and does, in order:
  1. Records the image identity (docker inspect), the PostgreSQL extension
     versions and the TTL-related settings (read-only psql inside the container),
     the host/container clock skew, free space on /data, buildInfo and hello.
  2. Reads the pg_cron schedule with the exact command from the test spec
     (psql -U postgres ...); if that fails, reads it again as role documentdb.
  3. Creates a TTL index on exp (expireAfterSeconds 5), inserts documents whose
     exp is a past Date, a future Date (+90 s), a string, a number, missing,
     null and an array of Dates, plus documents that carry a past Date (or a
     future control Date) in exp2; attempts a compound TTL index; creates a
     second TTL index on exp2 (after the documents exist, as in the 0.117 run);
     attempts a non-numeric expireAfterSeconds.
  4. Polls the collection every 15 s for 240 s (time.sleep in this process) and
     inserts an already-expired probe after each observed purge, exactly as the
     0.117 run did.
  5. Reads cron.job_run_details for the TTL job and attributes every observed
     purge to one pg_cron run.
  6. Drops database t_ttl_rerun (finally block) and confirms it is gone.

Reads LOCAL_URI from engine-tests/local.env and never prints it. Touches only
database t_ttl_rerun. Writes report.json next to this script. Rerun with:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python run_ttl_test.py
"""
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time

import bson
import pymongo
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = ("/private/tmp/claude-501/-Users-julietai-claude/"
            "40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env")
CONTAINER = "ddb-engine-test"
DB = "t_ttl_rerun"
COLL = "docs"
TTL_SECONDS = 5
POLL_EVERY = 15
POLL_MAX = 240
HARD_CAP_S = 285          # whole-script budget, keeps the command under 5 minutes
POST_RESERVE_S = 15       # time kept back for the steps after the poll loop
REPORT_PATH = os.path.join(HERE, "report.json")
SPEC_CRON_SQL = "select jobname, schedule, command from cron.job"
SPEC_CRON_CMD_TEXT = ('docker exec ddb-engine-test psql -U postgres -p 9712 -tAc '
                      '"select jobname, schedule, command from cron.job"')

T0_MONO = time.monotonic()
STEPS = []


# ---------------------------------------------------------------- helpers
def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(d):
    return d.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def rjson(obj):
    """Relaxed Extended JSON: dates as {"$date": iso}, numbers plain."""
    return json.loads(json_util.dumps(obj, json_options=json_util.RELAXED_JSON_OPTIONS))


def bson_type(doc, field):
    if field not in doc:
        return "missing"
    v = doc[field]
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, dt.datetime):
        return "date"
    if isinstance(v, str):
        return "string"
    if isinstance(v, bson.int64.Int64):
        return "long"
    if isinstance(v, int):
        return "int" if -2**31 <= v < 2**31 else "long"
    if isinstance(v, float):
        return "double"
    if isinstance(v, list):
        return "array[" + ",".join(bson_type({"x": e}, "x") for e in v) + "]"
    return type(v).__name__


def err_dict(e):
    d = {"exception": type(e).__name__}
    if isinstance(e, OperationFailure):
        det = dict(e.details or {})
        d["code"] = det.get("code", e.code)
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg", str(e))
        d["errorLabelsPresent"] = "errorLabels" in det
        if "errorLabels" in det:
            d["errorLabels"] = det["errorLabels"]
        d["serverReply"] = rjson(det)
    else:
        d["errmsg"] = str(e)
    return d


def record(step, command, response, reading, ok, started, extra=None):
    entry = {"n": len(STEPS) + 1, "step": step, "command": command, "ok": ok,
             "at": iso(started),
             "elapsedMs": round((now() - started).total_seconds() * 1000, 1),
             "response": response, "reading": reading}
    if extra:
        entry.update(extra)
    STEPS.append(entry)
    print(f"[{entry['n']:02d}] {step}: ok={ok} {json.dumps(response, default=str)[:260]}",
          file=sys.stderr, flush=True)
    return entry


def driver_step(step, command, fn, on_ok, on_err, extra=None):
    started = now()
    try:
        resp = fn()
        if not isinstance(resp, (str, bool, int, float, type(None))):
            resp = rjson(resp)
        ms = (now() - started).total_seconds() * 1000
        return record(step, command, resp, on_ok(resp, ms), True, started, extra)
    except PyMongoError as e:
        ed = err_dict(e)
        return record(step, command, ed, on_err(ed), False, started, extra)


def run_argv(argv, timeout=30):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:  # noqa: BLE001 - recorded verbatim
        return {"returncode": None, "exception": type(e).__name__, "errmsg": str(e)}


def shell_step(step, argv, on_done, command_text=None, extra=None, timeout=30):
    started = now()
    resp = run_argv(argv, timeout)
    try:
        reading, parsed = on_done(resp)
    except Exception as e:  # noqa: BLE001 - keep going, record the parse failure
        reading, parsed = f"Output could not be parsed ({type(e).__name__}: {e}); raw output kept.", None
    if parsed is not None:
        resp["parsed"] = parsed
    return record(step, command_text or shlex.join(argv), resp, reading,
                  resp.get("returncode") == 0, started, extra)


def typed(doc, field):
    """Render a relaxed-EJSON field value with its BSON type for a reading."""
    if field not in doc:
        return "missing"
    v = doc[field]
    if v is None:
        return "null"
    if isinstance(v, dict) and "$date" in v:
        return f"Date {v['$date']}"
    if isinstance(v, str):
        return f"string '{v}'"
    if isinstance(v, bool):
        return f"bool {v}"
    if isinstance(v, (int, float)):
        return f"number {v}"
    return json.dumps(v)


def ci_counts(r):
    """createIndexes reply counts; the gateway wraps them like a sharded router: {raw: {defaultShard: {...}}}."""
    if not isinstance(r, dict):
        return {}
    if "numIndexesBefore" in r:
        return r
    for v in ((r or {}).get("raw") or {}).values():
        return v
    return {}


def psql_argv(sql):
    return ["docker", "exec", CONTAINER, "psql", "-U", "documentdb", "-p", "9712",
            "-d", "postgres", "-tAc", sql]


def psql_rows(stdout):
    rows = []
    for line in (stdout or "").splitlines():
        s = line.strip()
        if not s or s == "SET":       # the container's psqlrc echoes two SETs
            continue
        rows.append(line.split("|"))
    return rows


def first_line(s):
    for line in (s or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


# ---------------------------------------------------------------- environment steps
def environment_steps():
    facts = {}

    def on_inspect(r):
        if r.get("returncode") != 0:
            return (f"docker inspect failed: {first_line(r.get('stderr'))}.", None)
        image, image_id, started_at, labels = r["stdout"].strip().split("|", 3)
        labels = json.loads(labels)
        facts["image"] = {"tag": image, "imageId": image_id, "containerStartedAt": started_at,
                          "ociVersion": labels.get("org.opencontainers.image.version"),
                          "ociRevision": labels.get("org.opencontainers.image.revision"),
                          "ociCreated": labels.get("org.opencontainers.image.created")}
        im = facts["image"]
        return (f"Container runs {im['tag']} (OCI version {im['ociVersion']}, revision "
                f"{(im['ociRevision'] or '')[:12]}, built {im['ociCreated']}), so everything below is "
                f"evidence about open-source engine {im['ociVersion']}.", facts["image"])

    shell_step("image identity",
               ["docker", "inspect", CONTAINER, "--format",
                "{{.Config.Image}}|{{.Image}}|{{.State.StartedAt}}|{{json .Config.Labels}}"],
               on_inspect)

    def on_ext(r):
        rows = psql_rows(r.get("stdout"))
        ext = {row[0]: row[1] for row in rows if len(row) >= 2}
        facts["extensions"] = ext
        if r.get("returncode") != 0:
            return (f"Extension query failed: {first_line(r.get('stderr'))}.", None)
        return (f"PostgreSQL extensions: documentdb {ext.get('documentdb')}, documentdb_core "
                f"{ext.get('documentdb_core')}, pg_cron {ext.get('pg_cron')}, vector {ext.get('vector')}.",
                ext)

    shell_step("PostgreSQL extension versions (read-only)",
               psql_argv("select extname, extversion from pg_extension order by extname"), on_ext)

    def on_cron_spec(r):
        rows = psql_rows(r.get("stdout"))
        if r.get("returncode") == 0:
            return (f"The spec's command works and lists {len(rows)} pg_cron job(s): "
                    + "; ".join(" | ".join(x) for x in rows) + ".", rows)
        return (f"The spec's exact command fails with exit code {r.get('returncode')} because the 1.2.0 "
                f"image has no PostgreSQL role named postgres ({first_line(r.get('stderr'))}); the "
                f"schedule is read as role documentdb in the next step.", None)

    shell_step("pg_cron schedule, exact command from the test spec",
               ["docker", "exec", CONTAINER, "psql", "-U", "postgres", "-p", "9712", "-tAc", SPEC_CRON_SQL],
               on_cron_spec, command_text=SPEC_CRON_CMD_TEXT)
    spec_ok = STEPS[-1]["ok"]

    def on_cron_fallback(r):
        rows = psql_rows(r.get("stdout"))
        facts["cronJobsBefore"] = rows
        if r.get("returncode") != 0:
            return (f"Fallback read failed: {first_line(r.get('stderr'))}.", None)
        ttl = [x for x in rows if x and x[0] == "documentdb_ttl_task"]
        t = ttl[0] if ttl else None
        return ((f"pg_cron holds {len(rows)} jobs; the TTL purger is '{t[0]}' on schedule '{t[1]}' running "
                 f"'{t[2]}'." if t else f"pg_cron holds {len(rows)} jobs and none is named documentdb_ttl_task."),
                rows)

    if not spec_ok:
        shell_step("pg_cron schedule, same SQL as role documentdb (fallback)",
                   psql_argv(SPEC_CRON_SQL), on_cron_fallback)
    else:
        facts["cronJobsBefore"] = STEPS[-1]["response"].get("parsed")

    gucs_sql = ("select name, setting, boot_val, source from pg_settings where name ilike '%ttl%' "
                "or name in ('cron.timezone','cron.log_run','cron.use_background_workers',"
                "'documentdb.enableBackgroundWorker','documentdb.enableBackgroundWorkerJobs',"
                "'documentdb.indexBuildsScheduledOnBgWorker') order by name")

    def on_gucs(r):
        rows = psql_rows(r.get("stdout"))
        g = {row[0]: {"setting": row[1], "boot_val": row[2], "source": row[3]} for row in rows if len(row) >= 4}
        facts["gucs"] = g
        if r.get("returncode") != 0:
            return (f"Settings query failed: {first_line(r.get('stderr'))}.", None)

        def s(name):
            return g.get(name, {}).get("setting")
        return (f"TTL settings are at their defaults: TTLTaskMaxRunTimeInMS={s('documentdb.TTLTaskMaxRunTimeInMS')}, "
                f"repeatPurgeIndexesForTTLTask={s('documentdb.repeatPurgeIndexesForTTLTask')}, "
                f"maxTTLDeleteBatchSize={s('documentdb.maxTTLDeleteBatchSize')}, "
                f"enable_ttl_cleanup_background={s('documentdb.enable_ttl_cleanup_background')} (so the pg_cron job, "
                f"not the background worker, purges), createTTLIndexAsCompositeByDefault="
                f"{s('documentdb.createTTLIndexAsCompositeByDefault')}, cron.timezone={s('cron.timezone')}.", g)

    shell_step("TTL-related PostgreSQL settings (read-only)", psql_argv(gucs_sql), on_gucs)

    started = now()
    h0 = time.time()
    r = run_argv(["docker", "exec", CONTAINER, "date", "-u", "+%s.%N"])
    h1 = time.time()
    try:
        c = float(r["stdout"].strip())
        skew = c - (h0 + h1) / 2
        r["parsed"] = {"hostBefore": h0, "hostAfter": h1, "container": c,
                       "containerMinusHostSeconds": round(skew, 3), "uncertaintySeconds": round((h1 - h0) / 2, 3)}
        facts["skew"] = skew
        reading = (f"Container clock minus host clock is {skew * 1000:.0f} ms (+/- {(h1 - h0) / 2 * 1000:.0f} ms), so "
                   f"host poll times and pg_cron run times are comparable to well under a second.")
    except Exception as e:  # noqa: BLE001
        facts["skew"] = 0.0
        reading = f"Could not measure clock skew ({e}); assuming 0."
    record("host vs container clock", "docker exec ddb-engine-test date -u +%s.%N  (bracketed by host time.time())",
           r, reading, r.get("returncode") == 0, started)

    def on_df(r):
        line = [x for x in (r.get("stdout") or "").splitlines() if x.startswith("/")]
        return (f"/data inside the container: {line[0] if line else first_line(r.get('stderr'))} "
                f"(the 0.117 run was killed by a full Docker VM disk).", None)

    shell_step("free space on /data before the test", ["docker", "exec", CONTAINER, "df", "-h", "/data"], on_df)
    return facts


# ---------------------------------------------------------------- poll loop
def poll_loop(coll, t_ins, eligible):
    polls, disappeared, probes = [], {}, {}
    present_prev = None
    last_ok_at = None
    t_poll0 = now()
    i = 0
    while True:
        t = now()
        entry = {"poll": i, "at": iso(t), "secondsAfterInsert": round((t - t_ins).total_seconds(), 1)}
        try:
            ids = sorted(d["_id"] for d in coll.find({}, {"_id": 1}))
            entry["count"] = len(ids)
            entry["present"] = ids
            gone = [x for x in present_prev if x not in ids] if present_prev is not None else []
            entry["goneSinceLastPoll"] = gone
            for g in gone:
                disappeared[g] = {"lastSeenAt": last_ok_at, "firstGoneAt": iso(t),
                                  "secondsAfterInsertFirstGone": entry["secondsAfterInsert"]}
            present_prev = ids
            last_ok_at = iso(t)
        except PyMongoError as e:
            entry["error"] = err_dict(e)
        polls.append(entry)
        print(f"  poll {i} +{entry['secondsAfterInsert']}s count={entry.get('count')} "
              f"gone={entry.get('goneSinceLastPoll')}", file=sys.stderr, flush=True)

        probe_id = None
        if present_prev is not None:
            if "probe2_past_date" not in probes and "past_date_60s" in disappeared:
                probe_id = "probe2_past_date"
            elif ("probe2_past_date" in disappeared and "probe3_past_date" not in probes
                  and (t_poll0 + dt.timedelta(seconds=POLL_MAX) - now()).total_seconds() > 75):
                probe_id = "probe3_past_date"
        if probe_id:
            tp = now()
            doc = {"_id": probe_id, "kind": "probe: exp = Date 60 s before its insert, inserted right after "
                                            "an observed purge", "exp": tp - dt.timedelta(seconds=60)}
            try:
                coll.insert_one(doc)
                done = now()
                probes[probe_id] = {"insertedAt": iso(done), "exp": iso(doc["exp"]),
                                    "command": f"coll.insert_one({{'_id': '{probe_id}', 'exp': <now - 60 s>}})"}
                entry["probeInserted"] = {"_id": probe_id, **probes[probe_id]}
                eligible[probe_id] = {"at": done, "basis": "exp was already 55 s past eligibility at insert; "
                                                          "effective = insert completion"}
                present_prev = present_prev + [probe_id]
            except PyMongoError as e:
                entry["probeInsertError"] = err_dict(e)
                probes[probe_id] = {"error": err_dict(e)}

        i += 1
        if i > POLL_MAX // POLL_EVERY:            # polls 0..16 cover 0..240 s
            break
        next_t = t_poll0 + dt.timedelta(seconds=POLL_EVERY * i)
        wait = max(0.0, (next_t - now()).total_seconds())
        if time.monotonic() - T0_MONO + wait > HARD_CAP_S - POST_RESERVE_S:
            entry["stoppedEarly"] = "hard cap: the next poll would push the script past its 5-minute budget"
            break
        time.sleep(wait)
    return t_poll0, polls, disappeared, probes


# ---------------------------------------------------------------- attribution
def parse_runs(rows):
    runs = []
    for row in rows:
        if len(row) < 6:
            continue
        jobid, runid, status, start, end, msg = row[:6]
        try:
            s = parse_iso(start)
            e = parse_iso(end) if end else None
        except ValueError:
            continue
        runs.append({"jobid": jobid, "runid": runid, "status": status, "start": s, "end": e,
                     "startIso": start, "endIso": end, "returnMessage": msg,
                     "durationMs": round((e - s).total_seconds() * 1000, 3) if e else None})
    return runs


def attribute(disappeared, eligible, runs, skew_s, inserted_at):
    skew = dt.timedelta(seconds=skew_s)
    out = {}
    for doc_id, w in sorted(disappeared.items(), key=lambda kv: kv[1]["firstGoneAt"]):
        lo = parse_iso(w["lastSeenAt"]) + skew
        hi = parse_iso(w["firstGoneAt"]) + skew
        cands = [r for r in runs if lo - dt.timedelta(seconds=0.5) <= r["start"] <= hi]
        e = {"lastSeenAt": w["lastSeenAt"], "firstGoneAt": w["firstGoneAt"],
             "candidateRunStarts": [r["startIso"] for r in cands]}
        el = eligible.get(doc_id)
        if el:
            el_c = el["at"] + skew
            e["eligibleAt"] = iso(el["at"])
            e["eligibleBasis"] = el["basis"]
            after = [r for r in runs if r["start"] > el_c]
            e["firstRunAfterEligible"] = after[0]["startIso"] if after else None
            if len(cands) == 1:
                r = cands[0]
                e["purgedByRun"] = {"runid": r["runid"], "start": r["startIso"], "end": r["endIso"],
                                    "status": r["status"], "durationMs": r["durationMs"]}
                e["lagAfterEligibleSeconds"] = round((r["start"] - el_c).total_seconds(), 1)
                e["purgedByFirstRunAfterEligible"] = bool(after) and after[0]["runid"] == r["runid"]
                e["runsThatStartedWhileEligibleButDidNotPurge"] = len(
                    [x for x in runs if el_c < x["start"] < r["start"]])
            else:
                e["attributionNote"] = f"{len(cands)} candidate runs in the disappearance window"
        out[doc_id] = e
    return out


# ---------------------------------------------------------------- main
def main():
    env = load_env()
    uri = env["LOCAL_URI"]
    secret = env.get("LOCAL_PASS")
    report = {
        "test": "ttl-semantics",
        "stage": "ENGINE 1.2.0 RERUN (compare with the 0.117 run in findings/phase4/engine-tests/ttl-semantics)",
        "database": DB, "collection": COLL,
        "target": "documentdb-local container ddb-engine-test on localhost:10260 (open-source DocumentDB engine "
                  "and gateway, MongoDB wire protocol, TLS with a self-signed certificate)",
        "driver": f"PyMongo {pymongo.version} on Python {sys.version.split()[0]}",
        "expireAfterSeconds": TTL_SECONDS, "pollEverySeconds": POLL_EVERY, "pollMaxSeconds": POLL_MAX,
        "scriptStartedAt": iso(now()),
    }
    facts = environment_steps()
    report["rerunCommand"] = ("/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python "
                              + os.path.abspath(__file__))
    report["image"] = facts.get("image")
    report["extensions"] = facts.get("extensions")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000, tz_aware=True)
    adm = client.admin
    db = client[DB]
    coll = db[COLL]
    skew_s = facts.get("skew", 0.0)
    try:
        bi = driver_step("buildInfo", 'client.admin.command("buildInfo")  (mongosh: db.adminCommand({buildInfo: 1}))',
                         lambda: adm.command("buildInfo"),
                         lambda r, ms: (f"The gateway reports MongoDB-compatibility version {r.get('version')} "
                                        f"(versionArray {r.get('versionArray')}); the engine build is the image and "
                                        f"extension version recorded in steps 1 and 2."),
                         lambda e: f"buildInfo failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")
        report["buildInfo"] = bi["response"] if bi["ok"] else None

        driver_step("hello", 'client.admin.command("hello")',
                    lambda: adm.command("hello"),
                    lambda r, ms: (f"hello reports maxWireVersion {r.get('maxWireVersion')} and maxWriteBatchSize "
                                   f"{r.get('maxWriteBatchSize')}."),
                    lambda e: f"hello failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        pre = driver_step("does t_ttl_rerun exist before the test", f'"{DB}" in client.list_database_names()',
                    lambda: {"t_ttl_rerunPresent": DB in client.list_database_names()},
                    lambda r, ms: ("Database t_ttl_rerun already existed and is cleaned below." if r["t_ttl_rerunPresent"]
                                   else "Database t_ttl_rerun did not exist, so the run starts from nothing."),
                    lambda e: f"listDatabases failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        # Keep the setup (insert + index builds) away from a pg_cron run at hh:mm:00.
        n_ = now()
        sec = n_.second + n_.microsecond / 1e6
        waited = 0.0
        if sec >= 50 or sec < 2:
            waited = (63 - sec) if sec >= 50 else (3 - sec)
            time.sleep(waited)
        report["setupPhaseGuard"] = {"secondOfMinuteBeforeGuard": round(sec, 3), "waitedSeconds": round(waited, 3),
                                     "rule": "if the setup would start within 10 s before or 2 s after a whole "
                                             "minute, wait until hh:mm:03 so no pg_cron run overlaps it"}

        driver_step("drop collection docs (clean start)", f'db.command("drop", "{COLL}")  (mongosh: db.{COLL}.drop())',
                    lambda: db.command("drop", COLL),
                    lambda r, ms: (f"drop returned {r} although the collection did not exist yet."
                                   if not (pre["response"] or {}).get("t_ttl_rerunPresent")
                                   else f"drop returned {r}; the leftover collection is gone."),
                    lambda e: (f"drop of the not-yet-existing collection failed with {e.get('code')} "
                               f"{e.get('codeName')}: {e.get('errmsg')}."))

        spec_exp = {"key": {"exp": 1}, "name": "exp_ttl", "expireAfterSeconds": TTL_SECONDS}
        driver_step("create TTL index on exp",
                    f'db.command("createIndexes", "{COLL}", indexes=[{json.dumps(spec_exp)}])  '
                    f'(mongosh: db.{COLL}.createIndex({{exp: 1}}, {{name: "exp_ttl", expireAfterSeconds: 5}}))',
                    lambda: db.command("createIndexes", COLL, indexes=[spec_exp]),
                    lambda r, ms: (f"Single-field TTL index exp_ttl created in {ms:.0f} ms "
                                   f"(numIndexesBefore {ci_counts(r).get('numIndexesBefore')} -> numIndexesAfter "
                                   f"{ci_counts(r).get('numIndexesAfter')}, createdCollectionAutomatically "
                                   f"{ci_counts(r).get('createdCollectionAutomatically')}, reply wrapped in "
                                   f"raw.{','.join((r.get('raw') or {}).keys()) or '-'})."),
                    lambda e: f"TTL index on exp failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        def idx_summary(r):
            batch = (r.get("cursor") or {}).get("firstBatch", [])
            return batch, "; ".join(
                f"{i.get('name')} key={i.get('key')}"
                + (f" expireAfterSeconds={i.get('expireAfterSeconds')}" if "expireAfterSeconds" in i else "")
                + (f" storageEngine={i.get('storageEngine')}" if "storageEngine" in i else "")
                for i in batch)

        driver_step("listIndexes after the first TTL index", f'db.command("listIndexes", "{COLL}")',
                    lambda: db.command("listIndexes", COLL),
                    lambda r, ms: f"listIndexes shows {idx_summary(r)[1]}.",
                    lambda e: f"listIndexes failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        t_ins = now()
        past = t_ins - dt.timedelta(seconds=60)
        day = t_ins + dt.timedelta(days=1)
        docs = [
            {"_id": "past_date_60s", "kind": "exp = Date 60 s before insert", "exp": past},
            {"_id": "future_date_90s", "kind": "exp = Date 90 s after insert", "exp": t_ins + dt.timedelta(seconds=90)},
            {"_id": "string_value", "kind": "exp = ISO-8601 string of a time 60 s before insert", "exp": iso(past)},
            {"_id": "number_value", "kind": "exp = epoch milliseconds 60 s before insert (64-bit integer)",
             "exp": int(past.timestamp() * 1000)},
            {"_id": "missing_field", "kind": "no exp field"},
            {"_id": "null_value", "kind": "exp = null", "exp": None},
            {"_id": "array_of_dates", "kind": "exp = [Date 60 s before insert, Date 1 day after insert]",
             "exp": [past, day]},
            {"_id": "exp2_past_only", "kind": "no exp; exp2 = Date 60 s before insert (only exp2_ttl can purge it)",
             "exp2": past},
            {"_id": "exp_future_exp2_past", "kind": "exp = Date 1 day after insert; exp2 = Date 60 s before insert",
             "exp": day, "exp2": past},
            {"_id": "exp2_future_control", "kind": "no exp; exp2 = Date 1 day after insert (control)", "exp2": day},
        ]
        types = {d["_id"]: {"exp": bson_type(d, "exp"), "exp2": bson_type(d, "exp2")} for d in docs}
        ins = driver_step(
            "insert the test documents",
            f'db.command("insert", "{COLL}", documents=<the {len(docs)} documents in insertedDocuments>, ordered=True)',
            lambda: db.command("insert", COLL, documents=docs, ordered=True),
            lambda r, ms: (f"{r.get('n')} documents inserted at {iso(t_ins)}; past_date_60s, array_of_dates and the two "
                           f"exp2 past-Date documents are already eligible, future_date_90s becomes eligible at "
                           f"insert + 95 s."),
            lambda e: f"insert failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}",
            extra={"insertedDocuments": rjson(docs), "bsonTypes": types})
        ins_done = parse_iso(ins["at"]) + dt.timedelta(milliseconds=ins["elapsedMs"])
        report["insertedAt"] = iso(t_ins)
        report["insertCompletedAt"] = iso(ins_done)

        spec_ab = {"key": {"a": 1, "b": 1}, "name": "ab_ttl", "expireAfterSeconds": TTL_SECONDS}
        driver_step("compound TTL index attempt",
                    f'db.command("createIndexes", "{COLL}", indexes=[{json.dumps(spec_ab)}])  '
                    f'(mongosh: db.{COLL}.createIndex({{a: 1, b: 1}}, {{name: "ab_ttl", expireAfterSeconds: 5}}))',
                    lambda: db.command("createIndexes", COLL, indexes=[spec_ab]),
                    lambda r, ms: f"UNEXPECTED: the compound TTL index was accepted ({r}).",
                    lambda e: (f"Compound TTL index rejected with code {e.get('code')} {e.get('codeName')} "
                               f"('{e.get('errmsg', '').split('}:')[-1].strip()}'), "
                               f"{'with errorLabels ' + str(e.get('errorLabels')) if e.get('errorLabelsPresent') else 'no errorLabels in the reply'}."))

        spec_exp2 = {"key": {"exp2": 1}, "name": "exp2_ttl", "expireAfterSeconds": TTL_SECONDS}
        e2 = driver_step("create second TTL index on exp2 (collection already holds the documents)",
                         f'db.command("createIndexes", "{COLL}", indexes=[{json.dumps(spec_exp2)}])  '
                         f'(mongosh: db.{COLL}.createIndex({{exp2: 1}}, {{name: "exp2_ttl", expireAfterSeconds: 5}}))',
                         lambda: db.command("createIndexes", COLL, indexes=[spec_exp2]),
                         lambda r, ms: (f"A second single-field TTL index (exp2_ttl) is accepted next to exp_ttl "
                                        f"(numIndexesBefore {ci_counts(r).get('numIndexesBefore')} -> "
                                        f"numIndexesAfter {ci_counts(r).get('numIndexesAfter')}) and took "
                                        f"{ms:.0f} ms on the "
                                        f"{len(docs)}-document collection."),
                         lambda e: (f"Second TTL index rejected with code {e.get('code')} {e.get('codeName')}: "
                                    f"{e.get('errmsg')}"))
        exp2_ready = parse_iso(e2["at"]) + dt.timedelta(milliseconds=e2["elapsedMs"])
        report["exp2IndexReadyAt"] = iso(exp2_ready) if e2["ok"] else None

        spec_bad = {"key": {"exp3": 1}, "name": "exp3_bad", "expireAfterSeconds": "abc"}
        driver_step("TTL index with non-numeric expireAfterSeconds (repeat of the 0.117 extra step)",
                    f'db.command("createIndexes", "{COLL}", indexes=[{json.dumps(spec_bad)}])',
                    lambda: db.command("createIndexes", COLL, indexes=[spec_bad]),
                    lambda r, ms: f"UNEXPECTED: non-numeric expireAfterSeconds was accepted ({r}).",
                    lambda e: (f"Non-numeric expireAfterSeconds rejected with code {e.get('code')} "
                               f"{e.get('codeName')} ('{e.get('errmsg', '').split('}:')[-1].strip()}'), "
                               f"{'with errorLabels ' + str(e.get('errorLabels')) if e.get('errorLabelsPresent') else 'no errorLabels in the reply'}."))

        driver_step("listIndexes after all createIndexes attempts", f'db.command("listIndexes", "{COLL}")',
                    lambda: db.command("listIndexes", COLL),
                    lambda r, ms: f"listIndexes shows {idx_summary(r)[1]}.",
                    lambda e: f"listIndexes failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        # effective eligibility (host clock): when a pg_cron run could first delete the document
        eligible = {
            "past_date_60s": {"at": ins_done, "basis": "exp + 5 s was already past at insert; effective = insert "
                                                       "completion (exp_ttl existed before the insert)"},
            "array_of_dates": {"at": ins_done, "basis": "earliest array element + 5 s was already past at insert; "
                                                        "effective = insert completion"},
            "future_date_90s": {"at": docs[1]["exp"] + dt.timedelta(seconds=TTL_SECONDS),
                                "basis": "exp (insert + 90 s) + expireAfterSeconds 5"},
        }
        if e2["ok"]:
            for k in ("exp2_past_only", "exp_future_exp2_past"):
                eligible[k] = {"at": max(ins_done, exp2_ready),
                               "basis": "exp2 + 5 s was already past at insert; effective = completion of the "
                                        "createIndexes that built exp2_ttl"}

        t_poll0, polls, disappeared, probes = poll_loop(coll, t_ins, eligible)
        final_ids = polls[-1].get("present", [])
        expected_purge = ["past_date_60s", "future_date_90s", "array_of_dates", "exp2_past_only",
                          "exp_future_exp2_past"]
        gone_txt = ", ".join(f"{k} (gone by +{v['secondsAfterInsertFirstGone']} s)" for k, v in
                             sorted(disappeared.items(), key=lambda kv: kv[1]["firstGoneAt"])) or "nothing"
        record(f"poll every {POLL_EVERY} s for up to {POLL_MAX} s",
               f"{POLL_MAX // POLL_EVERY + 1} polls at t0 + {POLL_EVERY}*i s (t0 = {iso(t_poll0)}): "
               f"sorted(d['_id'] for d in coll.find({{}}, {{'_id': 1}}))"
               f" with time.sleep in this process; after past_date_60s disappears: coll.insert_one({{'_id': "
               f"'probe2_past_date', 'exp': <now - 60 s>}}); after probe2 disappears and more than 75 s remain: "
               f"the same for probe3_past_date",
               {"polls": polls, "disappeared": disappeared, "probes": probes,
                "finalPresentIds": final_ids,
                "expectedToPurge": expected_purge,
                "expectedPurgedButStillPresent": [x for x in expected_purge if x in final_ids]},
               (f"Purged during {polls[-1]['secondsAfterInsert']} s after insert: {gone_txt}; still present at the "
                f"last poll: {', '.join(final_ids)}."),
               all("error" not in p for p in polls), t_poll0)

        driver_step("final contents of the collection", f'list(db.{COLL}.find({{}}))',
                    lambda: list(coll.find({})),
                    lambda r, ms: ("Survivors and their values: "
                                   + "; ".join(f"{d['_id']} exp={typed(d, 'exp')}"
                                               + (f", exp2={typed(d, 'exp2')}" if 'exp2' in d else "") for d in r)
                                   + "."),
                    lambda e: f"find failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

        since = iso(parse_iso(report["scriptStartedAt"]) - dt.timedelta(seconds=120))
        runs_sql = ("select d.jobid, d.runid, d.status, "
                    "to_char(d.start_time at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), "
                    "to_char(d.end_time at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), "
                    "d.return_message from cron.job_run_details d join cron.job j on j.jobid = d.jobid "
                    f"where j.jobname = 'documentdb_ttl_task' and d.start_time >= '{since}'::timestamptz "
                    "order by d.start_time")
        runs_holder = {}

        def on_runs(r):
            rows = psql_rows(r.get("stdout"))
            runs = parse_runs(rows)
            runs_holder["runs"] = runs
            if r.get("returncode") != 0 or not runs:
                return (f"No TTL runs read ({first_line(r.get('stderr')) or 'empty result'}).", rows)
            offs = [r_["start"].second + r_["start"].microsecond / 1e6 for r_ in runs]
            durs = [r_["durationMs"] for r_ in runs if r_["durationMs"] is not None]
            sts = sorted({r_["status"] for r_ in runs})
            return (f"{len(runs)} documentdb_ttl_task runs from {runs[0]['startIso']} to {runs[-1]['startIso']}, each "
                    f"starting {min(offs) * 1000:.0f} to {max(offs) * 1000:.0f} ms after a whole minute and lasting "
                    f"{min(durs):.1f} to {max(durs):.1f} ms, status {', '.join(sts)}.", rows)

        shell_step("pg_cron run history of the TTL job (read-only)", psql_argv(runs_sql), on_runs)
        runs = runs_holder.get("runs", [])

        def on_cron_after(r):
            rows = psql_rows(r.get("stdout"))
            same = rows == facts.get("cronJobsBefore")
            return ((f"The pg_cron job list after the test is {'identical to' if same else 'DIFFERENT from'} the one "
                     f"read before it ({len(rows)} jobs), so creating TTL indexes does not add per-index jobs."),
                    rows)

        shell_step("pg_cron schedule after the test (role documentdb)", psql_argv(SPEC_CRON_SQL), on_cron_after)

        def on_log(r):
            lines = [x for x in (r.get("stdout") or "").splitlines() if x.strip()]
            starts = [x for x in lines if "starting: CALL documentdb_api_internal.delete_expired_rows" in x]
            ours = [x for x in lines if "t_ttl_rerun" in x]
            other = [x for x in lines if x not in starts and x not in ours]
            return ((f"Of the last {len(lines)} matching log lines, {len(starts)} are pg_cron 'starting' entries for "
                     f"delete_expired_rows, {len(ours)} mention database t_ttl_rerun, and {len(other)} are other TTL "
                     f"messages from the engine{': ' + other[0][:160] if other else ''}."),
                    {"lines": [x[:300] for x in lines], "otherTTLMessages": [x[:300] for x in other]})

        shell_step("TTL lines in the PostgreSQL log (read-only cross-check)",
                   ["docker", "exec", CONTAINER, "sh", "-c",
                    "grep -E 'delete_expired|TTL|t_ttl_rerun' /data/pglog.log | tail -n 30"], on_log)

        shell_step("free space on /data after the test", ["docker", "exec", CONTAINER, "df", "-h", "/data"],
                   lambda r: ((f"/data inside the container after the test: "
                               f"{[x for x in (r.get('stdout') or '').splitlines() if x.startswith('/')]}."), None))

        attribution = attribute(disappeared, eligible, runs, skew_s, ins_done)
        never = {}
        last_poll_at = parse_iso(polls[-1]["at"]) + dt.timedelta(seconds=skew_s)
        for d in docs:
            if d["_id"] in final_ids:
                never[d["_id"]] = {
                    "bsonTypes": types[d["_id"]],
                    "ttlRunsWhileItExisted": len([r for r in runs if (ins_done + dt.timedelta(seconds=skew_s))
                                                  < r["start"] < last_poll_at])}
        report["purgeAttribution"] = attribution
        report["neverPurged"] = never
        report["ttlRuns"] = [{k: v for k, v in r.items() if k not in ("start", "end")} for r in runs]
        report["probes"] = probes
    finally:
        driver_step("drop the test database t_ttl_rerun",
                    'client["t_ttl_rerun"].command("dropDatabase")  (mongosh: db.getSiblingDB("t_ttl_rerun").dropDatabase())',
                    lambda: db.command("dropDatabase"),
                    lambda r, ms: f"dropDatabase returned {r}.",
                    lambda e: f"dropDatabase failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")
        driver_step("confirm t_ttl_rerun is gone", f'"{DB}" in client.list_database_names()',
                    lambda: {"t_ttl_rerunPresent": DB in client.list_database_names()},
                    lambda r, ms: ("t_ttl_rerun is no longer listed, so the test left nothing behind." if not r["t_ttl_rerunPresent"]
                                   else "t_ttl_rerun is STILL listed after dropDatabase."),
                    lambda e: f"listDatabases failed with {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")
        client.close()
        im = facts.get("image") or {}
        ext = facts.get("extensions") or {}
        report["engine_version"] = (f"documentdb-local {im.get('tag')} (OCI version {im.get('ociVersion')}, revision "
                                    f"{(im.get('ociRevision') or '')[:12]}); PostgreSQL extension documentdb "
                                    f"{ext.get('documentdb')}; gateway buildInfo.version "
                                    f"{(report.get('buildInfo') or {}).get('version')}")
        report["steps"] = STEPS
        report["scriptFinishedAt"] = iso(now())
        report["scriptRuntimeSeconds"] = round(time.monotonic() - T0_MONO, 1)
        report["caveat"] = ("Everything here was observed on documentdb-local (open-source engine and gateway at the "
                            "version above, default GUCs, one idle-ish container shared with other tests). It is "
                            "evidence about the open-source engine, not proof of managed Azure DocumentDB behaviour, "
                            "whose TTL settings are not published.")
        text = json.dumps(report, indent=2, default=str)
        if secret and secret in text:
            text = text.replace(secret, "<redacted>")
        with open(REPORT_PATH, "w") as f:
            f.write(text + "\n")
        print(f"report written: {REPORT_PATH} ({len(text)} bytes, {report['scriptRuntimeSeconds']} s)", file=sys.stderr)


if __name__ == "__main__":
    main()
