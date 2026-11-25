#!/usr/bin/env python
"""Compare the tester's report (tester_snapshot/report.json, database t_concern) with this rerun's
raw_run.json (database t_concern_rerun), step by step. Volatile values (durations, request and
connection ids, lsid/txnNumber, transaction numbers in errmsg, timestamps) are normalised; the
database name is mapped t_concern_rerun -> t_concern before comparing. Writes compare.json."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
VOLATILE = {"duration_micros", "request_id", "server_connection_id", "elapsed_ms", "lsid", "txnNumber",
            "localTime", "connectionId", "run_started_at", "run_finished_at"}

def load(p, rename=False):
    t = open(p).read()
    if rename:
        t = t.replace("t_concern_rerun", "t_concern")
    return json.loads(t)

def norm(o, key=None):
    if isinstance(o, dict):
        return {k: norm(v, k) for k, v in o.items() if k not in VOLATILE}
    if isinstance(o, list):
        return [norm(v) for v in o]
    if isinstance(o, str):
        o = re.sub(r"Cannot continue transaction \d+", "Cannot continue transaction N", o)
        o = re.sub(r"server connection \[\d+\]", "server connection [N]", o)
        o = re.sub(r"\[\d{6,}\]", "[N]", o)
        o = re.sub(r"\d+(\.\d+)? ?ms\b", "<t>ms", o)
        o = re.sub(r"Up \d+ (minutes|seconds|hours)", "Up <t>", o)
        return o
    return o

def diff(a, b, path=""):
    out = []
    if type(a) != type(b):
        return [f"{path}: type {type(a).__name__} vs {type(b).__name__}: {json.dumps(a)[:200]} | {json.dumps(b)[:200]}"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f"{path}.{k}: only in rerun: {json.dumps(b[k])[:200]}")
            elif k not in b: out.append(f"{path}.{k}: only in tester: {json.dumps(a[k])[:200]}")
            else: out += diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: list length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path}: {json.dumps(a)[:300]} | {json.dumps(b)[:300]}")
    return out

t = load(os.path.join(HERE, "tester_snapshot", "report.json"))
r = load(os.path.join(HERE, "raw_run.json"), rename=True)
ts = {s["id"]: s for s in t["steps"]}
rs = {s["id"]: s for s in r["steps"]}
rows = []
for sid in list(ts) + [x for x in rs if x not in ts]:
    a, b = ts.get(sid), rs.get(sid)
    if a is None or b is None:
        rows.append({"step": sid, "status": "missing in " + ("tester" if a is None else "rerun")}); continue
    key_fields = {}
    for f in ("outcome", "verdict", "matches_decisions"):
        key_fields[f] = [a.get(f), b.get(f)]
    ea, eb = a.get("error") or {}, b.get("error") or {}
    for f in ("code", "codeName", "errmsg", "errorLabels"):
        key_fields["error." + f] = [ea.get(f), eb.get(f)]
    same_key = all(x == y for x, y in key_fields.values())
    full = diff(norm(a), norm(b))
    rows.append({"step": sid, "key_fields_identical": same_key, "key_fields": key_fields,
                 "normalised_differences": full})
summary = {
    "tester_report": os.path.join(HERE, "tester_snapshot", "report.json"),
    "rerun_report": os.path.join(HERE, "raw_run.json"),
    "steps_tester": len(ts), "steps_rerun": len(rs),
    "steps_with_identical_outcome_verdict_code_codeName_errmsg_errorLabels_matches": sum(1 for x in rows if x.get("key_fields_identical")),
    "steps_with_any_normalised_difference": [x["step"] for x in rows if x.get("normalised_differences")],
    "tally_tester": t["decisions_comparison_tally"], "tally_rerun": r["decisions_comparison_tally"],
    "headlines_identical": norm(t["headlines_by_spec_item"]) == norm(r["headlines_by_spec_item"]),
    "final_docs_identical": norm(t["final_documents_in_t_concern.c_before_drop"]) == norm(r["final_documents_in_t_concern.c_before_drop"]),
    "engine_identical_except_volatile": diff(norm({k: v for k, v in t["engine"].items()}), norm({k: v for k, v in r["engine"].items()})),
}
json.dump({"summary": summary, "rows": rows}, open(os.path.join(HERE, "compare.json"), "w"), indent=2)
print(json.dumps(summary, indent=1)[:4000])
for x in rows:
    if x.get("normalised_differences"):
        print("==", x["step"]); [print("   ", d[:400]) for d in x["normalised_differences"][:12]]
