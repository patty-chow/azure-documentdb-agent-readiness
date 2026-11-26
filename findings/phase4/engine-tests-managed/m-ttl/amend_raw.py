#!/usr/bin/env python
"""m-ttl amendment (no server calls): corrects two readings in raw.json that run_m_ttl.py (first version) derived wrongly
from correct raw responses, then re-runs analyze.py. Raw responses are not changed.
1. createIndexes readings looked for numIndexesBefore/After at the top level, but the managed reply is
   {"raw": {"defaultShard": {...}}, "ok": 1}; the readings are regenerated from the recorded reply.
2. $$NOW offset: db.command() decodes dates naive (UTC); .timestamp() treated the naive value as Mac local time (UTC-8),
   giving 28800.011 s. Recomputed from the recorded $$NOW ISO value and client send/reply times."""
import json, os, sys, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
p = os.path.join(HERE, "raw.json")
raw = json.load(open(p))
am = raw.setdefault("amendments", [])
labels = {"create TTL index on exp (expireAfterSeconds 5)": "Single-field TTL index exp_ttl",
          "create second TTL index on exp2 (expireAfterSeconds 5)": "Second single-field TTL index exp2_ttl on the same collection"}
for s in raw["steps"]:
    if s["step"] in labels and s["ok"]:
        r = s["response"]
        shards = r.get("raw") or {"(top level)": r}
        parts = [f"{sh}: numIndexesBefore={d.get('numIndexesBefore')}, numIndexesAfter={d.get('numIndexesAfter')}, "
                 f"createdCollectionAutomatically={d.get('createdCollectionAutomatically')}" for sh, d in shards.items()]
        new = f"{labels[s['step']]} accepted (ok={r.get('ok')}); reply is per shard under raw: " + "; ".join(parts) + "."
        if s["reading"] != new:
            am.append({"step": s["step"], "field": "reading", "was": s["reading"], "now": new,
                       "why": "first-version reading read numIndexesBefore/After at the top level; the managed reply nests them under raw.defaultShard"})
            s["reading"] = new
    if s["step"] == "$$NOW clock check" and s["ok"]:
        r = s["response"]
        nv = dt.datetime.fromisoformat(r["reply"]["cursor"]["firstBatch"][0]["now"]["$date"])
        t0, t1 = dt.datetime.fromisoformat(r["clientSentAt"]), dt.datetime.fromisoformat(r["clientRepliedAt"])
        off = round((nv - (t0 + (t1 - t0) / 2)).total_seconds(), 3)
        if r.get("offsetSecondsServerMinusClient") != off:
            am.append({"step": s["step"], "field": "response.offsetSecondsServerMinusClient and reading", "was": r.get("offsetSecondsServerMinusClient"), "now": off,
                       "why": "db.command() returns a naive UTC datetime; the first version called .timestamp() on it, which applied the Mac's local UTC-8 offset (28800 s)"})
            r["offsetSecondsServerMinusClient"] = off
            s["reading"] = f"$$NOW minus client clock = {off} s (+/- {r.get('uncertaintySeconds')} s), matching the hello.localTime offset."
json.dump(raw, open(p, "w"), indent=1)
print(json.dumps(am, indent=1))
