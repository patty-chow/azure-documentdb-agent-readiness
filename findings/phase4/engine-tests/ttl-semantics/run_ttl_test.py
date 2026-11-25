#!/usr/bin/env python
"""ttl-semantics: TTL index behaviour on documentdb-local (database t_ttl).

Reads LOCAL_URI from ../local.env (never prints it). Writes report.json next to
this script. Rerunnable: drops and recreates only collections inside t_ttl.
"""
import json, os, sys, time, datetime as dt
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, OperationFailure

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "local.env")
DB = "t_ttl"
COLL = "docs"
POLL_EVERY = 15
POLL_MAX = 240
TTL_SECONDS = 5

def load_uri():
    env = {}
    with open(ENV) as f:
        for line in f:
            line = line.rstrip("\n")
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
    return env["LOCAL_URI"]

def now():
    return dt.datetime.now(dt.timezone.utc)

def iso(d):
    return d.isoformat(timespec="milliseconds")

def err_dict(e):
    d = {"type": type(e).__name__, "errmsg": str(e)}
    if isinstance(e, OperationFailure):
        det = e.details or {}
        d.update({"code": det.get("code", e.code), "codeName": det.get("codeName"),
                  "errmsg": det.get("errmsg", str(e)), "errorLabels": det.get("errorLabels", [])})
    return d

steps = []
def step(name, command, fn, reading_ok, reading_err=None):
    t0 = now()
    try:
        resp = fn()
        entry = {"step": name, "command": command, "at": iso(t0), "ok": True,
                 "response": resp, "reading": reading_ok(resp) if callable(reading_ok) else reading_ok}
    except PyMongoError as e:
        ed = err_dict(e)
        entry = {"step": name, "command": command, "at": iso(t0), "ok": False, "response": ed,
                 "reading": reading_err(ed) if callable(reading_err) else (reading_err or f"Failed with {ed.get('code')} {ed.get('codeName')}: {ed.get('errmsg')}")}
    steps.append(entry)
    print(json.dumps(entry, default=str)[:600], file=sys.stderr)
    return entry

