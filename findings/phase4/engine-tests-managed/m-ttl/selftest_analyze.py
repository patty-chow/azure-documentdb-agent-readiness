#!/usr/bin/env python
"""Offline self-test of analyze.py on a synthetic run (no server calls). mode=top: purge at every minute boundary;
mode=continuous: purge eligible docs within 2 s at any phase."""
import sys, json, datetime as dt, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A
iso, P, S = A.iso, A.P, A.S
mode = sys.argv[1] if len(sys.argv) > 1 else "top"
t_ins = dt.datetime(2026, 11, 25, 21, 0, 7, 12000, tzinfo=dt.timezone.utc)
past = t_ins - S(60); fut = t_ins + S(90)
docs_meta = [
 {"_id": "past_date_60s", "kind": "k", "ttlField": "exp", "valueType": "date", "value": None, "eligibleAt": iso(past + S(5)), "expectedToExpire": True},
 {"_id": "future_date_90s", "kind": "k", "ttlField": "exp", "valueType": "date", "value": None, "eligibleAt": iso(fut + S(5)), "expectedToExpire": True},
 {"_id": "string_value", "kind": "k", "ttlField": "exp", "valueType": "string", "value": None, "eligibleAt": None, "expectedToExpire": False},
 {"_id": "exp2_past_date_60s", "kind": "k", "ttlField": "exp2", "valueType": "date", "value": None, "eligibleAt": iso(past + S(5)), "expectedToExpire": True},
]
alive = {d["_id"]: (t_ins, P(d["eligibleAt"]) if d["eligibleAt"] else None) for d in docs_meta}
raw = {"database": "mt_ttl", "collection": "docs", "meta": {}, "steps": [], "clock": [{"offsetSecondsServerMinusClient": 0.006}],
       "insert": {"sentAt": iso(t_ins), "repliedAt": iso(t_ins + S(0.08)), "ok": True, "documents": docs_meta}, "polls": []}
last = [t_ins]
def purge_until(t):
    if mode == "top":
        for b in A.minute_boundaries(last[0], t):
            for k, (ti, el) in list(alive.items()):
                if el is not None and el < b and ti < b: del alive[k]
    else:
        for k, (ti, el) in list(alive.items()):
            if el is not None and max(el, ti) + S(2) < t: del alive[k]
    last[0] = t
for k in range(21):
    tb = t_ins + S(0.08 + 15 * k); purge_until(tb)
    p = {"poll": k, "sentAt": iso(tb), "repliedAt": iso(tb + S(0.08)), "secondsAfterInsert": round(15*k, 1), "ok": True, "present": sorted(alive)}
    if 1 <= k <= 15:
        tp = tb + S(0.09); pid = f"probe_{k:02d}"
        p["probeInserted"] = {"_id": pid, "kind": "probe", "exp": iso(tp - S(60)), "eligibleAt": iso(tp - S(55)), "sentAt": iso(tp), "repliedAt": iso(tp + S(0.08)), "ok": True}
        alive[pid] = (tp, tp - S(55))
    raw["polls"].append(p)
tf = t_ins + S(300.5); raw["fine"] = {"insertSentAt": iso(tf), "samples": []}
alive["fine_probe"] = (tf, tf - S(55))
t = tf + S(0.1)
while t < tf + S(75):
    purge_until(t); pres = "fine_probe" in alive
    raw["fine"]["samples"].append({"sentAt": iso(t), "repliedAt": iso(t + S(0.08)), "present": pres})
    if not pres: break
    t += S(1)
docs, events, ticks, cadence, lag, fine_res, off, oss = A.analyze(raw)
print(json.dumps({"cadence": {k: v for k, v in cadence.items() if k != "intervalsBetweenConsecutivePurgeEvents"},
                  "intervals": cadence["intervalsBetweenConsecutivePurgeEvents"][:3],
                  "lag": {k: v for k, v in lag.items() if k != "perDocument"}, "fine": fine_res}, indent=1, default=str))
for r in docs[:6]: print("-", r["reading"]); print("   ", r["vs_open_source"])
print(len(ticks), sorted(set(t["verdict"] for t in ticks)))
