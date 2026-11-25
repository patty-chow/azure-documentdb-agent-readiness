#!/usr/bin/env python
"""ttl-semantics rerun, SUPPLEMENTARY probe (not part of the tester's script), database t_ttl_rerun.

Run it only after run_ttl_test.py has finished (that script drops t_ttl_rerun at the end).
It checks generalisations in the tester's conclusions that the tester's script did not test:
  * more non-Date value types in a TTL field (int32, double, Decimal128, BSON Timestamp, ObjectId,
    embedded document, empty array, future-only array, reversed-order array holding one past Date);
  * whether a partialFilterExpression on a TTL index limits what the purger deletes;
  * which PostgreSQL op class a TTL index and a plain index get (createTTLIndexAsCompositeByDefault);
  * a few TTL createIndexes validation errors (negative, fractional, _id, hashed, out of range);
  * collMod of expireAfterSeconds.
Every step records the exact driver call or command, the exact reply or error and a reading.
Reads LOCAL_URI from engine-tests/local.env and never prints it. Touches only database t_ttl_rerun,
drops it at the end and confirms it is gone. Writes supplementary.json next to this script.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time

import bson
from bson import json_util, Decimal128, ObjectId, Timestamp
from bson.int64 import Int64
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = ("/private/tmp/claude-501/-Users-julietai-claude/"
            "40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env")
CONTAINER = "ddb-engine-test"
DB = "t_ttl_rerun"
COLL = "supp"
OUT = os.path.join(HERE, "supplementary.json")
STEPS = []


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
    return json.loads(json_util.dumps(obj, json_options=json_util.RELAXED_JSON_OPTIONS))


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
    entry = {"n": len(STEPS) + 1, "step": step, "command": command, "ok": ok, "at": iso(started),
             "elapsedMs": round((now() - started).total_seconds() * 1000, 1),
             "response": response, "reading": reading}
    if extra:
        entry.update(extra)
    STEPS.append(entry)
    print(f"[S{entry['n']:02d}] {step}: ok={ok} {json.dumps(response, default=str)[:240]}", file=sys.stderr, flush=True)
    return entry


def driver_step(step, command, fn, on_ok, on_err, extra=None):
    started = now()
    try:
        resp = fn()
        if not isinstance(resp, (str, bool, int, float, type(None))):
            resp = rjson(resp)
        return record(step, command, resp, on_ok(resp), True, started, extra)
    except PyMongoError as e:
        ed = err_dict(e)
        return record(step, command, ed, on_err(ed), False, started, extra)


def psql(sql):
    argv = ["docker", "exec", CONTAINER, "psql", "-U", "documentdb", "-p", "9712", "-d", "postgres", "-tAc", sql]
    p = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    rows = [ln.split("|") for ln in p.stdout.splitlines() if ln.strip() and ln.strip() != "SET"]
    return argv, {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}, rows


def psql_step(step, sql, reading_fn):
    started = now()
    argv, resp, rows = psql(sql)
    try:
        reading = reading_fn(rows, resp)
    except Exception as e:  # noqa: BLE001
        reading = f"Output could not be parsed ({type(e).__name__}: {e}); raw output kept."
    resp["parsedRows"] = rows
    return record(step, " ".join(argv[:10]) + " " + json.dumps(sql), resp, reading, resp["returncode"] == 0, started)


def err_txt(e):
    return (f"code {e.get('code')} {e.get('codeName')} ('{(e.get('errmsg') or '').split('}:')[-1].strip()}'), "
            + ("errorLabels " + str(e.get("errorLabels")) if e.get("errorLabelsPresent") else "no errorLabels in the reply"))


def ci_counts(r):
    if isinstance(r, dict) and "numIndexesBefore" in r:
        return r
    for v in ((r or {}).get("raw") or {}).values():
        return v
    return {}


def main():
    env = load_env()
    secret = env.get("LOCAL_PASS")
    client = MongoClient(env["LOCAL_URI"], serverSelectionTimeoutMS=10000, tz_aware=True)
    db = client[DB]
    coll = db[COLL]
    report = {"test": "ttl-semantics rerun, supplementary probe (not in the tester's script)", "database": DB,
              "collection": COLL, "scriptStartedAt": iso(now())}
    try:
        pre = driver_step(f"does {DB} exist before the probe", f'"{DB}" in client.list_database_names()',
                          lambda: {"present": DB in client.list_database_names()},
                          lambda r: (f"{DB} is {'still present (unexpected)' if r['present'] else 'absent'}, so the "
                                     f"probe starts from nothing." if not r["present"] else
                                     f"{DB} already exists; the probe stops so it does not disturb another run."),
                          lambda e: f"listDatabases failed: {err_txt(e)}.")
        if pre["ok"] and pre["response"]["present"]:
            return

        # keep setup away from a pg_cron run at hh:mm:00 (same guard as the tester's script)
        n_ = now()
        sec = n_.second + n_.microsecond / 1e6
        waited = 0.0
        if sec >= 50 or sec < 2:
            waited = (63 - sec) if sec >= 50 else (3 - sec)
            time.sleep(waited)
        report["setupPhaseGuard"] = {"secondOfMinuteBeforeGuard": round(sec, 3), "waitedSeconds": round(waited, 3)}

        specs = [
            ("TTL index on exp", {"key": {"exp": 1}, "name": "exp_ttl", "expireAfterSeconds": 5}),
            ("TTL index on pexp with partialFilterExpression {purge: {$eq: true}}",
             {"key": {"pexp": 1}, "name": "pexp_ttl_pfe", "expireAfterSeconds": 5,
              "partialFilterExpression": {"purge": {"$eq": True}}}),
            ("plain (non-TTL) single-field index on plain, for op-class comparison",
             {"key": {"plain": 1}, "name": "plain_idx"}),
        ]
        for label, spec in specs:
            driver_step(f"create {label}", f'db.command("createIndexes", "{COLL}", indexes=[{json.dumps(spec)}])',
                        lambda spec=spec: db.command("createIndexes", COLL, indexes=[spec]),
                        lambda r, spec=spec: (f"Index {spec['name']} accepted (numIndexesBefore "
                                              f"{ci_counts(r).get('numIndexesBefore')} -> numIndexesAfter "
                                              f"{ci_counts(r).get('numIndexesAfter')})."),
                        lambda e, spec=spec: f"Index {spec['name']} rejected with {err_txt(e)}.")

        t_ins = now()
        past = t_ins - dt.timedelta(seconds=60)
        day = t_ins + dt.timedelta(days=1)
        past_ms = int(past.timestamp() * 1000)
        docs = [
            {"_id": "date_control", "kind": "exp = Date 60 s before insert (positive control)", "exp": past},
            {"_id": "int32_epoch_s", "kind": "exp = 32-bit integer epoch seconds 60 s before insert",
             "exp": int(past.timestamp())},
            {"_id": "double_epoch_ms", "kind": "exp = double epoch milliseconds 60 s before insert",
             "exp": float(past_ms)},
            {"_id": "decimal_epoch_ms", "kind": "exp = Decimal128 epoch milliseconds 60 s before insert",
             "exp": Decimal128(str(past_ms))},
            {"_id": "bson_timestamp", "kind": "exp = BSON Timestamp of a time 60 s before insert",
             "exp": Timestamp(int(past.timestamp()), 1)},
            {"_id": "objectid_past", "kind": "exp = ObjectId whose embedded time is 60 s before insert",
             "exp": ObjectId.from_datetime(past)},
            {"_id": "embedded_doc", "kind": "exp = {at: Date 60 s before insert} (embedded document)",
             "exp": {"at": past}},
            {"_id": "array_future_then_past", "kind": "exp = [Date 1 day after insert, Date 60 s before insert]",
             "exp": [day, past]},
            {"_id": "array_future_only", "kind": "exp = [Date 1 day after insert, Date 2 days after insert]",
             "exp": [day, day + dt.timedelta(days=1)]},
            {"_id": "empty_array", "kind": "exp = []", "exp": []},
            {"_id": "pfe_match", "kind": "pexp = Date 60 s before insert, purge = true (matches the filter)",
             "pexp": past, "purge": True},
            {"_id": "pfe_nomatch", "kind": "pexp = Date 60 s before insert, purge = false (outside the filter)",
             "pexp": past, "purge": False},
            {"_id": "pfe_flag_missing", "kind": "pexp = Date 60 s before insert, no purge field (outside the filter)",
             "pexp": past},
        ]
        expected = {"date_control": True, "int32_epoch_s": False, "double_epoch_ms": False,
                    "decimal_epoch_ms": False, "bson_timestamp": False, "objectid_past": False,
                    "embedded_doc": False, "array_future_then_past": True, "array_future_only": False,
                    "empty_array": False, "pfe_match": True, "pfe_nomatch": False, "pfe_flag_missing": False}
        ins = driver_step("insert the supplementary documents",
                          f'db.command("insert", "{COLL}", documents=<the {len(docs)} documents in insertedDocuments>, ordered=True)',
                          lambda: db.command("insert", COLL, documents=docs, ordered=True),
                          lambda r: f"{r.get('n')} documents inserted at {iso(t_ins)}; every exp/pexp value refers to a time 60 s before the insert.",
                          lambda e: f"insert failed with {err_txt(e)}.",
                          extra={"insertedDocuments": rjson(docs),
                                 "expectedToPurgeIfOnlyDatesInsideTheFilterExpire": expected})
        ins_done = parse_iso(ins["at"]) + dt.timedelta(milliseconds=ins["elapsedMs"])
        report["insertCompletedAt"] = iso(ins_done)

        # TTL createIndexes validation probes (no waiting needed)
        bad = [
            ("negative expireAfterSeconds", {"key": {"neg": 1}, "name": "neg_ttl", "expireAfterSeconds": -1}),
            ("fractional expireAfterSeconds 5.7", {"key": {"frac": 1}, "name": "frac_ttl", "expireAfterSeconds": 5.7}),
            ("expireAfterSeconds above the 32-bit range",
             {"key": {"big": 1}, "name": "big_ttl", "expireAfterSeconds": Int64(2147483648)}),
            ("TTL on _id", {"key": {"_id": 1}, "name": "id_ttl", "expireAfterSeconds": 5}),
            ("TTL on a hashed key", {"key": {"h": "hashed"}, "name": "h_ttl", "expireAfterSeconds": 5}),
        ]
        for label, spec in bad:
            spec_txt = json.dumps(rjson(spec))
            driver_step(f"createIndexes with {label}", f'db.command("createIndexes", "{COLL}", indexes=[{spec_txt}])',
                        lambda spec=spec: db.command("createIndexes", COLL, indexes=[spec]),
                        lambda r, spec=spec: (f"Accepted: index {spec['name']} created (numIndexesAfter "
                                              f"{ci_counts(r).get('numIndexesAfter')})."),
                        lambda e, label=label: f"{label[0].upper() + label[1:]} rejected with {err_txt(e)}.")

        driver_step("listIndexes after the supplementary createIndexes calls", f'db.command("listIndexes", "{COLL}")',
                    lambda: db.command("listIndexes", COLL),
                    lambda r: "listIndexes shows " + "; ".join(
                        f"{i.get('name')} key={i.get('key')}"
                        + (f" expireAfterSeconds={i.get('expireAfterSeconds')}" if "expireAfterSeconds" in i else "")
                        + (f" partialFilterExpression={i.get('partialFilterExpression')}" if "partialFilterExpression" in i else "")
                        + (f" storageEngine={i.get('storageEngine')}" if "storageEngine" in i else "")
                        for i in (r.get("cursor") or {}).get("firstBatch", [])) + ".",
                    lambda e: f"listIndexes failed with {err_txt(e)}.")

        cid_holder = {}

        def on_cid(rows, resp):
            m = {r[2]: r[0] for r in rows if len(r) >= 3}
            cid_holder.update(m)
            return f"Catalog rows for {DB}: " + ", ".join(f"{k} -> collection_id {v}" for k, v in m.items()) + "."
        psql_step("PostgreSQL catalog: collection ids of the probe database (read-only)",
                  f"select collection_id, database_name, collection_name from documentdb_api_catalog.collections "
                  f"where database_name = '{DB}' order by collection_id", on_cid)
        cid = cid_holder.get(COLL)
        if cid:
            def on_idx(rows, resp):
                return "PostgreSQL index definitions: " + " | ".join(r[0] for r in rows) + "."
            psql_step("PostgreSQL index definitions for the probe collection (read-only)",
                      f"select indexname || ' ==> ' || indexdef from pg_indexes where schemaname = 'documentdb_data' "
                      f"and tablename = 'documents_{cid}' order by indexname", on_idx)

        # poll every 5 s until two whole-minute pg_cron runs have passed after the insert (+8 s margin)
        first_min = (ins_done + dt.timedelta(minutes=1)).replace(second=0, microsecond=0)
        stop_at = first_min + dt.timedelta(minutes=1, seconds=8)
        polls, gone_at, prev = [], {}, None
        t0 = now()
        while True:
            t = now()
            try:
                ids = sorted(d["_id"] for d in coll.find({}, {"_id": 1}))
                gone = [x for x in prev if x not in ids] if prev is not None else []
                for g in gone:
                    gone_at[g] = {"lastSeenAt": polls[-1]["at"], "firstGoneAt": iso(t)}
                polls.append({"at": iso(t), "secondsAfterInsert": round((t - ins_done).total_seconds(), 1),
                              "count": len(ids), "gone": gone})
                prev = ids
            except PyMongoError as e:
                polls.append({"at": iso(t), "error": err_dict(e)})
            if t >= stop_at:
                break
            time.sleep(max(0.0, min(5.0, (stop_at - now()).total_seconds())))
        survivors = prev or []
        mism = {k: v for k, v in expected.items() if (k not in survivors) != v}
        record("poll every 5 s until two TTL runs have passed after the insert",
               f"sorted(d['_id'] for d in coll.find({{}}, {{'_id': 1}})) every 5 s from {iso(t0)} to {iso(stop_at)}",
               {"polls": polls, "goneAt": gone_at, "finalPresentIds": survivors,
                "mismatchesWithExpectation": mism},
               ("Purged: " + (", ".join(f"{k} (first missing at {v['firstGoneAt']})" for k, v in gone_at.items()) or "nothing")
                + "; still present: " + ", ".join(survivors) + "; "
                + ("every document behaved as expected if only Dates (and arrays holding one) expire and the "
                   "partial filter limits the purge." if not mism else f"MISMATCHES with that expectation: {mism}.")),
               all("error" not in p for p in polls), t0)

        driver_step("final contents of the probe collection", f"list(db.{COLL}.find({{}}))",
                    lambda: list(coll.find({})),
                    lambda r: "Survivors: " + "; ".join(f"{d['_id']} exp={json.dumps(d.get('exp', '<missing>'))}"
                                                        + (f" pexp={json.dumps(d['pexp'])} purge={d.get('purge', '<missing>')}" if 'pexp' in d else "")
                                                        for d in r) + ".",
                    lambda e: f"find failed with {err_txt(e)}.")

        since = iso(ins_done - dt.timedelta(seconds=90))

        def on_runs(rows, resp):
            return (f"{len(rows)} documentdb_ttl_task runs since {since}: "
                    + "; ".join(f"{r[3]} -> {r[4]} {r[2]}" for r in rows if len(r) >= 5) + ".")
        psql_step("pg_cron run history of the TTL job during the probe (read-only)",
                  "select d.jobid, d.runid, d.status, "
                  "to_char(d.start_time at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), "
                  "to_char(d.end_time at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), d.return_message "
                  "from cron.job_run_details d join cron.job j on j.jobid = d.jobid "
                  f"where j.jobname = 'documentdb_ttl_task' and d.start_time >= '{since}'::timestamptz "
                  "order by d.start_time", on_runs)

        cm = {"collMod": COLL, "index": {"name": "exp_ttl", "expireAfterSeconds": 7}}
        driver_step("collMod: change expireAfterSeconds of exp_ttl from 5 to 7",
                    f'db.command({json.dumps(cm)})',
                    lambda: db.command(cm),
                    lambda r: f"collMod accepted with reply {r}.",
                    lambda e: f"collMod rejected with {err_txt(e)}.")
        driver_step("listIndexes after collMod", f'db.command("listIndexes", "{COLL}")',
                    lambda: db.command("listIndexes", COLL),
                    lambda r: "exp_ttl now has expireAfterSeconds=" + str(
                        [i.get("expireAfterSeconds") for i in (r.get("cursor") or {}).get("firstBatch", [])
                         if i.get("name") == "exp_ttl"]) + ".",
                    lambda e: f"listIndexes failed with {err_txt(e)}.")
    finally:
        driver_step(f"drop the probe database {DB}", f'client["{DB}"].command("dropDatabase")',
                    lambda: db.command("dropDatabase"),
                    lambda r: f"dropDatabase returned {r}.",
                    lambda e: f"dropDatabase failed with {err_txt(e)}.")
        driver_step(f"confirm {DB} is gone", f'"{DB}" in client.list_database_names()',
                    lambda: {"present": DB in client.list_database_names()},
                    lambda r: (f"{DB} is no longer listed, so the probe left nothing behind." if not r["present"]
                               else f"{DB} is STILL listed after dropDatabase."),
                    lambda e: f"listDatabases failed with {err_txt(e)}.")
        client.close()
        report["steps"] = STEPS
        report["scriptFinishedAt"] = iso(now())
        report["caveat"] = ("Observed on documentdb-local pg17-1.2.0 (open-source engine and gateway, default settings); "
                            "evidence about that build only, not about the managed Azure DocumentDB service.")
        text = json.dumps(report, indent=2, default=str)
        if secret and secret in text:
            text = text.replace(secret, "<redacted>")
        with open(OUT, "w") as f:
            f.write(text + "\n")
        print(f"written: {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
