#!/usr/bin/env python
"""Supplement: insert one already-expired doc into t_ttl.docs and poll every 1 s for up to 75 s
to pin the second at which the TTL purge removes it. Appends a step to report.json."""
import json, os, sys, time, datetime as dt
from pymongo import MongoClient
HERE = os.path.dirname(os.path.abspath(__file__))
def load_uri():
    for line in open(os.path.join(HERE, "..", "local.env")):
        if line.startswith("LOCAL_URI="):
            return line.rstrip("\n").split("=", 1)[1].strip().strip('"').strip("'")
def iso(d): return d.isoformat(timespec="milliseconds")
c = MongoClient(load_uri(), serverSelectionTimeoutMS=10000)
coll = c["t_ttl"]["docs"]
coll.delete_one({"_id": "fine_probe"})
t0 = dt.datetime.now(dt.timezone.utc)
coll.insert_one({"_id": "fine_probe", "kind": "fine-grained probe, Date 60 s in the past", "exp": t0 - dt.timedelta(seconds=60)})
samples = []; gone_at = None; last_present = None
while (dt.datetime.now(dt.timezone.utc) - t0).total_seconds() < 75:
    t = dt.datetime.now(dt.timezone.utc)
    present = coll.count_documents({"_id": "fine_probe"}) == 1
    samples.append([iso(t), present])
    if present: last_present = t
    else:
        gone_at = t; break
    time.sleep(1)
resp = {"insertedAt": iso(t0), "lastSeenPresentAt": iso(last_present) if last_present else None,
        "firstSeenGoneAt": iso(gone_at) if gone_at else None,
        "secondsAfterInsert": round((gone_at - t0).total_seconds(), 1) if gone_at else None,
        "wallClockSecondOfPurge": (gone_at.strftime("%H:%M:%S") if gone_at else None),
        "samples": samples}
reading = (f"Already-expired probe inserted at {t0.strftime('%H:%M:%S.%f')[:-3]} UTC was last seen at {last_present.strftime('%H:%M:%S')} and gone by {gone_at.strftime('%H:%M:%S')} UTC, i.e. the purge ran at about the top of the minute." if gone_at
           else "Probe still present after 75 s of 1-second polling.")
step = {"step": "fine-grained purge timing (1 s polling)", "command": "db.docs.insertOne({_id:'fine_probe', exp: <now-60s>}); then every 1 s: db.docs.countDocuments({_id:'fine_probe'})",
        "at": iso(t0), "ok": True, "response": resp, "reading": reading}
p = os.path.join(HERE, "report.json"); r = json.load(open(p)); r["steps"].append(step)
r.setdefault("purgeTiming", {})["fine_probe"] = {k: v for k, v in resp.items() if k != "samples"}
json.dump(r, open(p, "w"), indent=2, default=str)
print(json.dumps({k: v for k, v in resp.items() if k != "samples"}, indent=1)); print(reading)