def main():
    uri = load_uri()
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    adm = client.admin
    db = client[DB]
    coll = db[COLL]

    bi = step("buildInfo", "db.adminCommand({buildInfo: 1})", lambda: adm.command("buildInfo"),
              lambda r: f"Engine reports version {r.get('version')} (gitVersion {r.get('gitVersion')}); evidence below is about this open-source build only.")
    engine_version = (bi["response"] or {}).get("version") if bi["ok"] else None

    step("drop collection (clean rerun)", f"db.{COLL}.drop()", lambda: db.drop_collection(COLL),
         lambda r: "Collection dropped (or did not exist) so the run starts clean.")

    step("create TTL index on exp", f"db.{COLL}.createIndex({{exp: 1}}, {{expireAfterSeconds: {TTL_SECONDS}}})",
         lambda: coll.create_index([("exp", ASCENDING)], expireAfterSeconds=TTL_SECONDS, name="exp_ttl"),
         lambda r: f"Single-field TTL index '{r}' created with expireAfterSeconds={TTL_SECONDS}.")

    step("listIndexes after TTL create", f"db.{COLL}.getIndexes()", lambda: list(coll.list_indexes()),
         lambda r: f"{len(r)} index(es) listed; exp_ttl carries expireAfterSeconds={[i.get('expireAfterSeconds') for i in r if i.get('name')=='exp_ttl']}.")

    t_insert = now()
    docs = [
        {"_id": "past_date_60s", "kind": "Date 60 s in the past", "exp": t_insert - dt.timedelta(seconds=60)},
        {"_id": "future_date_90s", "kind": "Date 90 s in the future", "exp": t_insert + dt.timedelta(seconds=90)},
        {"_id": "string_value", "kind": "string", "exp": iso(t_insert - dt.timedelta(seconds=60))},
        {"_id": "number_value", "kind": "number (epoch ms, in the past)", "exp": int((t_insert - dt.timedelta(seconds=60)).timestamp() * 1000)},
        {"_id": "missing_field", "kind": "field absent"},
        {"_id": "array_of_dates", "kind": "array with one past Date and one future Date",
         "exp": [t_insert - dt.timedelta(seconds=60), t_insert + dt.timedelta(days=1)]},
        {"_id": "null_value", "kind": "null", "exp": None},
    ]
    ins = step("insertMany test documents", f"db.{COLL}.insertMany([...7 docs: past Date, future Date(+90s), string, number, missing, array of Dates, null...])",
               lambda: {"insertedIds": coll.insert_many(docs).inserted_ids, "insertedAt": iso(t_insert),
                        "expiryDeadlines": {"past_date_60s": iso(docs[0]["exp"] + dt.timedelta(seconds=TTL_SECONDS)),
                                            "future_date_90s": iso(docs[1]["exp"] + dt.timedelta(seconds=TTL_SECONDS))}},
               lambda r: "Seven documents inserted; the past Date is already eligible for purge, the future Date becomes eligible at insert+95 s.")

    step("create compound TTL index (two fields)", f"db.{COLL}.createIndex({{a: 1, b: 1}}, {{expireAfterSeconds: {TTL_SECONDS}}})",
         lambda: coll.create_index([("a", ASCENDING), ("b", ASCENDING)], expireAfterSeconds=TTL_SECONDS, name="ab_ttl"),
         lambda r: f"UNEXPECTED: compound TTL index '{r}' was accepted.",
         lambda e: f"Compound TTL index rejected with code {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

    step("create second TTL index on another field", f"db.{COLL}.createIndex({{exp2: 1}}, {{expireAfterSeconds: {TTL_SECONDS}}})",
         lambda: coll.create_index([("exp2", ASCENDING)], expireAfterSeconds=TTL_SECONDS, name="exp2_ttl"),
         lambda r: f"Second TTL index '{r}' on a different field accepted; multiple single-field TTL indexes per collection are allowed.",
         lambda e: f"Second TTL index rejected with code {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

    step("create TTL index with non-numeric expireAfterSeconds", f"db.{COLL}.createIndex({{exp3: 1}}, {{expireAfterSeconds: 'abc'}})",
         lambda: coll.create_index([("exp3", ASCENDING)], expireAfterSeconds="abc", name="exp3_bad"),
         lambda r: f"UNEXPECTED: non-numeric expireAfterSeconds accepted as '{r}'.",
         lambda e: f"Non-numeric expireAfterSeconds rejected with code {e.get('code')} {e.get('codeName')}: {e.get('errmsg')}")

    step("listIndexes after all createIndex attempts", f"db.{COLL}.getIndexes()", lambda: list(coll.list_indexes()),
         lambda r: f"Indexes present: {[i.get('name') for i in r]}.")

    # Poll
    polls = []
    present_prev = None
    disappeared = {}
    t_poll0 = now()
    deadline = t_poll0 + dt.timedelta(seconds=POLL_MAX)
    second_probe_inserted = None
    i = 0
    while True:
        t = now()
        ids = sorted(d["_id"] for d in coll.find({}, {"_id": 1}))
        elapsed_insert = (t - t_insert).total_seconds()
        gone_now = [x for x in (present_prev or []) if x not in ids] if present_prev is not None else []
        for g in gone_now:
            disappeared[g] = {"observedGoneAt": iso(t), "secondsAfterInsert": round(elapsed_insert, 1),
                              "windowStart": polls[-1]["at"] if polls else iso(t_poll0)}
        polls.append({"poll": i, "at": iso(t), "secondsAfterInsert": round(elapsed_insert, 1), "count": len(ids), "present": ids, "goneSinceLastPoll": gone_now})
        print(f"poll {i} +{elapsed_insert:.0f}s count={len(ids)} gone={gone_now}", file=sys.stderr)
        present_prev = ids
        # once the first purge is seen, insert a second already-expired probe to measure cadence
        if second_probe_inserted is None and "past_date_60s" in disappeared:
            tp = now()
            coll.insert_one({"_id": "probe2_past_date", "kind": "second probe, Date 60 s in the past, inserted after first purge", "exp": tp - dt.timedelta(seconds=60)})
            second_probe_inserted = iso(tp)
            present_prev = present_prev + ["probe2_past_date"]
            polls[-1]["probe2InsertedAt"] = second_probe_inserted
        # a third probe after the second one goes, if time permits
        if second_probe_inserted is not None and "probe2_past_date" in disappeared and "probe3_past_date" not in disappeared and not any("probe3InsertedAt" in p for p in polls) and (deadline - now()).total_seconds() > 75:
            tp = now()
            coll.insert_one({"_id": "probe3_past_date", "kind": "third probe, Date 60 s in the past", "exp": tp - dt.timedelta(seconds=60)})
            present_prev = present_prev + ["probe3_past_date"]
            polls[-1]["probe3InsertedAt"] = iso(tp)
        i += 1
        if now() >= deadline:
            break
        time.sleep(POLL_EVERY)

    final_docs = list(coll.find({}, {"_id": 1, "kind": 1}))
    steps.append({"step": "poll collection every 15 s for up to 4 min", "command": f"repeat every {POLL_EVERY}s: db.{COLL}.find({{}}, {{_id: 1}})  (plus insertOne of probe docs after each observed purge)",
                  "at": iso(t_poll0), "ok": True,
                  "response": {"polls": polls, "disappeared": disappeared, "finalDocuments": final_docs},
                  "reading": ("Disappeared: " + (", ".join("%s at +%ss" % (k, v["secondsAfterInsert"]) for k, v in disappeared.items()) or "nothing")
                              + "; still present at end: " + str([d["_id"] for d in final_docs]) + ".")})

    # Compute purge timing
    cadence = {}
    for pid, inserted_key in (("past_date_60s", iso(t_insert)), ("probe2_past_date", second_probe_inserted), ("probe3_past_date", next((p.get("probe3InsertedAt") for p in polls if p.get("probe3InsertedAt")), None))):
        if pid in disappeared and inserted_key:
            ins_t = dt.datetime.fromisoformat(inserted_key)
            gone_lo = dt.datetime.fromisoformat(disappeared[pid]["windowStart"])
            gone_hi = dt.datetime.fromisoformat(disappeared[pid]["observedGoneAt"])
            cadence[pid] = {"insertedAt": inserted_key, "alreadyEligibleAtInsert": True,
                            "goneBetweenSecondsAfterInsert": [round((gone_lo - ins_t).total_seconds(), 1), round((gone_hi - ins_t).total_seconds(), 1)]}
    if "future_date_90s" in disappeared:
        elig = docs[1]["exp"] + dt.timedelta(seconds=TTL_SECONDS)
        gone_lo = dt.datetime.fromisoformat(disappeared["future_date_90s"]["windowStart"])
        gone_hi = dt.datetime.fromisoformat(disappeared["future_date_90s"]["observedGoneAt"])
        cadence["future_date_90s"] = {"eligibleAt": iso(elig), "goneBetweenSecondsAfterEligible": [round((gone_lo - elig).total_seconds(), 1), round((gone_hi - elig).total_seconds(), 1)]}

    report = {
        "test": "ttl-semantics", "database": DB, "collection": COLL,
        "target": "documentdb-local container ddb-engine-test on localhost:10260 (open-source engine + gateway)",
        "engine_version": engine_version, "buildInfo": bi["response"] if bi["ok"] else None,
        "ranAt": iso(t_insert), "pollEverySeconds": POLL_EVERY, "pollMaxSeconds": POLL_MAX, "expireAfterSeconds": TTL_SECONDS,
        "steps": steps, "purgeTiming": cadence,
        "caveat": "Everything here was observed on documentdb-local at the buildInfo version above. It is evidence about the open-source engine and gateway defaults (pg_cron every-minute documentdb_ttl_task), not proof of managed Azure DocumentDB behaviour, whose GUC values are not published.",
    }
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps({"purgeTiming": cadence, "disappeared": disappeared, "final": [d["_id"] for d in final_docs]}, default=str, indent=1))

if __name__ == "__main__":
    main()
